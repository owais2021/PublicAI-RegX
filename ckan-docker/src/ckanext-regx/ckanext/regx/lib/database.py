############################################################
#                                                          #
#         Code implemented by Owais Khan                   #
#         Version: 1.0                                     #
#         Description: Handles database connections,       #
#                      table creation, data insertion,     #
#                      and updates for company and tender  #
#                      information in a PostgreSQL DB.     #
#                                                          #
############################################################
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
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,
        vat_number VARCHAR ,
        tax_id VARCHAR ,
        public_id VARCHAR,
        company_address VARCHAR(255) ,
        is_claimed BOOLEAN DEFAULT FALSE, -- Default to inactive,
        profile_created_by VARCHAR
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


def create_claimants_table(connection):
    """
    Create the 'regx_claimants' table in the database if it doesn't already exist.
    """
    create_table_query = """
            CREATE TABLE IF NOT EXISTS regx_claimants (
                id SERIAL PRIMARY KEY,
                claimant TEXT,
                claimant_role TEXT,
                status BOOLEAN DEFAULT FALSE,
                c_id VARCHAR NOT NULL,
                FOREIGN KEY (c_id) REFERENCES regx_company(id) ON DELETE CASCADE
            )
        """
    try:
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            connection.commit()
            log.info("Table 'regx_claimants' created successfully!")
    except Exception as e:
        connection.rollback()
        log.error(f"Error creating table 'regx_claimants': {e}")


def create_tender_table(connection):
    ###### Create the `regx_tender` table #####
    create_tender_table_query = """
        CREATE TABLE IF NOT EXISTS regx_tender (
        id SERIAL PRIMARY KEY,
        tender_id VARCHAR NULL,
        tender_title VARCHAR NULL,
        company_name VARCHAR NULL,
        company_id VARCHAR(255) REFERENCES regx_company(id),
        CONSTRAINT unique_tender UNIQUE (tender_id, company_name)
    );
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(create_tender_table_query)
            connection.commit()
            log.info("Table 'regx_tender' created successfully!")
    except Exception as e:
        connection.rollback()
        log.error(f"Error creating table 'regx_tender': {e}")

def create_alternative_names_table(connection):
    ###### Create the `regx_alternative_names` table #####
    create_alternative_names_table_query = """
        CREATE TABLE IF NOT EXISTS regx_alternative_names (
        id SERIAL PRIMARY KEY,
        company_id VARCHAR(255) NOT NULL,
        alternative_name TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES regx_company(id)
    );
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(create_alternative_names_table_query)
            connection.commit()
            log.info("Table 'regx_alternative_names' created successfully!")
    except Exception as e:
        connection.rollback()
        log.error(f"Error creating table 'regx_alternative_names': {e}")


def create_tables(connection):

    create_company_table(connection=connection)
    create_tender_table(connection=connection)
    create_alternative_names_table(connection=connection)
    create_claimants_table(connection=connection)


def insert_company_data(company_name, connection):
    """
    Ensure the `company_name` exists in the 'regx_company' table.
    If not, insert it and return the company_id.
    """
    try:
        with connection.cursor() as cursor:
            ###### Check if the company exists in `regx_company` #####
            check_company_query = "SELECT id FROM regx_company WHERE company_name = %s"
            cursor.execute(check_company_query, (company_name,))
            company_record = cursor.fetchone()

            if not company_record:
                ###### Insert the company if it doesn't exist #####
                insert_company_query = "INSERT INTO regx_company (company_name) VALUES (%s) RETURNING id"
                cursor.execute(insert_company_query, (company_name,))
                company_id = cursor.fetchone()[0]
                log.info(f"Inserted into 'regx_company': {company_name}")
            else:
                ###### Use existing company_id #####
                company_id = company_record[0]

            return company_id
    except Exception as e:
        log.error(f"Error inserting company data: {e}")
        return None
    
def insert_tender_data(tender_id, company_name, tender_title, connection):
    """
    Insert `tender_id`, `company_name`, and `tender_title` into the 'regx_tender' table.
    Ensure the `company_name` exists in the 'regx_company' table.
    """
    try:
        ###### Ensure the company exists and retrieve company_id #####
        company_id = insert_company_data(company_name, connection)
        if company_id is None:
            log.error("Company insertion failed. Tender data not inserted.")
            return

        # Insert into `regx_tender` #####
        with connection.cursor() as cursor:
            insert_tender_query = """
            INSERT INTO regx_tender (tender_id, company_name, tender_title, company_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tender_id, company_name) DO NOTHING;
            """
            cursor.execute(insert_tender_query, (tender_id, company_name, tender_title, company_id))
            connection.commit()
            log.info(f"Inserted into 'regx_tender': {tender_id}, {company_name}")
    except Exception as e:
        connection.rollback()
        log.error(f"Error inserting tender data: {e}")

def save_website_and_email(company_name, website_url, emails, resource_url, connection):
    """
    Update the website and emails for the specified company in the database.
    """
    try:
        # Update emails for the specified company
        if emails and isinstance(emails, list):
            for email in emails:
                email = email.strip()  # Clean up any whitespace
                if email:  # Ensure the email is not an empty string
                   # log.info(f"Updating email {email} for {company_name}")
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE regx_company
                            SET email = %s, modified = CURRENT_TIMESTAMP
                            WHERE company_name = %s;
                        """, (email, company_name))
                    connection.commit()

        # Update website for the specified company
        if website_url:
            log.info(f"Updating website {website_url} for {company_name}")
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE regx_company
                    SET website = %s, modified = CURRENT_TIMESTAMP
                    WHERE company_name = %s;
                """, (website_url, company_name))
            connection.commit()
        
        ######### Update resource URL for the specified company #########

        if resource_url:

            log.info(f"Updating resource URL {resource_url} for {company_name}")
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE regx_company
                    SET resource_url = %s, modified = CURRENT_TIMESTAMP
                    WHERE company_name = %s;
                """, (resource_url, company_name))
            connection.commit()

    except Exception as e:
        log.error(f"Error updating website and email for {company_name}: {e}")


def get_package_names_from_db(connection):
    """
    Retrieve the company names (PACKAGE_NAME) from the database.
    """
    try:
        with connection.cursor() as cursor:
            query = "SELECT company_name FROM regx_company;"  ######### Adjust the query as needed #########
            cursor.execute(query)
            result = cursor.fetchall()
            if result:
                ######### Return a list of company names #########
                return [row[0] for row in result]
            log.info("No company names found in the database.")
            return []
    except Exception as e:
        log.error(f"Error retrieving company names: {e}")
        return []


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
