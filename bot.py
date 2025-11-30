import os
import telebot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGERS = list(map(int, os.getenv("MANAGERS").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda m: True)
def forward(m):
    for uid in MANAGERS:
        try:
            bot.forward_message(uid, m.chat.id, m.message_id)
        except:
            pass

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
# обновление 1
