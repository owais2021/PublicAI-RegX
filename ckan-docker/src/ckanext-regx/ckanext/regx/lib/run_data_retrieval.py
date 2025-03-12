############################################################
#                                                          #
#         Code implemented by Owais Khan                   #
#         Version: 1.0                                     #
#         Description: Processes CKAN data, performs a     #
#                      Google search, and interacts with   #
#                      the CKAN API to create/update a     #
#                      dataset.                            #
#                                                          #
############################################################

import sys
import logging
import time
import schedule
import threading
import uuid
from ckanext.regx.lib.thread_manager import get_scheduler_thread
from ckanext.regx.lib.process_company_data import fetch_from_procurdat_main as process_ckan_data_main
from ckanext.regx.lib.google_search import fetch_additional_info_via_google_main as google_search_main
from ckanext.regx.lib.ckan_api import create_or_update_datasets_main as ckan_api_main
from ckanext.regx.lib.database import connect_to_db, close_db_connection

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Explicitly target stdout
)
log = logging.getLogger(__name__)


def main():
    log.info("Main function started!")
    scheduler_thread = get_scheduler_thread()  # Get the singleton thread

    if not scheduler_thread.is_alive():
        scheduler_thread.start()     

def run_fetching(scheduler_thread):
    log.info("Run fetching!")
    if not scheduler_thread.is_paused():
        log.info("################################# This is a log message!")
        ##### Testing
        connection = connect_to_db()
        if connection is None:
            log.error("Failed to establish a database connection. Exiting...")
            return
        close_db_connection(connection)
        #####
        
        try:
            # Step 1: Process CKAN data
            log.debug("Step 1: Processing CKAN data Parsing...")
            process_ckan_data_main(scheduler_thread)

            # Step 2: Perform Google search for company details
            log.debug("Step 2: Performing Google search for company details...")
           # google_search_main(scheduler_thread)

            # Step 3: Interact with CKAN API to create/update dataset
            log.debug("Step 3: Interacting with CKAN API...")
            ckan_api_main(scheduler_thread)

            log.debug("All steps completed successfully!!!!!!!!!!")

        except Exception as e:
            log.error(f"Error during execution: {e}")
            sys.exit(1)

def clear_all_scheduled_jobs():
    schedule.clear()

if __name__ == "__main__":
    main()
