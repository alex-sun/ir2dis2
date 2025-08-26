.PHONY: install tests run

install:
	docker compose run --rm python \
		pip install \
			--root-user-action ignore \
			--no-cache-dir \
			-r requirements.txt \
			--target ./.python_packages \
			--upgrade \

tests:
	docker compose run --rm python python -m pytest tests/ -v

run:
	docker compose run --rm python