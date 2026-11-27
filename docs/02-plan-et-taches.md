# Plan de travail et répartition (5 personnes)

> Date limite officielle encore inconnue (« xx/xx/2026 » dans les fichiers du prof) : **à demander au prof**.
> Le planning ci-dessous est en semaines ; on le cale sur la vraie date dès qu'on l'a.

## Principe

- Le pipeline **tourne déjà de bout en bout** avec des « stubs » (fausses implémentations).
  Chacun **remplace un stub** par la vraie version **sans casser le contrat** (`docs/04-contrat-api.md`).
- Personne n'est bloqué par les autres : on peut tester son service seul.
- Le **lead (P1)** relit et fusionne toutes les Pull Requests, et refait/vérifie chaque partie.

## Les 5 rôles

| | Rôle | Responsable de | Livrable « fini » quand… |
|---|---|---|---|
| **P1** | **Lead / intégration** | orchestrateur, contrat d'API, revue des PR, README, montage de la vidéo de démo | une vidéo déposée apparaît sur la page web avec de vraies métadonnées |
| **P2** | **Audio** | `services/langident` + `services/subtitle` (Whisper) | langue correcte et sous-titres lisibles sur 3 vidéos test (FR, EN, autre) |
| **P3** | **Vision + énergie** | `services/downscale` (ffmpeg), `services/animal` (YOLO), mesures d'énergie + gouverneur | vidéo réduite en 360p ; animaux détectés sur 3 vidéos test ; tableau de mesures W/temps avant/après |
| **P4** | **Cloud applicatif** | `cloud/production`, `cloud/lb`, `cloud/viewer`, MinIO (S3) + PostgreSQL | page web publique jolie, LB prouvé (`X-Served-By` alterne), coupure d'une VM production sans panne |
| **P5** | **DevOps / déploiement** | Ansible, Kubernetes (k3s), Terraform (si AWS), CI GitHub Actions, monitoring Prometheus/Grafana | `ansible-playbook` redéploie tout sur des IP vierges en < 10 min |

Chaque rôle écrit **sa section** dans le README / la doc et **la présente** dans la vidéo.

## Planning

### Semaine 1 — tout le monde sait lancer le projet
- [ ] **Tous** : installer Docker, cloner, `docker compose up --build`, déposer une vidéo, la voir sur http://localhost:8080
- [ ] **Tous** : lire `docs/01-comprendre-le-projet.md` + le TP correspondant à son rôle
- [ ] **Tous** : 1ʳᵉ PR (même petite) pour valider le workflow git
- [ ] P1 : créer le tableau GitHub Projects avec les tickets ci-dessous, inviter les 4 autres
- [ ] P1 : envoyer le mail au prof (date limite, clés AWS, machines de démo — voir `03-travailler-ensemble.md`)

### Semaine 2 — vraies implémentations
- [ ] P2 : langident avec faster-whisper `tiny` (modèle chargé une seule fois au démarrage)
- [ ] P2 : subtitle avec faster-whisper `base`, sortie WebVTT
- [ ] P3 : downscale avec ffmpeg (360p, H.264, métadonnées réelles via ffprobe)
- [ ] P3 : animal avec YOLO nano (ONNX Runtime), 1 image / 2 s
- [ ] P3 : premières mesures d'énergie (RAPL / powerstat) sur une vidéo de référence
- [ ] P4 : production stateless : fichiers dans MinIO (boto3), index dans PostgreSQL (psycopg)
- [ ] P4 : 2 répliques derrière le LB, en-tête `X-Served-By`
- [ ] P4 : page viewer finalisée (lecteur + sous-titres, langue, animaux, filtres), tests de charge du LB
- [ ] P5 : playbook Ansible « installer Docker + lancer cloud/ » sur une VM de test
- [ ] P1 : gestion des erreurs, tests automatiques (pytest) de l'orchestrateur

### Semaine 3 — déploiement et monitoring
- [ ] P5 : manifests Kubernetes (k3s) pour le pipeline local + PVC pour `data/`
- [ ] P5 : CI GitHub Actions qui construit et publie les images (GHCR) à chaque merge
- [ ] P5 / P1 : Prometheus + Grafana (CPU, mémoire, req/s, durée par étape) ; eBPF pkt/s en bonus
- [ ] P3 : comparer gouverneurs `powersave` / `schedutil` / `performance` sur le pipeline
- [ ] P4 : production sur 2 VMs distinctes derrière le LB (Ansible génère `nginx.conf` avec les IP)

### Semaine 4 — finition
- [ ] **Répétition de la démo live** : machines vierges → tout redéployé en < 10 min, chronométré
- [ ] README final : installation, test, architecture, choix énergie, mesures
- [ ] Vidéo de présentation (chacun sa partie, 2–3 min)
- [ ] Rendu avant la date limite (**retard = 0**)

## Dépendances (qui attend qui)

```
contrat d'API (fait) ──► P2, P3, P4 travaillent en parallèle
images Docker de P2/P3/P4 ──► P5 (CI + Kubernetes)
playbook Ansible (P5) ──► répétition de la démo (tous)
```

## Ce que P1 vérifie à chaque PR (check-list de revue)

- [ ] `docker compose up --build` marche toujours depuis zéro
- [ ] le contrat d'API est respecté (champs, chemins, codes d'erreur)
- [ ] pas de secret / clé / vidéo / modèle commité
- [ ] le modèle ML est chargé **une fois** (pas à chaque requête)
- [ ] le README ou la doc du dossier explique comment tester la modification
