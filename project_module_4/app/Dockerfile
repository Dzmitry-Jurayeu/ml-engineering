FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt /app/

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app"

EXPOSE 8080

CMD ["python", "main.py"]