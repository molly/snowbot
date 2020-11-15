# Snowbot

A Twitter bot that tells you the snow forecast, but more importantly tells you when
that forecast changes. It uses the
[weather.gov API](https://www.weather.gov/documentation/services-web-api).

It's basically a more push than pull version of my existing habit of checking the
forecast every few hours in the winter months.

If you would like to run a version of this for your city, feel free! Just update the
information in config.py, and copy a version of secrets_template.py to secrets.py and
update with your own Twitter app secrets. To find the office and grid x/y coordinates
for your location, hit this endpoint with your latitude/longitude and copy the
"officeID", "gridX", and "gridY" values from the response. Be sure to disable the 
french toast level behavior if you're not in Boston, or it will make no sense.

Find me at https://twitter.com/BostonSnowbot!
