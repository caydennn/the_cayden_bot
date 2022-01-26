from asyncio import tasks
import pytz
from datetime import datetime

from csv import excel_tab
from glob import escape
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from bot_logic.notion.NotionPage import NotionPage
from bot_logic.notion.notion_utils import generate_date_grouped_message,  generate_options_markup, handle_error, mark_as_done, postpone, retrieve_tasks_next_week, retrieve_tasks_today
from telegram.utils.helpers import escape_markdown
from telegram_bot_pagination import InlineKeyboardPaginator
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP,WMonthTelegramCalendar

time_zone = pytz.timezone('Asia/Singapore')
now = datetime.now(time_zone)

UPCOMING_TASKS_CONTEXT = "upcoming_tasks"
TODAY_TASKS_CONTEXT = "today_tasks"
'''
"Name": {
                    "id": "title",
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Capstone Conti Meeting ",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "Capstone Conti Meeting ",
                            "href": null
                        }
                    ]
                }
                '''

"""
/today
"""
def get_tasks_today(update: Update, context):
    try:
        update.message.reply_text("Loading your tasks for today...")

        today_tasks = retrieve_tasks_today()
    except requests.exceptions.HTTPError as e:
        update.message.reply_text("Something went wrong")
        return
   
    send_today_response(update, context, today_tasks)

"""
/today_all
"""
def get_tasks_today_all(update: Update, context):
    try:
        update.message.reply_text("Loading ALL your tasks for today...")
        today_tasks = retrieve_tasks_today(filter_done=False)
    except requests.exceptions.HTTPError as e:
        update.message.reply_text("Something went wrong")
        return
   
    send_today_response(update, context, today_tasks)


def send_today_response(update: Update, context, list_of_tasks):
    try:
        reply = []
        for task in list_of_tasks:
            reply.append(task.toEntryForm())
        if len(reply) > 0:
            context.user_data["task_context"] = TODAY_TASKS_CONTEXT
            context.user_data[TODAY_TASKS_CONTEXT] = list_of_tasks
            name = update.effective_user.first_name if update.effective_user.first_name else update.effective_user.username
            options_markup = generate_options_markup()
            update.message.reply_text(
                f"Hello {name}. Here are your tasks for today: ")
            update.message.reply_text(
                "\n".join(reply), parse_mode="MarkdownV2", reply_markup=options_markup)
        else:
            update.message.reply_text("You have no tasks today")

    except Exception as e:
        print(e)
        update.message.reply_text(
            "Something went wrong... :/ Please try again later.")


"""
/upcoming
"""
def get_tasks_upcoming(update: Update, context):
    try:
        update.message.reply_text("Loading your upcoming tasks...")
        tasks_next_week = retrieve_tasks_next_week(filter_done=True)
    except requests.exceptions.HTTPError as e:
        handle_error(update, context, e)

    send_upcoming_response(update, context, tasks_next_week)


"""
/upcoming_all 
"""
def get_tasks_upcoming_all(update: Update, context):
    try:
        update.message.reply_text("Loading ALL your upcoming tasks...")

        tasks_next_week = retrieve_tasks_next_week(filter_done=False)
    except requests.exceptions.HTTPError as e:
        handle_error(update, context, e)

    send_upcoming_response(update, context, tasks_next_week)


def send_upcoming_response(update: Update, context, list_of_tasks):
    try:
        paginate = False
        if len(list_of_tasks) < 4:
            output = generate_date_grouped_message(list_of_tasks)
        else:
            paginate = True
            output = generate_date_grouped_message(
                list_of_tasks, paginate=True)

            # output = paginated_output[0]

        if output:
            context.user_data["task_context"] = UPCOMING_TASKS_CONTEXT
            context.user_data[UPCOMING_TASKS_CONTEXT] = list_of_tasks

            name = update.effective_user.first_name if update.effective_user.first_name else update.effective_user.username
            update.message.reply_text(
                f"Hello {name}. Here are your upcoming tasks for the next week: ")

            if paginate:
                paginator = InlineKeyboardPaginator(
                    len(output),
                    data_pattern='task_paginator#{page}'
                )

                paginator_labels = [
                    task.getStartDateString(showWeekday=False, showYear=False) for task in list_of_tasks]

                print ("paginator labels")
                print (paginator_labels)



                paginator.current_page_label = paginator_labels[0] 
                paginator.next_page_label = ">"
                paginator.previous_page_label = "<"

                context.user_data[UPCOMING_TASKS_CONTEXT +
                                  "-paginate-data"] = output
                context.user_data[UPCOMING_TASKS_CONTEXT +
                                  "-paginator-labels"] = paginator_labels



                options_buttons = generate_options_markup(raw=True)
                for button in options_buttons:
                    paginator.add_before(button)
                update.message.reply_text(
                    text=output[0],
                    reply_markup=paginator.markup,
                    parse_mode='MarkdownV2'
                )
            else:
                options_markup = generate_options_markup()
                update.message.reply_text(
                    output, parse_mode="MarkdownV2", reply_markup=options_markup)
        else:
            update.message.reply_text("You have no upcoming tasks!")
    except Exception as e:
        print(e)
        update.message.reply_text(
            "Something went wrong... :/ Please try again later.")


