THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
THIS_DIR      := $(dir $(realpath $(THIS_MAKEFILE)))


.PHONY: tf-ecr-init
tf-ecr-init:
	@@cd $(THIS_DIR)/terraform && terraform init

.PHONY: tf-ecr-destroy
tf-ecr-destroy:
	@@cd $(THIS_DIR)/terraform && terraform destroy

.PHONY: tf-ecr-apply
tf-ecr-apply: tf-ecr-plan
	@@cd $(THIS_DIR)/terraform && terraform apply tfplan.json

.PHONY: tf-ecr-plan
tf-ecr-plan:
	@@cd $(THIS_DIR)/terraform && terraform plan -out tfplan.json

.PHONY: tf-ecr-graph
tf-ecr-graph:
	@@cd $(THIS_DIR)/terraform && terraform graph -type=plan

.PHONY: tf-ecr-upload
tf-ecr-upload:
	@@cd $(THIS_DIR)/scripts && bash upload.sh

.PHONY: tf-ecr-cleanup
tf-ecr-cleanup:
	@@cd $(THIS_DIR)/scripts && bash cleanup.sh
