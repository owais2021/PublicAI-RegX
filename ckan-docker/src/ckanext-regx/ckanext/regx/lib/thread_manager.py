from ckanext.regx.lib.thread import PausableThread
import logging
import sys

# Global singleton instance
scheduler_thread = PausableThread()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Explicitly target stdout
)
log = logging.getLogger(__name__)

def get_scheduler_thread():
    return scheduler_thread  

def reset_scheduler_thread():
    global scheduler_thread

    PausableThread.destroy_instance()
    scheduler_thread = PausableThread()
 
