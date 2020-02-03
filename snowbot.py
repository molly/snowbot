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


from datetime import datetime
import json
import os
import re
from secrets import *
import tweepy
from utils import fetch, log

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

forecast_url = "https://api.darksky.net/forecast/{}/42.3587,-71.0567?exclude=currently,minutely,hourly,flags" \
               "&lang=en&units=us".format(FORECAST_KEY)
french_toast_url = "http://universalhub.com/toast.xml"


def get_weather():
    """Fetch forecast from DarkSky API."""
    with open(os.path.join(__location__, "tmp.json"), 'r') as f:
        return json.load(f)
    # return fetch(forecast_url, is_json=True)


def get_french_toast():
    """Fetch french toast level from Universal Hub."""
    with open(os.path.join(__location__, "tmp_f.xml"), 'r') as f:
        return f.read()
    # return fetch(french_toast_url)


def process_weather(blob):
    """Pull out relevant portions of the forecast for storage and comparison."""
    weather = {}
    data = blob["daily"]["data"]
    for day in data:
        timestamp = str(day["time"])
        weather[timestamp] = {}
        weather[timestamp]["date_str"] = datetime.fromtimestamp(day["time"]).strftime("%a, %-m/%d")
        if day["precipType"] == "snow" and float(day["precipProbability"]) > 0.5:
            weather[timestamp]["accumulation"] = float(day["precipAccumulation"])
        elif "light snow" in day["summary"].lower():
            # Sometimes if it's sleety the precipType will be something else but the forecast summary describes snow
            # in which case we can assume <1 inch snow.
            weather[timestamp]["accumulation"] = 0.1
        else:
            weather[timestamp]["accumulation"] = 0
    return weather


def process_french_toast(text):
    """Get the french toast status."""
    m = re.search(r'<status>(.*?)</status>', text)
    if m:
        level = m.group(1)
        return level
    return None


def get_stored_weather():
    """Get the stored weather from the previous run."""
    try:
        with open(os.path.join(__location__, "weather.json"), 'r') as f:
            stored = json.load(f)
    except IOError:
        stored = None
    return stored


def diff_weather(new, stored):
    diff = {
        "weather": {},
        "toast": {}
    }
    changed = False
    for day in new["weather"]:
        if stored and day in stored["weather"]:
            if new["weather"][day]["accumulation"] != stored["weather"][day]["accumulation"]:
                changed = True
                diff["weather"][day] = {
                    "date_str": new["weather"][day]["date_str"],
                    "old": stored["weather"][day]["accumulation"],
                    "new": new["weather"][day]["accumulation"]
                }
        else:
            diff["weather"][day] = {
                "date_str": new["weather"][day]["date_str"],
                "new": new["weather"][day]["accumulation"]
            }
    if new["toast"]:
        if not stored or "toast" not in stored:
            diff["toast"] = {"new": new["toast"]}
        elif new["toast"] != stored["toast"]:
            changed = True
            diff["toast"] = {
                "new": new["toast"],
                "old": stored["toast"]
            }
    return diff if changed or not stored else {}


def store_weather(new):
    """Store the newest weather for next time."""
    with open(os.path.join(__location__, "weather.json"), "w") as f:
        json.dump(new, f, indent=2)


def get_accumulation_str(inches):
    """Round the float to the nearest integer, and display <1 if it rounds to 0."""
    rounded = round(inches)
    return str(rounded) if rounded > 0 else "<1"


def make_weather_sentences(diff):
    """Form sentences to tweet out of diff."""
    sentences = []
    for day in sorted(diff["weather"].keys()):
        if "old" in diff["weather"][day]:
            sentences.append(
                "{0}: {1} in. (prev. {2})".format(
                    diff["weather"][day]["date_str"],
                    get_accumulation_str(diff["weather"][day]["new"]),
                    get_accumulation_str(diff["weather"][day]["old"])
                )
            )
        else:
            if diff["weather"][day]["new"] != 0:
                sentences.append(
                    "{0}: {1} in.".format(
                        diff["weather"][day]["date_str"],
                        get_accumulation_str(diff["weather"][day]["new"])
                    )
                )
    return sentences


def make_french_toast_sentence(diff):
    if "toast" in diff:
        if "old" in diff["toast"]:
            return "New french toast alert level: {0} (prev. {1})".format(diff["toast"]["new"], diff["toast"]["old"])
        elif diff["toast"]["new"] != "low":
            return "New french toast alert level: {0}".format(diff["toast"]["new"])
    return None


def make_tweets(weather_sentences, french_toast_sentence, toast):
    """Format our sentences into tweet-length chunks."""
    tweet = ""
    tweets = []
    while weather_sentences:
        if len(tweet) + len(weather_sentences[0]) > 279:
            # Append what we have and start a new tweet.
            tweets.append(tweet)
            tweet = "(cont'd.):"
        else:
            if len(tweet) != 0:
                tweet += "\n"
            tweet += weather_sentences.pop(0)
    tweets.append(tweet)

    if french_toast_sentence:
        french_toast_emojis = " ".join(["🍞", "🥛", "🥚"])
        emojis = ""
        if toast["new"] == "severe":
            # It's a pain to see if there are spaces between these, so easier to just construct the string from an array
            emojis = " ".join(["🆘", "🔴", "‼️", "🚨"])
        elif toast["new"] == "high":
            emojis = " ".join(["🔴", "🚨", "🔴"])
        elif toast["new"] == "elevated":
            emojis = " ".join("⚠️", "⚠️", "⚠️")

        if len(emojis) > 0:
            # Update sentence with our emojis if need be
            french_toast_sentence += "\n" + emojis + " " + french_toast_emojis + " " + emojis[::-1]

        # Attribute the french toast rating
        french_toast_sentence += "\nhttp://www.universalhub.com/french-toast"

        # Try to append to the last tweet if we have enough space, otherwise make a new tweet.
        if len(tweets[-1]) + len(french_toast_sentence) < 278:
            tweets[len(tweets) - 1] = tweets[-1] + "\n\n" + french_toast_sentence
        else:
            tweets.append(french_toast_sentence)
    return tweets


def do_tweet(tweets):
    """Send out the tweets!"""
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)
    for tweet in tweets:
        try:
            api.update_status(tweet)
            log("Tweeted: \"" + tweet + "\".")
        except tweepy.TweepError as e:
            log("Failed to tweet: " + e.reason)


def main():
    new = {}
    weather = get_weather()
    if not weather:
        # Something's gone wrong, we've logged the issue, don't try to continue.
        return
    french_toast = get_french_toast()
    new["weather"] = process_weather(weather)
    new["toast"] = process_french_toast(french_toast)
    stored = get_stored_weather()
    diff = diff_weather(new, stored)
    store_weather(new)
    if diff:
        weather_sentences = make_weather_sentences(diff)
        french_toast_sentence = make_french_toast_sentence(diff)
        tweets = make_tweets(weather_sentences, french_toast_sentence, diff["toast"])
        do_tweet(tweets)


if __name__ == "__main__":
    main()
