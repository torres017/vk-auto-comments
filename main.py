import vk_api
from flask import Flask, request
import os
import requests

# Получаем значения из переменных окружения (зададим на Render.com)
VK_TOKEN = os.environ.get('VK_TOKEN')
GROUP_ID = os.environ.get('GROUP_ID')
CONFIRMATION_STRING = os.environ.get('CONFIRMATION_STRING')
HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN')

# Авторизация в VK
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

app = Flask(__name__)

# Функция генерации ответа с использованием HuggingFace API
def generate_ai_answer(user_text):
    API_URL = "https://api-inference.huggingface.co/models/sberbank-ai/rugpt3small_based_on_gpt2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": user_text})

    if response.status_code != 200:
        return "Извините, сейчас не могу ответить."

    generated_text = response.json()[0]['generated_text']
    reply = generated_text[len(user_text):].strip()

    if len(reply) < 2:
        reply = "Спасибо за комментарий!"

    return reply

@app.route('/', methods=['POST'])
def vk_webhook():
    data = request.json

    if data['type'] == 'confirmation':
        return CONFIRMATION_STRING

    if data['type'] == 'wall_reply_new':
        comment = data['object']

        # проверка, чтобы бот не реагировал на свои собственные комментарии
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

# запуск Flask приложения на сервере render.com
if __name__ == '__main__':
    app.run()
