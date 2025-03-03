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
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()
def connect_to_db():
    """
    Establish a connection to the PostgreSQL database using environment variables.
    """
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        print("Database connection established!")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def create_table(connection):
    """
    Create the 'regx_company', 'regx_tender', and 'alternative_company' tables in the database.
    """
    #### Create the `regx_company` table #####
    create_company_table_query = """
    CREATE TABLE IF NOT EXISTS regx_company (
        id SERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        website VARCHAR(255),
        email VARCHAR(255),
        resource_url TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_company_email UNIQUE (company_name, email)
    );
     """
    #### Create the `regx_tender` table ####
    create_tender_table_query = """
    CREATE TABLE IF NOT EXISTS regx_tender (
        id SERIAL PRIMARY KEY,
        tender_id TEXT NOT NULL,
        company_name TEXT NOT NULL,
        tender_title TEXT NOT NULL,
        company_id INT REFERENCES regx_company(id),
        CONSTRAINT unique_tender UNIQUE (tender_id, company_name)
    );
    """
    #### Create the `alternative_company` table ####
    create_alternative_company_table_query = """
    CREATE TABLE IF NOT EXISTS regx_alternative_company (
        id SERIAL PRIMARY KEY,
        company_id INT NOT NULL,
        company_name_updated TEXT NOT NULL,
        website_updated VARCHAR(255),
        email_updated VARCHAR(255) UNIQUE
    );
    """

    try:
        with connection.cursor() as cursor:
            #### Create `regx_company` table ####
            cursor.execute(create_company_table_query)
            print("Table 'regx_company' created successfully!")

            #### Create `regx_tender` table ####
            cursor.execute(create_tender_table_query)
            print("Table 'regx_tender' created successfully!")

            #### Create alternative_company table ####
            cursor.execute(create_alternative_company_table_query)
            print("Table 'alternative_company' created successfully!")

        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Error creating tables: {e}")

def insert_company_data(company_name, connection):
    """
    Ensure the `company_name` exists in the 'regx_company' table.
    If not, insert it and return the company_id.
    """
    try:
        with connection.cursor() as cursor:
            #### Check if the company exists in `regx_company` ####
            check_company_query = "SELECT id FROM regx_company WHERE company_name = %s"
            cursor.execute(check_company_query, (company_name,))
            company_record = cursor.fetchone()

            if not company_record:
                #### Insert the company if it doesn't exist ####
                insert_company_query = "INSERT INTO regx_company (company_name) VALUES (%s) RETURNING id"
                cursor.execute(insert_company_query, (company_name,))
                company_id = cursor.fetchone()[0]
                print(f"Inserted into 'regx_company': {company_name}")
            else:
                #### Use existing company_id ####
                company_id = company_record[0]

            return company_id
    except Exception as e:
        print(f"Error inserting company data: {e}")
        return None

def insert_tender_data(tender_id, company_name, tender_title, connection):
    """
    Insert `tender_id`, `company_name`, and `tender_title` into the 'regx_tender' table.
    Ensure the `company_name` exists in the 'regx_company' table.
    """
    try:
        #### Ensure the company exists and retrieve company_id ####
        company_id = insert_company_data(company_name, connection)
        if company_id is None:
            print("Company insertion failed. Tender data not inserted.")
            return

        #### Insert into `regx_tender` with `tender_title` ####
        with connection.cursor() as cursor:
            insert_tender_query = """
            INSERT INTO regx_tender (tender_id, company_name, tender_title, company_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tender_id, company_name) DO NOTHING;
            """
            cursor.execute(insert_tender_query, (tender_id, company_name, tender_title, company_id))
            connection.commit()
            print(f"Inserted into 'regx_tender': {tender_id}, {company_name}, {tender_title}")
    except Exception as e:
        connection.rollback()
        print(f"Error inserting tender data: {e}")

def save_website_and_email(company_name, website_url, emails, resource_url, connection):
    """
    Update the website, emails, and resource URL for the specified company in the database.
    """
    try:
        #### Update emails for the specified company ####
        if emails and isinstance(emails, list):
            for email in emails:
                email = email.strip()  #### Clean up any whitespace ####
                if email:  #### Ensure the email is not an empty string ####
                    print(f"Updating email {email} for {company_name}")
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE regx_company
                            SET email = %s, modified = CURRENT_TIMESTAMP
                            WHERE company_name = %s;
                        """, (email, company_name))
                    connection.commit()

        #### Update website for the specified company ####
        if website_url:
            print(f"Updating website {website_url} for {company_name}")
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE regx_company
                    SET website = %s, modified = CURRENT_TIMESTAMP
                    WHERE company_name = %s;
                """, (website_url, company_name))
            connection.commit()

        #### Update resource URL for the specified company ####
        if resource_url:
            print(f"Updating resource URL {resource_url} for {company_name}")
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE regx_company
                    SET resource_url = %s, modified = CURRENT_TIMESTAMP
                    WHERE company_name = %s;
                """, (resource_url, company_name))
            connection.commit()
    except Exception as e:
        print(f"Error updating website, email, and resource URL for {company_name}: {e}")

def get_package_names_from_db(connection):
    """
    Retrieve the company names (PACKAGE_NAME) from the database.
    """
    try:
        with connection.cursor() as cursor:
            query = "SELECT company_name FROM regx_company;"  #### Adjust the query as needed ####
            cursor.execute(query)
            result = cursor.fetchall()
            if result:
                #### Return a list of company names ####
                return [row[0] for row in result]
            print("No company names found in the database.")
            return []
    except Exception as e:
        print(f"Error retrieving company names: {e}")
        return []
        
def close_db_connection(connection):
    """
    Close the database connection.
    """
    try:
        connection.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"Error closing database connection: {e}")

def main():
    """
    Main function to execute the script.
    """
    #### Connect to the database ####
    connection = connect_to_db()
    if connection is None:
        print("Failed to establish a database connection. Exiting...")
        return

    create_table(connection)   
    close_db_connection(connection)

if __name__ == "__main__":
    main()
