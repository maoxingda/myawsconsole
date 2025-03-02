import re
from datetime import datetime, timedelta

from django import template

register = template.Library()


@register.filter
def date_format(value):
    datetime_pattern = re.compile(r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d.?(?:\d\d\d)?Z?")

    value = str(value)

    if datetime_pattern.match(value):
        return (
            datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=8)
        ).isoformat()
    else:
        return value  # Return the original value if it doesn't match datetime pattern
