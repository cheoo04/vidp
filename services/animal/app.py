"""Service Animal detect : détecte les animaux présents dans la vidéo.

>>> STUB : renvoie une liste vide. À remplacer (voir TODO). <<<
Contrat : docs/04-contrat-api.md
"""
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="vidp-animal")

# Classes « animaux » du jeu de données COCO (celui sur lequel YOLO est entraîné)
COCO_ANIMALS = {"bird", "cat", "dog", "horse", "sheep", "cow",
                "elephant", "bear", "zebra", "giraffe"}


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

    # TODO (responsable vision) : vraie détection. Piste conseillée :
    #  1. extraire 1 image toutes les 2 s :  ffmpeg -i video -vf fps=0.5 frame_%04d.jpg
    #  2. lancer un détecteur léger (YOLOv8n / YOLO11n, idéalement exporté en ONNX
    #     et exécuté avec onnxruntime : beaucoup plus léger que PyTorch -> moins d'énergie)
    #  3. garder les détections dont le label est dans COCO_ANIMALS et confiance > 0.5
    #  4. agréger par label : count, first_seen_s, max_confidence
    animals: list[dict] = []
    frames_analyzed = 0

    return {
        "service": "animal",
        "outputs": {},
        "metadata": {"animals": animals, "frames_analyzed": frames_analyzed},
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "stub": True,
    }
