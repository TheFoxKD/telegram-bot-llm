import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import openai

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Настройка OpenAI API с OpenRouter
from openai import OpenAI

# Инициализируем клиент OpenAI с параметрами OpenRouter
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Словарь для хранения истории диалогов
user_messages = {}

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот, который использует AI для ответов на ваши вопросы. "
        "Просто напишите мне сообщение, и я постараюсь помочь!"
    )

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Инструкция по использованию бота:\n"
        "1. Просто напишите свой вопрос в чат\n"
        "2. Бот использует AI для генерации ответа\n"
        "3. Ваша история сообщений сохраняется для контекста\n"
        "4. Чтобы очистить историю, используйте команду /clear"
    )

# Обработчик команды /clear
@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    if user_id in user_messages:
        user_messages[user_id] = []
    await message.answer("История сообщений очищена!")

# Обработчик текстовых сообщений
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    # Инициализация истории сообщений пользователя, если ее нет
    if user_id not in user_messages:
        user_messages[user_id] = []

    # Добавление сообщения пользователя в историю
    user_messages[user_id].append({"role": "user", "content": user_input})

    # Ограничение истории сообщений до 10 для экономии токенов
    if len(user_messages[user_id]) > 10:
        user_messages[user_id] = user_messages[user_id][-10:]

    try:
        # Отправка индикатора набора текста
        await bot.send_chat_action(chat_id=user_id, action="typing")

        # Формирование запроса к LLM
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-thinking-exp:free",  # Полное название модели на OpenRouter
            messages=user_messages[user_id],
            extra_headers={
                "HTTP-Referer": "https://example.com",  # Требуется OpenRouter
                "X-Title": "Telegram Bot"  # Требуется OpenRouter
            }
        )

        # Получение ответа от LLM
        ai_response = response.choices[0].message.content

        # Добавление ответа LLM в историю
        user_messages[user_id].append({"role": "assistant", "content": ai_response})

        # Отправка ответа пользователю
        await message.answer(ai_response)

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз позже.")

# Функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())