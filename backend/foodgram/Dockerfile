FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app


RUN apt-get update && \
    apt-get install -y nano openssl curl python3 build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install gunicorn==20.1.0

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000"]
