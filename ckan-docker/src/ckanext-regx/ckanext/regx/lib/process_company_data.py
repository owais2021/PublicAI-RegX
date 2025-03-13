############################################################
#                                                          #
#         Code implemented by Owais Khan                   #
#         Version: 1.0                                     #
#         Description: Processes CKAN data, extracts       #
#                      relevant information from JSON      #
#                      resources, and interacts with the   #
#                      CKAN API and a database to update   #
#                      dataset details.                    #
#                                                          #
############################################################

import requests
import json
import sys
import os
import logging
from dotenv import load_dotenv
from ckanext.regx.lib.database import connect_to_db, insert_company_data, insert_tender_data, close_db_connection


######### Load environment variables file ###########
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

CKAN_BASE_URL = os.getenv("CKAN_BASE_URL")

sys.stdout.reconfigure(encoding='utf-8')

def fetch_all_organizations():
    """
    Fetch all organizations from CKAN API.
    """
    url = f"{CKAN_BASE_URL}organization_list"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        log.debug(f"Response data from CKAN API:\n{json.dumps(data, indent=4)}")
        if data.get("success"):
            return data["result"]
    log.debug(f"Failed to fetch organizations: {response.status_code} - {response.text}")
    return []


def fetch_all_datasets(organization_id):
    """
    Fetch all datasets for a specific organization from CKAN API, handling pagination.
    """
    url = f"{CKAN_BASE_URL}package_search"
    params = {"fq": f"organization:{organization_id}", "start": 0, "rows": 100}

    all_datasets = []

    while True:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                datasets = data["result"]["results"]
                log.debug(f"Datasets for organization '{organization_id}' retrieved successfully!")
                all_datasets.extend(datasets)

                if len(datasets) < params["rows"]:
                    break

                params["start"] += params["rows"]
            else:
                log.debug(f"Error fetching datasets: {data.get('error')}")
                break
        else:
            log.debug(f"Failed to connect to CKAN API: {response.status_code}")
            log.debug(f"Response: {response.text}")
            break

    return all_datasets

def get_json_resource_url(resources):
    """
    Find the resource named 'Meta.json' in the dataset.
    """
    if not resources:
        log.debug("No resources found in this dataset!")
    for resource in resources:
        if resource.get("name", "").lower() == "meta.json":
            log.debug(f"Processing resource: {resource.get('name')}")
            return resource.get("url")
    log.debug("No 'Meta.json' resource found in the dataset!")
    return None

def download_and_parse_json(resource_url):
    """
    Download the JSON resource and extract 'legalName' and 'ocid' fields.
    """
    response = requests.get(resource_url)
    if response.status_code == 200:
        try:
            data = response.json()
            log.debug("JSON file parsed successfully!")
            return extract_names_and_ocids_from_json(data)
        except json.JSONDecodeError:
            log.debug("Error parsing JSON!")
    else:
        log.debug(f"Failed to download resource: {response.text}")
    return []


######### Check supplier role also
# def extract_names_and_ocids_from_json(data):
#     """
#     Extract 'legalName', 'ocid', and 'roles' (supplier) from nested JSON data.
#     Always process data if numberOfTenderers > 0 and role is 'supplier'.
#     """
#     extracted_entries = []
#     seen_legalNames = set()  ######### Track unique legalNames #########

#     def extract(data):
#         if isinstance(data, dict):
#             ########## Process numberOfTenderers if present #########
#             number_of_tenderers = data.get("numberOfTenderers")
#             if number_of_tenderers:
#                 print(f"Found numberOfTenderers: {number_of_tenderers}")  ######### Debugging numberOfTenderers #########

#             if number_of_tenderers and number_of_tenderers > 0:
#                 ocid = data.get("ocid", "")
#                 #########Retain only the numeric part of the OCID (after the last hyphen) #########
#                 ocid_number = ocid.split("-")[-1] if ocid else ""

#                 print(f"Processing OCID: {ocid_number}")
#                ######### Process parties and roles #########
#                 parties = data.get("parties", [])
#                 for party in parties:
#                     roles = party.get("roles", [])
#                     if "supplier" in roles:
#                        ######### Ensure the legalName exists under 'identifier' key #########
#                         legal_name = party.get("identifier", {}).get("legalName", party.get("name"))
#                         if legal_name and legal_name not in seen_legalNames:
#                             seen_legalNames.add(legal_name)
#                             extracted_entries.append({
#                                 "ocid": ocid_number,
#                                 "legalName": legal_name,
#                                 "roles": ["supplier"]
#                             })

