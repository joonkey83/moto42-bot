import os
import time
import threading
import telebot
from flask import Flask

print("=== НОВЫЙ ЗАПУСК ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGERS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

@bot.message_handler(func=lambda m: True)
def forward(m):
    for uid in MANAGERS:
        try:
            bot.forward_message(uid, m.chat.id, m.message_id)
        except Exception as e:
            print(f"Ошибка пересылки: {e}")

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

def run_bot():
    while True:
        try:
            print("Запуск бота...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

# Запуск бота в отдельном потоке при старте
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask — это основной процесс для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
