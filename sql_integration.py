import sys
import pandas as pd

sys.path.append("./SQL-Data-Load/")

import src.pysql.pySQL as pySQL
import conn

tables = ["dbo.elo_competition", "dbo.elo_raking", "dbo.elo_matches"]


class EloDataLoad:
    def __init__(self):
        ssh = pySQL.SSHtunnel(
            ssh_host=conn.ssh_host,
            ssh_username=conn.ssh_username,
            ssh_password=conn.ssh_password,
            remote_bind_address=conn.remote_bind_address,
        )
        tunnel = ssh.create_tunnel()
        tunnel.start()
        self.sql = pySQL.SQL(
            host=conn.host,
            database=conn.database,
            user=conn.user,
            password=conn.password,
            port=tunnel.local_bind_port,
            connect_type="MySQL",
        )

    def load_data(self, df, table_name, truncate: bool):
        self.sql.load_data_to_SQL(
            df=df, table=f"{table_name}", truncate=truncate, batch_size=10
        )

    def truncate_table(self, table):
        self.sql.read_query(f"truncate table {table}")

    def truncate_tables(self):
        for i in tables:
            self.truncate_table(table=i)


if "__main__" == __name__:
    sql = EloDataLoad()
