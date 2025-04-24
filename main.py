import vk_api
from flask import Flask, request
import os
from transformers import pipeline

# Получаем значения из переменных окружения (их будем задавать в Render.com позже)
VK_TOKEN = os.environ.get("VK_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")
CONFIRMATION_STRING = os.environ.get("CONFIRMATION_STRING")

# Авторизация в ВК с помощью специального API-токена сообщества
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Загрузка модели с Hugging Face для бесплатной генерации текста на русском
generator = pipeline('text-generation', model='cointegrated/rubert-tiny')

# Flask - это библиотека для создания веб-приложения
app = Flask(__name__)

# Функция генерации ответа на комментарий
def generate_answer(prompt):
    responses = generator(prompt, max_length=100, num_return_sequences=1, do_sample=True)
    generated_text = responses[0]['generated_text']
    # Убираем из ответа повтор вопроса:
    answer = generated_text[len(prompt):].strip()
    # Простая проверка, если очень короткий ответ:
    if len(answer) < 3:
        answer = "Хороший вопрос! 🤔"
    return answer

# Основной обработчик входящих запросов
@app.route('/', methods=['POST'])
def vk_webhook():
    # Получаем пришедший запрос от ВК
    data = request.json

    # На первоначальный запрос-подтверждение присылаем специальную строку
    if data['type'] == 'confirmation':
        return CONFIRMATION_STRING

    # Если пришёл новый комментарий к записи
    if data['type'] == 'wall_reply_new':
        comment = data['object']
        comment_id = comment['id']
        post_id = comment['post_id']
        user_text = comment['text']

        # Тут AI генерирует текст ответа на комментарий
        reply_text = generate_answer(user_text)

        # Публикуем комментарий-ответ в ветке комментариев ВК
        vk.wall.createComment(
            owner_id=-int(GROUP_ID),
            post_id=post_id,
            reply_to_comment=comment_id,
            message=reply_text
        )

    # ВКонтакте требует именно такой ответ, чтобы понять, что запрос получен:
    return 'ok', 200
    import os
import requests

HUGGINGFACE_TOKEN = os.environ['HUGGINGFACE_TOKEN']

# Функция генерации ответа через API Hugging Face (лёгкая модель)
def generate_ai_answer(user_text):
    API_URL = "https://api-inference.huggingface.co/models/sberbank-ai/rugpt3small_based_on_gpt2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

    response = requests.post(API_URL, headers=headers, json={"inputs": user_text})

    if response.status_code != 200:
        return "Извините, сейчас не могу ответить."

    generated_text = response.json()[0]['generated_text']
    reply = generated_text[len(user_text):].strip()
    return reply

# запуск Flask приложения (на сервере render.com)
if __name__ == '__main__':
    app.run()
