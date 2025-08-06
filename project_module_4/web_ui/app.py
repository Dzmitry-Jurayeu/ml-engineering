import streamlit as st
import requests
import json
from urllib.parse import urljoin
from streamlit_cookies_manager import EncryptedCookieManager
import os

ECM_PASS = os.getenv("ECM_PASS")


def auth_request(method: str, url: str, **kwargs):
    token = cookies.get("access_token")
    resp = requests.request(method, url, cookies={"access_token": token}, **kwargs)
    if resp.status_code == 401:
        cookies["access_token"] = ""
        cookies.save()
        st.rerun()
    resp.raise_for_status()
    return resp


def resolve_ref(ref: str, spec: dict) -> dict:
    parts = ref.lstrip("#/").split("/")
    node = spec
    for key in parts:
        node = node.get(key)
        if node is None:
            raise KeyError(f"Не удалось найти часть {key} в spec по {ref}")
    return node


st.set_page_config(page_title="Toxic Chat", layout="wide")

cookies = EncryptedCookieManager(
    password=ECM_PASS,
)

# Встроенный хук: пока cookie не готовы, не выводим UI
if not cookies.ready():
    st.stop()

# Получаем сохранённый токен (или None)
token = cookies.get("access_token")

# Заголовок и кнопка выхода
st.title("Toxic Chat UI")
st.subheader("Сервис для определения токсичности сообщений.")

if token:
    st.sidebar.markdown("**Вы вошли в систему**")
    if st.sidebar.button("Выйти"):
        cookies["access_token"] = ""
        cookies.save()  # сбросить токен
        st.rerun()

# --- БЛОК НЕАВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---
if not token:
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])

    # Форма Login
    with tab1:
        if cookies.get("access_token") == "":
            st.write("Время жизни токена истекло. Авторизуйтесь снова.")
        st.subheader("Вход")
        username = st.text_input("Email")
        password = st.text_input("Пароль", type="password")
        if st.button("Войти"):
            try:
                resp = requests.post(
                    urljoin("http://app:8080/api/users" + "/", "signin"),
                    data={"username": username, "password": password}
                )
                resp.raise_for_status()
                data = resp.json()
                tok = data.get("access_token")
                if not tok:
                    st.error("Токен не получен")
                else:
                    cookies["access_token"] = tok
                    cookies.save()
                    st.success("Успешный вход")
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка входа: {e}")

    # Форма Registration
    with tab2:
        st.subheader("Регистрация")
        new_email = st.text_input("Новый Email")
        new_password = st.text_input("Пароль", type="password", key="reg_pw")
        # Новый чекбокс для админ-прав
        is_admin = st.checkbox(
            "Администратор",
            help="Отметьте, если пользователь должен получить права администратора"
        )
        if st.button("Зарегистрироваться"):
            try:
                resp = requests.post(
                    "http://app:8080/api/users" + "/" + "signup",
                    json={
                        "email": new_email,
                        "password": new_password,
                        "is_admin": is_admin
                    }
                )
                resp.raise_for_status()
                st.success("Регистрация прошла успешно. Выполните вход.")
            except Exception as e:
                st.error(f"Ошибка регистрации: {e}")
    st.stop()

# --- БЛОК АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---
base_url = "http://app:8080"

# 1. Подтягиваем информацию о текущем пользователе
try:
    user_info_resp = requests.get(
        urljoin(base_url + "/", "api/users/me"),
        cookies={"access_token": token}
    )
    user_info_resp.raise_for_status()
    user_info = user_info_resp.json()
    is_admin_user = user_info.get("is_admin", False)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        cookies["access_token"] = ""
        cookies.save()
        st.rerun()
except Exception as e:
    st.error(f"Не удалось получить информацию о пользователе: {e}")
    st.stop()

# --- UI для баланса ---
st.sidebar.markdown("## Баланс")

# 2. Отобразим текущий баланс
try:
    bal_resp = requests.get(
        urljoin(base_url + "/", "api/balances/me"),
        cookies={"access_token": token}
    )
    bal_resp.raise_for_status()
    current_balance = bal_resp.json().get("balance_value", 0)
except Exception as e:
    st.sidebar.error(f"Ошибка при получении баланса: {e}")
    current_balance = None

st.sidebar.write("Текущий баланс:", current_balance)

# 3. Поле и кнопка для пополнения
st.sidebar.markdown("---")
recharge_amount = st.sidebar.number_input("Сумма пополнения", min_value=0, step=1)

