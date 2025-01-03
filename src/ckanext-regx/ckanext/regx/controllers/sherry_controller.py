from flask import request, redirect, url_for
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

# Configure logging
log = logging.getLogger(__name__)


class SherryController:
    @staticmethod
    def sherry_form():
        """
        Display the form to collect name and address.
        """
        log.debug("Rendering sherry form.")
        return tk.render('sherry_form.html')

    @staticmethod
    def submit_sherry():
        """
        Handle the form submission and save data into the 'sherry' table.
        """
        try:
            # Retrieve form data
            name = request.form.get('name')
            address = request.form.get('address')
            log.debug(f"Form data received - Name: {name}, Address: {address}")

            # Validate form data
            if not name or not address:
                tk.h.flash_error('Both fields are required!')
                return redirect(url_for('regx.sherry_form'))

            # Connect to database
            connection = connect_to_db()
            if connection:
                try:
                    # Insert data into database
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO sherry (name, address) VALUES (%s, %s)",
                            (name, address)
                        )
                        connection.commit()
                        tk.h.flash_success('Data saved successfully!')
                        log.info("Data saved successfully to 'sherry' table.")
                except Exception as e:
                    connection.rollback()
                    log.error(f"Error saving data: {e}")
                    tk.h.flash_error(f"Error saving data: {e}")
                finally:
                    close_db_connection(connection)
            else:
                tk.h.flash_error("Failed to connect to the database.")
                log.error("Database connection failed.")

        except Exception as e:
            log.error(f"Unexpected error: {e}")
            tk.h.flash_error(f"An unexpected error occurred: {e}")

        # Redirect back to the form
        return redirect(url_for('regx.sherry_form'))
