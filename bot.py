import os
import time
import threading
import telebot
from flask import Flask

print("=== БОТ С ПОДДЕРЖКОЙ ОТВЕТОВ ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения последнего chat_id клиента, который писал менеджеру
# (не идеально, но для 1–2 клиентов сойдёт)
client_chats = {}

@bot.message_handler(func=lambda m: m.chat.id not in MANAGER_IDS)
def handle_client(m):
    """Клиент пишет — пересылаем менеджерам"""
    for mid in MANAGER_IDS:
        try:
            forwarded = bot.forward_message(mid, m.chat.id, m.message_id)
            # Запоминаем, от кого пришло сообщение (для ответа)
            client_chats[mid] = m.chat.id
        except Exception as e:
            print(f"Не смог переслать менеджеру {mid}: {e}")

@bot.message_handler(func=lambda m: m.chat.id in MANAGER_IDS)
def handle_manager_reply(m):
    """Менеджер отвечает — отправляем клиенту"""
    if m.reply_to_message:
        # Ищем оригинального клиента через пересланное сообщение
        original_chat_id = m.reply_to_message.forward_from_chat.id if m.reply_to_message.forward_from_chat \
            else m.reply_to_message.forward_from.id if m.reply_to_message.forward_from \
            else None

        if original_chat_id:
            try:
                bot.send_message(original_chat_id, m.text)
                print(f"Ответ отправлен клиенту {original_chat_id}")
            except Exception as e:
                bot.reply_to(m, f"❌ Не смог отправить: {e}")
        else:
            bot.reply_to(m, "⚠️ Не удалось определить клиента. Ответьте на пересланное сообщение.")
    else:
        bot.reply_to(m, "ℹ️ Чтобы ответить клиенту — используйте «Ответить» на его сообщение.")

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
