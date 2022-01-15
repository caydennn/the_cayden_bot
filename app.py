
import os
from dotenv import load_dotenv
from os.path import join, dirname
from flask import Flask, request

from bot_logic.responses import get_response
import telegram

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


global bot
TOKEN = os.environ.get("TOKEN")
bot = telegram.Bot(token=TOKEN)
URL = os.environ.get("URL")


app = Flask(__name__)


@app.route("/{}".format(TOKEN), methods=["POST"])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    # get the chat_id to be able to respond to the same user
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    # get the message id to be able to reply to this specific message
    # Telegram understands UTF-8, so encode text for unicode compatibility
    msg_id = update.message.message_id
    text = update.message.text.encode('utf-8').decode()
    print("got text message :", text)  # here we call our super AI
    response = get_response(text)  # now just send the message back
    # notice how we specify the chat and the msg we reply to
    bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    print("Setting webhook...")
     # For development, use ngrok to port forward flask app
    if (os.environ.get('MODE') == 'dev'):
       DEV_URL = os.environ.get("DEV_URL")
       print("In production mode... Setting to: {}".format(DEV_URL))
       s = bot.setWebhook('{DEV_URL}/{HOOK}'.format(DEV_URL=DEV_URL, HOOK=TOKEN))
    else:
       s = bot.setWebhook('{URL}/{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route("/")
def index():
    return 'the bot is running'

if __name__ == '__main__':
    app.run(threaded=True)