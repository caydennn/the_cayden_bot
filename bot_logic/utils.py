from datetime import date, time, datetime

def hasTime(s):
    if len(s) > 10:
        return True 
    else: 
        return False
    # """
    # Parameters
    # ----------
    # s : string
    #     ISO 8601 formatted date / datetime string.

    # Returns
    # -------
    # tuple, (bool, datetime.datetime).
    #     boolean will be True if input specifies a time, otherwise False.
    # """
    # try:
    #     return False, datetime.combine(date.fromisoformat(s), time.min)
    # except ValueError:
    #     return True, datetime.fromisoformat(s)
        # do nothing else here; will raise an error if input can't be parsed