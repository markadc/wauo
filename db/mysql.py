from contextlib import contextmanager
from urllib.parse import urlparse, parse_qs

import pymysql
from dbutils.pooled_db import PooledDB
from loguru import logger
from pymysql.cursors import DictCursor


class MysqlClient:
    """MySQL客户端"""

    def __init__(self, host="localhost", port=3306, user="root", password: str = None, database: str = None, charset="utf8mb4", **pool_kwargs):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": charset,
        }

        # 默认连接池配置
        self.pool_config = {
            "creator": pymysql,
            "autocommit": True,
            "cursorclass": DictCursor,
            "mincached": 1,
            "maxcached": 20,
            "maxshared": 10,
            "maxconnections": 100,
            "blocking": True,
            "maxusage": 0,
            "setsession": [],
            "ping": 1,
            **pool_kwargs,  # 允许自定义连接池参数
        }

        self.pool: PooledDB = None
        self._init()

    @classmethod
    def from_url(cls, url: str, **pool_kwargs):
        """从URL创建MySQL客户端实例

        Args:
            url: MySQL连接URL，格式如: mysql://user:password@host:port/database
            **pool_kwargs: 连接池配置参数

        Returns:
            MySQLClient: MySQL客户端实例
        """
        parsed = urlparse(url)

        if parsed.scheme != "mysql":
            raise ValueError("URL必须以mysql://开头")

        # 解析主机和端口
        host = parsed.hostname
        port = parsed.port or 3306
        user = parsed.username
        password = parsed.password
        database = parsed.path.lstrip("/")

        # 解析查询参数
        query_params = parse_qs(parsed.query)

        # 处理charset参数
        charset = "utf8mb4"
        if "charset" in query_params:
            charset = query_params["charset"][0]

        # 其他查询参数可以作为连接池参数
        for key, values in query_params.items():
            if key not in ["charset"]:
                value = values[0]
                # 尝试转换为整数，如果失败则保持字符串
                try:
                    if key in [
                        "mincached",
                        "maxcached",
                        "maxshared",
                        "maxconnections",
                        "maxusage",
                        "ping",
                    ]:
                        pool_kwargs[key] = int(value)
                    elif key in ["blocking"]:
                        pool_kwargs[key] = value.lower() in ["true", "1", "yes"]
                    else:
                        pool_kwargs[key] = value
                except ValueError:
                    pool_kwargs[key] = value

        return cls(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            **pool_kwargs,
        )

    def _init(self):
        """初始化数据库连接池"""
        config = self.pool_config | self.config
        try:
            self.pool = PooledDB(**config)
            logger.info(
                f"数据库连接池初始化成功: {self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = self.pool.connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作异常: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute(self, sql: str, args: tuple | list | None = None) -> int:
        """执行SQL语句"""
        if not sql or not sql.strip():
            raise ValueError("SQL语句不能为空")

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, args)
                return affected_rows

    def fetchone(self, sql: str, args: tuple = None) -> dict:
        """获取单条记录"""
        if not sql or not sql.strip():
            raise ValueError("SQL语句不能为空")

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchone() or {}

    def fetchall(self, sql: str, args: tuple = None) -> list[dict]:
        """获取所有记录"""
        if not sql or not sql.strip():
            raise ValueError("SQL语句不能为空")

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchall() or []

    def fetchmany(self, sql: str, args: tuple = None, n=2) -> list[dict]:
        """获取多条记录"""
        if not sql or not sql.strip():
            raise ValueError("SQL语句不能为空")

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchmany(n) or []

    def insert_one(self, table: str, item: dict) -> int:
        """插入单条记录"""
        if not item:
            logger.warning("插入数据为空")
            return 0

        if not table or not table.strip():
            raise ValueError("表名不能为空")

        try:
            columns = list(item.keys())
            placeholders = ["%s"] * len(columns)
            values = list(item.values())

            sql = f"INSERT INTO `{table}` ({', '.join(f'`{col}`' for col in columns)}) VALUES ({', '.join(placeholders)})"

            return self.execute(sql, tuple(values))
        except Exception as e:
            logger.error(f"插入单条记录失败: {e}")
            raise

    def insert_many(self, table: str, items: list[dict]) -> int:
        """批量插入记录"""
        if not items:
            logger.warning("批量插入数据为空")
            return 0

        if not table or not table.strip():
            raise ValueError("表名不能为空")

        try:
            columns = list(items[0].keys())
            placeholders = ["%s"] * len(columns)

            sql = f"INSERT INTO `{table}` ({', '.join(f'`{col}`' for col in columns)}) VALUES ({', '.join(placeholders)})"

            values_list = [tuple(data[col] for col in columns) for data in items]

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    affected_rows = cursor.executemany(sql, values_list)
                    return affected_rows
        except Exception as e:
            logger.error(f"批量插入记录失败: {e}")
            raise

    def update(
            self,
            table: str,
            item: dict,
            where: str,
            args: tuple | list | None = None,
    ) -> int:
        """更新记录"""
        if not item:
            logger.warning("更新数据为空")
            return 0

        if not table or not table.strip():
            raise ValueError("表名不能为空")

        if not where or not where.strip():
            raise ValueError("WHERE条件不能为空")

        try:
            set_clauses = []
            values = []

            for column, value in item.items():
                set_clauses.append(f"`{column}` = %s")
                values.append(value)

            sql = f"UPDATE `{table}` SET {', '.join(set_clauses)} WHERE {where}"

            if args:
                if isinstance(args, (list, tuple)):
                    values.extend(args)
                else:
                    values.append(args)

            return self.execute(sql, tuple(values))
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise

    def delete(self, table: str, where: str, args: tuple | list | None = None) -> int:
        """删除记录"""
        if not table or not table.strip():
            raise ValueError("表名不能为空")

        if not where or not where.strip():
            raise ValueError("WHERE条件不能为空")

        try:
            sql = f"DELETE FROM `{table}` WHERE {where}"
            return self.execute(sql, args)
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            raise

    def query(self, sql: str, args: tuple | list | None = None) -> list[dict]:
        """查询方法"""
        return self.fetchall(sql, args)

    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        if self.pool:
            return {
                "min_cached": self.pool_config.get("mincached", 0),
                "max_cached": self.pool_config.get("maxcached", 0),
                "max_connections": self.pool_config.get("maxconnections", 0),
                "current_connections": (
                    len(self.pool._idle_cache)
                    if hasattr(self.pool, "_idle_cache")
                    else 0
                ),
            }
        return {}

    def close(self):
        """关闭连接池"""
        if self.pool:
            try:
                self.pool.close()
                logger.info("数据库连接池已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接池时出错: {e}")
        else:
            logger.warning("连接池未初始化或已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()


if __name__ == "__main__":
    # 使用URL创建连接
    db = MysqlClient.from_url("mysql://root:root@0@localhost:3306/test")
    print(id(db))
    print(db.get_pool_status())

    # 带查询参数的URL
    db = MysqlClient.from_url(
        "mysql://root:root@0@localhost:3306/test?charset=utf8mb4&mincached=5&maxcached=20"
    )
    print(id(db))
    print(db.get_pool_status())

    # 也可以混合使用
    db = MysqlClient.from_url(
        "mysql://root:root@0@localhost:3306/test", mincached=10, maxconnections=200
    )

    print(id(db))
    print(db.get_pool_status())

    db = MysqlClient(password="root@0", database="test")
    print(id(db))
    print(db.get_pool_status())

    db = MysqlClient(password="root@0", database="test")
    print(id(db))
    print(db.get_pool_status())
