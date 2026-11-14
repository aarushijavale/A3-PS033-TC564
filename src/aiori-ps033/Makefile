.PHONY: up down restart build ps logs test demo clean

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose up -d --build

ps:
	docker compose ps

logs:
	docker compose logs -f

test:
	pytest -v

demo:
	docker exec aiori-client python /app/discovery_client.py latency
	docker exec aiori-client python /app/discovery_client.py traceroute
	docker exec aiori-client python /app/discovery_client.py pathmtu

clean:
	docker compose down --remove-orphans
