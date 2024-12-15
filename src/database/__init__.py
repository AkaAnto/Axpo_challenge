from functools import lru_cache
from sqlmodel import  Session, SQLModel, create_engine

from src import config


@lru_cache
def get_settings():
    return config.Settings()


database_file_name = f'./database/{get_settings().database_name}.db'
sqlite_url = f"sqlite:///{database_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session