FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data
ENV DB_PATH=/app/data/database.db

EXPOSE 5000

CMD ["python", "app.py"]
