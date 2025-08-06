import streamlit as st
import requests
import json
from urllib.parse import urljoin
from streamlit_cookies_manager import EncryptedCookieManager
import os

ECM_PASS = os.getenv("ECM_PASS")


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
# 1. Ввод базового URL и загрузка OpenAPI
base_url = "http://app:8080"
try:
    spec = requests.get(f"{base_url}/openapi.json").json()
except Exception as e:
    st.error(f"Не удалось загрузить OpenAPI: {e}")
    st.stop()

# 2. Список путей и методов
paths = spec.get("paths", {})
endpoint_choices = []
for path, methods in paths.items():
    for method, info in methods.items():
        # Пропускаем пути регистрации и логина
        if path.endswith("/signin") or path.endswith("/signup") or path.endswith("/task_result"):
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

# 3. Генерация формы по JSON-схеме
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
# else:
#     raw = st.text_area("Введите JSON-тело запроса", height=200, value="{}")
#     try:
#         req_data = json.loads(raw)
#     except:
#         st.error("Некорректный JSON")
#         st.stop()

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

# 4. Отправка запроса с токеном в заголовках
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
