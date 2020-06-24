import logging

from motor.motor_asyncio import AsyncIOMotorClient
from app.core import config


class Database:
    client: AsyncIOMotorClient = None


db = Database()


def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect_to_mongo():
    logging.info("Connecting to Mongo...")
    db.client = AsyncIOMotorClient(
        str(config.MONGODB_URI),
        maxPoolSize=config.MAX_CONNECTIONS_COUNT,
        minPoolSize=config.MIN_CONNECTIONS_COUNT
        )
    logging.info("Connected.")

    # TODO init indexes
    await init_user_indexes(db.client)
    await init_company_indexes(db.client)
    await init_persona_indexes(db.client)
    # await init_project_indexes(db.client)


async def close_connection():
    logging.info("Closing Mongo connection...")
    db.client.close()
    logging.info("Connection closed.")


async def init_user_indexes(db: AsyncIOMotorClient):
    logging.info(f">>> {__name__}:{init_user_indexes.__name__}")
    logging.info(">>> Checking user indexes...")
    # db_name = config.MONGODB_NAME
    collection = db[config.MONGODB_NAME][config.DOCTYPE_USER]
    # collection = db['behavioral_db']['users']
    info = await collection.index_information()
    index_name = "username_index"
    if index_name in info:
        logging.info(f"Found index: {index_name}")
    else:
        logging.info(f"Index not found, creating index: {index_name}")
        await collection.create_index(
            [("username", 1)],
            unique=True,
            name=index_name
        )
    index_name = "email_index"
    if index_name in info:
        logging.info(f"Found index: {index_name}")
    else:
        logging.info(f"Index not found, creating index: {index_name}")
        await collection.create_index(
            [("email", 1)],
            unique=True,
            name=index_name
        )


async def init_company_indexes(db: AsyncIOMotorClient):
    logging.info(f">>> {__name__}:{init_company_indexes.__name__}")
    logging.info(">>> Checking company indexes...")
    collection = db[config.MONGODB_NAME][config.DOCTYPE_COMPANY]
    info = await collection.index_information()
    index_name = "creator_symbol_index"
    if index_name in info:
        logging.info(f"Found index: {index_name}")
    else:
        logging.info(f"Index not found, creating index: {index_name}")
        await collection.create_index(
            [("created_by", 1), ("symbol", 1)],
            unique=True,
            name=index_name
        )


async def init_project_indexes(db: AsyncIOMotorClient):
    logging.info(">>> " + __name__ + ":" + init_project_indexes.__name__ )
    logging.info("Cheking project indexes...")
    collection = db[config.MONGODB_NAME][config.DOCTYPE_PROJECT]

    info = await collection.index_information()
    index_name = "project_complex_index"
    if index_name in info:
        logging.info("Found " + index_name)
    else:
        logging.info("Index not found, creating one...")
        await collection.create_index(
            [("batches.batch_id", 1), ("batches.workbook_sessions.workbook", 1)],
            unique=True,
            name=index_name
        )


async def init_persona_indexes(db: AsyncIOMotorClient):
    logging.info(">>> " + __name__ + ":" + init_persona_indexes.__name__ )
    logging.info("Cheking persona indexes...")
    collection = db[config.MONGODB_NAME][config.DOCTYPE_PERSONA]

    info = await collection.index_information()
    index_name = "projectid_username_index"
    if index_name in info:
        logging.info("Found " + index_name)
    else:
        logging.info("Index not found, creating one...")
        await collection.create_index(
            [("prj_id", 1), ("username", 1)],
            unique=True,
            name=index_name
        )


