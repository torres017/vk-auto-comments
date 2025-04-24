import vk_api
from flask import Flask, request
import os
import requests

# Получение значений из переменных окружения
VK_TOKEN = os.environ.get('VK_TOKEN')
GROUP_ID = os.environ.get('GROUP_ID')
CONFIRMATION_STRING = os.environ.get('CONFIRMATION_STRING')
print(f"HUGGINGFACE_TOKEN='{HUGGINGFACE_TOKEN}'")
# Авторизация в VK
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

app = Flask(__name__)

# Функция генерации ответа с помощью HuggingFace API
def generate_ai_answer(user_text):
    API_URL = "https://api-inference.huggingface.co/models/DeepPavlov/rudialogpt3_medium_based_on_gpt2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": user_text})

    # добавил: здесь подробно проверяем ответ от модели
    if response.status_code != 200:
        return f"Ошибка API: status {response.status_code}, detail: {response.text}"

    result = response.json()

    if isinstance(result, dict) and 'error' in result:
        # добавил: выводим конкретную ошибку от самой модели huggingface
        return f"Ошибка модели: {result['error']}"

    generated_text = result[0]['generated_text']
    reply = generated_text[len(user_text):].strip()

    if len(reply) < 2:
        reply = "Спасибо за комментарий!"

    return reply

# Основной обработчик VK-вебхуков
@app.route('/', methods=['POST'])
def vk_webhook():
    data = request.json

    if data['type'] == 'confirmation':
        return CONFIRMATION_STRING

    if data['type'] == 'wall_reply_new':
        comment = data['object']

        # проверка, чтобы бот не реагировал на самого себя
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

# запуск Flask-приложения на сервере
if __name__ == '__main__':
    app.run()
