#!/usr/bin/env zsh

# Needed for the awssso-env shell function (defined in ~/.zshrc).
source ~/.zshrc >/dev/null 2>&1

set -euo pipefail

IMAGE_REPO="262303671570.dkr.ecr.eu-west-1.amazonaws.com/kido-kanchi-prod"
AWS_REGION="eu-west-1"

gum confirm "Deploy kanchi to PRODUCTION (${IMAGE_REPO}:latest)?" || exit 1

gum spin --spinner dot --title "Building image..." --show-error -- \
  docker build -t kanchi -t "${IMAGE_REPO}:latest" .

awssso-env --pick infra_prod

gum spin --spinner dot --title "Logging in to ECR..." --show-error -- \
  zsh -c "aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $IMAGE_REPO"

gum spin --spinner dot --title "Pushing image..." --show-error -- \
  docker push "${IMAGE_REPO}:latest"

gum log -l info "Deployed ${IMAGE_REPO}:latest"
