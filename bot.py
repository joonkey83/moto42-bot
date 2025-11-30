import os
import time
import threading
import telebot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

# --- Обработка клиентов ---
@bot.message_handler(func=lambda m: m.chat.id not in MANAGER_IDS)
def handle_client(m):
    for mid in MANAGER_IDS:
        try:
            bot.forward_message(mid, m.chat.id, m.message_id)
        except Exception as e:
            print(f"[Пересылка] Ошибка для менеджера {mid}: {e}")

# --- Обработка ответов менеджеров ---
@bot.message_handler(func=lambda m: m.chat.id in MANAGER_IDS and m.reply_to_message is not None)
def handle_manager_reply(m):
    # Получаем оригинальное сообщение, на которое ответили
    reply_msg = m.reply_to_message

    # Определяем ID клиента
    client_id = None

    if reply_msg.forward_from:
        # Обычный пользователь
        client_id = reply_msg.forward_from.id
    elif reply_msg.forward_from_chat:
        # Канал или бот (редко)
        client_id = reply_msg.forward_from_chat.id
    else:
        # Если пересылка скрыта (например, "forwarded from @username")
        # Telegram не даёт ID — но в таком случае клиент и так не получит ответ
        pass

    if client_id:
        try:
            bot.send_message(client_id, m.text)
            print(f"[Ответ] Отправлен клиенту {client_id}")
        except Exception as e:
            bot.reply_to(m, f"❌ Не удалось отправить: {e}")
    else:
        bot.reply_to(m, "⚠️ Не могу определить клиента. Убедитесь, что вы отвечаете на пересланное сообщение.")

# --- Запуск бота ---
def start_bot():
    while True:
        try:
            print("✅ Бот запущен и готов к работе...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔁 Перезапуск из-за ошибки: {e}")
            time.sleep(5)

# Запуск в фоне (для Render)
threading.Thread(target=start_bot, daemon=True).start()
