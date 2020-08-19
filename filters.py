import math
from datetime import datetime

# ------------- Custom filters -------------
def minutes(value):
    """ Converts milliseconds to minutes format"""
    minutes = value / 60000.0
    if minutes > 1.0:
        seconds = minutes % math.floor(minutes) * 60.0
    # if track is less than 1 minute long
    else:
        seconds = minutes * 60.0
    output = "{:02d}:{:02d}".format(math.floor(minutes), math.floor(seconds))
    return output

def datetimeformat(value):
    """ Converts ISO 8601 format to YYYY-MM-DD"""
    if value is None:
        return ""
    # Create date object from given ISO 8601 string
    temp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return temp.strftime("%Y-%m-%d")
