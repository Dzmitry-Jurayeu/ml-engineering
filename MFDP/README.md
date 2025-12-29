# Рекомендательная система премиум-танков для игры Tanks Blitz

### Информация о проекте
Сервис предназначен для персональных рекомендаций топ-3 премиум-танка по урону игроку на основе его статистики игры на обычных танках.  
С презентацией по проекту можно ознакомиться по [ссылке](https://docs.google.com/presentation/d/1IuSZdavwnjeEllOtOxgP_lJ7mt0mbb6EQjj-teB7rYU/edit?usp=sharing).

### Техническая информация
Готовый проект находится в директории "6. Упаковка. MVP".  
Для запуска сервиса необходимо создать .env файлы по соответствующим шаблонам .env.template.  
Запуск сервиса осуществляется командой:
```shell
docker compose up -d
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
pytest tests/test_model_route.py tests/test_event_routes.py tests/test_user_routes.py tests/test_tank_route.py
```
P.S. Перед повторным запуском тестов необходимо удалить файл "testing.db".