# 4. Если администратор — выпадающий список пользователей
target_user_id = None
if is_admin_user:
    try:
        users_resp = requests.get(
            urljoin(base_url + "/", "api/users/get_all_users"),
            cookies={"access_token": token}
        )
        users_resp.raise_for_status()
        users_list = users_resp.json()
        # Собираем mapping email => id
        email_to_id = {u["email"]: u["user_id"] for u in users_list}
        sel_email = st.sidebar.selectbox(
            "Выберите пользователя для пополнения",
            list(email_to_id.keys())
        )
        target_user_id = email_to_id[sel_email]
    except Exception as e:
        st.sidebar.error(f"Не удалось загрузить список пользователей: {e}")

if st.sidebar.button("Пополнить баланс"):
    if recharge_amount <= 0:
        st.sidebar.error("Сумма пополнения должна быть больше нуля")
    else:
        payload = {"amount": recharge_amount}
        # если админ, укажем user_id
        params_data = {}
        if target_user_id is not None:
            params_data["user_id"] = target_user_id
            url = urljoin(base_url + "/", "api/events/new_balance_event")
        else:
            url = urljoin(base_url + "/", "api/events/new_my_balance_event")

        try:
            recharge_resp = requests.post(
                url,
                json=payload,
                params=params_data,
                cookies={"access_token": token}
            )
            recharge_resp.raise_for_status()
            st.sidebar.success("Баланс успешно пополнен")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Не удалось пополнить баланс: {e}")

tab_names = ["Баланс", "Модели", "Предсказания"]
if is_admin_user:
    tab_names.append("Endpoints")

tabs = st.tabs(tab_names)
tab_objs = dict(zip(tab_names, tabs))

# 5. Balance History
with tab_objs["Баланс"]:
    st.subheader("История пополнения баланса")
    history = auth_request("GET", urljoin(base_url + "/", "api/events/retrieve_all_balance_events")).json()
    st.table(history)

# 6. Models
with tab_objs["Модели"]:
    st.subheader("Доступные модели")
    models = auth_request("GET", urljoin(base_url + "/", "api/models")).json()
    st.table(models)

# 7. Predictions
with tab_objs["Предсказания"]:
    st.subheader("Новое предсказание")
    text = st.text_area("Введите текст для оценки")

    # Подгружаем список моделей
    all_models = auth_request("GET", urljoin(base_url + "/", "api/models")).json()
    tasks = sorted({m["task"] for m in all_models})
    selected_task = st.selectbox("Выберите задачу", tasks)

    # Шаг 2: фильтруем модели под выбранную задачу
    filtered_models = [m for m in all_models if m["task"] == selected_task]
    model_names = [m["model_name"] for m in filtered_models]

    # Шаг 3: выбор конкретной модели по имени
    selected_model_name = st.selectbox("Выберите модель", model_names)
    model_map = {
        "task": selected_task,
        "model_name": selected_model_name
    }

    if st.button("Получить предсказание"):
        if not text.strip():
            st.error("Текст для предсказания не может быть пустым")
        else:
            payload = {
                "text": text,
            }
            result = auth_request(
                "POST",
                urljoin(base_url + "/", "api/events/send_task"),
                json=payload,
                params=model_map
            ).json()
            st.json(result)

    st.markdown("---")
    st.subheader("История запросов к модели")
    preds = auth_request("GET", urljoin(base_url + "/", "api/events/retrieve_all_model_events")).json()
    st.table(preds)

