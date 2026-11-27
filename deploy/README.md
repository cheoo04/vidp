# Déploiement automatique (responsable : P5)

Objectif de la démo live : le prof donne des **adresses IP** → on redéploie tout en **quelques minutes**.

## ansible/ — PRIORITÉ 1
Configure des machines existantes via SSH. À produire :
- `inventory.ini` : groupes `[lb]`, `[production]`, `[viewer]`, `[db]`, `[pipeline]` avec les IP
- `site.yml` : installe Docker, copie le code (ou tire les images de GHCR), lance les containers,
  génère `nginx.conf` avec les IP des VMs `production` (template Jinja2)
- commande unique : `ansible-playbook -i inventory.ini site.yml`

## k8s/ — PRIORITÉ 2
Manifests Kubernetes (k3s ou minikube) pour le pipeline local :
`Deployment` + `Service` par service, `PersistentVolumeClaim` pour `/data`.
Modèles dans le dossier du prof : `deployment.yaml`, `loadbalancer.yaml`.

## terraform/ — seulement si on obtient des clés AWS
Crée les VMs EC2, le security group (ports 22, 80, 8000) et le bucket S3,
puis génère l'inventaire Ansible. Ne JAMAIS commiter `*.tfstate` ni les clés.
