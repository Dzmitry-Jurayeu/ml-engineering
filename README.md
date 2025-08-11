# ml-engineering

### Модуль 4. Проект

Для запуска сервиса необходимо создать .env файлы по соответствующим шаблонам .env.template.  
Запуск сервиса осуществляется командой:
```shell
docker compose up
```

В результате будет запущено 6 сервисов:
1. Сервис "app" – REST API интерфейс на FastAPI, доступный по адресу: http://localhost/api/docs#/
2. Сервис "web-ui" – Пользовательский WevUI интерфейс, доступный по адресу: http://localhost:8501/
3. Сервис "web-proxy" – Web Server на NGINX.
4. Сервис "rabbitmq" – Брокер сообщений на RabbitMQ, доступный по адресу: http://localhost:15672/
5. Сервис "worker" – 3 worker'а для обработки сообщений, поступающих в очередь RabbitMQ.
6. Сервис "database" – База данных PostgreSQL.

Для запуска тестов сервиса "app" из директории tests необходимо использовать команду, находясь в директории app:  
```python
pytest tests/test_user_routes.py tests/test_model_route.py tests/test_event_routes.py tests/test_balance_routes.py
```