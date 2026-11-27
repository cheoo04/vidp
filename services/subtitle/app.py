"""Service Subtitle : génère les sous-titres (WebVTT) de la vidéo.

>>> STUB : écrit un fichier .vtt factice. À remplacer (voir TODO). <<<
Contrat : docs/04-contrat-api.md
"""
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="vidp-subtitle")


class Job(BaseModel):
    job_id: str
    video: str
    language: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


def ts(seconds: float) -> str:
    """12.5 -> '00:00:12.500' (format horaire WebVTT)."""
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


@app.post("/process")
def process(job: Job):
    src = Path(job.video)
    if not src.is_file():
        raise HTTPException(404, f"vidéo introuvable : {src}")
    t0 = time.monotonic()

    # TODO (responsable audio) : vraie transcription. Piste conseillée :
    #   from faster_whisper import WhisperModel
    #   model = WhisperModel("base", device="cpu", compute_type="int8")  # charger UNE fois
    #   segments, _ = model.transcribe(str(src), language=job.language, vad_filter=True)
    #   segments = [(s.start, s.end, s.text.strip()) for s in segments]
    segments = [(0.0, 4.0, "(sous-titres pas encore implémentés)")]

    dst = src.parent / "subtitles.vtt"
    lines = ["WEBVTT", ""]
    for i, (start, end, text) in enumerate(segments, 1):
        lines += [str(i), f"{ts(start)} --> {ts(end)}", text, ""]
    dst.write_text("\n".join(lines), encoding="utf-8")

    return {
        "service": "subtitle",
        "outputs": {"subtitles": str(dst)},
        "metadata": {"format": "vtt", "segments": len(segments), "language": job.language},
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "stub": True,
    }
