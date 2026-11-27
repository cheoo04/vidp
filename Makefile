# Raccourcis. Usage : make <cible>
.PHONY: up down logs ps test-video clean-data local-only cloud-only

up:            ## tout lancer (pipeline + cloud)
	docker compose up --build -d

down:          ## tout arrêter
	docker compose down

logs:          ## suivre les logs de l'orchestrateur
	docker compose logs -f orchestrator

ps:            ## état des containers
	docker compose ps

test-video:    ## génère une vidéo de test (mire + bip, 10 s) dans data/input
	mkdir -p data/input
	ffmpeg -v error -y -f lavfi -i testsrc=size=1280x720:rate=25 -f lavfi -i sine=frequency=440 \
	  -t 10 -c:v libx264 -c:a aac data/input/test-$$(date +%H%M%S).mp4

local-only:    ## pipeline seul, hors-ligne (résultats dans data/done/)
	CLOUD_URL= docker compose -f services/docker-compose.yml up --build

cloud-only:    ## cloud seul
	docker compose -f cloud/docker-compose.yml up --build

clean-data:    ## vide data/ (garde les dossiers)
	find data -mindepth 2 -delete
