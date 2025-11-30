import os
import time
import threading
import telebot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

# Временное хранилище: {manager_id: last_client_chat_id}
last_client = {}

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

@bot.message_handler(func=lambda m: m.chat.id not in MANAGER_IDS)
def handle_client(m):
    client_id = m.chat.id
    # Сохраняем ID клиента для каждого менеджера
    for mid in MANAGER_IDS:
        last_client[mid] = client_id
        try:
            bot.forward_message(mid, client_id, m.message_id)
        except Exception as e:
            print(f"[Forward] Error to {mid}: {e}")

@bot.message_handler(func=lambda m: m.chat.id in MANAGER_IDS)
def handle_manager(m):
    if m.reply_to_message:
        # Ответ на пересланное сообщение → получаем client_id из контекста
        client_id = None
        if m.reply_to_message.forward_from:
            client_id = m.reply_to_message.forward_from.id
        else:
            # Если ID скрыт — используем последнего клиента (простое решение)
            client_id = last_client.get(m.chat.id)

        if client sent and client_id:
            try:
                bot.send_message(client_id, m.text)
                print(f"[Reply] Sent to {client_id}")
                return
            except Exception as e:
                print(f"[Reply] Failed: {e}")

        # Если не получилось — пытаемся использовать последний chat_id
        client_id = last_client.get(m.chat.id)
        if client_id:
            try:
                bot.send_message(client_id, m.text)
                print(f"[Reply via fallback] Sent to {client_id}")
                return
            except Exception as e:
                bot.reply_to(m, f"❌ Не смог отправить: {e}")
                return

    # Если не ответ на сообщение — просто игнорируем или логируем
    bot.reply_to(m, "ℹ️ Используйте «Ответить» на сообщение клиента.")

def run_bot():
    while True:
        try:
            print("✅ Бот слушает...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔁 Ошибка: {e}")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()
