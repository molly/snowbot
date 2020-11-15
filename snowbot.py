#!/usr/bin/python
#  -*- coding: utf-8 -*-
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

from utils import fetch, log

from config import *
from secrets import *

FORECAST_API_URL = "https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}"
HEADERS = {"user_agent": "{name} {url}".format(name=APP_NAME, url=REPO_URL)}


def get_date_range():
    today = date.today()
    return [today + timedelta(days=x) for x in range(6)]


def get_snow_data():
    url = FORECAST_API_URL.format(office=OFFICE, grid_x=GRID_X, grid_y=GRID_Y)
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    return {
        "snowfallAmount": data["properties"]["snowfallAmount"],
        "probabilityOfPrecipitation": data["properties"]["probabilityOfPrecipitation"],
    }


def parse_snow_data(data, date_range):
    weather = {d: 0 for d in date_range}
    tz = timezone(TIMEZONE)
    amounts = data["snowfallAmount"]["values"]
    for amount in amounts:
        if amount["value"] > 0:
            [datetime_str, duration] = amount["validTime"].split("/PT")
            start_time = datetime.fromisoformat(datetime_str).astimezone(tz)
            if start_time.date() in weather:
                prob = next(
                    (
                        x
                        for x in data["probabilityOfPrecipitation"]["values"]
                        if x["validTime"] == amount["validTime"]
                    ),
                    None,
                )
                if prob:
                    if prob > 50:
                        weather[start_time.date()] += amount["value"]
                else:
                    print("oh no")
    print("hi")
    return weather


def run():
    snow_data = get_snow_data()
    date_range = get_date_range()
    parse_snow_data(snow_data, date_range)
    print("hi")


if __name__ == "__main__":
    run()
