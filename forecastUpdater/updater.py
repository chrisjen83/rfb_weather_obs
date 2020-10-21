from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from forecastUpdater import forecastApi
import logging

logger = logging.getLogger(__name__)

def start():
    scheduler = BackgroundScheduler()

    try:
        scheduler.add_job(forecastApi.post_influxdb, 'interval', minutes=5)
    except IndexError:
        logger.exception("Something went wrong")

    scheduler.add_job(forecastApi.post_influxdb, 'interval', minutes=5)

    scheduler.start()
