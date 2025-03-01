#!/bin/bash

APPS_DIR=../../../../starter/apps

ENVIRONMENT=$1
ENVIRONMENT=${ENVIRONMENT:-devopstht}

AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

ORDER_API_REPO=$(terraform -chdir=../terraform output -raw order_api_repository_url)
ORDER_PROCESSOR_REPO=$(terraform -chdir=../terraform output -raw order_processor_repository_url)

aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "Building Order API image..."
echo "- Repository: ${ORDER_API_REPO}"

docker buildx build --no-cache --load --platform linux/amd64,linux/arm64 --progress plain  -t ${ORDER_API_REPO}:latest ${APPS_DIR}/order-api

TAG=${ORDER_API_REPO}:$(date +%Y%m%d_%H%M%S)
docker tag ${ORDER_API_REPO}:latest $TAG

ORDER_API_TAG=${TAG}
echo "Pushing Order API image..."
docker push ${ORDER_API_REPO}:latest
docker push ${TAG}


echo "Building Order Processor image..."
echo "- Repository: ${ORDER_PROCESSOR_REPO}"

docker buildx build --no-cache --load --platform linux/amd64,linux/arm64 --progress plain -t ${ORDER_PROCESSOR_REPO}:latest ${APPS_DIR}/order-processor

TAG=${ORDER_PROCESSOR_REPO}:$(date +%Y%m%d_%H%M%S)
docker tag ${ORDER_PROCESSOR_REPO}:latest $TAG

echo "Pushing Order Processor image..."
docker push ${ORDER_PROCESSOR_REPO}:latest
docker push ${TAG}


echo "Pushed Order API Tag: ${ORDER_API_TAG}"
echo "Pushed Order Processor Tag: ${TAG}"
echo "Successfully built and pushed all images!"
