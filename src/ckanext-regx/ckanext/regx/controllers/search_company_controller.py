from flask import request, render_template, jsonify
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

log = logging.getLogger(__name__)


class CompanySearchController:
    @staticmethod
    def search_company():
        company = None
        form_submitted = False  # Track if the form was submitted

        if request.method == 'POST':
            form_submitted = True  # Set form_submitted to True when POST is handled
            company_name = request.form.get('company_name')
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT company_name, email_address, website, created, id FROM regx_company WHERE company_name ILIKE %s AND status=TRUE AND is_claimed=TRUE",
                            (f"%{company_name}%",)
                        )
                        company = cursor.fetchall()
                        print(company)
                finally:
                    close_db_connection(connection)

        return render_template('search_company.html', company=company, form_submitted=form_submitted)
