.PHONY: bootstrap lint test build verify

bootstrap:
	python packages/workspace-tooling/workspace.py bootstrap

lint:
	python packages/workspace-tooling/workspace.py lint

test:
	python packages/workspace-tooling/workspace.py test

build:
	python packages/workspace-tooling/workspace.py build-all --output-dir deploy/artifacts

verify:
	python packages/workspace-tooling/workspace.py verify --output-dir deploy/artifacts
