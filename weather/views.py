from django.shortcuts import render
import requests
from lxml import html
import math
import json
import os
from django.core.exceptions import ImproperlyConfigured


# Create your views here.

# direction function is converting the wind direction reported in degrees into direction.  It is a simple calculation but effective.

def direction(degrees):
    val = int((degrees/22.5)+.5)
    comp_sector = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE",
                   "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return comp_sector[(val % 16)]


# Drought function is scrapping the BOM website for the drought factor.  This requires a paid login to receive the information

def drought():

    user = 'bomw0107'
    passwd = '50cLampe'

    login = requests.get('http://reg.bom.gov.au/products/reg/IDN60034.shtml', auth=(user, passwd))
    doc = html.fromstring(login.content)
    row1 = doc.xpath('//tr[54]/td[2]')
    df = row1[0].text.strip()

    row2 = doc.xpath('//tr[54]/td[5]')
    observed = row2[0].text.strip()

    return [df, observed]

# FFDI calculation uses the local weather sensors and the drought factor calculated in the drought() function.  The FFDI is localises to where the sensors measuring.  Present it is Mount Kuring-Gai


def ffdi(temp, humidity, df, windsp):

    temp = float(temp)
    humidity = float(humidity)
    df = float(df)
    windsp = float(windsp)

    k = 2*(math.exp((.987*math.log(df+0.001))-.45-(.0345*humidity)+(.0338*temp)+(.0234*windsp)))

    return k

# fire_danger_rate function takes the ffdi founction output and converts to the RFS standard FDR index of low, High, Very High, Severe, Catastrophic


def fire_danger_rate(fdi):

    ffdi_to_fda = [12, "Low/Moderate", 25, "High", 50, "Very High", 75,
                   "Severe", 100, "Extreme", 101, "Catastrophic"]

    for i in range(len(ffdi_to_fda)//2):
        if fdi < ffdi_to_fda[i*2]:
            fda = ffdi_to_fda[(i*2)+1]
            break

    return fda

# Index is the main body of the view and where all of the PWS is converting JSON results into local variables.
# This function uses weather underground API, to use other PWS you will need to attached your PWS to the Weather Underground API systme.
# To customise to your weather station change stationId= and apiKey= to match your Weather Underground Account.


def index(request):
    url = 'https://api.weather.com/v2/pws/observations/current?stationId=ISYDNE764&format=json&units=m&apiKey=3d6cf8b25a784eb8acf8b25a784eb8c0&numericPrecision=decimal'
    mtk_weather = requests.get(url).json()

    weather = {
        'stationid': mtk_weather['observations'][0]['stationID'],
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

    }

    df = drought()
    fdi = ffdi(weather["temp"], weather["humidity"], df[0], weather["windspeed"])

# Conext is allowing the functions and information above to be exported to an HTML template.

    context = {'weather': weather,
               'direction': direction(weather["winddir"]),
               'drought': df,
               'ffdi': ffdi(weather["temp"], weather["humidity"], df[0], weather["windspeed"]),
               'fire_danger_rate': fire_danger_rate(fdi),
               }

    return render(request, 'weather/index.html', context)
