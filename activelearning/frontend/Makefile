NAME   := lsirepfl/gendertracker-frontend
TAG    := $$(git log -1 --pretty=%h)
IMG    := ${NAME}:${TAG}
LATEST := ${NAME}:latest

.PHONY:build
build:
	@echo ${IMG}
	@docker build -f Dockerfile.production -t ${IMG} .
	@docker tag ${IMG} ${LATEST}
 
push: 
	@docker push ${NAME}
