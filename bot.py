import os
import time
import threading
import telebot
from flask import Flask

print("🚀 Запуск системы...")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Переменная BOT_TOKEN не установлена!")

MANAGERS = list(map(int, os.getenv("MANAGERS", "").split(",")))
if not MANAGERS:
    raise ValueError("❌ MANAGERS пуст или неверен")

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище последних клиентов
last_client = {}

@bot.message_handler(func=lambda m: m.chat.id not in MANAGERS)
def handle_client(m):
    for mid in MANAGERS:
        last_client[mid] = m.chat.id
        try:
            bot.forward_message(mid, m.chat.id, m.message_id)
        except Exception as e:
            print(f"[Пересылка] Ошибка для {mid}: {e}")

@bot.message_handler(func=lambda m: m.chat.id in MANAGERS)
def handle_manager(m):
    client_id = None
    if m.reply_to_message:
        if m.reply_to_message.forward_from:
            client_id = m.reply_to_message.forward_from.id
        elif m.reply_to_message.forward_from_chat:
            client_id = m.reply_to_message.forward_from_chat.id
    if not client_id:
        client_id = last_client.get(m.chat.id)
    if client_id:
        try:
            bot.send_message(client_id, m.text)
            print(f"[Ответ] Отправлен клиенту {client_id}")
        except Exception as e:
            print(f"[Ответ] Ошибка: {e}")
    else:
        print("[Ответ] Нет активного клиента")

# ЗАПУСК БОТА В ФОНЕ — ДО Flask
def run_bot():
    print("✅ Бот запущен и слушает...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔁 Перезапуск бота: {e}")
            time.sleep(5)

# Стартуем бота СРАЗУ
threading.Thread(target=run_bot, daemon=True).start()

# Flask — только для health-check
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

# Главный запуск
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"📡 Flask слушает на порту {port}")
    app.run(host="0.0.0.0", port=port)
