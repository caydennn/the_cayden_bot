from unittest.util import strclass
from telegram.utils.helpers import escape_markdown
from datetime import datetime
from dateutil.parser import parse

from bot_logic.utils import hasTime

NO_DUE_DATE = "No Due Date"


class NotionPage:
    def __init__(self, pageInfo):
        self.pageId = pageInfo["id"]
        self.properties = pageInfo["properties"]
        self.title = self.properties["Name"]["title"][0]["text"]["content"]
        self.icon = pageInfo["icon"]["emoji"] if pageInfo["icon"] else ''
        self.done = self.properties["Done"]["checkbox"]

        # Dates
        self.date = self.properties["Date"]["date"] if self.properties["Date"] else None
        self.dueDate = self.properties["Due Date"]["date"]["start"] if (
            self.properties["Due Date"] and self.properties["Due Date"]["date"]) else None
        self._processDates()

        self.priority = self.properties["Priority"]["select"]["name"] if (
            self.properties["Priority"] and self.properties["Priority"]["select"]) else None
        self.url = pageInfo["url"]

    def _processDates(self):
        if self.date:
            if self.date["start"]:
                if hasTime(self.date["start"]):
                    # datetime
                    print(f"DATETIME EXISTS: {self.date}")
                    self.date["type"] = "datetime"
                else:
                    # date
                    print(f"DATE EXISTS: {self.date}")
                    self.date["type"] = "date"
                self.date["start"] = parse(self.date["start"])

            if self.date["end"]:
                if hasTime(self.date["end"]):
                    # datetime
                    self.date["type"] = "datetime"
                else:
                    # date
                    self.date["type"] = "date"
                self.date["end"] = parse(self.date["end"])
        if self.dueDate:
            self.dueDate = datetime.strptime(self.dueDate, "%Y-%m-%d")
            print(f"converted to date: {self.dueDate}")

    def _escape_markdown(self, text, version=2):
        return escape_markdown(text, version=version)

    def getPageId(self):
        return self.pageId
    def getDone(self):
        return self.done

    def getTitle(self) -> str:
        return self.title

    def getIcon(self) -> str:
        return self.icon

    def getDateType(self):
        if self.date:
            return self.date["type"]

    def getStartDate(self):
        if self.date:
            return self.date["start"]
        return None

    def getStartDay(self):
        if self.date:
            return self.getStartDate().wee

    def getEndDate(self):
        if self.date:
            return self.date["end"]
        return None

    def getStartDateString(self, showWeekday=False, showYear=True) -> str:
        if self.date:
            base = "%d/%m"
            return self.date["start"].strftime(base + f"{'/%y' if showYear else ''}" + f"{' %A' if showWeekday else ''} ")
        return "-"

    def getStartTimeString(self) -> str:
        if self.date["type"] == "datetime":
            return self.date["start"].strftime("%H:%M")
        return "Full Day"

    def getEndDateString(self) -> str:
        if self.date:
            return self.date["end"].strftime("%d/%m/%y")
        return "-"

    def getEndTimeString(self) -> str:
        if self.date:
            return self.date["end"].strftime("%H:%M")
        return "No End Time"

    def getDueDate(self):
        return self.dueDate

    def getDueDateString(self) -> str:
        if self.dueDate:
            return self.dueDate.strftime("%d/%m/%y")
        return "-"

    def getPriority(self) -> str:
        if self.priority:
            return self.priority
        return "-"

    def getUrl(self) -> str:
        return self.url

    def toEntryForm(self):
        """
        <Icon>[<Title>](<url>) 
        Due: <DueDate> 
        Priority: <Priority>
        """

        return f"""*{self.getIcon()} [{self._escape_markdown(self.getTitle())}]({self._escape_markdown(self.getUrl())})*
    *Time:* {self._escape_markdown(self.getStartTimeString() + ((" -> " + self.getEndTimeString()) if self.getEndDate() else ""))}
    *Due:* {self._escape_markdown(self.getDueDateString())}
    *Priority:* {self._escape_markdown(self.getPriority())}
    *Done:* {"✅ "if self.getDone() else "❌" }
"""
