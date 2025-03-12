import sys
import logging
import time
import schedule
import threading
import uuid

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


class PausableThread(threading.Thread):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):  # Prevent re-initialization
            return
        super().__init__()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.running = True
        self.daemon = True  # Ensure it stops with the main process
        self.id = uuid.uuid4()  # Debugging
        self.initialized = True  # Prevents re-initialization

    def run(self):
        log.info(f"Thread started with UUID: {self.id}")
        schedule.every(30).seconds.do(lambda: run_fetching(self.pause_event))

        while self.running:
            self.pause_event.wait()  # Block execution if paused
            schedule.run_pending()
            time.sleep(1)

    def pause(self):
        log.info(f"Thread paused with UUID: {self.id}")
        self.pause_event.clear()

    def resume(self):
        log.info(f"Thread resumed with UUID: {self.id}")
        self.pause_event.set()

    def stop(self):
        log.info(f"Thread stopped with UUID: {self.id}")
        self.running = False
        self.pause_event.set()

    def is_paused(self):
        return not self.pause_event.is_set()
    
    @classmethod
    def destroy_instance(cls):
        """Stops and deletes the singleton instance."""
        with cls._lock:
            if cls._instance is not None:
                log.info(f"Destroying thread with UUID: {cls._instance.id}")
                cls._instance.stop()
                cls._instance.join()  # Ensure the thread fully stops
                cls._instance = None 


def run_fetching(scheduler_thread):
    log.info("Run fetching!")
    #if not scheduler_thread.is_paused():
    if scheduler_thread.is_set():
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
            google_search_main(scheduler_thread)

            # Step 3: Interact with CKAN API to create/update dataset
            log.debug("Step 3: Interacting with CKAN API...")
            ckan_api_main(scheduler_thread)

            log.debug("All steps completed successfully!")

        except Exception as e:
            log.error(f"Error during execution: {e}")
            sys.exit(1)

def clear_all_scheduled_jobs():
    schedule.clear()