#             ######### Recursively process all nested dictionaries and lists #########
#             for value in data.values():
#                 if isinstance(value, (dict, list)):
#                     extract(value)

#         elif isinstance(data, list):
#             for item in data:
#                 extract(item)

#     ######### Start extraction #########
#     extract(data)
#     return extracted_entries


def extract_names_and_ocids_from_json(data):
    """
    Extract 'legalName', 'ocid', and 'tender title'
    Always process data if numberOfTenderers > 0 .
    """
    extracted_entries = []
    seen_legalNames = set()  ########## Track unique legalNames #########

    def extract(data, ocid_number="", tender_title=""):
        if isinstance(data, dict):
            ######### Process numberOfTenderers if present #########
            number_of_tenderers = data.get("numberOfTenderers")
            if number_of_tenderers:
                log.debug(f"Found numberOfTenderers: {number_of_tenderers}")
            ########## Extract OCID at the current level and update ocid_number #########
            ocid = data.get("ocid", "")
            if ocid:
                ocid_number = ocid.replace("ocds-mnwr74-", "")######### Remove the fixed prefix #########

            ########## Extract Tender Title #########

            if "tender" in data and "title" in data["tender"]:
                tender_title = data["tender"]["title"]

            if number_of_tenderers and number_of_tenderers > 0:
                ########## Process parties and roles #########
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

            ########## Recursively process all nested dictionaries and lists #########
            for value in data.values():
                if isinstance(value, (dict, list)):
                    extract(value, ocid_number, tender_title)

        elif isinstance(data, list):
            for item in data:
                extract(item, ocid_number, tender_title)

    ########## Start extraction #########
    extract(data)
    return extracted_entries


def save_to_single_file(data, file_path):
    """
    Save all extracted data to a single JSON file.
    """
    try:
        ######### Check if the file already exists and load existing data #########
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    ###### Create a set of existing names for fast look-up ######
    existing_entries = {(entry["ocid"], entry["legalName"]) for entry in existing_data}

    ####### Add only new entries that don't exist in the existing data ######
    new_data = [entry for entry in data if (entry["ocid"], entry["legalName"]) not in existing_entries]

    ####### Add new data to the existing data list ######
    existing_data.extend(new_data)

    ####### Save the updated data back to the JSON file ######
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4, ensure_ascii=False)
    log.debug(f"All extracted data saved to {file_path}")

def fetch_from_procurdat_main(pause_event):
    ##### Step 1: Fetch all organizations ######
    organizations = fetch_all_organizations()

    if not organizations:
        log.debug("No organizations found.")
        return

    log.debug(f"Found {len(organizations)} organizations.")

    all_extracted_data = []
    ####### Step 2: Loop through all organizations and their datasets ######
    for org_name in organizations:
        pause_event.wait()
        log.debug(f"Processing organization: {org_name}")  # Use the organization name directly
        datasets = fetch_all_datasets(org_name)  # Pass the organization name instead of id

        if not datasets:
            log.debug(f"No datasets found for organization {org_name}.")
            continue
        
        log.debug(f"Found {len(datasets)} datasets for organization {org_name}.")  # Dataset count per organization

        ####### Step 3: Loop through datasets to find 'meta.json' ######
        for dataset in datasets:
            log.debug(f"Processing dataset: {dataset.get('title')}")
            json_url = get_json_resource_url(dataset.get("resources", []))
            if json_url:
                extracted_names = download_and_parse_json(json_url)
                if extracted_names:
                    all_extracted_data.extend(extracted_names)
                    log.debug(f"Extracted legalName: {extracted_names}")

    if not all_extracted_data:
        log.debug("No legalName extracted.")
        return

    ####### Step 4: Save all extracted data to a single JSON file ######
    # output_file_path = "scripts/parse-data/all_datasets_data.json"
    # save_to_single_file(all_extracted_data, output_file_path)

     ####### Step 5: Insert unique names and OCID (tender ID) into the database ######
    connection = connect_to_db()
    #create_table(connection)

    if connection:
     for entry in all_extracted_data:
        pause_event.wait()
        log.debug(f"Attempting to insert: ocid={entry['ocid']}, legalName={entry['legalName']}")
        insert_company_data(entry["legalName"], connection)
        if "tenderTitle" in entry:
            log.debug("tender_title exists.")
        else:
            log.debug("tender_title does not exist.")
        log.debug("Tender Title: ")
        log.debug(entry["tenderTitle"])
        
        insert_tender_data(entry["legalName"], entry["ocid"], entry["tenderTitle"], connection)

    close_db_connection(connection)
