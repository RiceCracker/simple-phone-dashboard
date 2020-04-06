from app.configuration import Config
import requests


class Connector:
    def __init__(self):
        self.uri = Config.API_SSL + "://" + Config.API_URI + ":" + Config.API_PORT + "/"

    def get(self, type):

        response = requests.get(self.uri + type, auth=(Config.API_AUTH_USER, Config.API_AUTH_PASS))
        print(self.uri + type, response.status_code)

        return response
