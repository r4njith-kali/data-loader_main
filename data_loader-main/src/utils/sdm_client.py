import psycopg2
from definitions import CONFIG_DIR
from src.utils.utilities import config_param
from sqlalchemy import create_engine, inspect, URL
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sal

db_config = config_param(config_file=f'{CONFIG_DIR}/sdm_config.yaml', field='sdm_db')


def pg_client(config: dict = db_config) -> [sal.engine, sal.engine.Connection, sal.orm.session, sal.inspect]:
    """
    Create PostgresSQL client
    Args:
        config: Database information - IP, PORT, USERNAME, PASSWORD, DATABASE
    Returns:
        sqlalchemy: engine, connection, session and inspection
    """
    url_object = URL.create(
        'postgresql+psycopg2',
        username=config['user'],
        password=config['password'],
        host=config['host'],
        port=config['port'],
        database=config['database']
    )
    # connect_object = {'options': '-c search_path={}'.format(config['schema'], '-c timezone=utc')}
    connect_object = {'options': '-c search_path={}'.format(config['schema'])}

    engine = create_engine(url_object, connect_args=connect_object)
    Session = sessionmaker(bind=engine)
    connect = engine.connect()
    session = Session()
    inspection = inspect(engine)
    print('Server:', config['host'])
    print('Database:', config['database'])
    print('Schema:', inspection.get_schema_names())

    return engine, connect, session, inspection


def pg_cursor(config: dict = db_config) -> [psycopg2.connect, psycopg2.extensions.cursor]:
    """
    Create psycopg2 connection and cursor for table create/delete/update
    Args:
        config: Database information - IP, PORT, USERNAME, PASSWORD, DATABASE
    Returns:
        psycopg2: cursor and connection
    """
    connection = psycopg2.connect(
        host=config['host'],
        database=config['database'],
        port=config['port'],
        user=config['user'],
        password=config['password'])

    cursor = connection.cursor()

    return connection, cursor


if __name__ == '__main__':
    eng, conn, sess, insp = pg_client(db_config)
