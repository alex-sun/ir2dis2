.PHONY: test bot last-race discord-bot-with-timeout

test:
	python -m pytest tests/ -v

bot:
	python src/discord_bot.py

bot-with-timeout:
	timeout 20s python src/discord_bot.py

last-race:
	python src/last_race_details.py

