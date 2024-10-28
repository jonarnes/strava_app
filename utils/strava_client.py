import os
import time

import requests

from utils import manage_pg_db
from utils.exceptions import StravaAPIError


class StravaClient:
    def __init__(self, athlete_id, activity_id):
        self.__athlete_id = athlete_id
        self.__activity_id = activity_id
        self.__session = requests.Session()
        tokens = manage_pg_db.get_athlete(athlete_id)
        tokens = self._update_tokens(tokens)
        manage_pg_db.add_athlete(tokens)
        self.__headers = {'Authorization': f"Bearer {tokens.access_token}"}

    def _update_tokens(self, tokens):
        if tokens.expires_at > time.time():
            return tokens

        params = {
            "client_id": os.environ.get('STRAVA_CLIENT_ID'),
            "client_secret": os.environ.get('STRAVA_CLIENT_SECRET'),
            "refresh_token": tokens.refresh_token,
            "grant_type": "refresh_token"
        }
        try:
            refresh_response = self.__session.post("https://www.strava.com/oauth/token", data=params).json()
            return manage_pg_db.Tokens(tokens.id, refresh_response['access_token'],
                                    refresh_response['refresh_token'], refresh_response['expires_at'])
        except(KeyError, ValueError):
            raise StravaAPIError(f'Failed to refresh token ID={tokens.id}. Athlete ID={self.__athlete_id}.')

    @property
    def __activity_url(self) -> str:
        return f'https://www.strava.com/api/v3/activities/{self.__activity_id}'

    @property
    def get_activity(self) -> dict:
        """Get information about activity

        :return: dictionary with activity data
        """
        try:
            return self.__session.get(self.__activity_url, headers=self.__headers).json()
        except ValueError:
            raise StravaAPIError(f'Failed to get activity ID={self.__activity_id}. Athlete ID={self.__athlete_id}.')

    def modify_activity(self, payload: dict):
        """Method can change UpdatableActivity parameters such that description, name, type, gear_id.
        See https://developers.strava.com/docs/reference/#api-models-UpdatableActivity

        :param payload: dictionary with keys description, name, type, gear_id, trainer, commute
        :return: dictionary with updated activity parameters
        """
        if not self.__session.put(self.__activity_url, headers=self.__headers, data=payload).ok:
            raise StravaAPIError(f'Failed modify activity ID={self.__activity_id}. Athlete ID={self.__athlete_id}')
