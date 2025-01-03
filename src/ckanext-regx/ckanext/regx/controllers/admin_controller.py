from flask import jsonify, render_template, request
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging

log = logging.getLogger(__name__)


class AdminController:
    @staticmethod
    def admin_all_profiles():
        """
        Render admin profiles page or return JSON for DataTables.
        """
        try:
            connection = connect_to_db()
            if not connection:
                raise Exception("Failed to connect to the database.")

            companies = []
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, company_name, address, website, status FROM regx_company")
                rows = cursor.fetchall()
                companies = [
                    {
                        "id": row[0],
                        "company_name": row[1],
                        "address": row[2],
                        "website": row[3],
                        "status": row[4],
                    }
                    for row in rows
                ]

            close_db_connection(connection)

            # Check if the request is an AJAX request (used by DataTables)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"data": companies})
            else:
                # Render the HTML page with an empty companies list for initial load
                return tk.render("admin_all_profiles.html", {"companies": []})

        except Exception as e:
            log.error(f"Error fetching companies: {e}")
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def toggle_status():
        """
        Toggle the status of a company profile.
        """
        try:
            company_id = request.form.get("company_id")
            new_status = request.form.get("new_status") == "true"

            connection = connect_to_db()
            if not connection:
                raise Exception("Failed to connect to the database.")

            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE regx_company SET status = %s WHERE id = %s",
                    (new_status, company_id),
                )
                connection.commit()

            close_db_connection(connection)

            return jsonify({"message": "Status updated successfully!"})

        except Exception as e:
            log.error(f"Error toggling status: {e}")
            return jsonify({"error": str(e)}), 500
