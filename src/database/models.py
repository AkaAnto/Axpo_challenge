from sqlmodel import Field, SQLModel, select
from datetime import datetime

from src.database import get_session


class ApiResponse(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    station: str
    date_time: str
    temperature: float
    pressure: float
    speed: float

    def to_json_response(self):
        try:
            return {
                'station': self.station,
                'datetime': self.date_time,
                'temperature': self.temperature,
                'pressure': self.pressure,
                'speed': self.speed
            }
        except Exception as e:
            print(f"Error parsing {self} {e}")


    @staticmethod
    def get_saved_records_by_datetime(start_time, end_time):
        session = next(get_session())
        return session.exec(select(ApiResponse).where(ApiResponse.json_reference == json_reference)).all()