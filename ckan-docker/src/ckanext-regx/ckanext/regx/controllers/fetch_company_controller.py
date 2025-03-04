from flask import request, redirect, url_for
from flask import jsonify
from ckan.plugins import toolkit as tk
from ckanext.regx.lib.database import connect_to_db, close_db_connection
import logging
from ckanext.regx.lib.run_data_retrieval import main, clear_all_scheduled_jobs
from ckanext.regx.lib.thread_manager import get_scheduler_thread, reset_scheduler_thread

log = logging.getLogger(__name__)


class FetchCompanyController:
    
    @staticmethod
    def start_fetching():
        log.debug("Start fetching")

        try:
            main()
            return jsonify({"message": "Start fetching data!"}), 200
        except Exception as e:
            log.error(f"Error while fetching: {str(e)}")
            return jsonify({"message": "Fetching failed", "error": str(e)}), 400
        

    @staticmethod
    def pause_fetching():
 
        log.debug("Pause fetching")

        scheduler_thread = get_scheduler_thread()
        
        if scheduler_thread.is_alive():
            scheduler_thread.pause()
            log.debug("Controller")
            log.debug(scheduler_thread.is_paused())
            return jsonify({"message": "Scheduler stopped"}), 200
        return jsonify({"error": "No scheduler running currently"}), 400

     
    @staticmethod
    def continue_fetching():
 
        log.debug("Continue fetching")
        scheduler_thread = get_scheduler_thread()
        if scheduler_thread.is_alive():
            scheduler_thread.resume()
            log.debug("Controller")
            log.debug(scheduler_thread.is_paused())
            return jsonify({"message": "Scheduler resumed"}), 200
        return jsonify({"error": "No scheduler running currently"}), 400
    @staticmethod
    def stop_fetching():
 
        log.debug("Stop fetching")

        scheduler_thread = get_scheduler_thread()
        if scheduler_thread:
            scheduler_thread.stop()
            clear_all_scheduled_jobs()
            reset_scheduler_thread()
            return jsonify({"message": "Scheduler stopped"}), 200
        return jsonify({"error": "Scheduler not running"}), 400

    
    


        