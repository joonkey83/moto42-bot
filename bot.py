import os
import time
import threading
import telebot
from flask import Flask

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

# Временное хранилище последнего клиента для каждого менеджера
last_client_chat = {}

# === Flask для Render ===
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

# === Обработка клиентов ===
@bot.message_handler(func=lambda m: m.chat.id not in MANAGER_IDS)
def handle_client(m):
    client_id = m.chat.id
    # Запоминаем chat_id клиента для каждого менеджера
    for mid in MANAGER_IDS:
        last_client_chat[mid] = client_id
    # Пересылаем всем менеджерам
    for mid in MANAGER_IDS:
        try:
            bot.forward_message(mid, client_id, m.message_id)
        except Exception as e:
            print(f"[Пересылка] Ошибка для {mid}: {e}")

# === Обработка ответов менеджеров ===
@bot.message_handler(func=lambda m: m.chat.id in MANAGER_IDS)
def handle_manager(m):
    client_id = None

    # Если ответ на пересланное сообщение — пробуем получить ID
    if m.reply_to_message:
        if m.reply_to_message.forward_from:
            client_id = m.reply_to_message.forward_from.id
        elif m.reply_to_message.forward_from_chat:
            client_id = m.reply_to_message.forward_from_chat.id

    # Если не получилось — используем последний chat_id
    if not client_id:
        client_id = last_client_chat.get(m.chat.id)

    if client_id:
        try:
            bot.send_message(client_id, m.text)
            print(f"[Ответ] Отправлен клиенту {client_id}")
        except Exception as e:
            print(f"[Ответ] Ошибка: {e}")
            bot.reply_to(m, "❌ Не смог отправить ответ клиенту.")
    else:
        bot.reply_to(m, "⚠️ Нет активного клиента. Подождите первого сообщения.")

# === Запуск бота в фоне ===
def run_bot():
    print("✅ Бот запущен и слушает на порту", os.getenv("PORT", 10000))
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔁 Перезапуск бота: {e}")
            time.sleep(5)

# Запускаем бота в отдельном потоке
threading.Thread(target=run_bot, daemon=True).start()

# === Запуск Flask на нужном порту ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
