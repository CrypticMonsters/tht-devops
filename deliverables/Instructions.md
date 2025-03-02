# Terraform and ECS-EC2 cluster

Note that the same prerequisites are required as in the main `README.md`.

## How to deploy

Ensuring that you're connected and authenticated to your own AWS account. You may then run the following commands in a terminal:

### ECR

- `cd deliverables/deploy/ecr`
- `make tf-ecr-init` to initiate the terraform setup for ECR
- `make tf-ecr-apply` to create the required ECR repos
- `make tf-ecr-upload` to build and upload the required images to ECR

### ECS

- Return to the root of the repo
- `make tf-cluster-init` to initiate the terraform setup for ECS
- `make tf-cluster-apply` to deploy all required resources for ECS

## How to Test

Run the following commands to test that ECS was successfully deployed

- `make tf-cluster-get-url` to fetch the ALB URL to use
- `SERVER_ENDPOINT=<your URL> ./starter/apps/scripts/test_docker_compose.sh`

---

# Kubernetes and Helm

## How to deploy to MiniKube

Due to lack of time to formalize this into a `Makefile`, these instructions are similar to what is found in `MINIKUBE.md`

For brevity, we assume you have minikube already running and connected to via `kubectl`

Run the following from the root of the repo:

- `eval $(minikube docker-env)` to allow for local images to be used
- `make docker-build` to build up-to-date images to be used
- `helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace` to install grafana and prometheus dependencies
- `make helm-apply` to deploy the helm chart
- `kubectl port-forward deployment/dynamodb-local  8088:8000 &` to setup a port-forward to dynamodb
- `DDB_ENDPOINT=http://localhost:8088 python './starter/apps/scripts/init-dynamodb.py'` to prepopulate dynamodb

## How to Test

Run the following commands to test that kubernetes resources were successfully deployed

- `kubectl port-forward service/order-api 8090:8000` to setup a port-forward for the order api service, keep this running in your shell
- in a separate shell, run `SERVER_ENDPOINT=localhost:8090 ./starter/apps/scripts/test_docker_compose.sh`

### Grafana/Prometheus

- Fetch the admin password by running `kubectl --namespace monitoring get secrets kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo` (defaults to "prom-operator")
- Access grafana by running the following
  - `export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=kube-prometheus-stack" -oname)`
  - `kubectl --namespace monitoring port-forward $POD_NAME 3000`
  - Browse to `localhost:3000` in another shell
- To stay within time limits I did not have time to build bespoke dashboards. But if you browse to the "Explorer" tab, you can use the query `count by (job) ({job=~"order-(api|processor)"})` to see a total number of metrics being pulled from each service.
- `group by (__name__, job) ({job=~"order-(api|processor)"})` to see individual metric names available.

---

## NOTES

In my local testing for some reason I was getting HTTP500 errors when calling order-api in kubernetes. For transparency sake, I did not do any further debugging to resolve this, trying to keep within time restrictions.
The error was coming from the `self.table.get_item()` call in the order-processor service, complaining that a required key was missing.

I would see these logs in the processor service

```
devopstht-devops-takehometest-processor-68f55bcd5c-5fpqh devops-takehometest-processor 2025-03-02 18:42:54,115 - [main - INFO - Processing order for pro
duct PROD001
devopstht-devops-takehometest-processor-68f55bcd5c-5fpqh devops-takehometest-processor 2025-03-02 18:42:54,130 - [main - ERROR - Inventory operation fai
led: An error occurred (ValidationException) when calling the GetItem operation: One of the required keys was not given a value
```

One can replicate this by calling `self.table.get_item(Key="foo": "bar")`

If I had further time to debug I would check if the request payload was somehow getting changed when the API would call the service.
