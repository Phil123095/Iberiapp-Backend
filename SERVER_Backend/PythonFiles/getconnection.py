from sqlalchemy import create_engine, engine

def get_db_connections():
    engine_final = create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        engine.url.URL.create(
            drivername="mysql+mysqlconnector",
            username='admin',  # e.g. "my-database-user"
            password='blockchaintest1',  # e.g. "my-database-password"
            host='blockchain-db.c1gc1t7hjfvr.eu-central-1.rds.amazonaws.com',  # e.g. "127.0.0.1"
            port=3306,  # e.g. 3306
            database='TI_database'  # e.g. "my-database-name",
        )
    )
    return engine_final