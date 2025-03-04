import logging
import json
from ckan.common import c
from flask import jsonify, Response, request
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
from ckanext.regx.lib.otp_manager import OTPManager

log = logging.getLogger(__name__)


class AdminController:
    @staticmethod
    def admin_all_profiles():
        try:
            if "application/json" in request.headers.get("Accept", ""):
                connection = connect_to_db()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT c.id, c.company_name, c.email_address, c.website, c.status, c.created,
                                       array_agg(a.alternative_name) FILTER (WHERE a.alternative_name IS NOT NULL) AS alternative_names
                                FROM regx_company c
                                LEFT JOIN regx_alternative_names a ON c.id = a.company_id
                                GROUP BY c.id
                                ORDER BY c.created DESC
                            """)
                            rows = cursor.fetchall()
                            companies = [
                                {
                                    "id": row[0],
                                    "company_name": row[1],
                                    "email_address": row[2],
                                    "website": row[3],
                                    "status": row[4],
                                    "created": row[5].strftime('%Y-%m-%d') if row[5] else None,
                                    "alternative_names": row[6] if row[6] else []
                                }
                                for row in rows
                            ]
                            return jsonify({"data": companies})
                    finally:
                        close_db_connection(connection)
                else:
                    return jsonify({"error": "Database connection failed."}), 500
            else:
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
            # claimant = request.form.get("claimant")
            company_name = request.form.get("company_name")
            log.debug(
                f"Preparing to send claim request email to {company_id}, {company_name}.")

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

                        # if new_status:
                        # OTPManager.profile_approve_email(
                        #     claimant, company_name)
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
            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT id, company_name, email_address, website, status FROM regx_company WHERE id = %s",
                            (company_id,),
                        )
                        row = cursor.fetchone()
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
                            response.headers["Content-Disposition"] = (f"attachment; filename=company_{company_id}.json")  # noqa
                            return response
                        else:
                            return jsonify({"error": "Company not found."}), 404
                finally:
                    close_db_connection(connection)
            else:
                return jsonify({"error": "Database connection failed."}), 500
        except Exception as e:
            log.error(f"Error downloading dataset: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

    def view_profile(company_id):
        try:
            log.debug(f"uuid {company_id}")
            connection = connect_to_db()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            c.id,
                            c.company_name,
                            c.email_address,
                            c.website,
                            c.status,
                            c.created,
                            c.vat_number,
                            c.tax_id,
                            c.company_address,
                            c.resource_url,       
                            COALESCE(a.alternative_names, ARRAY[]::VARCHAR[]) AS alternative_names,
                            COALESCE(cl.claimants, ARRAY[]::VARCHAR[]) AS claimant,
                            COALESCE(cl.claimant_roles, ARRAY[]::VARCHAR[]) AS claimant_role,
                            COALESCE(cl.claimant_statuses, ARRAY[]::BOOLEAN[]) AS claimant_status,
                            COALESCE(t.tender_ids, ARRAY[]::VARCHAR[]) AS tender_ids,
                            COALESCE(t.tender_titles, ARRAY[]::VARCHAR[]) AS tender_titles
                        FROM regx_company c
                        LEFT JOIN (
                            SELECT 
                                company_id,
                                array_agg(DISTINCT alternative_name) AS alternative_names
                            FROM regx_alternative_names
                            GROUP BY company_id
                        ) a ON c.id = a.company_id
                        LEFT JOIN (
                            SELECT 
                                c_id,
                                array_agg(claimant ORDER BY id) AS claimants,
                                array_agg(claimant_role ORDER BY id) AS claimant_roles,
                                array_agg(status ORDER BY id) AS claimant_statuses
                            FROM regx_claimants
                            GROUP BY c_id
                        ) cl ON c.id = cl.c_id
                        LEFT JOIN (
                            SELECT
                                company_id,
                                array_agg(tender_id ORDER BY id) AS tender_ids,
                                array_agg(tender_title ORDER BY id) AS tender_titles
                            FROM regx_tender
                            GROUP BY company_id
                        ) t ON c.id = t.company_id
                        WHERE c.id = %s
                        ORDER BY c.created DESC;
                    """, (company_id,))
                    company = cursor.fetchone()
                    if company:
                        company_details = {
                            "id": company[0],
                            "company_name": company[1],
                            "email_address": company[2],
                            "website": company[3],
                            "status": company[4],
                            "created": company[5].strftime('%Y-%m-%d') if company[5] else None,
                            "vat_number": company[6],
                            "tax_id": company[7],
                            "company_address": company[8],
                            "resource_url": company[9],
                            "alternative_names": company[10] if company[10] else [],
                            "claimant": company[11] if company[11] else [],
                            "claimant_role": company[12] if company[12] else [],
                            "claimant_status": company[13] if company[13] else [],
                            "tender_ids": company[14] if company[14] else [],
                            "tender_titles": company[15] if company[15] else []
                        }
                        return tk.render('view_profile.html', extra_vars={'company': company_details})
                    else:
                        return "Company not found", 404
            else:
                return "Database connection failed", 500
        except Exception as e:
            log.error(f"Error fetching company details: {e}")
            return "Unexpected error occurred", 500
