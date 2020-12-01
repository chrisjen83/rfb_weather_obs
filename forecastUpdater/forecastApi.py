from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import json
from lxml import html
import math
import logging
# import configparser

logr = logging.getLogger(__name__)

# Reading in config.ini into the script to be used to connect to ECS.
# config = configparser.ConfigParser()
# config.read('forecast_config.ini')
#
# bom_user = config["CONFIG"]["BOM_USER"]
# bom_pass = config['CONFIG']['BOM_PASS']
# u_weather_uri = config['CONFIG']['U_WEATHER_API']
# influx_server = config['CONFIG']['INFLUX_SERVER']
# influx_token = config['CONFIG']['INFLUX_TOKEN']
# influx_org = config['CONFIG']['INFLUX_ORG']
# influx_bucket = config['CONFIG']['INFLUX_BUCKET']

# Enviroment Variables set for Webapp deployment
bom_user = os.environ['BOM_USER']
bom_pass = os.environ['BOM_PASS']
u_weather_uri = os.environ['U_WEATHER_API']
influx_server = os.environ['INFLUX_SERVER']
influx_token = os.environ['INFLUX_TOKEN']
influx_org = os.environ['INFLUX_ORG']
influx_bucket = os.environ['INFLUX_BUCKET']

# Calculate Fire Danger Index from local observation


def ffdi(temp, humidity, df, windsp):

    temp = float(temp)
    humidity = float(humidity)
    df = float(df)
    windsp = float(windsp)

    k = 2*(math.exp((.987*math.log(df+0.001))-.45-(.0345*humidity)+(.0338*temp)+(.0234*windsp)))
    logr.debug(k)

    return k

# Retrieve drought factor from BOM


def drought():

    user = bom_user
    passwd = bom_pass

    login = requests.get('http://reg.bom.gov.au/products/reg/IDN60034.shtml', auth=(user, passwd))
    doc = html.fromstring(login.content)
    row1 = doc.xpath('//tr[54]/td[2]')
    df = row1[0].text.strip()
    logr.debug(df)

    row2 = doc.xpath('//tr[54]/td[5]')
    observed = row2[0].text.strip()

    return [df, observed]


def post_influxdb():

    url = u_weather_uri
    mtk_weather = requests.get(url).json()

    logr.debug('UG Weather API Results', mtk_weather)

    weather = {
        'stationid': mtk_weather['observations'][0]['stationID'],
        'obsTimeUTC': mtk_weather['observations'][0]['obsTimeUtc'],
        'localtime': mtk_weather['observations'][0]['obsTimeLocal'],
        'winddir': mtk_weather['observations'][0]['winddir'],
        'humidity': mtk_weather['observations'][0]['humidity'],
        'temp': mtk_weather['observations'][0]['metric']['temp'],
        'heatindex': mtk_weather['observations'][0]['metric']['heatIndex'],
        'dewPoint': mtk_weather['observations'][0]['metric']['dewpt'],
        'windchill': mtk_weather['observations'][0]['metric']['windChill'],
        'windspeed': mtk_weather['observations'][0]['metric']['windSpeed'],
        'windgust': mtk_weather['observations'][0]['metric']['windGust'],
        'psure': mtk_weather['observations'][0]['metric']['pressure'],
        'precip': mtk_weather['observations'][0]['metric']['precipRate'],
        'obsTimeUTC': mtk_weather['observations'][0]['obsTimeUtc'],

    }

    # Calculate FFDI data point
    df = drought()
    fdi = ffdi(weather["temp"], weather["humidity"], df[0], weather["windspeed"])


    # Setup connection to the DB
    client = InfluxDBClient(url='{}' .format(influx_server), token='{}' .format(influx_token), org= '{}' .format(influx_org))
    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    # Form the data to ingest into InfluxDB database
    p = Point("weather") \
        .tag("location", "Mount Kuring-Gai") \
        .field("temperature", float(weather['temp'])) \
        .field("Heat Index", float(weather['heatindex'])) \
        .field("Dew Point", float(weather['dewPoint'])) \
        .field("humidity", int(weather['humidity'])) \
        .field("Wind Speed", float(weather['windspeed'])) \
        .field("Wind Gust", float(weather['windgust'])) \
        .field("Pressure", float(weather['psure'])) \
        .field("Wind Direction", float(weather['winddir'])) \
        .field("Precipitation", float(weather['precip'])) \
        .field("Heat Index", float(weather['heatindex'])) \
        .field("DroughtF", float(df[0])) \
        .field("FFDI", float(fdi)) \
        .time((weather['obsTimeUTC']))


    # Write that into the InfluxDB
    write_api.write(record=p, bucket='{}' .format(influx_bucket), time_precision='s')


    return None

try:
    post_influxdb()
except Exception as e:
    logr.exception("Error logging to InfluxDB:\n%s" % e)

post_influxdb()
logr.info("Posted to InfluxDB")
