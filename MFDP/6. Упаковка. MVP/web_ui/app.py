import streamlit as st
import requests
import json
from urllib.parse import urljoin
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components
import os
from datetime import datetime

ECM_PASS = os.getenv("ECM_PASS")
BACKEND_BASE = "http://app:8080"
SIGNIN_ENDPOINT = urljoin(BACKEND_BASE, "/api/users/signin")
STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501/")


def auth_request(method: str, url: str, **kwargs):
    token = cookies.get("access_token")
    resp = requests.request(method, url, cookies={"access_token": token}, **kwargs)
    if resp.status_code == 401:
        cookies["access_token"] = ""
        cookies.save()
        st.rerun()
    resp.raise_for_status()
    return resp

def safe_rerun():
    try:
        # если доступна, используем прямой rerun
        st.experimental_rerun()
    except Exception:
        # fallback: bump session_state trigger и остановить выполнение,
        # чтобы Streamlit перезапустил скрипт при следующем запросе
        st.session_state["_rerun_trigger"] = st.session_state.get("_rerun_trigger", 0) + 1
        st.stop()

def resolve_ref(ref: str, spec: dict) -> dict:
    parts = ref.lstrip("#/").split("/")
    node = spec
    for key in parts:
        node = node.get(key)
        if node is None:
            raise KeyError(f"Не удалось найти часть {key} в spec по {ref}")
    return node

def render_preds(preds):
    for p in preds:
        prediction_id = p['prediction_id']
        user_id = p['creator_id']
        prediction_date = datetime.fromisoformat(p['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"## Предсказание {prediction_id} — Пользователь {user_id} — Дата: {prediction_date}")

        candidates = p.get('candidates') or []
        if not candidates:
            st.write("Результаты пока не готовы")
            st.markdown("---")
            continue

        cols = st.columns(len(candidates))
        for col, c in zip(cols, candidates):
            with col:
                # картинка по URL; можно указать width
                if c.get("tank_image"):
                    st.image(c["tank_image"], caption=f"{c['tank_name']} ({c['tank_nation']}, уровень {c['tank_tier']})")
                else:
                    st.write("No image")
                st.write(f"Ранг: {c['rank']}")
                st.write(f"Предсказываемый урон: {c['predicted_damage']}")
        st.markdown("---")

st.set_page_config(page_title="Premium Tanks RecSys", layout="wide")

cookies = EncryptedCookieManager(
    password=ECM_PASS,
)

# Встроенный хук: пока cookie не готовы, не выводим UI

if not cookies.ready():
    st.stop()

qp = st.query_params

if "access_token" in qp:
    account_id_param = qp["access_token"]

    cookies["access_token"] = account_id_param
    saved = cookies.save()
    # st.success("Успешная авторизация.")

    # # очистим параметры в адресной строке
    # try:
    #     st.query_params.clear()
    # except Exception:
    #     st.experimental_set_query_params()
    #     pass
    #
    # # безопасно перезапускаем приложение
    # st.rerun()

# Получаем сохранённый токен (или None)
token = cookies.get("access_token")

# Заголовок и кнопка выхода
st.title("Premium Tanks RecSys UI")
st.subheader("Сервис для предсказания Топ-3 премиум танков от 5 уровня по урону.")

if token:
    st.sidebar.markdown("**Вы вошли в систему**")
    if st.sidebar.button("Выйти"):
        # if "access_token" in cookies:
        #     del cookies["access_token"]
        #     cookies.save()

        # try:
        #     st.query_params.clear()
        # except Exception:
        #     st.experimental_set_query_params()

        st.markdown(
            '<meta http-equiv="refresh" content="0; url=/">',
            unsafe_allow_html=True
        )
        st.stop()


# --- БЛОК НЕАВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---
if not token:

    if cookies.get("access_token") == "":
        st.write("Срок действия сессии истек. Авторизуйтесь снова.")
    st.subheader("Вход")
    if st.button("Войти"):
        try:
            signin_url = (
                    "http://localhost/api/users/signin"
                    f"?redirect={STREAMLIT_URL}"
            )

            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={signin_url}">',
                unsafe_allow_html=True
            )
            st.stop()
        except Exception as e:
            st.error(f"Ошибка при получении URL авторизации: {e}")

    st.stop()

# --- БЛОК АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---

# 1. Подтягиваем информацию о текущем пользователе
try:
    user_info_resp = requests.get(
        urljoin(BACKEND_BASE + "/", "api/users/me"),
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

target_user_id = None

# 5. Управление правами администратора
if is_admin_user:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Управление правами администратора")

    try:
        # Получаем список всех пользователей
        users_resp = requests.get(
            urljoin(BACKEND_BASE + "/", "api/users/get_all_users"),
            cookies={"access_token": token}
        )
        users_resp.raise_for_status()
        users_list = users_resp.json()

        # Формируем маппинг email => user_id
        ids = [u["user_id"] for u in users_list if u.get("user_id") != user_info.get("user_id")]
        sel_email = st.sidebar.selectbox(
            "Выберите пользователя",
            ids,
        )
        target_user_id = sel_email

        # Выбор действия: выдать или отозвать права администратора
        action = st.sidebar.radio(
            "Действие",
            ("Выдать права", "Отозвать права")
        )

        if st.sidebar.button("Применить"):
            if action == "Выдать права":
                endpoint = "api/users/grant_admin"
                success_msg = "Права администратора выданы"
            else:
                endpoint = "api/users/revoke_admin"
                success_msg = "Права администратора отозваны"

            url = urljoin(BACKEND_BASE + "/", endpoint)
            params = {"user_id": target_user_id}

            try:
                resp = requests.post(
                    url,
                    params=params,
                    cookies={"access_token": token}
                )
                resp.raise_for_status()
                st.sidebar.success(success_msg)
            except Exception as e:
                st.sidebar.error(f"Не удалось выполнить запрос: {e}")

    except Exception as e:
        st.sidebar.error(f"Не удалось загрузить список пользователей: {e}")

tab_names = ["Модели", "Предсказания"]
if is_admin_user:
    tab_names.append("Endpoints")

tabs = st.tabs(tab_names)
tab_objs = dict(zip(tab_names, tabs))

# 6. Models
with tab_objs["Модели"]:
    st.subheader("Доступные модели")
    models = auth_request("GET", urljoin(BACKEND_BASE + "/", "api/models")).json()
    st.table(models)

# 7. Predictions
with tab_objs["Предсказания"]:
    st.subheader("Новое предсказание")

    if st.button("Получить предсказание"):
        result = auth_request(
            "GET",
            urljoin(BACKEND_BASE + "/", "api/events/send_task"),
        ).json()
        st.json(result)

    st.markdown("---")
    st.subheader("История запросов к модели")
    preds = auth_request("GET", urljoin(BACKEND_BASE + "/", "api/events/retrieve_all_model_events")).json()
    render_preds(preds)

# 8. Endpoints — доступно только администратору
if is_admin_user:
    with tab_objs["Endpoints"]:
        # 4. Загрузка OpenAPI
        try:
            spec = requests.get(f"{BACKEND_BASE}/openapi.json").json()
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
            url = urljoin(BACKEND_BASE + "/", sel_path.lstrip("/"))
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
