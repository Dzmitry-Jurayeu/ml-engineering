FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update && apt-get install -y libgomp1 && pip install --upgrade pip && pip install -r /app/requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app"

CMD ["python", "main.py"]