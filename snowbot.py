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


import argparse
import tweepy

from secrets import *
from scripts.forecast import *
from scripts.french_toast import get_french_toast
from scripts.utils import *

FORECAST_API_URL = "https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}"
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def make_tweets(sentences, append=None):
    tweet = ""
    tweets = []
    if append:
        sentences.append(append)
    while sentences:
        if len(tweet) + len(sentences[0]) > 278:
            # Append what we have and start a new tweet.
            tweets.append(tweet)
            tweet = "(cont'd.):"
        else:
            if len(tweet) != 0:
                tweet += "\n"
                if len(sentences) == 1 and append:
                    tweet += "\n"
            tweet += sentences.pop(0)
    if len(tweet):
        tweets.append(tweet)
    return tweets


def send_tweets(tweets):
    auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_KEY)
    api = tweepy.API(auth)
    for tweet in tweets:
        try:
            api.update_status(tweet)
            log('Tweeted: "' + tweet)
        except tweepy.TweepError as e:
            log("Failed to tweet: " + e.reason)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        help="dry run without sending any tweets or storing the new forecast",
        action="store_true",
    )
    args = parser.parse_args()
    return args


def run():
    args = parse_args()

    # Gather forecast, etc. data
    snow_data = get_snow_data()
    date_range = get_date_range()
    current_forecast = parse_snow_data(snow_data, date_range)
    prev_forecast = get_stored_snow_data()
    diff = diff_forecasts(current_forecast, prev_forecast, date_range)
    if ENABLE_FRENCH_TOAST:
        toast_details = get_french_toast(args.dry_run)

    # Form tweets
    sentences = make_forecast_sentences(diff, date_range)
    if ENABLE_FRENCH_TOAST:
        tweets = make_tweets(sentences, toast_details["sentence"])
    else:
        tweets = make_tweets(sentences)

    # Send tweets
    if not args.dry_run:
        if len(tweets):
            send_tweets(tweets)
        else:
            log("No changed forecast to tweet.")
        if ENABLE_FRENCH_TOAST:
            should_tweet_gif = get_should_tweet_gif(
                toast_details["current_toast_level"], toast_details["gif_last_tweeted"]
            )
            if should_tweet_gif:
                log("Tweeting toast gif.")
                send_tweets([SEVERE_TOAST_GIF])

        # Store forecast for next time
        store_forecast(current_forecast)
    else:
        if len(tweets):
            print("Would tweet:")
            [print(tweet) for tweet in tweets]
        else:
            print("No changed forecast to tweet.")
        if ENABLE_FRENCH_TOAST:
            should_tweet_gif = get_should_tweet_gif(
                toast_details["current_toast_level"], toast_details["gif_last_tweeted"]
            )
            if should_tweet_gif:
                print(SEVERE_TOAST_GIF)


if __name__ == "__main__":
    run()
