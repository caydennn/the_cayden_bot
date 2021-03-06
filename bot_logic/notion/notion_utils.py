
from lib2to3.pytree import convert
import os
import json
from pickle import NONE
import requests
from datetime import date, datetime
from dateutil.relativedelta import *
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from bot_logic.notion.NotionPage import NotionPage

time_zone = pytz.timezone('Asia/Singapore')
aware_local_now_temp = datetime.utcnow()

aware_local_now_temp = aware_local_now_temp.replace(tzinfo=pytz.utc)
aware_local_now = aware_local_now_temp.astimezone(time_zone)

TASKS_DB = os.environ.get("NOTION_TASKS_DB_ID")
print(f"tasks db: {TASKS_DB}")
NOTION_KEY = os.environ.get("NOTION_KEY")
base_url = "https://api.notion.com/v1"
headers = {
    "Authorization": NOTION_KEY,
    "Notion-Version": "2021-08-16",
    "Content-Type": "application/json"
}

"""
If raw is True, returns just a list of the InlineKeyboardButtons
"""


def generate_options_markup(raw=False):
    mark_done_button = InlineKeyboardButton(
        'Mark Done', callback_data="markdone")

    postpone_button = InlineKeyboardButton('Postpone',
                                           callback_data="pp")

    if raw:
        return [mark_done_button, postpone_button]
    keyboard = [
        [mark_done_button], [postpone_button]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def handle_error(update: Update, context, e: str):
    print(e)
    update.message.reply_text(
        "Something went wrong while retrieving your Notion tasks.")
    update.message.reply_text(
        f"Error: {e}")
    return


"""
TODO: Think about how to incorporate this.
Input: page - Notion page in Dictionary format
Returns: Custom NotionPage object
"""


def build_notion_page(page):
    id = page["id"]
    properties = page["properties"]
    title = properties["Name"]["title"][0]["text"]["content"]
    icon = page["icon"]["emoji"] if page["icon"] else ''
    done = properties["Done"]["checkbox"]

    # Dates
    date = properties["Date"]["date"] if properties["Date"] else None
    dueDate = properties["Due Date"]["date"]["start"] if (
        properties["Due Date"] and properties["Due Date"]["date"]) else None
    # _processDates()

    priority = properties["Priority"]["select"]["name"] if (
        properties["Priority"] and properties["Priority"]["select"]) else None
    url = page["url"]

    notionPage = NotionPage(id, title, icon, done,
                            date, dueDate, priority, url)


def retrieve_tasks_yesterday(filter_done=True):
    yesterday = aware_local_now+relativedelta(days=-1)
    yesterday_string = yesterday.strftime("%Y-%m-%d")
    done_filter = {
        "property": "Done",
        "checkbox": {
            "equals": False
        }
    }
    body = {
        "filter": {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "equals": yesterday_string
                    }

                }

            ]
        },

        "sorts": [
            {
                "property": "Priority",
                "direction": "ascending"
            }
        ]
    }

    if filter_done:
        print("Filtering done tasks...")
        body["filter"]["and"].append(done_filter)
    query_url = "{}/databases/{}/query".format(base_url, TASKS_DB)
    response = requests.post(query_url, headers=headers, json=body)
    response.raise_for_status()
    output = []
    for task_page in response.json()['results']:
        output.append(NotionPage(task_page))

    return output


def retrieve_tasks_today(filter_done=True):

    today_string = aware_local_now.strftime("%Y-%m-%d")
    done_filter = {
        "property": "Done",
        "checkbox": {
            "equals": False
        }
    }
    body = {
        "filter": {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "equals": today_string
                    }

                }

            ]
        },

        "sorts": [
            {
                "property": "Priority",
                "direction": "ascending"
            }
        ]
    }

    if filter_done:
        print("Filtering done tasks...")
        body["filter"]["and"].append(done_filter)
    query_url = "{}/databases/{}/query".format(base_url, TASKS_DB)
    response = requests.post(query_url, headers=headers, json=body)
    response.raise_for_status()

    output = []
    for task_page in response.json()['results']:
        output.append(NotionPage(task_page))

    return output


def retrieve_tasks_next_week(filter_done=True):
    today_string = aware_local_now.strftime("%Y-%m-%d")
    done_filter = {
        "property": "Done",
        "checkbox": {
            "equals": False
        }
    }

    body = {
        "filter": {
            "and": [
                # {
                #     "property": "Done",
                #     "checkbox": {
                #         "equals": False
                #     }
                # },
                {
                    "property": "Date",
                    "date": {
                        "is_not_empty": True
                    }
                },
                {
                    "or": [
                        {
                            "property": "Date",
                            "date": {
                                "equals": today_string
                            }
                        },
                        {
                            "property": "Date",
                            "date": {
                                "next_week": {}
                            }
                        }
                    ]
                }
            ]
        },
        "sorts": [
            {
                "property": "Date",
                "direction": "ascending"
            }
        ]
    }

    if filter_done:
        print("Filtering done tasks...")
        body["filter"]["and"].append(done_filter)

    query_url = "{}/databases/{}/query".format(base_url, TASKS_DB)
    response = requests.post(query_url, headers=headers, json=body)
    response.raise_for_status()

    output = []
    for task_page in response.json()['results']:
        output.append(NotionPage(task_page))
    # return response.json()['results']
    return output


def mark_as_done(pageId):
    payload = {
        "properties": {
            "Done": {
                "checkbox": True
            }
        }
    }
    page_url = "{}/pages/{}".format(base_url, pageId)
    response = requests.request(
        "PATCH", page_url, json=payload, headers=headers)
    response.raise_for_status()


def postpone(pageId, startDate = None, endDate = None):
    if startDate:
        start_date_string = convert_date_to_string(startDate)
    else:
        start_date_string = None

    if endDate:
        end_date_string = convert_date_to_string(startDate)
    else:
        end_date_string = None
    payload = {
        "properties": {
            "Date": {
                "date": {
                    # "start": "2022-01-26T08:00:00Z",
                    "start": start_date_string,
                    "end": end_date_string,
                    "time_zone": None
                }

            }
        }
    }

    page_url = "{}/pages/{}".format(base_url, pageId)
    response = requests.request(
        "PATCH", page_url, json=payload, headers=headers)

    response.raise_for_status()



def convert_date_to_string(date, format="%Y-%m-%d"):
    return date.strftime(format)

def generate_date_grouped_message(list_of_tasks, paginate=False):
    # 1) Group the events by date
    temp_dict = {}  # map of dateStrings to list of tasks
    for task in list_of_tasks:
        date = task.getStartDateString(showWeekday=True, showYear=False)
        if date not in temp_dict.keys():
            temp_dict[date] = []
        temp_dict[date].append(task.toEntryForm())

    # 2) Construct formatted reply
    if len(temp_dict) > 0:
        output = ""

        for date in temp_dict.keys():
            date_header = "*\-\-\-__" + date + "__\-\-\-*\n"
            output += date_header
            events = temp_dict[date]

            for idx, event in enumerate(events):
                temp = f"{idx+1}\){event}\n"
                output += temp

            if paginate and list(temp_dict.keys())[-1] != date:
                output += "@"  # delimiter to split
        if paginate:
            # output = output.rstrip("@")
            paginated_temp = output.split("@")
            return paginated_temp, list(temp_dict.keys())
        return output
    else:
        return None

# TODO: REFACTOR - take in paginator and formats it accordingly


def format_paginated_buttons(paginator):
    pass
