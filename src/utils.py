from datetime import datetime
from typing import Optional, List

import requests
import re

from fastapi import HTTPException
from pydantic import BaseModel, field_validator, ConfigDict
from functools import lru_cache
from enum import Enum

from src import config


@lru_cache
def get_settings():
    return config.Settings()


DATE_FORMAT = "%Y-%m-%dT%H:%M:%SUTC"
VALID_AGGREGATIONS = [None, "Hourly", "Daily", "Monthly"]
VALID_DATA_TYPES = ["temperature", "pressure", "speed"]
AEMET_BASE_URL = "https://opendata.aemet.es/opendata/api/"
AEMET_HEADERS =  {"api_key": get_settings().aemet_api_key, "accept": "application/json"}


class StationEnum(str, Enum):

    STATION_89064 = "89064- Estación Meteorológica Juan Carlos I"
    STATION_89064R = "89064R- Estación Radiométrica Juan Carlos I"
    STATION_89064RA = "89064RA- Estación Radiométrica Juan Carlos I (hasta 08/03/2007)"
    STATION_89070 = "89070- Estación Meteorológica Gabriel de Castilla"


class AEMETRequest(BaseModel):
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
        url = f"{AEMET_BASE_URL}antartida/datos/fechaini/{self.start_date}/fechafin/{self.end_date}/estacion/{station}"
        response = requests.get(url, headers=AEMET_HEADERS)
        if response.status_code == 200:
            return response.json(), True
        else:
            print(f"Error: {response.status_code}")
            return response, False




class APIRequest(BaseModel):
    station_id: StationEnum
    start_date: str
    end_date: str
    aggregation: Optional[str] = None
    data_types: Optional[List[str]] = None

    @field_validator('start_date', 'end_date')
    def validate_datetime_format(cls, v, field):
        try:
            datetime.strptime(v, DATE_FORMAT)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"{field} must be in format: {DATE_FORMAT}"
            )
        return v

    @field_validator('aggregation')
    def validate_aggregation(cls, value):
        if value and value not in VALID_AGGREGATIONS:
            raise HTTPException(status_code=400,
                                detail=f"Invalid aggregation type. Allowed values are: {', '.join(VALID_AGGREGATIONS)}")
        return value

    @field_validator('data_types')
    def validate_data_types(cls, value):
        for item in value:
            if item not in VALID_DATA_TYPES:
                raise HTTPException(status_code=400,
                                    detail=f"Invalid data type. Allowed values are: {', '.join(VALID_DATA_TYPES)}")
        return value