# Contrat d'API entre les services

> **Règle d'or :** tant qu'un service respecte ce contrat, son code interne peut changer
> sans casser les autres. Toute modification de ce fichier = discussion d'équipe + PR dédiée.

## 1. Dossier partagé (« Local video store »)

Tous les services du pipeline local voient le **même dossier** monté en `/data`
(un volume Docker en local, un PersistentVolume dans Kubernetes).

```
/data/
├── input/            ← on dépose les vidéos ici (.mp4 .mkv .mov .webm)
├── work/<job_id>/    ← dossier de travail d'une vidéo en cours
│   ├── source.mp4        (vidéo originale, déplacée par l'orchestrateur)
│   ├── downscaled.mp4    (écrit par downscale)
│   ├── subtitles.vtt     (écrit par subtitle)
│   └── metadata.json     (écrit par l'orchestrateur à la fin)
├── done/<job_id>/    ← jobs terminés (déplacés par l'orchestrateur)
└── failed/<job_id>/  ← jobs en erreur (+ error.txt)
```

On **ne transfère jamais la vidéo dans les requêtes HTTP** entre services locaux :
on transfère seulement le **chemin** du fichier. C'est plus rapide et ça consomme moins.

`job_id` = `AAAAMMJJ-HHMMSS-<nom-du-fichier-simplifié>`, ex. `20261127-181500-chat-qui-dort`.

## 2. Services du pipeline local

Chaque service est un serveur HTTP (FastAPI, port **8000** dans son container) qui expose :

| Méthode | Chemin     | Rôle |
|---------|------------|------|
| GET     | `/health`  | renvoie `{"status": "ok"}` (utilisé par Docker/Kubernetes) |
| POST    | `/process` | traite une vidéo |

### Requête `POST /process`

```json
{
  "job_id": "20261127-181500-chat-qui-dort",
  "video": "/data/work/20261127-181500-chat-qui-dort/downscaled.mp4",
  "language": "fr"
}
```

- `video` : chemin absolu de la vidéo à traiter.
  - `downscale` reçoit `source.mp4`, tous les autres reçoivent `downscaled.mp4`
    (plus petite, donc traitement plus rapide et moins d'énergie).
- `language` : optionnel, rempli par l'orchestrateur après `langident` (utile pour `subtitle`).

### Réponse (HTTP 200)

```json
{
  "service": "langident",
  "outputs":  { "...": "chemins des fichiers produits (peut être vide)" },
  "metadata": { "...": "données propres au service, voir ci-dessous" },
  "duration_ms": 1234,
  "stub": false
}
```

En cas d'erreur : code HTTP 4xx/5xx avec `{"detail": "message lisible"}`.
`stub: true` signale une implémentation factice (à remplacer).

### `metadata` attendu par service

| Service    | `outputs`                       | `metadata` |
|------------|---------------------------------|------------|
| downscale  | `{"video": ".../downscaled.mp4"}` | `{"original": {width,height,duration_s,size_bytes}, "downscaled": {idem}}` |
| langident  | `{}`                            | `{"language": "fr", "confidence": 0.97}` (code ISO 639-1) |
| subtitle   | `{"subtitles": ".../subtitles.vtt"}` | `{"format": "vtt", "segments": 42, "language": "fr"}` |
| animal     | `{}`                            | `{"animals": [{"label": "dog", "count": 3, "first_seen_s": 1.5, "max_confidence": 0.91}], "frames_analyzed": 60}` |

Sous-titres au format **WebVTT** (`.vtt`) car c'est le format que la balise HTML
`<track>` sait afficher directement dans la page web.

## 3. Le fichier final `metadata.json` (assemblé par l'orchestrateur)

```json
{
  "job_id": "20261127-181500-chat-qui-dort",
  "filename": "chat qui dort.mp4",
  "created_at": "2026-11-27T18:15:00Z",
  "video":     { "original": {...}, "downscaled": {...} },
  "language":  { "language": "fr", "confidence": 0.97 },
  "subtitles": { "format": "vtt", "segments": 42, "language": "fr" },
  "animals":   { "animals": [...], "frames_analyzed": 60 },
  "timings_ms": { "downscale": 2100, "langident": 900, "subtitle": 8000, "animal": 3000 }
}
```

## 4. API du cloud (« Video Production », derrière le load balancer)

Base : `CLOUD_URL` (ex. `http://<ip-du-load-balancer>:8000`).

| Méthode | Chemin | Corps / réponse |
|---------|--------|-----------------|
| GET  | `/health` | `{"status":"ok","served_by":"<hostname>"}` |
| POST | `/jobs/{job_id}/status` | JSON `{"filename": "...", "status": "processing", "step": "subtitle"}` — `status` ∈ `processing`, `failed` |
| POST | `/videos` | **multipart** : `metadata` (texte JSON), `video` (fichier), `subtitles` (fichier, optionnel) → `{"job_id": "...", "status": "done"}` |
| GET  | `/videos` | liste : `[{"job_id","filename","status","step","metadata","updated_at"}]` |
| GET  | `/videos/{job_id}/video` | le fichier vidéo (mp4) |
| GET  | `/videos/{job_id}/subtitles` | le fichier `.vtt` |

Chaque réponse porte un en-tête `X-Served-By: <hostname>` pour **prouver le load balancing** pendant la démo.

Stockage : fichiers dans un bucket **S3** (`<job_id>/video.mp4`, `<job_id>/subtitles.vtt`,
`<job_id>/metadata.json`), index dans une base **PostgreSQL** (table `videos`).
