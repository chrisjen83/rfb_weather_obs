from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class WeatherConfig(AppConfig):
    name = 'weather'

    # def ready(self):
    #     from forecastUpdater import updater
    #     updater.start()
