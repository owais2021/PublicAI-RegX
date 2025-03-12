# DB
import os
import logging
from ckan.plugins import SingletonPlugin, implements
from ckan.plugins import toolkit as tk
from ckan.plugins.interfaces import IBlueprint, IConfigurer
from functools import wraps
from flask import Blueprint, request, render_template, session, abort
from ckanext.regx.controllers.company_controller import CompanyController
from ckanext.regx.controllers.fetch_company_controller import FetchCompanyController
from ckanext.regx.controllers.edit_company_controller import EditCompanyController
from ckanext.regx.controllers.admin_controller import AdminController
from ckanext.regx.controllers.admin_user_controller import AdminUserController
from ckanext.regx.controllers.claim_profile_controller import ClaimProfileController
from ckanext.regx.controllers.search_company_controller import CompanySearchController
from ckanext.regx.lib.database import (
    connect_to_db,
    create_tables,
    close_db_connection
)
from ckanext.regx.lib.thread_manager import get_scheduler_thread

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class RegxPlugin(SingletonPlugin):
    implements(IBlueprint)
    implements(IConfigurer)

    def _check_access(self, admin_only=False):
        """
        Check access based on user role.
        :param admin_only: If True, only admin users can access the page.
        """
        user = tk.c.userobj
        if not user:
            # If no user is logged in, return 404
            tk.abort(404, "Page not found")
        if admin_only and not user.sysadmin:
            # If the page requires admin access and the user is not admin, return 404
            tk.abort(404, "Page not found")

    def otp_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'otp_verified' not in session or not session['otp_verified']:
                # Return a 404 Not Found error instead of redirecting
                abort(404)
            return f(*args, **kwargs)
        return decorated_function

    def get_blueprint(self):
        blueprint = Blueprint(
            'regx',
            __name__,
            template_folder=os.path.join(
                os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'public'),
            url_prefix='/regx'
        )

        @blueprint.route('/')
        def index():
            scheduler_thread=get_scheduler_thread()
            is_paused = scheduler_thread.is_paused()
            extra_vars = {
                'pause_job': is_paused  
            }
            """
            Index route for the plugin.
            """
            return tk.render('index.html', extra_vars)

        @blueprint.route('/view_profile/<company_id>', methods=['GET'])
        def view_profile(company_id):
            return AdminController.view_profile(company_id)

        @blueprint.route('/get_profiles/', methods=['GET'])
        def get_profiles():
            self._check_access()
            return CompanyController.get_profiles()

        @blueprint.route('/view_claimants/<company_id>', methods=['GET'])
        def view_claimants(company_id):
            log.debug("Accessing Claimants page.")
            self._check_access()
            return CompanyController.view_claimants(company_id)

        @blueprint.route('/toggle_status_claimant', methods=['POST'])
        def toggle_status_claimant():
            self._check_access()
            return CompanyController.toggle_status_claimant()

        # Routes for the Company form
        @blueprint.route('/company_form', methods=['GET'])
        def company_form():
            self._check_access()  # Ensure only logged-in users can access
            return CompanyController.company_form()
        blueprint.add_url_rule('/submit_company', 'submit_company',
                               CompanyController.submit_company, methods=['POST'])

        # Claim Your Profile Routes
        @blueprint.route('/claim_profile', methods=['GET'])
        def claim_profile():
            log.debug("Accessing Claim Profile page.")
            self._check_access()
            return ClaimProfileController.claim_profile()

        blueprint.add_url_rule(
            '/submit_claim_profile',
            'submit_claim_profile',
            ClaimProfileController.submit_claim_profile,
            methods=['POST']
        )

        blueprint.add_url_rule(
            '/verify_otp',
            'verify_otp',
            ClaimProfileController.verify_otp,
            methods=['POST']
        )

        @blueprint.route('/update_claim_form/<company_id>', methods=['GET', 'POST'])
        def update_claim_form(company_id):
            self._check_access()
            if 'otp_verified' in session:
                if request.method == 'POST':
                    return ClaimProfileController.update_record(company_id)
                else:
                    return ClaimProfileController.fetch_record(company_id)
            else:
                abort(404)

        @blueprint.route('/edit_company/<company_id>', methods=['GET', 'POST'])
        def edit_company(company_id):
            log.info("Request method received: " + request.method)
            self._check_access()
            if request.method == 'POST':
                log.info("Handling POST request")
                # Handle POST logic here
            return EditCompanyController.edit_company(company_id)

        blueprint.add_url_rule(
            '/verify_otp_edit',
            'verify_otp_edit',
            EditCompanyController.verify_otp,
            methods=['POST'])

        # Add route for search Company page

        @blueprint.route('/search_company', methods=['GET'])
        def render_search_page():
            return tk.render('search_company.html')

        # Add route for fetching company details
        blueprint.add_url_rule(
            '/search_company',
            'search_company',
            CompanySearchController.search_company,
            methods=['POST']
        )
        # Route to handle updates EXTRA I THINK
        # blueprint.add_url_rule(
        #     '/update_company',
        #     'update_company',
        #     CompanySearchController.update_company,
        #     methods=['POST']
        # )

    # Admin Side Routes
        @blueprint.route('/admin_all_profiles')
        def admin_all_profiles():
            self._check_access(admin_only=True)
            return AdminController.admin_all_profiles()

        @blueprint.route('/toggle_status', methods=['POST'])
        def toggle_status():
            """
            Admin-only endpoint to toggle the status of a company profile.
            """
            self._check_access(admin_only=True)
            return AdminController.toggle_status()

        @blueprint.route('/download_dataset/<int:company_id>', methods=['GET'])
        def download_dataset(company_id):
            self._check_access(admin_only=True)
            return AdminController.download_dataset(company_id)

        @blueprint.route('/admin_all_user_profiles')
        def admin_all_user_profiles():
            self._check_access(admin_only=True)
            return AdminUserController.admin_all_user_profiles()
        

        @blueprint.route('/fetch_companies', methods=['POST'])
        def fetch_companies():
            """
            Admin-only page to view all user profiles.
            """
            #self._check_access(admin_only=True)
            return FetchCompanyController.start_fetching()

        @blueprint.route('/pause_fetching', methods=['POST'])
        def pause_fetching():
            """
            Admin-only page to view all user profiles.
            """
            #self._check_access(admin_only=True)
            return FetchCompanyController.pause_fetching()
        

        @blueprint.route('/continue_fetching', methods=['POST'])
        def continue_fetching():
            """
            Admin-only page to view all user profiles.
            """
            #self._check_access(admin_only=True)
            return FetchCompanyController.continue_fetching()
        
        @blueprint.route('/stop_fetching', methods=['POST'])
        def stop_fetching():
            """
            Admin-only page to view all user profiles.
            """
            #self._check_access(admin_only=True)
            return FetchCompanyController.stop_fetching()

        return blueprint

    def update_config(self, config):
        """
        Update CKAN configuration and initialize database tables.
        """
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')

        config['ckan.auth.create_user_via_web'] = 'true'

        # Create tables during plugin initialization
        connection = connect_to_db()
        if connection:
            try:
                create_tables(connection)
            except Exception as e:
                log.error(f"Error initializing database tables: {e}")
            finally:
                close_db_connection(connection)
        else:
            log.error(
                "Failed to connect to the database during plugin initialization.")
