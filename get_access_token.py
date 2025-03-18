import requests

# Замените на свои данные
CLIENT_ID = "ВАШ_CLIENT_ID"
CLIENT_SECRET = "ВАШ_CLIENT_SECRET"
AUTH_CODE = "ВАШ_AUTH_CODE"
REDIRECT_URI = "ВАШ_REDIRECT_URI"

# URL для получения токена
TOKEN_URL = "https://hh.ru/oauth/token"

# Параметры запроса
payload = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": AUTH_CODE,
    "redirect_uri": REDIRECT_URI
}

# Отправка запроса
response = requests.post(TOKEN_URL, data=payload)

# Проверка ответа
if response.status_code == 200:
    tokens = response.json()
    print("Access Token:", tokens.get("access_token"))
    print("Refresh Token:", tokens.get("refresh_token"))
else:
    print("Ошибка получения токена:", response.json())
