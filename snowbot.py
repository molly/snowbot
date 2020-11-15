# Copyright (c) 2015–2020 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from datetime import date, datetime, timedelta
from pytz import timezone
import json
import os
import re
import requests
import tweepy

from french_toast import get_french_toast
from config import *
from secrets import *
from utils import *

FORECAST_API_URL = "https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}"
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_date_range():
    today = date.today()
    return [today + timedelta(days=x) for x in range(6)]


def get_snow_data():
    url = FORECAST_API_URL.format(office=OFFICE, grid_x=GRID_X, grid_y=GRID_Y)
    data = fetch(url, True)
    return {
        "snowfallAmount": data["properties"]["snowfallAmount"],
        "probabilityOfPrecipitation": data["properties"]["probabilityOfPrecipitation"],
    }


def get_probability_for_duration(datetime_str, start_time, duration, data):
    numeric_duration = int(duration.strip("H"))
    total_duration = 0
    probability = []
    ind, curr_probability = next(
        (
            (ind, x)
            for ind, x in enumerate(data["probabilityOfPrecipitation"]["values"])
            if x["validTime"].startswith(datetime_str)
        ),
        (None, None),
    )
    if ind is None:
        log("Couldn't find corresponding probability for snowfall period")
        return 0
    else:
        curr_duration = parse_duration_string(curr_probability["validTime"])[1]
        if curr_duration != duration:
            while total_duration < numeric_duration:
                numeric_curr_duration = int(curr_duration.strip("H"))
                total_duration += numeric_curr_duration
                probability.append(
                    {
                        "numeric_duration": numeric_curr_duration,
                        "probability": curr_probability["value"],
                    }
                )
                ind += 1
                curr_probability = data["probabilityOfPrecipitation"]["values"][ind]
                curr_duration = parse_duration_string(curr_probability["validTime"])[1]
            hourly_probability = sum(
                [x["probability"] * x["numeric_duration"] for x in probability]
            ) / sum([x["numeric_duration"] for x in probability])
            return hourly_probability
        else:
            return curr_probability["value"]


def parse_snow_data(data, date_range):
    weather = {d: 0 for d in date_range}
    tz = timezone(TIMEZONE)
    amounts = data["snowfallAmount"]["values"]
    for amount in amounts:
        if amount["value"] > 0:
            [datetime_str, duration] = parse_duration_string(amount["validTime"])
            start_time = datetime.fromisoformat(datetime_str).astimezone(tz)
            if start_time.date() in weather:
                # Find probability of snowfall for this given duration
                probability = get_probability_for_duration(
                    datetime_str, start_time, duration, data
                )
                if probability >= PROBABILITY_THRESHOLD:
                    weather[start_time.date()] += amount["value"]
    return weather


def get_stored_snow_data():
    stored = None
    try:
        with open(os.path.join(__location__, "weather.json"), "r") as f:
            stored = json.load(f)
    finally:
        return stored


def diff_forecasts(current_forecast, prev_forecast, date_range):
    diff = {}
    for d in date_range:
        isodate = d.isoformat()
        if not (prev_forecast or isodate in prev_forecast) and current_forecast[d] > 0:
            diff[d] = {"new": current_forecast[d]}
        elif prev_forecast and prev_forecast[isodate] != current_forecast[d]:
            diff[d] = {
                "new": current_forecast[d],
                "old": prev_forecast[isodate],
            }
    return diff


def make_forecast_sentences(diff, date_range):
    if not diff:
        return
    sentences = []
    for d in date_range:
        if d in diff:
            if "old" in diff[d]:
                sentences.append(
                    "{0}: {1} in. (prev. {2})".format(
                        d.strftime("%a, %-m/%d"),
                        get_accumulation_string(diff[d]["new"]),
                        get_accumulation_string(diff[d]["old"]),
                    )
                )
            else:
                sentences.append(
                    "{0}: {1} in.".format(
                        d.strftime("%a, %-m/%d"),
                        get_accumulation_string(diff[d]["new"]),
                    )
                )
    return sentences


def make_tweets(sentences, append=None):
    tweet = ""
    tweets = []
    if append:
        sentences.append(append)
    while sentences:
        if len(tweet) + len(sentences[0]) > 279:
            # Append what we have and start a new tweet.
            tweets.append(tweet)
            tweet = "(cont'd.):"
        else:
            if len(tweet) != 0:
                tweet += "\n"
            tweet += sentences.pop(0)
    tweets.append(tweet)
    return tweets


def send_tweets(tweets):
    auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_TOKEN)
    api = tweepy.API(auth)
    for tweet in tweets:
        try:
            api.update_status(tweet)
            log('Tweeted: "' + tweet)
        except tweepy.TweepError as e:
            log("Failed to tweet: " + e.reason)


def store_forecast(current_forecast):
    forecast_to_store = {}
    for key, val in current_forecast.items():
        forecast_to_store[key.isoformat()] = val
    with open(os.path.join(__location__, "weather.json"), "w") as f:
        json.dump(forecast_to_store, f, indent=2)


def run():
    # Gather forecast, etc. data
    snow_data = get_snow_data()
    date_range = get_date_range()
    current_forecast = parse_snow_data(snow_data, date_range)
    prev_forecast = get_stored_snow_data()
    diff = diff_forecasts(current_forecast, prev_forecast, date_range)
    if ENABLE_FRENCH_TOAST:
        toast_details = get_french_toast()

    # Form tweets
    sentences = make_forecast_sentences(diff, date_range)
    if ENABLE_FRENCH_TOAST:
        tweets = make_tweets(sentences, toast_details["sentence"])
    else:
        tweets = make_tweets(sentences)

    # Send tweets
    if len(tweets):
        send_tweets(tweets)
    else:
        print("No changed forecast to tweet.")
    if ENABLE_FRENCH_TOAST:
        should_tweet_gif = get_should_tweet_gif(
            toast_details["current_toast_level"], toast_details["gif_last_tweeted"]
        )
        if should_tweet_gif:
            log("Tweeting toast gif at " + datetime.now().isoformat())
            send_tweets([SEVERE_TOAST_GIF])

    # Store forecast for next time
    store_forecast(current_forecast)


if __name__ == "__main__":
    run()
