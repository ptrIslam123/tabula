BOARD_PORT ?= 5000

board.image:
	sudo docker build -t boadr .

app.build:
	sudo docker compose build --no-cache

app.run:
	sudo docker compose up

app.stop:
	sudo docker compose down --remove-orphans

# Подключение к PostgreSQL с чтением из .env.db
db.attach:
	@$(eval include .env.db)
	@$(eval export)
	sudo docker exec -it sqldb psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)