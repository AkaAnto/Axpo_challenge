from functools import lru_cache
from fastapi import FastAPI, BackgroundTasks, Depends, Query
from contextlib import asynccontextmanager
from typing import Annotated, Optional, List

from sqlmodel import Session
import pandas as pd

from src import config
from src.consumer.main import AEMETConsumer, NoDataResponse
from src.database import create_db_and_tables, get_session
from src.utils import APIRequest, StationEnum


@lru_cache
def get_settings():
    return config.Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]



@app.get("/station_data/")
async def root(
    background_tasks: BackgroundTasks, session: SessionDep,
    start_date: str = Query(..., description="Start time in 'YYYY-MM-DDTHH:MM:SSUTC' format"),
    end_date: str = Query(..., description="End time in 'YYYY-MM-DDTHH:MM:SSUTC' format"),
    station_id: StationEnum = Query(..., description=f"Meteo station id"),
    data_types: List[str] = Query(..., description="List of required data types (temperature, pressure, speed)"),
    aggregation: Optional[str] = Query(None, description="Time aggregation (None, Hourly, Daily, Monthly)"),
):
    def update_database(new_record_list, session):
        for record in new_record_list:
            try:
                session.add(record)
            except Exception as e:
                print(f'Problem saving record {record} - {e}')
        session.commit()

    def aggregate_response(response, aggregation: Optional[str]):
        df = pd.DataFrame(response)
        df['datetime'] = pd.to_datetime(df['datetime'])
        aggregate_fields = {
            'temperature': 'mean',
            'pressure': 'mean',
            'speed': 'mean'
        }
        if aggregation == "Hourly":
            df['hour'] = df['datetime'].dt.hour
            df_aggregated = df.groupby(['hour']).agg(aggregate_fields).reset_index()
        elif aggregation == "Daily":
            df['date'] = df['datetime'].dt.date
            df_aggregated = df.groupby(['date']).agg(aggregate_fields).reset_index()
        elif aggregation == "Monthly":
            df['month'] = df['datetime'].dt.to_period('M')
            df_aggregated = df.groupby(['month']).agg(aggregate_fields).reset_index()
        else:
            return response
        aggregated_result = df_aggregated.to_dict(orient="records")
        return aggregated_result

    request_data = APIRequest(
        start_date=start_date,
        end_date=end_date,
        station_id=station_id,
        aggregation=aggregation,
        data_types=data_types
    )
    response, created = AEMETConsumer(
        station=request_data.station_id,
        start_date=request_data.start_date,
        end_date=request_data.end_date
    ).collect_data()
    if created:
        background_tasks.add_task(update_database, response, session)
    if isinstance(response, NoDataResponse):
        return {"data": response.model_dump()}
    response = aggregate_response([record.to_json_response() for record in response], aggregation)
    return {"data":  response}