def markdone_choice_callback(update: Update, context):
    # Don't need to edit text, just give the user a keyboard to select which task to mark done
    query = update.callback_query
    query.answer()
    task_context = context.user_data["task_context"]
    tasks = context.user_data[task_context]

    keyboard = []
    temp = []

    for task in tasks:
        print("TASk")
        print(task.getTitle())
        if (task.getDone() == False):
            temp.append(InlineKeyboardButton(task.getTitle(),
                        callback_data=f"markdone#{task.getPageId()}"))
            print(temp)
            if len(temp) == 2:
                keyboard.append(temp)
                temp = []
    if len(temp) > 0:
        keyboard.append(temp)

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_reply_markup(reply_markup=reply_markup)


def markdone_callback(update: Update, context):
    query = update.callback_query
    task_context = context.user_data["task_context"]
    print(f"TASK CONTEXT: {task_context}")
    _, pageId = query.data.split('#')

    try:
        pageTitle = None
        upcoming_tasks = context.user_data[task_context]
        for task in upcoming_tasks:

            if task.getPageId() == pageId:
                pageTitle = task.getTitle()
                # remove from the list
                upcoming_tasks.remove(task)
            elif task.getDone():
                upcoming_tasks.remove(task)

        query.answer(
            f"Marking {pageTitle if pageTitle else pageId} as done...")
        mark_as_done(pageId)

        # refresh message with output
        context.user_data[task_context] = upcoming_tasks
        output = generate_date_grouped_message(upcoming_tasks)
        if output:
            update.effective_message.reply_text(
                f"Nice! Here are your remaining tasks")
            query.edit_message_text(text=output, parse_mode="MarkdownV2")
        else:
            query.edit_message_text(
                text="No more tasks left", parse_mode="MarkdownV2")

    except Exception as e:
        query.edit_message_text("Sorry something went wrong")
        update.message.reply_text(e)


def pagination_callback(update, context):
    query = update.callback_query

    query.answer()

    page = int(query.data.split('#')[1])

    task_context = context.user_data["task_context"]
    paginate_data = context.user_data[task_context + "-paginate-data"]
    paginator_labels = context.user_data[task_context + "-paginator-labels"]

    paginator = InlineKeyboardPaginator(
        len(paginate_data),
        current_page=page,
        data_pattern='task_paginator#{page}'
    )

    paginator.current_page_label = paginator_labels[page-1]

    options_buttons = generate_options_markup(raw=True)
    for button in options_buttons:
        paginator.add_before(button)

    
    query.edit_message_text(
        text=paginate_data[page - 1],
        reply_markup=paginator.markup,
        parse_mode='MarkdownV2'
    )


def postpone_choice_callback(update, context):
    query = update.callback_query
    query.answer()
    task_context = context.user_data["task_context"]
    tasks = context.user_data[task_context]

    keyboard = []
    temp = []

    for task in tasks:
        print("TASk")
        print(task.getTitle())
        if (task.getDone() == False):
            temp.append(InlineKeyboardButton(task.getTitle(),
                        callback_data=f"pp#{task.getPageId()}"))
            print(temp)
            if len(temp) == 2:
                keyboard.append(temp)
                temp = []
    if len(temp) > 0:
        keyboard.append(temp)

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_reply_markup(reply_markup=reply_markup)

def postpone_choose_date(update, context):
    query = update.callback_query
    task_context = context.user_data["task_context"]
    print(f"TASK CONTEXT: {task_context}")

    _, pageId = query.data.split('#')
    context.user_data["task_to_postpone"] = pageId

    calendar, step = WMonthTelegramCalendar(min_date = now.date()).build()
    query.edit_message_reply_markup(reply_markup=calendar)
    
    # update.message.reply_text(f"Select {LSTEP[step]}",
    #                     reply_markup=calendar)

def postpone_callback(update, context):
    task_context = context.user_data["task_context"]
    tasks = context.user_data[task_context]

    task_id_to_postpone = context.user_data["task_to_postpone"] 
    c = update.callback_query
    print(c.data)
    result, key, step = WMonthTelegramCalendar(min_date = now.date()).process(c.data)
    print(type(result))
    if not result and key:
        c.eedit_message_reply_markup(reply_markup=key)
    elif result:
        # c.edit_message_text(f"You selected {result}")
        try: 
            
            postpone(task_id_to_postpone, result)
            
            for task in tasks:
                pageTitle = "Your task"
                if task.getPageId() == task_id_to_postpone:
                    pageTitle = task.getIcon() + task.getTitle()
                    break 
            c.edit_message_text(f"{pageTitle} has been postponed to {result}")

        except requests.exceptions.HTTPError as e:
            update.message.reply_text("Something went wrong")
            return