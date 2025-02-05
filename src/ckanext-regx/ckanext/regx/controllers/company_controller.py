from flask import request, redirect, url_for, flash, get_flashed_messages
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import psycopg2
import logging

# Setting up logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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
            official_email = request.form.get('official_email')
            your_email = request.form.get('your_email')
            role = request.form.get('role')
            alternative_names = request.form.getlist('alt_names[]')

            # Log received data
            log.debug(f"Received data: {company_name}, {website}, {official_email}, {your_email}, {role}, {alternative_names}")  # noqa

            # Validate form data
            if not all([company_name, website, official_email, your_email, role]) or not alternative_names:
                flash("All fields are required.", "error")
                return redirect(url_for('regx.company_form'))

            # Database connection
            connection = connect_to_db()
            if connection:
                try:
                    connection.autocommit = False
                    with connection.cursor() as cursor:
                        # Check if the company already exists
                        cursor.execute(
                            "SELECT COUNT(*) FROM regx_company WHERE LOWER(company_name) = LOWER(%s)",
                            (company_name,)
                        )
                        if cursor.fetchone()[0] > 0:
                            flash("Company already exists in our database.", "error")
                            return redirect(url_for('regx.company_form'))

                        # Insert new company
                        cursor.execute(
                            """
                            INSERT INTO regx_company (company_name, website, email_address, claimant, claimant_role, status)
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                            """,
                            (company_name, website, official_email,
                             your_email, role, False)
                        )
                        company_id = cursor.fetchone()[0]

                        # Insert alternative names
                        for alt_name in alternative_names:
                            cursor.execute(
                                """
                                INSERT INTO regx_alternative_names (alternative_name, company_id)
                                VALUES (%s, %s)
                                """,
                                (alt_name, company_id)
                            )
                        connection.commit()
                        flash("Company created successfully!", "success")
                except psycopg2.Error as e:
                    connection.rollback()
                    log.error(f"PostgreSQL Error: {e.pgerror}")
                    flash("An error occurred while saving the company.", "error")
                finally:
                    close_db_connection(connection)
            else:
                flash("Failed to connect to the database.", "error")

        except Exception as e:
            log.error(f"Unexpected error: {e}")
            flash("An unexpected error occurred.", "error")

        return redirect(url_for('regx.company_form'))
