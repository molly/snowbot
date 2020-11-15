# Be sure to update these values if you decide to run this bot!

APP_NAME = "Boston Snowbot"
REPO_URL = "https://github.com/molly/snowbot"

# Precipitation probability above which we will add snowfall to prediction
PROBABILITY_THRESHOLD = 0

# Get these values from hitting this URL with your latitude and longitude:
# https://www.weather.gov/documentation/services-web-api#/default/get_points__point_
OFFICE = "BOX"  # resp["properties"]["officeId"]
GRID_X = 70  # resp["properties"]["gridX"]
GRID_Y = 76  # resp["properties"]["gridY"]
TIMEZONE = "US/Eastern"

# If your bot isn't reporting Boston weather, set this to False or this will make no
# sense
ENABLE_FRENCH_TOAST = True
# Delay between tweeting toast level gif if the above is set to True
TOAST_GIF_DELAY = 24 * 60 * 60  # 24 hours
# GIF to tweet if the french toast level is "severe"
SEVERE_TOAST_GIF = "https://www.mollywhite.net/storage/breadandmilk.gif"
