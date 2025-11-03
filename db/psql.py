from contextlib import contextmanager

from loguru import logger as log
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


class PostgresqlClient:
    """PostgreSQL 客户端（连接池）"""

    def __init__(self, host="localhost", port=5432, db: str = None, user: str = None, password: str = None, minconn=1, maxconn=10):
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
            self.pool = ThreadedConnectionPool(minconn=self.minconn, maxconn=self.maxconn, host=self.host, port=self.port, dbname=self.db, user=self.user, password=self.password)
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
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
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

        columns = ", ".join(datas[0].keys())
        values = ", ".join(["%s"] * len(datas[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        params = [tuple(item.values()) for item in datas]

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params)
            conn.commit()
            return cursor.rowcount

    def update(self, table: str, updated: dict, where_clause, where_params=None):
        """更新"""
        set_clause = ", ".join([f"{k} = %s" for k in updated.keys()])
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
        fields_sql = ", ".join(field_defs)
        sql = f'CREATE TABLE public."{name}" (id SERIAL PRIMARY KEY, {fields_sql})'
        self.execute(sql)
        log.success(f"表 {name} 创建成功")

    def drop_table(self, name: str, schema: str = "public"):
        """删除表"""
        sql = f'DROP TABLE IF EXISTS {schema}."{name}"'
        self.execute(sql)
        log.success(f"✅ 表 {name} 删除成功")

    def create_great_table(self, name: str, fields: list[str]):
        """
        创建表
        - 额外包含 id 主键、created_at 和 updated_at 字段
        - 数据新增时，created_at 自动设置为当前时间（精确到秒）
        - 数据更新时，updated_at 自动设置为当前时间（精确到秒）

        Args:
            name: 表名
            fields: 字段列表，每个字段名，默认类型为varchar(255)
        """
        if not name or not name.strip():
            raise ValueError("表名不能为空")

        if not fields or not all(isinstance(f, str) and f.strip() for f in fields):
            raise ValueError("字段列表不能为空且必须为字符串")

        field_defs = [f'"{field}" VARCHAR(255)' for field in fields]
        fields_sql = ", ".join(field_defs) if field_defs else ""

        # 时间字段放在最后，精度为秒 TIMESTAMP(0)
        if fields_sql:
            sql = f"""
            CREATE TABLE public."{name}" (
                id SERIAL PRIMARY KEY,
                {fields_sql},
                created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP(0)
            )
            """
        else:
            sql = f"""
            CREATE TABLE public."{name}" (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP(0)
            )
            """

        # 创建表
        self.execute(sql)

        # 创建触发器函数（如果不存在）
        # TIMESTAMP(0) 表示精度到秒
        trigger_func_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP::TIMESTAMP(0);
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        self.execute(trigger_func_sql)

        # 为表创建触发器（BEFORE UPDATE）
        trigger_sql = f"""
        CREATE TRIGGER update_{name}_updated_at
        BEFORE UPDATE ON public."{name}"
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
        self.execute(trigger_sql)

        log.success(f"✅ 表 {name} 创建成功")


if __name__ == "__main__":
    psql = PostgresqlClient(host="localhost", port=5432, db="my", user="wauo", password="admin1")
    psql.connect()
    name = "acc"
    psql.create_great_table(name, ["username", "password"])
    input(f"按回车键删除表 {name}...")
    psql.drop_table(name)
