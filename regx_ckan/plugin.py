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
from dotenv import load_dotenv
from scripts.process_company_data import main as process_company_data_main
from scripts.google_search import main as google_search_main
from scripts.ckan_api import main as ckan_api_main

load_dotenv()
def main():
    try:

       #### Step 1: Process CKAN data ####
        print("Step 1: Processing CKAN data Parsing...")
        process_company_data_main()

        #### Step 2: Perform Google search for company details ####
        print("Step 2: Performing Google search for company details...")
        google_search_main()

        #### Step 3: Interact with CKAN API to create/update dataset ####
        print("Step 3: Interacting with CKAN API...")
        ckan_api_main()

        print("All steps completed successfully!!!!!!!!!!")

    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
