include starter/apps/Makefile
include deliverables/deploy/ecs-ec2/terraform/Makefile

.PHONY: docker-build docker-build-api docker-build-processor  helm-apply helm-restart helm-destroy

all: helm-restart

docker-build-api:
	@docker build --progress plain -t order-api starter/apps/order-api/. 

docker-build-processor:
	@docker build --progress plain -t order-processor starter/apps/order-processor/. 

docker-build: docker-build-api docker-build-processor

helm-destroy:
	helm uninstall devopstht

helm-apply:
	helm upgrade --force --install devopstht ./deliverables/deploy/kubernetes/charts/microservices/   

helm-restart: helm-destroy helm-apply

ddb-seed:
	DDB_ENDPOINT=http://localhost:8088 python './starter/apps/scripts/init-dynamodb.py'
