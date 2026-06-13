
### Сборка докер образа Backend приложения 
```bash
sudo docker build -t boadr .
```

### Запуск приложения в докере с проброской портов
```bash
sudo docker run -p 5000:5000 boadr
```
