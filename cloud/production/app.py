"""Video Production : reçoit vidéo + métadonnées du pipeline local et les stocke.

>>> STUB : stocke tout sur le disque du container + une liste en mémoire. <<<
Ça suffit pour que le pipeline marche de bout en bout, mais :
  - tout est perdu au redémarrage du container ;
  - avec 2 copies derrière le load balancer, chaque copie a SA liste => incohérent.
Le service doit donc devenir « stateless » (ne rien garder en mémoire).

TODO (responsable cloud applicatif, P4) :
  1. fichiers  -> un bucket S3 (MinIO en local, même protocole qu'AWS : bibliothèque boto3)
  2. index     -> une table PostgreSQL `videos` (bibliothèque psycopg)
  3. ajouter l'en-tête `X-Served-By: <hostname>` à chaque réponse (preuve du load balancing)
  4. ajouter les services MinIO et PostgreSQL dans cloud/docker-compose.yml, puis 2 répliques

Contrat à respecter : docs/04-contrat-api.md (section 4)
"""
import json
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

HOSTNAME = socket.gethostname()
STORAGE = Path("/tmp/vidp-storage")  # STUB : à remplacer par S3

# STUB : à remplacer par PostgreSQL. job_id -> {job_id, filename, status, step, metadata, updated_at}
VIDEOS: dict[str, dict] = {}

app = FastAPI(title="vidp-production")


def save(job_id: str, filename: str, status: str, step: str | None, metadata: dict | None):
    old = VIDEOS.get(job_id, {})
    VIDEOS[job_id] = {
        "job_id": job_id,
        "filename": filename,
        "status": status,
        "step": step,
        "metadata": metadata if metadata is not None else old.get("metadata"),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


@app.get("/health")
def health():
    return {"status": "ok", "served_by": HOSTNAME}


class Status(BaseModel):
    filename: str
    status: str
    step: str | None = None


@app.post("/jobs/{job_id}/status")
def set_status(job_id: str, body: Status):
    if body.status not in ("processing", "failed"):
        raise HTTPException(422, "status doit être processing ou failed")
    save(job_id, body.filename, body.status, body.step, None)
    return {"job_id": job_id, "status": body.status}


@app.post("/videos")
def upload(metadata: str = Form(...), video: UploadFile = ..., subtitles: UploadFile | None = None):
    meta = json.loads(metadata)
    job_id = meta["job_id"]
    folder = STORAGE / job_id
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "video.mp4", "wb") as f:
        shutil.copyfileobj(video.file, f)
    if subtitles is not None:
        with open(folder / "subtitles.vtt", "wb") as f:
            shutil.copyfileobj(subtitles.file, f)
    save(job_id, meta.get("filename", job_id), "done", None, meta)
    return {"job_id": job_id, "status": "done"}


@app.get("/videos")
def list_videos():
    return sorted(VIDEOS.values(), key=lambda v: v["updated_at"], reverse=True)


def send(path: Path, media_type: str):
    if not path.is_file():
        raise HTTPException(404, "fichier introuvable")
    return FileResponse(path, media_type=media_type)


@app.get("/videos/{job_id}/video")
def get_video(job_id: str):
    return send(STORAGE / job_id / "video.mp4", "video/mp4")


@app.get("/videos/{job_id}/subtitles")
def get_subtitles(job_id: str):
    return send(STORAGE / job_id / "subtitles.vtt", "text/vtt")
