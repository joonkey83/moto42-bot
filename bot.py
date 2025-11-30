import os
import time
import threading
import telebot
from flask import Flask

print("=== ЗАПУСК БОТА ДЛЯ RENDER ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

client_chats = {}

@bot.message_handler(func=lambda m: m.chat.id not in MANAGER_IDS)
def handle_client(m):
    for mid in MANAGER_IDS:
        try:
            bot.forward_message(mid, m.chat.id, m.message_id)
        except Exception as e:
            print(f"Пересылка менеджеру {mid} не удалась: {e}")

@bot.message_handler(func=lambda m: m.chat.id in MANAGER_IDS)
def handle_manager_reply(m):
    if m.reply_to_message:
        orig = None
        if m.reply_to_message.forward_from:
            orig = m.reply_to_message.forward_from.id
        elif m.reply_to_message.forward_from_chat:
            orig = m.reply_to_message.forward_from_chat.id

        if orig:
            try:
                bot.send_message(orig, m.text)
                print(f"Ответ отправлен клиенту {orig}")
            except Exception as e:
                bot.reply_to(m, f"❌ Ошибка: {e}")
        else:
            bot.reply_to(m, "⚠️ Не могу определить клиента. Ответьте на пересланное сообщение.")
    else:
        bot.reply_to(m, "ℹ️ Используйте «Ответить» на сообщение клиента.")

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

# === ЗАПУСК БОТА БЕЗ if __name__ == "__main__" ===
def start_bot_in_background():
    def run():
        while True:
            try:
                print("➡️ Бот запущен и слушает сообщения...")
                bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
            except Exception as e:
                print(f"🔄 Перезапуск бота из-за ошибки: {e}")
                time.sleep(5)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# Запускаем бота сразу при импорте
start_bot_in_background()
