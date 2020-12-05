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

import json
import re
from utils import *

FRENCH_TOAST_URL = "http://universalhub.com/toast.xml"
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fetch_french_toast():
    """Fetch french toast level from Universal Hub."""
    toast = fetch(FRENCH_TOAST_URL)
    m = re.search(r"<status>(.*?)</status>", toast)
    if m:
        level = m.group(1)
        return level
    return None


def get_stored_toast_data():
    stored = None
    try:
        with open(os.path.join(__location__, "toast.json"), "r") as f:
            stored = json.load(f)
    finally:
        return stored


def make_french_toast_emojis(current):
    french_toast_emojis = " ".join(["🍞", "🥛", "🥚"])
    emojis = ""
    if current == "severe":
        # It's a pain to see if there are spaces between these, so easier to just
        # construct the string from an array
        emojis = " ".join(["🆘", "🔴", "‼️", "🚨"])
    elif current == "high":
        emojis = " ".join(["🔴", "🚨", "🔴"])
    elif current == "elevated":
        emojis = " ".join(["⚠️", "⚠️", "⚠️"])
    if len(emojis):
        return emojis + " " + french_toast_emojis + " " + emojis[::-1]
    return emojis


def make_french_toast_sentence(current, stored):
    sentence = ""
    if stored and current != stored:
        sentence = "New french toast alert level: {0} (prev. {1})".format(
            current, stored
        )
    elif not stored and current and current != "low":
        cased_current = current[0].upper() + current[1:]
        sentence = "New french toast alert level: {0}".format(cased_current)
    if len(sentence) > 0:
        return make_french_toast_emojis(current) + "\n" + sentence
    return None


def store_french_toast(current, gif_last_tweeted):
    toast_to_store = {"level": current, "gif_last_tweeted": gif_last_tweeted}
    with open(os.path.join(__location__, "toast.json"), "w") as f:
        json.dump(toast_to_store, f, indent=2)


def get_french_toast(dry_run):
    toast = fetch_french_toast()
    stored_toast = get_stored_toast_data()
    sentence = make_french_toast_sentence(
        toast, stored_toast["level"] if stored_toast else None
    )
    gif_last_tweeted = stored_toast["gif_last_tweeted"] if stored_toast else None
    should_tweet_gif = get_should_tweet_gif(toast, gif_last_tweeted)
    if not dry_run:
        store_french_toast(toast, time.time() if should_tweet_gif else gif_last_tweeted)
    return {
        "current_toast_level": toast,
        "sentence": sentence,
        "gif_last_tweeted": gif_last_tweeted,
    }
