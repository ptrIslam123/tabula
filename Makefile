board.image:
	sudo docker build -t boadr .

board.run:
	sudo docker run  \
	-p 5000:5000 \
	-e GOOGLE_CLIENT_ID="$(shell cat .local/GOOGLE_CLIENT_ID)" \
	-e GOOGLE_CLIENT_SECRET="$(shell cat .local/GOOGLE_CLIENT_SECRET)" \
	boadr
