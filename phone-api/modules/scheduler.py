# -*- coding: utf-8 -*-
import time
import atexit
import config
import requests

from apscheduler.schedulers.background import BackgroundScheduler

class Scheduler():
    def __init__(self, interval):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(func=self.update, trigger="interval", seconds=interval)
        self.scheduler.start()

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: self.scheduler.shutdown())

    def update(self):
        print("Attempt DB update on", time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
        result = requests.get(config.SSL + "://localhost:" + str(config.PORT) + "/api/db/update")
