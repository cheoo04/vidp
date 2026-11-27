# Comprendre VidP (en partant de zéro)

> À lire en entier par **les 5 membres** avant de coder. ~30 min.
> Sujet officiel : `Projet Cloud (2).pdf`, page 2 (dossier `cloud_course_resources-main/projet/`).

---

## 1. Le projet en une phrase

On dépose une vidéo sur **notre machine** ; une chaîne de petits programmes l'analyse
(langue parlée, sous-titres, animaux présents…) ; le résultat est envoyé dans **le cloud**,
où il est stocké et affiché sur **une page web publique**. Le tout doit être
**déployable automatiquement en quelques minutes** et **surveillé** (monitoring),
en consommant **le moins d'énergie possible** (bonus).

C'est un projet « **hybride** » : une partie tourne en local, une partie dans le cloud.

## 2. Le schéma du prof, décodé

```
          PARTIE LOCALE (nos machines)                          PARTIE CLOUD (AWS ou VMs du prof)
┌─────────────────────────────────────────────┐        ┌──────────────────────────────────────────────┐
│                                             │        │                                              │
│  data/input ──► orchestrator                │        │   Load Balancer (nginx)                      │
│                   │                         │  HTTP  │       │           │                          │
│                   ├─► 1. downscale  (ffmpeg)│───────►│       ▼           ▼                          │
│                   ├─► 2. langident (Whisper)│        │   production  production   (2 VMs ou +)      │
│                   ├─► 3. subtitle  (Whisper)│        │       │  « combine et enregistre »           │
│                   └─► 4. animal    (YOLO)   │        │       ▼                                      │
│                                             │        │   S3 (fichiers) + PostgreSQL (métadonnées)   │
│  « Local video store » = dossier data/      │        │       ▲                                      │
│                                             │        │   viewer (Apache) ◄── navigateur du public   │
│  + gouverneur d'énergie + monitoring eBPF   │        │                                              │
└─────────────────────────────────────────────┘        └──────────────────────────────────────────────┘
        Kubernetes (ou docker compose)                       déployé par Terraform + Ansible
```

| Boîte du schéma | Ce que c'est concrètement chez nous | Dossier |
|---|---|---|
| Downscale Pod | réduit la vidéo en 360p avec `ffmpeg` (plus léger pour la suite) | `services/downscale` |
| LangIdent Pod | détecte la langue parlée (modèle Whisper « tiny ») | `services/langident` |
| Subtitle Pod | génère les sous-titres `.vtt` (Whisper) | `services/subtitle` |
| Animal detect pod | extrait des images, détecte chiens/chats/oiseaux… (YOLO) | `services/animal` |
| *(pas sur le schéma)* | **orchestrateur** : surveille le dossier, appelle les 4 services dans l'ordre, envoie au cloud | `services/orchestrator` |
| Local video store | le dossier partagé `data/` | `data/` |
| Load Balancer | nginx qui répartit les requêtes entre les VMs production | `cloud/lb` |
| Video Production (VM) | API qui reçoit vidéo + métadonnées et les range dans S3 + la base | `cloud/production` |
| Amazon S3 + DynamoDB | stockage des fichiers + base de métadonnées. Sans AWS : **MinIO** (faux S3) + **PostgreSQL** | `cloud/docker-compose.yml` |
| Video Viewer Page VM (Apache2) | page web publique : vidéos traitées + métadonnées + celles en cours | `cloud/viewer` |
| Energy optimizer governor | réglage de la politique CPU pour consommer moins | `monitoring/` |
| EBPF/Grafana Pkt/s | mesure du trafic réseau (paquets/s) affichée dans Grafana | `monitoring/` |
| Ansible – Terraform | scripts de déploiement automatique | `deploy/` |

## 3. Les concepts, un par un

