# Explain decisions made during the implimentation of the test

## AWS Infra

- Started off with trying to refine makefiles a bit to speed up local development
- Added the ability to specify further tags wherever relevant to aid with cost breakdowns
- Provisioned dynamodb with set write/read capacity to stay within free tier limits
- Removed some dependencies on arns since there were things that could be determined more dynamically
- Changed the immutability of ECR published images since pushing `latest` would cause failures on subsequent builds
- Added one or two missing data resources as certain pointers weren't working correctly
- Explicitly configured CloudWatch log groups to make it clear were logs were stored, as well as provide direct control of them
- Opted for "bridge" networking mode since there were some existing opinionated resources setup for it, along with having built-in support for SRV record resolution within the codebase.
- Made sure all required configs and resources were then present to make this work, recall one ingress rule was missing in a provided module

## Kubernetes

- Separated out template resources into their own directories to make it easier to organise
- Used the same methodology as docker-compose to setup readiness and liveness probes
- Identified common variables and placed them in a shared config map, with unique values in standalone config maps. Also included a simple mechanism to ensure that pods get recreated should these values change
- Created `Services` to allow for internal communications between pods, via a consistent naming convention
- Provided some flexibility in chart values should users wish to add further data such as envvars, additional labels, or further security hardening configs

## Observability

- Opted to deploy kube-prometheus-stack for convenience. This stack deploys grafana, the prometheus operator as well as some other services
- More importantly, it also includes Prometheus CRDs. This operator saves time because it deploys a prometheus server, and prepopulates that as a datasource into Grafana
- Added `ServiceMonitor` resources for our chart in order for those targets to be discovered and scraped automatically by Prometheys
- Extended codebase on both services to create some custom metrics as well as expose a prometheus endpoint, making sure this additional dependency reflected in the currently used package manager

## Docs and testing

- Left for last :), but largely refining notes and instructions before submission, ensuring to re-deploy everything from scratch to validate that the process still functions as expected, returning the same results each time
- Leveraged the existing script to test wherever possible

---

# What is missing

- Everything that was added in order to make this project functional:
  - dynamodb resources
  - ecs resources
  - kubernetes charts
- Since this is stored in a git repo, there are numerous CI workflows that could be configured for this. None are included in this submission.
- The Makefile helps a lot but it can be cumbersome when working with a complex codebase with various ecosystems (docker, terraform, k8s, etc). Reconsidering this approach could lead to better devex.
- Automated deployment is also missing. Depending on what systems would be in place to deploy, we could introduce direct deployments from a CI/CD pipeline, or use gitops frameworks for this.
- No SSL enabled on ALB

# What could be improved

- Better dynamic naming of resources. There are one or two that aren't being discovered dynamically or need to be specified manually (such as image names in ECR)
- Testability of both terraform and helm deployments. Currently the testing is done manually _after_ everything is deployed. While I wouldn't combine these tests into the deployments themselves (there could be other separate e2e tests running that validate systems, aligning more with SLO/SLI methodologies), we could use CI actions to run these tests as part of the acceptance criteria to merge changes in, increasing confidence that no issues would be introduced before deploying changes.
- I was able to add dynamodb bootstrapping into the terraform module, but left it out of the kubernetes chart for the sake of simplicity and script duplication, but this could've been added in, or again, just be made part of some testing workflows.
- Python dependency and venv management can be painful, we could introduce something like poetry to improve devex and consistency
- Add mTLS between both services to ensure secure communication even within private networks
- Enable encryption at rest on dynamodb tables
- Improve support for custom domains at the public endpoint level

# What I would do if this was in a production environment and I had more time

- Introduce a robust set of CI workflows to address any gaps we have and ensure a high quality of codebase, providing a short feedback loop back to contributors.
- These workflows should include static checks like linting and code formatting, static vulnerability checks, secret detection, integration testing, basic ephemeral deployment testing, automated deployments, as some examples.
- Ensure consistent tagging so we can accurately derive costs by collating all related services as one entity
- Add cloudwatch alerts
- Further extend ACLs in vpc module
- Add structured logging to codebase
- Add tracing support to codebase
- Investigate ways to run external pentesting to identify any security gaps we may not be aware of
- Separate out image storage into a separate AWS account for security
- Add pod network policies
- Ensure we have proper persistent storage and backups in k8s and AWS
- Separate metrics into a port that isn't exposed as part of both services
- Ensure we identify key user critical happy paths, and that we have sufficient monitoring in place or any e2e-tests to ensure that these paths are accessible at all times
- Spend more time refining metrics and dashboards
- Run performance benchmarks to measure what our thresholds are under what operational load
- Configure alert expressions via prometheus rules, ensuring we can cover expected operational issues, as well as others informed by known performance thresholds
- Ensure we have runbooks for expected incidents, as well as a framework to handle any and all incidents
- Improve healthchecks across the board to not introduce unecessary restarts, particularly in kubernetes
- Ensure all public endpoints with are exposed with SSL
- Ensure we use an ingress controller to expose public endpoints
- Setup DNS automation such that records are automatically created for services and ingress resources if need be
