import logging
import json
from flask import jsonify, Response, request, render_template
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection

log = logging.getLogger(__name__)


class AdminController:
    @staticmethod
    def admin_all_profiles():
        """
        Render the admin profiles page or return JSON data for AJAX requests.
        """
        try:
            if "application/json" in request.headers.get("Accept", ""):
                # AJAX request for JSON data
                connection = connect_to_db()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "SELECT id, company_name, address, website, status FROM regx_company"
                            )
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
                            return jsonify({"data": companies})
                    finally:
                        close_db_connection(connection)
                else:
                    return jsonify({"error": "Database connection failed."}), 500
            else:
                # Render the HTML page
                return tk.render("admin_all_profiles.html")
        except Exception as e:
            log.error(f"Error fetching companies: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

    @staticmethod
    def toggle_status():
        """
        Toggle the active/inactive status of a company profile.
        """
        try:
            company_id = request.form.get("company_id")
            new_status = request.form.get("new_status") == "true"

            if not company_id:
                return jsonify({"error": "Company ID is required."}), 400

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE regx_company SET status = %s WHERE id = %s",
                            (new_status, company_id),
                        )
                        connection.commit()
                        return jsonify({"message": "Status updated successfully."})
                finally:
                    close_db_connection(connection)
            else:
                return jsonify({"error": "Database connection failed."}), 500
        except Exception as e:
            log.error(f"Error toggling status: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

    @staticmethod
    def download_dataset(company_id):
        """
        Download dataset for a specific company as JSON.
        """
        try:
            log.debug(f"Downloading dataset for company_id: {company_id}")
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id, company_name, address, website, status FROM regx_company WHERE id = %s",
                            (company_id,),
                        )
                        row = cursor.fetchone()
                        log.debug(f"Query result for company_id {company_id}: {row}")  # noqa
                        if row:
                            company_data = {
                                "id": row[0],
                                "company_name": row[1],
                                "address": row[2],
                                "website": row[3],
                                "status": row[4],
                            }
                            response = Response(
                                json.dumps(company_data, indent=4),
                                content_type="application/json",
                            )
                            response.headers["Content-Disposition"] = (f"attachment; filename=company_{company_id}.json"  # noqa
                                                                       )
                            return response
                        else:
                            log.error(
                                f"No company found for company_id {company_id}")
                            return Response(
                                json.dumps({"error": "Company not found."}),
                                content_type="application/json",
                                status=404,
                            )
                finally:
                    close_db_connection(connection)
            else:
                log.error("Database connection failed.")
                return Response(
                    json.dumps({"error": "Database connection failed."}),
                    content_type="application/json",
                    status=500,
                )
        except Exception as e:
            log.error(f"Error downloading dataset: {e}")
            return Response(
                json.dumps({"error": "Unexpected error occurred."}),
                content_type="application/json",
                status=500,
            )
