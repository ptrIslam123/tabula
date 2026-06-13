FROM python:3.11-slim

WORKDIR /app

# Копируем только requirements сначала (для кэширования слоёв)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем весь код приложения
COPY src/ .

CMD ["python", "main.py"]
