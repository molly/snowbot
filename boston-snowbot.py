#!/usr/bin/python
#  -*- coding: utf-8 -*-
# Copyright (c) 2015–2016 Molly White
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
from urllib2 import build_opener, URLError
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

url = "https://api.darksky.net/forecast/{}/42.3587,-71.0567?exclude=currently,minutely,hourly," \
      "alerts,flags".format(FORECAST_KEY)
french_toast_url = "http://www.universalhub.com/toast.xml"

auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
api = tweepy.API(auth)

opener = build_opener()
opener.addheaders = [('User-Agent', 'Boston Snowbot (https://github.com/molly/boston-snowbot)')]

under_match = re.compile(r'snow \((?:under|<) (?P<max>\d+) in\.\)')
range_match = re.compile(r'snow \((?P<min>\d+)\W(?P<max>\d+) in.\)')
changed_text = "{0}: {1} in. (prev. {2})."
after_match = re.compile(r'\((?P<min>\d+)\W(?P<max>\d+) in. of snow\)')
new_text = "{0}: {1} in."
changed_french_toast = "French toast level: {0}. (prev. {1})"
new_french_toast = "French toast level: {0}"


def get_weather():
    """Hit the Forecast.io API and return the response parsed into json."""
    try:
        resp = opener.open(url)
    except URLError:
        log("URLError when trying to hit the DarkSky API.")
        return None
    else:
        html = resp.read().decode('utf-8')
        return json.loads(html)


def get_french_toast_level():
    """Hit the french toast alert system to get the current french toast level."""
    try:
        resp = opener.open(french_toast_url)
    except URLError as e:
        log("URLError when trying to hit the french toast API.")
        return None
    else:
        body = resp.read().decode('utf-8')
        m = re.search(r'<status>(.*?)</status>', body)
        return m.group(1) if m else None

def parse_weather(blob):
    """Parse the JSON response to get rid of shit we don't want."""
    weather = {}
    b = blob["daily"]["data"]
    for t in b:
        timestamp = str(t["time"])
        weather[timestamp] = {}
        weather[timestamp]["date_str"] = datetime.fromtimestamp(t["time"]).strftime("%a, %-m/%d")
        summary = t["summary"].lower()
        if "snow" in summary:
            if "under" in summary:
                m = re.search(under_match, summary)
                if m:
                    weather[timestamp]["min"] = 0
                    weather[timestamp]["max"] = int(m.group("max"))
                else:
                    weather[timestamp]["min"] = 0
                    weather[timestamp]["max"] = 1
                    log("Couldn't parse \"" + summary + "\" with \"under\" regex.")
            elif "of snow" in summary:
                m = re.search(after_match, summary)
                if m:
                    weather[timestamp]["min"] = int(m.group("min"))
                    weather[timestamp]["max"] = int(m.group("max"))
                else:
                    weather[timestamp]["min"] = 0
                    weather[timestamp]["max"] = 1
                    log("Couldn't parse \"" + summary + "\" with \"after\" regex.")
            elif "light snow" in summary:
                weather[timestamp]["min"] = 0
                weather[timestamp]["max"] = 1
            else:
                m = re.search(range_match, summary)
                if m:
                    weather[timestamp]["min"] = int(m.group("min"))
                    weather[timestamp]["max"] = int(m.group("max"))
                else:
                    weather[timestamp]["min"] = 0
                    weather[timestamp]["max"] = 1
                    log("Couldn't parse \"" + summary + "\" with \"range\" regex.")
        else:
            weather[timestamp]["min"] = 0
            weather[timestamp]["max"] = 0
    return weather


def get_stored():
    """Get the stored weather from the weather file."""
    try:
        with open(os.path.join(__location__, "weather.json"), 'r') as f:
            stored = json.load(f)
    except IOError:
        stored = None
    return stored


