.PHONY: install

install:
	docker compose run --rm python \
		pip install \
			--root-user-action ignore \
			--no-cache-dir \
			-r requirements.txt \
			--target ./.python_packages \
			--upgrade \
