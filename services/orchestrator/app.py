"""Orchestrateur du pipeline local.

Surveille DATA_DIR/input, et pour chaque nouvelle vidéo :
  downscale -> langident -> subtitle -> animal -> envoi au cloud (CLOUD_URL)
Il informe le cloud de l'avancement (pour afficher « en cours de traitement »).

Si CLOUD_URL est vide : mode hors-ligne, le résultat reste dans DATA_DIR/done/<job_id>/.
Contrat : docs/04-contrat-api.md
"""
import json
import logging
import os
import re
import shutil
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
CLOUD_URL = os.getenv("CLOUD_URL", "").rstrip("/")
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "3"))
VIDEO_EXT = {".mp4", ".mkv", ".mov", ".webm", ".avi"}

# Ordre du pipeline : (nom, URL du service). Les URL viennent de variables d'environnement
# pour pouvoir tourner aussi bien dans docker compose que dans Kubernetes.
STEPS = [
    ("downscale", os.getenv("DOWNSCALE_URL", "http://downscale:8000")),
    ("langident", os.getenv("LANGIDENT_URL", "http://langident:8000")),
    ("subtitle", os.getenv("SUBTITLE_URL", "http://subtitle:8000")),
    ("animal", os.getenv("ANIMAL_URL", "http://animal:8000")),
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [orchestrator] %(message)s")
log = logging.getLogger()


def make_job_id(filename: str) -> str:
    slug = unicodedata.normalize("NFKD", Path(filename).stem).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-").lower()[:40] or "video"
    return f"{datetime.now():%Y%m%d-%H%M%S}-{slug}"


def notify_cloud(client: httpx.Client, job_id: str, filename: str, status: str, step: str | None):
    """Prévient le cloud de l'avancement. Une panne du cloud ne doit pas bloquer le pipeline."""
    if not CLOUD_URL:
        return
    try:
        client.post(f"{CLOUD_URL}/jobs/{job_id}/status",
                    json={"filename": filename, "status": status, "step": step}, timeout=5)
    except httpx.HTTPError as e:
        log.warning("cloud injoignable pour le statut (%s) : %s", job_id, e)


def upload_to_cloud(client: httpx.Client, job_dir: Path, metadata: dict):
    files = {"video": ("video.mp4", open(job_dir / "downscaled.mp4", "rb"), "video/mp4")}
    if (job_dir / "subtitles.vtt").exists():
        files["subtitles"] = ("subtitles.vtt", open(job_dir / "subtitles.vtt", "rb"), "text/vtt")
    try:
        r = client.post(f"{CLOUD_URL}/videos", data={"metadata": json.dumps(metadata)},
                        files=files, timeout=300)
        r.raise_for_status()
    finally:
        for _, f, _ in files.values():
            f.close()


def process(client: httpx.Client, src: Path):
    job_id = make_job_id(src.name)
    job_dir = DATA_DIR / "work" / job_id
    job_dir.mkdir(parents=True)
    source = job_dir / f"source{src.suffix.lower()}"
    shutil.move(src, source)
    log.info("nouveau job %s (%s)", job_id, src.name)

    metadata = {
        "job_id": job_id,
        "filename": src.name,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timings_ms": {},
    }
    video, language = str(source), None
    try:
        for name, url in STEPS:
            notify_cloud(client, job_id, src.name, "processing", name)
            payload = {"job_id": job_id, "video": video, "language": language}
            r = client.post(f"{url}/process", json=payload, timeout=1800)
            if r.status_code != 200:
                raise RuntimeError(f"{name} a répondu {r.status_code} : {r.text[:300]}")
            res = r.json()
            metadata["timings_ms"][name] = res["duration_ms"]
            if res.get("stub"):
                metadata.setdefault("stubs", []).append(name)

            if name == "downscale":
                metadata["video"] = res["metadata"]
                video = res["outputs"]["video"]  # les étapes suivantes travaillent sur la petite vidéo
            elif name == "langident":
                metadata["language"] = res["metadata"]
                language = res["metadata"].get("language")
            elif name == "subtitle":
                metadata["subtitles"] = res["metadata"]
            elif name == "animal":
                metadata["animals"] = res["metadata"]
            log.info("  %-9s ok en %d ms", name, res["duration_ms"])

        (job_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        if CLOUD_URL:
            notify_cloud(client, job_id, src.name, "processing", "upload")
            upload_to_cloud(client, job_dir, metadata)
            log.info("  envoyé au cloud")
        shutil.move(job_dir, DATA_DIR / "done" / job_id)
        log.info("job %s terminé", job_id)
    except Exception as e:  # on isole chaque vidéo : une erreur ne doit pas arrêter le pipeline
        log.error("job %s en échec : %s", job_id, e)
        (job_dir / "error.txt").write_text(str(e))
        notify_cloud(client, job_id, src.name, "failed", None)
        shutil.move(job_dir, DATA_DIR / "failed" / job_id)


def main():
    for d in ("input", "work", "done", "failed"):
        (DATA_DIR / d).mkdir(parents=True, exist_ok=True)
    log.info("surveillance de %s/input (cloud : %s)", DATA_DIR, CLOUD_URL or "hors-ligne")
    sizes: dict[Path, int] = {}
    with httpx.Client() as client:
        while True:
            for f in sorted((DATA_DIR / "input").iterdir()):
                if f.suffix.lower() not in VIDEO_EXT:
                    continue
                size = f.stat().st_size
                # on attend que la taille soit stable 2 fois de suite = copie du fichier terminée
                if sizes.get(f) == size and size > 0:
                    sizes.pop(f)
                    process(client, f)
                else:
                    sizes[f] = size
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
