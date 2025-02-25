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

# Extra


def create_company_table(connection):
    """
    Create the 'regx_company' table in the database if it doesn't already exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS regx_company (
        id VARCHAR(255) PRIMARY KEY,
        company_name TEXT ,
        website TEXT ,
        email_address TEXT ,
        status BOOLEAN DEFAULT FALSE, -- Default to inactive
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        vat_number TEXT ,
        tax_id TEXT ,
        company_address TEXT ,
        is_claimed BOOLEAN DEFAULT FALSE, -- Default to inactive,
        profile_created_by TEXT
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
