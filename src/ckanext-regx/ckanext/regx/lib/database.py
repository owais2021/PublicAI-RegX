import os
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def connect_to_db():
    """
    Establish a connection to the PostgreSQL database using environment variables.
    """
    try:
        dbname = os.getenv("CKAN_DB")
        user = os.getenv("CKAN_DB_USER")
        password = os.getenv("CKAN_DB_PASSWORD")
        host = os.getenv("DB_HOST", "db")  # Default to 'db' if not set
        port = os.getenv("DB_PORT", 5432)  # Default to 5432 if not set

        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        log.info("Database connection established!")
        return connection
    except Exception as e:
        log.error(f"Database connection failed: {e}")
        return None


def create_sherry_table(connection):
    """
    Create the 'sherry' table in the database if it doesn't already exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS sherry (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            connection.commit()
            log.info("Table 'sherry' created successfully!")
    except Exception as e:
        connection.rollback()
        log.error(f"Error creating table 'sherry': {e}")


def create_company_table(connection):
    """
    Create the 'regx_company' table in the database if it doesn't already exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS regx_company (
        id SERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        website TEXT NOT NULL,
        address TEXT NOT NULL,
        status BOOLEAN DEFAULT FALSE, -- Default to inactive
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            connection.commit()
            log.info("Table 'regx_company' created successfully!")
    except Exception as e:
        connection.rollback()
        log.error(f"Error creating table 'regx_company': {e}")


def close_db_connection(connection):
    """
    Close the database connection.
    """
    try:
        if connection:
            connection.close()
            log.info("Database connection closed.")
    except Exception as e:
        log.error(f"Error closing database connection: {e}")
