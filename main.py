import vk_api
from flask import Flask, request
import os
import requests
import time

# Переменные окружения
VK_TOKEN = os.environ.get('VK_TOKEN')
GROUP_ID = os.environ.get('GROUP_ID')
CONFIRMATION_STRING = os.environ.get('CONFIRMATION_STRING')
HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN')

if VK_TOKEN is None or GROUP_ID is None or CONFIRMATION_STRING is None or HUGGINGFACE_TOKEN is None:
    raise ValueError("Переменные окружения не заданы на Render.com")

# Авторизация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Создание Flask-приложения
app = Flask(__name__)

# Функция получения ответа по API HuggingFace с retry, верный API URL
def generate_ai_answer(user_text, retries=3):
    API_URL = "https://api-inference.huggingface.co/models/sberbank-ai/rugpt3medium_based_on_gpt2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

    for _ in range(retries):
        response = requests.post(API_URL, headers=headers, json={"inputs": user_text})

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, dict) and "error" in result:
                return f"Ошибка модели: {result['error']}"

            generated_text = result[0].get('generated_text', '')
            reply = generated_text[len(user_text):].strip()

            if len(reply) < 2:
                reply = "Спасибо за комментарий!"

            return reply

        elif response.status_code == 503:
            time.sleep(3)
            continue
        else:
            return f"Ошибка API: статус {response.status_code}, детали: {response.text}"

    return "Сервис временно недоступен."

# Обработка вебхуков VK
@app.route('/', methods=['POST'])
def vk_webhook():
    data = request.json

    if data['type'] == 'confirmation':
        return CONFIRMATION_STRING

    if data['type'] == 'wall_reply_new':
        comment = data['object']

        if comment['from_id'] == -int(GROUP_ID):
            return 'ok', 200

        comment_id = comment['id']
        post_id = comment['post_id']
        user_text = comment['text']

        reply_text = generate_ai_answer(user_text)

        vk.wall.createComment(
            owner_id=-int(GROUP_ID),
            post_id=post_id,
            reply_to_comment=comment_id,
            message=reply_text
        )

    return 'ok', 200

# Запуск Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
