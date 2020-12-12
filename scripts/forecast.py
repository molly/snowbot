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

from datetime import date, timedelta
from pytz import timezone
import json

from scripts.probability import get_probability_for_duration
from scripts.utils import *

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
                    datetime_str, start_time, duration, data, tz
                )
                if probability >= PROBABILITY_THRESHOLD:
                    weather[start_time.date()] += amount["value"]
    return weather


def get_stored_snow_data():
    stored = None
    try:
        with open(os.path.join(__location__, "..", "data/weather.json"), "r") as f:
            stored = json.load(f)
    finally:
        return stored


def diff_forecasts(current_forecast, prev_forecast, date_range):
    diff = {}
    for d in date_range:
        isodate = d.isoformat()
        if (not prev_forecast or isodate not in prev_forecast) and current_forecast[
            d
        ] > 0:
            diff[d] = {"new": current_forecast[d]}
        elif (
            prev_forecast
            and isodate in prev_forecast
            and (current_forecast[d] > 0 or prev_forecast[isodate] > 0)
        ):
            diff[d] = {
                "new": current_forecast[d],
                "old": prev_forecast[isodate],
            }
    return diff


def make_forecast_sentences(diff, date_range):
    if not diff:
        return
    has_changed_forecast = False
    sentences = []
    for d in date_range:
        if d in diff:
            if (
                "old" in diff[d]
                and diff[d]["new"] != diff[d]["old"]
                and not (0 < diff[d]["new"] < 25.4 and 0 < diff[d]["old"] < 25.4)
            ):
                has_changed_forecast = True
                sentences.append(
                    "{0}: {1} in. (prev. {2} in.)".format(
                        d.strftime("%a, %-m/%d"),
                        get_accumulation_string(diff[d]["new"]),
                        get_accumulation_string(diff[d]["old"]),
                    )
                )
            else:
                if "old" not in diff[d]:
                    has_changed_forecast = True
                # Either we don't have data on the old forecast, or the old forecast
                # has not changed. Just print the current forecast.
                sentences.append(
                    "{0}: {1} in.".format(
                        d.strftime("%a, %-m/%d"),
                        get_accumulation_string(diff[d]["new"]),
                    )
                )
    return sentences if has_changed_forecast else []


def store_forecast(current_forecast):
    forecast_to_store = {}
    for key, val in current_forecast.items():
        forecast_to_store[key.isoformat()] = val
    with open(os.path.join(__location__, "..", "data/weather.json"), "w") as f:
        json.dump(forecast_to_store, f, indent=2)
