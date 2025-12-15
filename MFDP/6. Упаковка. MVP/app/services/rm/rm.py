import pika
import os

RABBIT_HOST = os.getenv("RABBIT_HOST")
RABBIT_PORT = os.getenv("RABBIT_PORT")
PIKA_USERNAME = os.getenv("RABBITMQ_DEFAULT_USER")
PIKA_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host=RABBIT_HOST,  # Замените на адрес вашего RabbitMQ сервера
    port=RABBIT_PORT,          # Порт по умолчанию для RabbitMQ
    virtual_host='/',   # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username=PIKA_USERNAME,  # Имя пользователя по умолчанию
        password=PIKA_PASSWORD   # Пароль по умолчанию
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

def send_task(message:str):
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Имя очереди
    queue_name = 'ml_task_queue'

    # Отправка сообщения
    channel.queue_declare(queue=queue_name)  # Создание очереди (если не существует)

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message
    )

    # Закрытие соединения
    connection.close()