.PHONY: test discord-bot last-race

test:
	python -m pytest tests/ -v

discord-bot:
	python src/discord_bot.py

last-race:
	python src/last_race_details.py