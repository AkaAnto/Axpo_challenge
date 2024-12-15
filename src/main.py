from functools import lru_cache
from fastapi import FastAPI, BackgroundTasks, Depends
from contextlib import asynccontextmanager
from typing import Annotated
from sqlmodel import Session

from src import config
from src.consumer.main import AEMETConsumer
from src.database import create_db_and_tables, get_session


@lru_cache
def get_settings():
    return config.Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/")
async def root(background_tasks: BackgroundTasks, session: SessionDep):
    def update_database(new_record_list, session):
        for record in new_record_list:
            try:
                session.add(record)
            except Exception as e:
                print(f'Problem saving record {record} - {e}')
        session.commit()

    response, created = AEMETConsumer().collect_data()
    if created:
        background_tasks.add_task(update_database, response, session)
    return {"data":  [record.to_json_response() for record in response]}