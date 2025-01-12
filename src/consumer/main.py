import requests
import math
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel

from src.utils import AEMETRequest, StationEnum
from src.database.models import ApiResponse


class NoDataResponse(BaseModel):
    descripcion : str
    estado : int


class AEMETConsumer(BaseModel):
    start_date: str = "2024-03-15T14:30:00UTC"
    end_date: str = "2024-04-15T14:30:00UTC"
    station: StationEnum = StationEnum.STATION_89070

    def collect_data(self):
        initial_request_response, success = AEMETRequest(start_date=self.start_date, end_date=self.end_date, station=self.station).get()
        print(initial_request_response, success)
        if success is True and initial_request_response.get('datos', None):
            existing_record_list = None
            # existing_record_list = ApiResponse.get_saved_records_by_json_reference(json_reference)
            if existing_record_list is None:
                data_response = requests.get(initial_request_response.get('datos'))
                new_record_list = []
                for record in data_response.json():
                    temperature = float(record.get('temp'))
                    pressure = float(record.get('pres'))
                    speed = float(record.get('vel'))
                    if math.isnan(temperature) is False and math.isnan(pressure) is False and math.isnan(speed) is False: # https://github.com/fastapi/fastapi/issues/459
                        new_record = ApiResponse(
                            id= str(uuid4()),
                            station=record.get('nombre'),
                            date_time=record.get('fhora'),
                            temperature=temperature,
                            pressure=pressure,
                            speed=speed
                        )
                        new_record_list.append(new_record)
                return new_record_list, True
            print("Found the records on the db")
            return existing_record_list, False
        return NoDataResponse(**initial_request_response), False