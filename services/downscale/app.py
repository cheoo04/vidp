"""Service Downscale : réduit la résolution de la vidéo pour alléger les étapes suivantes.

>>> STUB : copie la vidéo sans la réduire, et renvoie des métadonnées factices. À remplacer (voir TODO). <<<
Contrat : docs/04-contrat-api.md
"""
import shutil
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="vidp-downscale")


class Job(BaseModel):
    job_id: str
    video: str
    language: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process")
def process(job: Job):
    src = Path(job.video)
    if not src.is_file():
        raise HTTPException(404, f"vidéo introuvable : {src}")
    t0 = time.monotonic()
    dst = src.parent / "downscaled.mp4"

    # TODO (responsable vision + énergie, P3) : vraie réduction. Piste conseillée :
    #  1. installer ffmpeg dans l'image (Dockerfile : apt-get install ffmpeg)
    #  2. réencoder en 360p (hauteur réglable par variable d'environnement), en mp4 lisible
    #     par un navigateur (H.264 + AAC, option -movflags +faststart)
    #  3. lire largeur / hauteur / durée / taille avant et après avec ffprobe (sortie JSON)
    #  4. bonus énergie : comparer presets et qualités (-preset, -crf) en temps et en Watts
    shutil.copy(src, dst)
    fake = {"width": 0, "height": 0, "duration_s": 0.0, "size_bytes": src.stat().st_size}

    return {
        "service": "downscale",
        "outputs": {"video": str(dst)},
        "metadata": {"original": fake, "downscaled": fake},
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "stub": True,
    }
