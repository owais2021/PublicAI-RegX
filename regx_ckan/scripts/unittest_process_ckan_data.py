########### For testing using ckan local env (localhost:5000)#########
import os
import requests
import ckanapi
import json
from dotenv import load_dotenv
import sys
import urllib3
from database import connect_to_db, create_table, insert_company_data, insert_tender_data, close_db_connection

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Retrieve the API key and other configuration values from the environment variables
API_KEY = os.getenv("CKAN_API_KEY")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")  # Remove trailing slash if any
CKANORGANIZATION_ID = os.getenv("CKANORGANIZATION_ID")

# Validate essential configurations
if not API_KEY or not BASE_URL or not CKANORGANIZATION_ID:
    sys.exit("Error: Missing required environment variables. Ensure CKAN_API_KEY, BASE_URL, and CKANORGANIZATION_ID are set.")

# CKAN session with disabled SSL verification
session = requests.Session()
session.verify = False  # Disable SSL verification
ckan = ckanapi.RemoteCKAN(BASE_URL, apikey=API_KEY, session=session)

# Ensure proper encoding for output
sys.stdout.reconfigure(encoding="utf-8")


def fetch_dataset(organization_id):
    """
    Fetch dataset details for a specific organization from CKAN API.
    """
    url = f"{BASE_URL}/api/3/action/package_search"  # Corrected endpoint
    params = {"fq": f"organization:{organization_id}"}

    try:
        response = session.get(url, params=params)  # Use session with SSL disabled
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        if data.get("success"):
            print(f"Datasets for organization '{organization_id}' retrieved successfully!")
            return data["result"]["results"]
        else:
            print(f"Error fetching datasets: {data.get('error')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to CKAN API: {e}")

    return None


def get_json_resource_url(resources):
    """
    Find the first JSON resource in the dataset.
    """
    for resource in resources:
        if resource.get("format", "").lower() == "json":
            print(f"Processing JSON resource: {resource.get('url')}")
            return resource.get("url")
    print("No JSON resource found in the dataset!")
    return None


def download_and_parse_json(json_url):
    try:
        response = session.get(json_url)
        response.raise_for_status()
        json_data = response.json()
        print("Downloaded JSON:", json_data)  # Debug log
        extracted_data = extract_names_and_ocids_from_json(json_data)
        return extracted_data
    except requests.exceptions.RequestException as e:
        print(f"Failed to download JSON from {json_url}: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from {json_url}: {e}")
    return None

# def extract_names_and_ocids_from_json(data):
#     """
#     Extract 'legalName', 'ocid', and 'roles' (supplier) from nested JSON data.
#     Always process data if numberOfTenderers > 0 and role is 'supplier'.
#     """
#     extracted_entries = []
#     seen_legalNames = set()  # Track unique legalNames

#     def extract(data):
#         if isinstance(data, dict):
#             # Process numberOfTenderers if present
#             number_of_tenderers = data.get("numberOfTenderers")
#             if number_of_tenderers:
#                 print(f"Found numberOfTenderers: {number_of_tenderers}")  # Debugging numberOfTenderers

#             if number_of_tenderers and number_of_tenderers > 0:
#                 ocid = data.get("ocid", "")
#                 # Retain only the numeric part of the OCID (after the last hyphen)
#                 ocid_number = ocid.split("-")[-1] if ocid else ""

#                 print(f"Processing OCID: {ocid_number}")
#                 # Process parties and roles
#                 parties = data.get("parties", [])
#                 for party in parties:
#                     roles = party.get("roles", [])
#                     print(f"Found roles in party: {roles}")  # Debugging roles in each party
#                     if "supplier" in roles:
#                         # Ensure the legalName exists under 'identifier' key
#                         legal_name = party.get("legalName", party.get("name"))
#                         if legal_name and legal_name not in seen_legalNames:
#                             seen_legalNames.add(legal_name)
#                             extracted_entries.append({
#                                 "ocid": ocid_number,
#                                 "legalName": legal_name,
#                                 "roles": ["supplier"]
#                             })

#             # Recursively process all nested dictionaries and lists
#             for value in data.values():
#                 if isinstance(value, (dict, list)):
#                     extract(value)

#         elif isinstance(data, list):
#             for item in data:
#                 extract(item)

#     # Start extraction
#     extract(data)
#     return extracted_entries

def extract_names_and_ocids_from_json(data):
    """
    Extract 'legalName', 'ocid', and 'tender title'
    Always process data if numberOfTenderers > 0.
    """
    extracted_entries = []
    seen_legalNames = set()  # Track unique legalNames

    def extract(data, ocid_number="", tender_title=""):
        if isinstance(data, dict):
            # Process numberOfTenderers if present
            number_of_tenderers = data.get("numberOfTenderers")
            if number_of_tenderers:
                print(f"Found numberOfTenderers: {number_of_tenderers}")
            
            # Extract OCID at the current level and update ocid_number
            ocid = data.get("ocid", "")
            if ocid:
                ocid_number = ocid.replace("ocds-mnwr74-", "")  # Remove fixed prefix
            
            # Extract Tender Title
            if "tender" in data and "title" in data["tender"]:
                tender_title = data["tender"]["title"]

            # Process tenderers and add data
            if number_of_tenderers and number_of_tenderers > 0:
                tenderers = data.get("tenderers", [])
                for tender in tenderers:
                    legal_name = tender.get("legalName", tender.get("name"))
                    if legal_name and legal_name not in seen_legalNames:
                        seen_legalNames.add(legal_name)
                        extracted_entries.append({
                            "ocid": ocid_number,  
                            "legalName": legal_name,
                            "tenderTitle": tender_title
                        })

            # Recursively process all nested dictionaries and lists
            for value in data.values():
                if isinstance(value, (dict, list)):
                    extract(value, ocid_number, tender_title)

        elif isinstance(data, list):
            for item in data:
                extract(item, ocid_number, tender_title)

    # Start extraction
    extract(data)
    return extracted_entries


# def save_to_single_file(data, output_file_path):
#     """
#     Save extracted data to a single JSON file.
#     """
#     try:
#         with open(output_file_path, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4, ensure_ascii=False)
#         print(f"Data saved to {output_file_path}")
#     except IOError as e:
#         print(f"Failed to save data to file: {e}")


def main():
    """
    Main function to fetch, process, and save datasets.
    """
    print(f"Connecting to CKAN at {BASE_URL} with organization ID '{CKANORGANIZATION_ID}'")

    # Step 1: Fetch datasets
    datasets = fetch_dataset(CKANORGANIZATION_ID)
    if not datasets:
        print("No datasets found or an error occurred.")
        return

    # Process datasets
    # output_file_path = "scripts/parse-data/all_datasets_data.json"
    # os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    all_extracted_data = []
    for dataset in datasets:
        print(f"Processing dataset: {dataset.get('title')}")
        json_url = get_json_resource_url(dataset.get("resources", []))
        if not json_url:
            continue

        extracted_names = download_and_parse_json(json_url)
        if extracted_names:
            all_extracted_data.extend(extracted_names)
            print(f"Extracted data: {extracted_names}")

    if not all_extracted_data:
        print("No data extracted from the datasets.")
        return

    # save_to_single_file(all_extracted_data, output_file_path)

    connection = connect_to_db()
    create_table(connection)

    if connection:
     for entry in all_extracted_data:
        print(f"Attempting to insert: ocid={entry['ocid']}, legalName={entry['legalName']}")
        insert_company_data(entry["legalName"], connection)
        insert_tender_data(entry["ocid"], entry["legalName"], entry["tenderTitle"], connection)

    close_db_connection(connection)

if __name__ == "__main__":
    main()
