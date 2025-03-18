# filename: get_current_time.py
import datetime
import pytz

def get_current_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.datetime.now(tz)
        return current_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    except pytz.UnknownTimeZoneError:
        return "Unknown timezone. Please provide a valid timezone."

# Example usage:
print(get_current_time('UTC'))  # Get current time in UTC
print(get_current_time('America/New_York'))  # Get current time in New York timezone