# 8. Endpoints — доступно только администратору
if is_admin_user:
    with tab_objs["Endpoints"]:
        # 4. Загрузка OpenAPI
        try:
            spec = requests.get(f"{base_url}/openapi.json").json()
        except Exception as e:
            st.error(f"Не удалось загрузить OpenAPI: {e}")
            st.stop()

        # 9. Список путей и методов
        paths = spec.get("paths", {})
        endpoint_choices = []
        for path, methods in paths.items():
            for method, info in methods.items():
                # Пропускаем пути регистрации и логина
                if (path.endswith("/signin")
                        or path.endswith("/signup")
                        or path.endswith("/task_result")
                        or path.endswith("/me")):
                    continue
                endpoint_choices.append((info.get("summary"), path, method))
        endpoint_choices.sort()

        choice = st.selectbox("Выберите эндпоинт", [c[0] for c in endpoint_choices])
        _, sel_path, sel_method = next(c for c in endpoint_choices if c[0] == choice)
        meta = paths[sel_path][sel_method]

        st.markdown("---")
        st.subheader(f"{sel_method.upper()} {sel_path}")
        if meta.get("description"):
            st.write(meta["description"])

        # 10. Генерация формы по JSON-схеме
        schema = {}
        if meta.get("requestBody", {}).get("content", {}).get("application/json"):
            schema = meta["requestBody"]["content"]["application/json"]["schema"]

        if "$ref" in schema:
            schema = resolve_ref(schema["$ref"], spec)

        req_data = {}
        if schema.get("properties"):
            required = schema.get("required", [])
            for name, prop in schema["properties"].items():
                title = prop.get("title", name)
                default = prop.get("default", None)
                dtype = prop.get("type", "string")

                if dtype == "integer":
                    req_data[name] = st.number_input(title, value=default or 0, step=1)
                elif dtype == "number":
                    req_data[name] = st.number_input(title, value=default or 0.0, format="%.5f")
                elif dtype == "boolean":
                    req_data[name] = st.checkbox(title, value=bool(default))
                elif dtype == "array":
                    txt = st.text_area(f"{title} (JSON-массив)", value=json.dumps(default or []), height=100)
                    try:
                        req_data[name] = json.loads(txt)
                    except:
                        st.error(f"Некорректный JSON в поле {name}")
                else:
                    req_data[name] = st.text_input(title, value=str(default or ""))

        required_params = [
            p for p in meta.get("parameters", [])
            if p.get("required", False)
        ]
        optional_params = [
            p for p in meta.get("parameters", [])
            if not p.get("required", False) and p.get("name") != "access_token"
        ]

        # Словарь для собранных данных
        params_data = {}

        if len(required_params) > 0:
            st.write("### Заполните обязательные параметры API")

        for param in required_params:
            name = param["name"]
            location = param.get("in", "query")  # path, query, cookie, header
            schema = param.get("schema", {})
            title = schema.get("title", name)
            dtype = schema.get("type", "string")

            label = f"{title} ({location}) *"

            if dtype == "integer":
                req_data[name] = st.number_input(
                    label,
                    value=0,
                    step=1,
                    key=name
                )
                params_data[name] = req_data[name]
            elif dtype == "number":
                req_data[name] = st.number_input(
                    label,
                    value=0.0,
                    format="%.5f",
                    key=name
                )
                params_data[name] = req_data[name]
            elif dtype == "boolean":
                req_data[name] = st.checkbox(
                    label,
                    value=False,
                    key=name
                )
                params_data[name] = req_data[name]
            else:
                # Для строковых типов
                req_data[name] = st.text_input(
                    label,
                    value="",
                    key=name
                )
                params_data[name] = req_data[name]

        for param in optional_params:
            name = param["name"]
            location = param.get("in", "query")  # path, query, cookie, header
            schema = param.get("schema", {})
            title = schema.get("title", name)
            dtype = schema.get("type", "string")

            label = f"{title} (Optional)"

            if dtype == "integer":
                req_data[name] = st.number_input(
                    label,
                    value=schema.get("default", 0),
                    step=1,
                    key=name
                )
                params_data[name] = req_data[name]
            elif dtype == "number":
                req_data[name] = st.number_input(
                    label,
                    value=schema.get("default", 0.0),
                    format="%.5f",
                    key=name
                )
                params_data[name] = req_data[name]
            elif dtype == "boolean":
                req_data[name] = st.checkbox(
                    label,
                    value=schema.get("default", False),
                    key=name
                )
                params_data[name] = req_data[name]
            else:
                # Для строковых типов
                req_data[name] = st.text_input(
                    label,
                    value=schema.get("default", ""),
                    key=name
                )
                params_data[name] = req_data[name]

        # Показываем собранные значения
        if len(params_data) > 0:
            st.write("#### Примеры необходимых параметров:", params_data)

        # 11. Отправка запроса с токеном в заголовках
        if st.button("Отправить запрос"):
            token = cookies.get("access_token")
            req_cookies = {"access_token": token}
            if "{" in sel_path:
                try:
                    sel_path = sel_path.format(**req_data)
                except KeyError as e:
                    st.write("Добавьте параметр:", e.args[0])
            url = urljoin(base_url + "/", sel_path.lstrip("/"))
            try:
                resp = requests.request(sel_method, url, json=req_data, params=params_data, cookies=req_cookies)
                if resp.status_code == 401:
                    cookies["access_token"] = ""
                    cookies.save()  # сбросить токен
                    st.rerun()
                st.write("Код ответа:", resp.status_code)
                st.json(resp.json())
            except Exception as e:
                st.error(f"Ошибка при запросе: {e}")