### 3.1 Machine virtuelle (VM)
Un « faux ordinateur » complet (avec son propre système d'exploitation) qui tourne sur un
vrai ordinateur grâce à un **hyperviseur** (QEMU/KVM, VirtualBox…). Dans le cloud, quand on loue
une machine AWS **EC2**, on loue en fait une VM.
→ Lourd (un OS entier, démarre en dizaines de secondes) mais très bien isolé.
*Pour apprendre : TP1, TP2, cours « virtualisation ».*

### 3.2 Container (Docker)
Un processus isolé qui embarque **son application et ses dépendances** (Python, ffmpeg…),
mais **partage le noyau** de la machine hôte. Démarre en ~1 s, pèse quelques centaines de Mo.
- **Image** = le modèle figé (comme un `.iso`), construite à partir d'un **Dockerfile**.
- **Container** = une image en cours d'exécution.
- **Volume** = un dossier de l'hôte monté dans le container (notre `data/`).
- Intérêt pour nous : « ça marche chez moi » ⇒ ça marche chez les 4 autres **et** sur les VMs de démo.

```bash
docker build -t vidp-downscale services/downscale   # construit l'image
docker run -p 8000:8000 vidp-downscale              # lance un container
```
*Pour apprendre : TP3, TP4, cours « Virtualisation et containers ».*

### 3.3 docker compose
Un fichier YAML qui décrit **plusieurs containers** et comment ils se parlent, pour tout lancer
d'une commande : `docker compose up --build`. Dans un compose, les containers se joignent
**par leur nom** (`http://downscale:8000`).
*Pour apprendre : TP5.*

### 3.4 Microservices et API HTTP
Au lieu d'un gros programme, on fait **un petit service par tâche**, qui communique en HTTP + JSON.
Chaque service expose `POST /process` et `GET /health` (voir `docs/04-contrat-api.md`).
Avantages : chacun du groupe travaille sur son service sans toucher aux autres, et on peut
dupliquer seulement le service lent. On utilise **FastAPI** (Python) : quelques lignes suffisent.
*Pour apprendre : cours « communication inter-services », « impact sur l'architecture ».*

### 3.5 Kubernetes (k8s)
Un **orchestrateur de containers** : on lui décrit l'état voulu (« 2 copies de downscale,
1 de subtitle ») et il le maintient (redémarre ce qui plante, répartit sur les machines).
Vocabulaire minimal :
- **Pod** = 1 ou plusieurs containers qui tournent ensemble (le schéma dit « Downscale Pod »).
- **Deployment** = « je veux N copies de ce pod ».
- **Service** = un nom DNS stable pour joindre les pods (`http://downscale:8000`).
- **PersistentVolumeClaim (PVC)** = un disque partagé (notre `data/`).
- En local on utilise **minikube** ou **k3s** (un Kubernetes léger, idéal pour l'énergie).

Le sujet dit « Kubernetes **ou autre** » : on **commence avec docker compose** (simple),
on passe à Kubernetes une fois que tout marche.
*Pour apprendre : TP6, TP7, cours « orchestration et automatisation ».
Exemples dans le dossier du prof : `deployment.yaml`, `loadbalancer.yaml`.*

### 3.6 Cloud, AWS, EC2, S3, DynamoDB
- **Cloud** = louer des ressources (machines, stockage) à la demande chez un fournisseur.
- **EC2** = les VMs d'AWS. **S3** = stockage de fichiers (« objets ») dans des « buckets ».
  **DynamoDB** = base de données NoSQL d'AWS.
- **Nous n'avons pas de clés AWS.** Solution : on utilise des équivalents qui parlent **le même
  protocole** — **MinIO** imite S3 à l'identique (même code Python `boto3`), et PostgreSQL remplace
  DynamoDB (le sujet autorise « ou BD simple »). Le jour où on a AWS, on change **seulement des
  variables d'environnement** (`S3_ENDPOINT`, clés) et le code ne bouge pas.

### 3.7 Load balancer (répartiteur de charge)
Un serveur placé devant plusieurs copies d'un service, qui distribue les requêtes entre elles.
Si une copie tombe, les autres prennent le relais (**disponibilité**) ; si la charge monte, on en
ajoute (**passage à l'échelle**). On utilise **nginx**. Pour que ça marche, les copies doivent être
**stateless** (ne rien garder en mémoire) : tout est dans S3 + la base.
*Pour apprendre : TP4, cours « disponibilité dans le cloud ».*

### 3.8 Infrastructure as Code : Terraform vs Ansible
Deux outils complémentaires, à ne pas confondre :

| | **Terraform** | **Ansible** |
|---|---|---|
| Rôle | **crée** l'infrastructure (VMs, réseaux, buckets) | **configure** des machines qui existent déjà |
| Exemple | « crée 3 VMs EC2 + 1 bucket S3 » | « installe Docker sur ces IP et lance nos containers » |
| Langage | HCL (`.tf`) | YAML (playbooks) |
| Besoin | un compte cloud (clés AWS) | juste un accès **SSH** aux machines |

⚠️ **Point clé pour la note** : à la démo live, le prof donne **des adresses IP** et on doit
redéployer en quelques minutes. Ces machines existent déjà ⇒ c'est **Ansible** qui fait le travail.
Terraform ne sert que si on a AWS. **Priorité : Ansible.**
*Pour apprendre : TP5 (« apport de l'automatisation »).*

### 3.9 Monitoring
Surveiller ce qui tourne : CPU, mémoire, requêtes/s, temps de traitement.
- **Prometheus** collecte des mesures à intervalles réguliers ; **Grafana** les affiche en graphiques.
- **eBPF** : technique pour exécuter de petits programmes **dans le noyau Linux** de façon sûre,
  par exemple pour compter les paquets réseau (« Pkt/s » sur le schéma) sans modifier les applis.
- Outils rapides en terminal : `htop`, `btop`, `docker stats`.
*Pour apprendre : TP8 (eBPF/XDP).*

### 3.10 Énergie : gouverneur CPU et mesure
Le **gouverneur** (« governor ») est la politique Linux qui choisit la fréquence du CPU :
- `performance` : toujours à fond → rapide mais gourmand,
- `powersave` : fréquence basse → économe,
- `schedutil` (défaut) : s'adapte à la charge.

Démo du prof le 10/11 (enregistrement) : la même charge consommait **~18 W en powersave,
~35 W en schedutil, ~42 W en performance**. Sur un cluster, ça se paie sur la facture et en chaleur.
```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor        # gouverneur actuel
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```
Mesurer la consommation : compteurs **RAPL** d'Intel/AMD (`/sys/class/powercap/`), outils
`powerstat`, `turbostat`, ou `scaphandre` (exporte vers Prometheus).

**Leviers d'économie dans VidP** (bonus énergie) : réduire la vidéo **d'abord** (downscale en 1er),
utiliser les **plus petits modèles** (Whisper tiny, YOLO nano), n'analyser qu'**une image toutes les
2 s**, préférer **ONNX Runtime** à PyTorch, éteindre ce qui ne sert pas, choisir le bon gouverneur.

## 4. Le parcours d'une vidéo (ce qui se passe vraiment)

1. Tu copies `chat.mp4` dans `data/input/`.
2. L'orchestrateur la voit, crée le job `20261127-181500-chat`, la déplace dans `data/work/<job>/source.mp4`,
   et prévient le cloud : « job en cours, étape downscale » → la page web l'affiche « en cours ».
3. Il appelle `downscale` → `downscaled.mp4` (360p). Puis `langident` → `"fr"`.
   Puis `subtitle` → `subtitles.vtt`. Puis `animal` → `[{"label":"cat","count":4}]`.
4. Il assemble `metadata.json` et envoie vidéo + sous-titres + métadonnées au **load balancer**.
5. Une VM `production` reçoit, range les fichiers dans **S3** et une ligne dans **PostgreSQL**.
6. La page **viewer** interroge l'API toutes les 4 s et affiche la vidéo avec ses sous-titres,
   la langue et les animaux.

## 5. Ce qui est évalué (et donc nos priorités)

1. **Dépôt git** : code + doc pour tester (README clair).
2. **Démo live** : redéployer sur des IP fournies **en quelques minutes** ⇒ Ansible + images prêtes.
3. **Vidéo de présentation** : design + démo, chaque membre explique sa partie.
4. **Bonus énergie** : mesures avant/après dans la doc.

Le prof a montré (page 6 du PDF) un projet rendu inachevé par un étudiant seul et démotivé :
d'où l'importance d'un **pipeline qui marche de bout en bout tôt**, même avec des stubs, puis qu'on améliore.
C'est exactement l'état actuel du dépôt.
