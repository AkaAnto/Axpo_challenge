import requests
import re
from pydantic import BaseModel, field_validator
from functools import lru_cache
from enum import Enum

from src import config


@lru_cache
def get_settings():
    return config.Settings()


class StationEnum(str, Enum):
    STATION_89064 = "89064- Estación Meteorológica Juan Carlos I"
    STATION_89064R = "89064R- Estación Radiométrica Juan Carlos I"
    STATION_89064RA = "89064RA- Estación Radiométrica Juan Carlos I (hasta 08/03/2007)"
    STATION_89070 = "89070- Estación Meteorológica Gabriel de Castilla"


class AEMETRequest(BaseModel):
    base_url: str = 'https://opendata.aemet.es/opendata/api/'
    headers: dict = {"api_key": get_settings().aemet_api_key, "accept": "application/json"}
    start_date: str = "2024-03-15T14:30:00UTC"
    end_date: str = "2024-04-15T14:30:00UTC"
    station: StationEnum = StationEnum.STATION_89070

    @field_validator('start_date', 'end_date')
    def validate_datetime_format(cls, v, field):
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}UTC$'
        if not re.match(pattern, v):
            raise ValueError('Datetime must be in the format YYYY-MM-DDTHH:MM:SSUTC')
        return v

    def get(self):
        station = self.station.split("-")[0]
        url = f"{self.base_url}antartida/datos/fechaini/{self.start_date}/fechafin/{self.end_date}/estacion/{station}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json(), True
        else:
            print(f"Error: {response.status_code}")
            return response, False
