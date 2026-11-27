# VidP — pipeline hybride de traitement vidéo

Projet du module Cloud (ESIR). Des vidéos stockées **en local** sont analysées par une chaîne
de containers (réduction, langue, sous-titres, animaux) ; vidéos + métadonnées sont envoyées
**dans le cloud** (VMs derrière un load balancer, stockage S3 + base de données) et affichées
sur une **page web publique**. Déploiement automatisé + monitoring.

```
data/input ─► orchestrator ─► downscale ─► langident ─► subtitle ─► animal ─┐
                                                                            │ HTTP
   page web (Apache) ◄── production ×2 ◄── load balancer (nginx) ◄──────────┘
                              │
                     S3 (MinIO) + PostgreSQL
```

## Démarrage rapide

Prérequis : Docker + docker compose (voir [docs/03-travailler-ensemble.md](docs/03-travailler-ensemble.md)).

```bash
docker compose up --build -d        # tout lancer (pipeline + cloud) sur sa machine
cp ma_video.mp4 data/input/         # déposer une vidéo
docker compose logs -f orchestrator # suivre le traitement
```

| URL | Quoi |
|---|---|
| http://localhost:8080 | page web publique (viewer) |
| http://localhost:8000/videos | API du cloud (via le load balancer) |

Raccourcis : `make up`, `make logs`, `make test-video`, `make down` (voir `Makefile`).

## Documentation

1. [Comprendre le projet et les concepts](docs/01-comprendre-le-projet.md) — **à lire en premier**
2. [Plan de travail et répartition des tâches](docs/02-plan-et-taches.md)
3. [Travailler ensemble (git, Docker, sans clés AWS)](docs/03-travailler-ensemble.md)
4. [Contrat d'API entre les services](docs/04-contrat-api.md)

## Structure

```
services/            pipeline LOCAL (un dossier = un container)
  orchestrator/        surveille data/input, enchaîne les étapes, envoie au cloud
  downscale/           ffmpeg → 360p                       🚧 stub (copie sans réduire)
  langident/           détection de langue (Whisper)       🚧 stub
  subtitle/            sous-titres WebVTT (Whisper)        🚧 stub
  animal/              détection d'animaux (YOLO)          🚧 stub
cloud/               partie CLOUD
  production/          API qui stocke dans S3 + PostgreSQL 🚧 stub (disque + mémoire)
  lb/                  load balancer nginx                 🚧 stub (1 seul serveur)
  viewer/              page web Apache                     🚧 stub (liste brute)
deploy/              ansible/ · k8s/ · terraform/          🚧 à faire
monitoring/          Prometheus/Grafana, eBPF, énergie     🚧 à faire
data/                dossier partagé des vidéos (ignoré par git)
```

## État

- [x] Pipeline de bout en bout avec stubs (dépôt → traitement → upload → API → page web)
- [x] Orchestrateur
- [ ] Downscale réel (ffmpeg)
- [ ] LangIdent / Subtitle réels (Whisper)
- [ ] Animal detect réel (YOLO)
- [ ] Cloud réel : production stateless (S3 + PostgreSQL), 2 répliques derrière le LB, page web finale
- [ ] Déploiement Ansible + Kubernetes (+ Terraform si clés AWS)
- [ ] Monitoring + mesures d'énergie
