from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)


def send_message(chat_id, text):
    bot.send_message(chat_id=chat_id, text=text)