import vk_api
from flask import Flask, request
import os
import openai
import time

# Переменные окружения
VK_TOKEN = os.environ.get('VK_TOKEN')
GROUP_ID = os.environ.get('GROUP_ID')
CONFIRMATION_STRING = os.environ.get('CONFIRMATION_STRING')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if VK_TOKEN is None or GROUP_ID is None or CONFIRMATION_STRING is None or OPENAI_API_KEY is None:
    raise ValueError("Переменные окружения не заданы на Render.com")

openai.api_key = OPENAI_API_KEY

# Авторизация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Создание Flask-приложения
app = Flask(__name__)

# Функция для запроса к OpenAI API GPT (с retry-повторами при ошибке)
def generate_ai_answer(user_text, retries=3):
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # или используй "gpt-4", если доступен
                messages=[
                    {"role": "system", "content": "Ты доброжелательный бот для комментариев сообщества ВК, отвечай кратко и по теме."},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            reply = response.choices[0].message.content.strip()
            return reply

        except openai.error.OpenAIError as e:
            print(f"Ошибка OpenAI (попытка {attempt + 1}/{retries}): {e}")
            time.sleep(2)

    return "Временно не могу ответить, попробуйте позже."

# Обработка вебхуков запросов VK
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

# Запуск Flask-сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
