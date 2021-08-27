import json
import pickle

import psycopg2
from dbutils.pooled_db import PooledDB
from psycopg2 import extras  # 不能少

from config import config


class PostgresPool:
    def __init__(self, user=None, password=None, database=None, host=None, port=None):
        try:
            self.psycopg_pool = PooledDB(psycopg2,
                                         mincached=5,
                                         blocking=True,
                                         user=config.PG_USER if not user else user,
                                         password=config.PG_PASSWORD if not password else password,
                                         database=config.PG_DBNAME if not database else database,
                                         host=config.PG_HOST if not host else host,
                                         port=config.PG_PORT if not port else port)
            self.connection = self.psycopg_pool.connection()
            # self.connection.autocommit = True
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)  # 字典形式返回游标
        except Exception as e:
            print(e)
            raise e

    # 取单条数据
    def query_one(self, sql):
        cur = self.cursor
        cur.execute(sql)
        coloumns = [row[0] for row in cur.description]
        value = [[str(item) for item in row] for row in cur.fetchall()]
        return [dict(zip(coloumns, row)) for row in value]

    def query_all(self, sql):
        cur = self.cursor
        cur.execute(sql)
        coloumns = [row[0] for row in cur.description]
        value = [[str(item) for item in row] for row in cur.fetchall()]
        return [dict(zip(coloumns, row)) for row in value]

    def insert_data(self, sql):
        cur = self.cursor
        try:
            cur.execute(sql)
            # self.cursor.commit()
            self.connection.commit()
            return "success"
        except Exception as e:
            print(e)
            return "failed"


remote_db_instance = PostgresPool()
local_db_instance = PostgresPool(user="postgres",
                                 port="5435",
                                 database="test_db",
                                 password="postgres",
                                 host="127.0.0.1"
                                 )

result = remote_db_instance.query_all("select * from file_content where file_type='RESIDENTIAL_UNIT' limit 4 ")
print(result)