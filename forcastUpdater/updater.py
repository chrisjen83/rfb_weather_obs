from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from forecastUpdater import forecastApi

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(forecastApi.post_influxdb, 'interval', minutes=5)
    scheduler.start()
