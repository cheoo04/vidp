# Travailler ensemble à distance

## 1. L'environnement partagé : GitHub + Docker

On n'a pas besoin d'une machine commune : **le dépôt GitHub + Docker** suffisent.
Docker garantit que le code tourne **pareil chez les 5** (mêmes versions de Python, ffmpeg…).

| Besoin | Outil |
|---|---|
| Code partagé, historique | dépôt GitHub `cheoo04/vidp` |
| Qui fait quoi, avancement | **GitHub Projects** (tableau À faire / En cours / En revue / Fini) + **Issues** |
| Relecture du code | **Pull Requests** (relues et fusionnées par P1) |
| Même environnement pour tous | **Docker + docker compose** |
| Discussion rapide, réunions | Discord / WhatsApp + un point visio de 20 min par semaine |
| Tester ensemble le cloud | une personne lance `cloud/` et partage son URL avec **Tailscale** (VPN gratuit) ou `ngrok` |
| Environnement sans rien installer | **GitHub Codespaces** (VS Code dans le navigateur, Docker inclus, heures gratuites avec le Student Pack) |

### Mise en place (P1, une fois)
1. GitHub → *Settings → Collaborators* → inviter les 4 membres.
2. *Settings → Branches → Add rule* sur `main` : cocher **Require a pull request before merging**
   (personne ne pousse directement sur `main`).
3. *Projects → New project → Board*, créer une issue par case à cocher de `02-plan-et-taches.md`,
   l'assigner à son responsable.

## 2. Installer son poste (chaque membre)

| Système | Installation |
|---|---|
| Linux (Ubuntu/Debian) | `sudo apt install -y docker.io docker-compose-v2 git && sudo usermod -aG docker $USER` puis se déconnecter/reconnecter |
| Windows | installer **WSL2** (Ubuntu) puis **Docker Desktop** (option « WSL2 backend »), travailler dans le terminal Ubuntu |
| macOS | installer **Docker Desktop** |

Vérifier : `docker run hello-world` puis `docker compose version`.

```bash
git clone https://github.com/cheoo04/vidp.git
cd vidp
docker compose up --build          # 1er lancement : quelques minutes
# dans un autre terminal :
cp ma_video.mp4 data/input/
docker compose logs -f orchestrator
# ouvrir http://localhost:8080
```

## 3. Workflow git (simple, à suivre par tous)

```bash
git switch main && git pull                 # partir de la dernière version
git switch -c feat/subtitle-whisper         # une branche par tâche : feat/..., fix/..., docs/...
# ... coder, tester avec docker compose ...
git add services/subtitle
git commit -m "subtitle: transcription avec faster-whisper base"
git push -u origin feat/subtitle-whisper
# sur GitHub : « Compare & pull request », décrire comment tester, assigner P1 en relecteur
```

Règles :
- **Petites PR** (un service, une fonctionnalité) : plus faciles à relire.
- **Ne jamais commiter** : vidéos, modèles ML (`.pt`, `.onnx`), clés (`.pem`, `.env`), `*.tfstate`.
  Le `.gitignore` les bloque déjà, mais vérifiez `git status` avant chaque commit.
- On ne modifie le **contrat d'API** qu'après accord du groupe.

## 4. Pas de clés AWS : notre stratégie

1. **Tout le développement se fait sans AWS** : MinIO remplace S3, PostgreSQL remplace DynamoDB,
   des containers remplacent les VMs EC2. Rien à payer, rien à attendre.
2. **Le code est déjà prêt pour AWS** : passer à AWS = vider `S3_ENDPOINT`, mettre les vraies clés
   dans les variables d'environnement, et écrire le Terraform qui crée les EC2.
3. **La démo live se fait sur les IP fournies par le prof** ⇒ c'est Ansible (SSH) qui compte.
4. Si on veut quand même tester sur un vrai cloud : AWS Free Tier (compte perso, carte bancaire
   demandée), ou **AWS Academy / GitHub Student Pack** (crédits gratuits) — **jamais** de clés dans git.

### Mail à envoyer au prof (P1)
> Bonjour Monsieur,
> Nous sommes un groupe de 5 sur le projet VidP (noms…). Pourriez-vous nous préciser :
> 1. la date limite de rendu et la date de la démo live ;
> 2. si des clés AWS seront fournies, et quand — sinon, si l'utilisation de VMs (ou des machines
>    de TP) avec un stockage compatible S3 (MinIO) est acceptée ;
> 3. le type de machines fournies pour la démo (OS, accès SSH par clé, nombre de machines, ports ouverts).
> Merci, cordialement.
