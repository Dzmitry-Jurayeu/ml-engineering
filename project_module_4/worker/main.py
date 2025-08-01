import pika
from loguru import logger
import os
import json
from transformers import pipeline
import requests


RABBIT_HOST = os.getenv("RABBIT_HOST")
RABBIT_PORT = os.getenv("RABBIT_PORT")
PIKA_USERNAME = os.getenv("RABBITMQ_DEFAULT_USER")
PIKA_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")
API_ENDPOINT = os.getenv("API_ENDPOINT")

connection_params = pika.ConnectionParameters(
    host=RABBIT_HOST,  # Замените на адрес вашего RabbitMQ сервера
    port=RABBIT_PORT,  # Порт по умолчанию для RabbitMQ
    virtual_host='/',  # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username=PIKA_USERNAME,  # Имя пользователя по умолчанию
        password=PIKA_PASSWORD  # Пароль по умолчанию
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
queue_name = 'ml_task_queue'
channel.queue_declare(queue=queue_name)  # Создание очереди (если не существует)

def send_result(result: dict):
    try:
        response = requests.post(API_ENDPOINT, json=result, timeout=5)
        return {"message": "Task result sent successfully!"}
    except Exception as e:
        logger.error(f"Failed to send result to API: {e}")


# Функция, которая будет вызвана при получении сообщения
def callback(ch, method, properties, body):
    logger.info(f"Received: '{body}'")
    body = json.loads(body)
    cost = len(body.get("text").split())

    if body.get("balance") < cost:
        event_data = {
            "score": None,
            "response": f"Insufficient funds. You need {cost} credits.",
            "amount": cost
        }
    else:
        model = pipeline(body.get("task"), model=body.get("model_name"))
        score = model(body.get("text"))[0].get("score")
        event_data = {
            "score": score,
            "response": "Yes" if score > 0.5 else "No",
            "amount": cost
        }
    body.update(event_data)
    logger.info(body)
    send_result(body)

    ch.basic_ack(delivery_tag=method.delivery_tag)  # Ручное подтверждение обработки сообщения


# Подписка на очередь и установка обработчика сообщений
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False  # Автоматическое подтверждение обработки сообщений
)

logger.info('Waiting for messages. To exit, press Ctrl+C')
channel.start_consuming()
