from contextlib import contextmanager

from loguru import logger as log
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


class PostgresqlClient:
    """PostgreSQL 客户端（连接池）"""

    def __init__(
            self,
            host='localhost',
            port=5432,
            db: str = None,
            user: str = None,
            password: str = None,
            minconn=1,
            maxconn=10
    ):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password
        self.minconn = minconn
        self.maxconn = maxconn
        self.pool = None

    def connect(self):
        """初始化连接池"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=self.minconn,
                maxconn=self.maxconn,
                host=self.host,
                port=self.port,
                dbname=self.db,
                user=self.user,
                password=self.password
            )
            log.debug(f"连接池初始化成功，最大连接数：{self.maxconn}")
        except OperationalError as e:
            log.debug(f"连接池初始化失败: {e}")
            raise

    def get_connection(self):
        """从连接池获取一个数据库连接"""
        if not self.pool:
            self.connect()
        return self.pool.getconn()

    def release_connection(self, conn):
        """将数据库连接归还到连接池"""
        if conn:
            self.pool.putconn(conn)

    @contextmanager
    def connection(self):
        """上下文管理器，用于自动获取和释放数据库连接"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            log.error(f"数据库操作失败: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)

    def execute(self, query: str, args: tuple = None) -> int:
        """执行 SQL 语句"""
        with self.connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, args)
            conn.commit()
            return cursor.rowcount

    def fetchall(self, query: str, args: tuple = None) -> list:
        """查询所有结果"""
        with self.connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, args)
            return cursor.fetchall() or []

    def fetchone(self, query: str, args: tuple = None):
        """查询单条结果"""
        with self.connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, args)
            return cursor.fetchone() or {}

    def query(self, query: str, args: tuple = None):
        """查询"""
        return self.fetchall(query, args)

    def insert_one(self, table: str, data: dict):
        """插入单条"""
        columns = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        return self.execute(query, tuple(data.values()))

    def insert_many(self, table: str, datas: list[dict]):
        """插入多条"""
        if not datas:
            raise ValueError("数据列表不能为空")

        first_keys = set(datas[0].keys())
        for item in datas:
            if set(item.keys()) != first_keys:
                raise ValueError("所有记录的字段必须一致")

        columns = ', '.join(datas[0].keys())
        values = ', '.join(['%s'] * len(datas[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        params = [tuple(item.values()) for item in datas]

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params)
            conn.commit()
            return cursor.rowcount

    def update(self, table: str, updated: dict, where_clause, where_params=None):
        """更新"""
        set_clause = ', '.join([f"{k} = %s" for k in updated.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(updated.values()) + (where_params or ())
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def delete(self, table: str, where_clause: str, where_params: tuple = None):
        """删除"""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, where_params)
            conn.commit()
            return cursor.rowcount

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pool:
            self.pool.closeall()
            log.warning("连接池已关闭")

    def create_table(self, name: str, fields: list[str]):
        """创建表"""
        field_defs = [f'"{field}" VARCHAR(255)' for field in fields]
        fields_sql = ', '.join(field_defs)
        sql = f'CREATE TABLE public."{name}" (id SERIAL PRIMARY KEY, {fields_sql})'
        self.execute(sql)
        log.success(f"表 {name} 创建成功")

    def drop_table(self, name: str, schema: str = "public"):
        """删除表"""
        sql = f'DROP TABLE IF EXISTS {schema}."{name}"'
        self.execute(sql)
