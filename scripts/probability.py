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
from scripts.utils import *


def get_aggregate_probability(
    target_datetime_str,
    target_start_time,
    target_duration,
    data,
    tz,
    start_ind,
    start_duration=None,
):
    """For target time ranges that span multiple entries in the dataset, get an
    aggregate probability from all entries that apply."""
    target_duration_int = get_duration_as_int(target_duration)
    if start_duration is None:
        _, dur = parse_duration_string(
            data["probabilityOfPrecipitation"]["values"][start_ind]["validTime"]
        )
        start_duration = get_duration_as_int(dur)
    total_duration = start_duration
    probabilities = [
        {
            "numeric_duration": start_duration,
            "probability": data["probabilityOfPrecipitation"]["values"][start_ind][
                "value"
            ],
        }
    ]
    ind = start_ind + 1

    # Gather all probabilities that apply to the target time range
    while total_duration < target_duration_int:
        x = data["probabilityOfPrecipitation"]["values"][ind]
        start, duration = parse_duration_string(x["validTime"])
        duration_int = get_duration_as_int(duration)
        probabilities.append(
            {
                "numeric_duration": duration_int,
                "probability": data["probabilityOfPrecipitation"]["values"][start_ind][
                    "value"
                ],
            }
        )
        ind += 1
    aggregate_probability = sum(
        [x["probability"] * x["numeric_duration"] for x in probabilities]
    ) / sum([x["numeric_duration"] for x in probabilities])
    return aggregate_probability


def get_probability_for_duration(
    target_datetime_str, target_start_time, target_duration, data, tz
):
    """Find the probability of snowfall corresponding to a snowfall amount time range"""
    target_duration_int = get_duration_as_int(target_duration)
    prev_ind, prev_x = None, None
    for ind, x in enumerate(data["probabilityOfPrecipitation"]["values"]):
        curr_start, curr_duration = parse_duration_string(x["validTime"])
        if curr_start == target_datetime_str and curr_duration == target_duration:
            # Exact match, return probability
            return x["value"]
        elif curr_start == target_datetime_str:
            # Start time matches, but duration is different
            curr_duration_int = get_duration_as_int(curr_duration)
            if curr_duration_int > target_duration_int:
                # This duration is greater than the target, so we can just use it
                # directly
                return x["value"]
            else:
                # This duration is less than the target, so we need to combine multiple
                # entries to get an aggregate probability
                return get_aggregate_probability(
                    target_datetime_str,
                    target_start_time,
                    target_duration,
                    data,
                    tz,
                    ind,
                )
        if prev_x:
            curr_start_dt = datetime.fromisoformat(curr_start).astimezone(tz)
            prev_start, prev_duration = parse_duration_string(prev_x["validTime"])
            prev_start_dt = datetime.fromisoformat(prev_start).astimezone(tz)
            if prev_start_dt < target_start_time < curr_start_dt:
                prev_duration_int = get_duration_as_int(prev_duration)
                offset_hours = (target_start_time - prev_start_dt).seconds / (60 * 60)
                if prev_duration_int - offset_hours >= target_duration_int:
                    # Target period is wholly contained inside this period
                    return prev_x["value"]
                else:
                    # Target period extends beyond this period, so we need to get the
                    # aggregate probability
                    return get_aggregate_probability(
                        target_datetime_str,
                        target_start_time,
                        target_duration,
                        data,
                        tz,
                        prev_ind,
                        prev_duration_int - offset_hours,
                    )
            elif target_start_time < curr_start_dt:
                # We've passed the period we're looking for; break early.
                break
        prev_ind = ind
        prev_x = x
    log("Couldn't find any relevant probability time period")
    return 0
