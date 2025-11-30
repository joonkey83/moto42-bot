import os
import time
import threading
import telebot
from flask import Flask

print("🚀 Запуск системы...")

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGERS = list(map(int, os.getenv("MANAGERS", "").split(",")))

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не задан!")
if not MANAGERS:
    raise RuntimeError("❌ MANAGERS пуст!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

last_client = {}

@bot.message_handler(func=lambda m: m.chat.id not in MANAGERS)
def handle_client(m):
    for mid in MANAGERS:
        last_client[mid] = m.chat.id
    for mid in MANAGERS:
        try:
            bot.forward_message(mid, m.chat.id, m.message_id)
        except Exception as e:
            print(f"[Forward] {e}")

@bot.message_handler(func=lambda m: m.chat.id in MANAGERS)
def handle_reply(m):
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
            print(f"[Reply] → {client_id}")
        except Exception as e:
            print(f"[Reply error] {e}")
    else:
        print("[Reply] Клиент не найден")

# === ЗАПУСК БОТА ТОЛЬКО ОДИН РАЗ ===
_bot_started = False

def ensure_bot_started():
    global _bot_started
    if _bot_started:
        return
    _bot_started = True
    def run():
        print("✅ Бот начал polling...")
        while True:
            try:
                bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
            except Exception as e:
                print(f"🔁 Перезапуск: {e}")
                time.sleep(5)
    threading.Thread(target=run, daemon=True).start()

# Запускаем бота ДО Flask
ensure_bot_started()

# Flask — только для health-check
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
