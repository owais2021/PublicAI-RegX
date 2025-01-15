from flask import request, redirect, url_for, flash, get_flashed_messages
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

log = logging.getLogger(__name__)


class CompanyController:
    @staticmethod
    def company_form():
        """
        Display the company form with flash messages.
        """
        log.debug("Rendering company form.")
        # Fetch flash messages
        flash_messages = get_flashed_messages(with_categories=True)
        return tk.render('company_form.html', extra_vars={'flash_messages': flash_messages})

    @staticmethod
    def submit_company():
        """
        Handle form submission and save data into the 'regx_company' table.
        """
        try:
            company_name = request.form.get('company_name')
            website = request.form.get('website')
            address = request.form.get('address')

            # Validate form data
            if not all([company_name, website, address]):
                flash("All fields are required.", "error")
                return redirect(url_for('regx.company_form'))

            # Check if company name already exists (case-insensitive)
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT COUNT(*) FROM regx_company WHERE LOWER(company_name) = LOWER(%s)",
                            (company_name,)
                        )
                        exists = cursor.fetchone()[0] > 0

                        if exists:
                            flash("Company already exists in our database.", "error")
                            return redirect(url_for('regx.company_form'))

                        # Insert new company
                        cursor.execute(
                            """
                            INSERT INTO regx_company (company_name, website, email_address, status)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (company_name, website, address, False)
                        )
                        connection.commit()
                        flash("Company created successfully!", "success")
                except Exception as e:
                    connection.rollback()
                    log.error(f"Error saving data: {e}")
                    flash("An error occurred while saving the company.", "error")
                finally:
                    close_db_connection(connection)
            else:
                flash("Failed to connect to the database.", "error")

        except Exception as e:
            log.error(f"Unexpected error: {e}")
            flash("An unexpected error occurred.", "error")

        return redirect(url_for('regx.company_form'))