def diff_weather(new, stored):
    """Diff the newest API response with the stored one."""
    diff = {
        "weather": {},
        "french_toast": {}
    }
    changed = False
    for t in new["weather"]:
        if stored and t in stored:
            if new["weather"][t]["max"] != stored[t]["max"] or new["weather"][t]["min"] != stored[t]["min"]:
                changed = True
                diff["weather"][t] = {}
                diff["weather"][t]["date_str"] = new["weather"][t]["date_str"]
                diff["weather"][t]["old"] = {}
                diff["weather"][t]["old"]["min"] = stored[t]["min"]
                diff["weather"][t]["old"]["max"] = stored[t]["max"]
                diff["weather"][t]["new"] = {}
                diff["weather"][t]["new"]["min"] = new["weather"][t]["min"]
                diff["weather"][t]["new"]["max"] = new["weather"][t]["max"]
                continue
        diff["weather"][t] = {}
        diff["weather"][t]["date_str"] = new["weather"][t]["date_str"]
        diff["weather"][t]["new"] = {}
        diff["weather"][t]["new"]["min"] = new["weather"][t]["min"]
        diff["weather"][t]["new"]["max"] = new["weather"][t]["max"]
    if new["french_toast"]:
        if stored and "french_toast" in stored and stored["french_toast"] != new["french_toast"]:
            changed = True
            diff["french_toast"] = {}
            diff["french_toast"]["old"] = stored["french_toast"]
            diff["french_toast"]["new"] = new["french_toast"]
        else:
            diff["french_toast"] = {}
            diff["french_toast"]["new"] = new["french_toast"]

    return diff if changed or not stored else {}


def store_weather(new):
    """Store the newest weater in the weather file for next time."""
    with open(os.path.join(__location__, "weather.json"), 'w') as f:
        json.dump(new, f, indent=4)


def bread_and_milk_with_embellishment(french_toast):
    tweet = []
    if "old" in french_toast:
        tweet.append(changed_french_toast.format(french_toast["old"], french_toast["new"]))
    else:
        tweet.append(new_french_toast.format(french_toast["new"]))

    if french_toast["new"] == "severe":
        tweet.append('🔴 🚨 🔴 🚨 🔴 🚨 🔴')
    elif french_toast["new"] == "high":
        tweet.append('⚠️ ⚠️ ⚠️')

    tweet.append("\n\nhttp://www.universalhub.com/french-toast")
    return tweet


def make_sentences(diff):
    """Create human-readable sentences out of the diff dict."""
    info = []
    for t in sorted(diff["weather"].keys()):
        if "old" in diff["weather"][t]:
            old_range = make_range(diff["weather"][t]["old"]["min"], diff["weather"][t]["old"]["max"])
            new_range = make_range(diff["weather"][t]["new"]["min"], diff["weather"][t]["new"]["max"])
            info.append(changed_text.format(diff["weather"][t]["date_str"], new_range, old_range))
        else:
            if diff["weather"][t]["new"]["max"] != 0:
                new_range = make_range(diff["weather"][t]["new"]["min"], diff["weather"][t]["new"]["max"])
                info.append(new_text.format(diff["weather"][t]["date_str"], new_range))
    if info and "old" in diff["french_toast"]:
        info.append(changed_french_toast.format(diff["french_toast"]["old"], diff["french_toast"]["new"]))
    else:
        return bread_and_milk_with_embellishment(diff["french_toast"])
    return info


def make_range(min, max):
    """Format the accumulation range."""
    if min == max == 0:
        return 0
    elif min == 0:
        return "<{}".format(max)
    else:
        return "{}–{}".format(min, max)


def form_tweets(sentences):
    """Create a tweet, or multiple tweets if the tweets are too long, out of the sentences."""
    tweet = ""
    tweets = []
    while sentences:
        if len(tweet) + len(sentences[0]) > 139:
            tweets.append(tweet)
            tweet = "(cont'd.):"
        else:
            if len(tweet) != 0:
                tweet += "\n"
            tweet += sentences.pop(0)
    tweets.append(tweet)
    return tweets


def do_tweet(tweets):
    """Send out the tweets!"""
    for tweet in tweets:
        api.update_status(tweet)
        log("Tweeting: \"" + tweet + "\".")


def log(message):
    """Write message to a logfile."""
    with open(os.path.join(__location__, "snowbot.log"), 'a') as f:
        f.write(("\n" + datetime.today().strftime("%H:%M %Y-%m-%d") + " " + message).encode('utf-8'))


def do_the_thing():
    """Hit the DarkSky API, diff the weather with the stored weather, and tweet out any
    differences."""
    new = {}
    blob = get_weather()
    new["weather"] = parse_weather(blob)
    new["french_toast"] = get_french_toast_level()
    stored = get_stored()
    diff = diff_weather(new, stored)
    store_weather(new)
    if diff:
        sentences = make_sentences(diff)
        tweets = form_tweets(sentences)
        do_tweet(tweets)
    else:
        log("No tweets!")

if __name__ == "__main__":
    do_the_thing()
