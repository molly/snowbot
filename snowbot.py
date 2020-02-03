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
import os
from secrets import *

forecast_url = "https://api.darksky.net/forecast/{}/42.3587,-71.0567?exclude=currently,minutely,hourly,flags" \
               "&lang=en&units=us".format(FORECAST_KEY)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def get_weather():
    with open(os.path.join(__location__, "tmp.json"), 'r') as f:
        return json.load(f)
    # try:
    #     resp = opener.open(url)
    # except URLError:
    #     log("URLError when trying to hit the DarkSky API.")
    #     return None
    # else:
    #     blob = resp.read().decode('utf-8')
    #     return json.loads(blob)

def main():
    weather = get_weather()

if __name__ == "__main__":
    main()