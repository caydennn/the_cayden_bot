
from dotenv import load_dotenv
from os.path import join, dirname
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.utils.helpers import escape_markdown
from telegram.ext import Dispatcher
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import Bot
from bot_logic import forms_handler
from bot_logic.notion import notion_handler
from markupsafe import escape
import os
from flask import Flask, request
from threading import Thread
from queue import Queue
from datetime import datetime
import pytz
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP,WMonthTelegramCalendar
time_zone = pytz.timezone('Asia/Singapore')
now = datetime.now(time_zone)

def test(update, context):
    update.message.reply_text(text="*test*", parse_mode='MarkdownV2')


def inline_test(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton(
                'Mark Done', callback_data="action#mark_done"),
            InlineKeyboardButton('Postpone', callback_data="action#postpone"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("hey", reply_markup=reply_markup)



def calendar_test(update,context):
    
    print (now.date())
    calendar, step = WMonthTelegramCalendar(min_date = now.date()).build()
    update.message.reply_text(f"Select {LSTEP[step]}",
                     reply_markup=calendar)

def calendar_test_callback(update, context):
    c = update.callback_query
    print(c.data)
    result, key, step = WMonthTelegramCalendar(min_date = now.date()).process(c.data)
    print(type(result))
    if not result and key:
        c.edit_message_text(f"Select {LSTEP[step]}",
                              reply_markup=key)
    elif result:
        c.edit_message_text(f"You selected {result}")
# Bot Setup


TOKEN = os.environ.get("TOKEN")


def setup():
    global bot
    bot = Bot(token=TOKEN)

    update_queue = Queue()

    dispatcher = Dispatcher(bot, update_queue)

    ##### Register handlers here #####

    dispatcher.add_handler(CommandHandler(
        "today", notion_handler.get_tasks_today))
    dispatcher.add_handler(CommandHandler(
        "today_all", notion_handler.get_tasks_today_all))
    dispatcher.add_handler(CommandHandler(
        "upcoming", notion_handler.get_tasks_upcoming))
    dispatcher.add_handler(CommandHandler(
    "upcoming_all", notion_handler.get_tasks_upcoming_all))
    dispatcher.add_handler(CallbackQueryHandler(notion_handler.markdone_callback, pattern="^markdone#"))
    dispatcher.add_handler(CallbackQueryHandler(notion_handler.markdone_choice_callback, pattern="^markdone"))
    dispatcher.add_handler(CallbackQueryHandler(notion_handler.pagination_callback, pattern="^task_paginator#"))

    dispatcher.add_handler(CallbackQueryHandler(notion_handler.postpone_choose_date, pattern="^pp#"))
    dispatcher.add_handler(CallbackQueryHandler(notion_handler.postpone_choice_callback, pattern="^pp"))
    dispatcher.add_handler(CallbackQueryHandler(notion_handler.postpone_callback, pattern="^cbcal_"))

    # ! Dev Handlers
  
    # dispatcher.add_handler(CommandHandler("test_cal", calendar_test))
    # dispatcher.add_handler(CallbackQueryHandler(calendar_test_callback, pattern="^cbcal_"))

    dispatcher.add_handler(CommandHandler("inline_test", inline_test))
    
    # dispatcher.add_handler(CallbackQueryHandler(
    #     inline_test_callback, pattern="^action#"))
    # dispatcher.add_handler(CallbackQueryHandler(
    #     inline_test_markdone_callback, pattern="^markdone#"))

    # Start the thread
    thread = Thread(target=dispatcher.start, name='dispatcher')
    thread.start()
    return update_queue


update_queue = setup()


URL = os.environ.get("URL")
global MY_CHAT_ID, TEST_GROUP_ID
MY_CHAT_ID = os.environ.get("MY_CHAT_ID")
TEST_GROUP_ID = os.environ.get("TEST_GROUP_ID")


app = Flask(__name__)


@app.route("/{}".format(TOKEN), methods=["POST"])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    # get the chat_id to be able to respond to the same user
    update = Update.de_json(request.get_json(force=True), bot)

    chat_id = update.effective_message.chat.id
    # Make the bot only reply to me :)
    if chat_id == 80749729:
        update_queue.put(update)
 


    return '.'


@app.route("/forms/<form_id>", methods=["POST"])
def send_test(form_id):
    # bot.sendMessage(chat_id=, text="test send !")
    if form_id == 'arts_fiesta':
        request_data = request.get_json()
        response = forms_handler.handle_arts_fiesta(request_data)
        if response:
            bot.sendMessage(chat_id=os.environ.get(
                "ARTS_FIESTA_GROUP_ID"), text=response,  parse_mode='MarkdownV2')
            # bot.sendMessage(chat_id=TEST_GROUP_ID, text=response,  parse_mode= 'MarkdownV2' )
        return f'json_received for {form_id}'

    return f'test_id: {escape(form_id)}'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    print("Setting webhook...")
    # For development, use ngrok to port forward flask app
    if (os.environ.get('MODE') == 'dev'):
        DEV_URL = os.environ.get("DEV_URL")
        print("In production mode... Setting to: {}".format(DEV_URL))
        s = bot.setWebhook(
            '{DEV_URL}/{HOOK}'.format(DEV_URL=DEV_URL, HOOK=TOKEN))
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

    #! If on Mac, RUN THE APP WITH 'python flask run --port=5003
    # This is because Mac os Mojave uses the default port for flask.
    # Refer to this https://stackoverflow.com/questions/70247195/flask-ngrok-access-to-subdomain-ngrok-io-was-denied-403-error
    if (os.environ.get('MODE') == 'dev'):
        app.run(threaded=True, port=5003)
    else:
        app.run(threaded=True)
