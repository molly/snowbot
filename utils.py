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

from datetime import datetime
import os
import requests

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
headers = {'User-Agent': 'Boston Snowbot (https://github.com/molly/boston-snowbot)'}


def log(message):
    """Write message to a logfile."""
    with open(os.path.join(__location__, "snowbot.log"), 'a') as f:
        f.write("\n" + datetime.today().strftime("%H:%M %Y-%m-%d") + " " + message)


def fetch(url, is_json = False):
    """Make a request to a URL, and handle errors as needed."""
    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except requests.exceptions.Timeout:
        log("Request timed out when trying to hit {}".format(url))
    except requests.exceptions.ConnectionError:
        log("Connection error when trying to hit {}".format(url))
    except requests.exceptions.HTTPError:
        log("HTTP error when trying to hit {}".format(url))
    else:
        if is_json:
            return resp.json()
        return resp.text
