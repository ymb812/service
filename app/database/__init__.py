import copy
from tortoise import Tortoise
from settings.settings import settings


conn_mask = 'postgres://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
config_mask = {
    'connections': {
        'default': ''
    },
    'apps': {
        'models': {
            'models': ['database.models'],
            'default_connection': 'default',
        }
    }
}

async def start(conn: dict):
    await Tortoise.init(config=conn)
    await Tortoise.generate_schemas()


async def teardown():
    await Tortoise.close_connections()


def get_config(connection) -> dict:
    config = copy.deepcopy(config_mask)
    config['connections']['default'] = connection
    return config


def get_connection():
    return conn_mask.format(
        DB_USERNAME=settings.db_user,
        DB_PASSWORD=settings.db_pass.get_secret_value(),
        DB_HOST=settings.db_host,
        DB_PORT=settings.db_port,
        DB_NAME=settings.db_name.get_secret_value(),
    )
