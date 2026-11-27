"""Service LangIdent : détecte la langue parlée dans la vidéo.

>>> STUB : renvoie une langue factice. À remplacer (voir TODO). <<<
Contrat : docs/04-contrat-api.md
"""
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="vidp-langident")


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

    # TODO (responsable audio) : vraie détection de langue. Piste conseillée :
    #   from faster_whisper import WhisperModel
    #   model = WhisperModel("tiny", device="cpu", compute_type="int8")  # charger UNE fois, hors de la fonction
    #   _, info = model.transcribe(str(src), beam_size=1)  # ne lit que le début pour la langue
    #   language, confidence = info.language, info.language_probability
    language, confidence = "fr", 0.0

    return {
        "service": "langident",
        "outputs": {},
        "metadata": {"language": language, "confidence": confidence},
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "stub": True,
    }
