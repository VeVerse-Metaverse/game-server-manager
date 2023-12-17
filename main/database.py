import os
import typing

import psycopg2
from psycopg2 import sql


class Database(object):
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database


db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_name = os.getenv("DB_NAME")

instance = Database(host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name)


class ServerModel(object):
    def index(self, db: Database, offset: int = 0, limit: int = 20) -> typing.Dict[str, typing.Union[typing.List[str], typing.List[typing.Dict]]]:
        result = {"rows": [], "columns": []}
        try:
            with psycopg2.connect(host=db.host, port=db.port, user=db.user, password=db.password, database=db.database) as connection:
                with connection.cursor() as cursor:
                    query = sql.SQL("SELECT * FROM servers OFFSET %s LIMIT %s")
                    cursor.execute(query, (offset, limit))
                    result["columns"] = [description[0] for description in cursor.description]
                    result["rows"] = cursor.fetchall()
        except psycopg2.DatabaseError as e:
            print(e.pgerror)

        return result

    def update_status(self, db: Database, id: str, status: str):
        if status not in ["starting", "online", "offline"]:
            raise ValueError(f"invalid status: {status}")

        with psycopg2.connect(host=db.host, port=db.port, user=db.user, password=db.password, database=db.database) as connection:
            with connection.cursor() as cursor:
                query = sql.SQL("UPDATE servers SET status = %s WHERE id = %s")
                cursor.execute(query, (status, id))

    def update_port(self, db: Database, id: str, port: int):
        if int(port) < 30000 or int(port) > 65535:
            raise ValueError(f"invalid port: {port}")

        with psycopg2.connect(host=db.host, port=db.port, user=db.user, password=db.password, database=db.database) as connection:
            with connection.cursor() as cursor:
                query = sql.SQL("UPDATE servers SET port = %s WHERE id = %s")
                cursor.execute(query, (int(port), id))


server_model = ServerModel()
