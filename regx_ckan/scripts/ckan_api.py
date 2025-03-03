############################################################
#                                                          #
#         Code implemented by Owais Khan                   #
#         Version: 1.0                                     #
#         Description: Interacts with the CKAN API to      #
#                      create or update datasets and       #
#                      resources using meta.json files, and#
#                      synchronizes data with a            #
#                      PostgreSQL database.                #
#                                                          #
############################################################
import os
import requests
import ckanapi
import re
import json
from dotenv import load_dotenv
from scripts.database import connect_to_db, close_db_connection, save_website_and_email, get_package_names_from_db

load_dotenv()
API_KEY = os.getenv("CKAN_API_KEY")
CKAN_URL = os.getenv("CKAN_URL")
CKAN_ORGANIZATION_ID = os.getenv("CKAN_ORGANIZATION_ID")
LOCAL_JSON_FOLDER = os.getenv("LOCAL_JSON_FOLDER")  # Directory where 'scrape-data' is located
LOCAL_JSON_FILE = os.getenv("LOCAL_JSON_FILE")  # Folder like 'scrape-data'

#### Ensure that LOCAL_JSON_FOLDER and LOCAL_JSON_FILE are set ####
if not LOCAL_JSON_FOLDER or not LOCAL_JSON_FILE:
    raise ValueError("LOCAL_JSON_FOLDER and LOCAL_JSON_FILE must be defined in the .env file.")

#### CKAN session with disabled SSL verification ####
session = requests.Session()
session.verify = False  #### Disable SSL verification ####
ckan = ckanapi.RemoteCKAN(CKAN_URL, apikey=API_KEY, session=session)

#### Generate Resource URL for Frontend ####
def generate_resource_url(package_id, resource_id):
    """
    Generate the CKAN URL for a resource based on package ID and resource ID.
    """
    return f"{CKAN_URL}/dataset/{package_id}/resource/{resource_id}/download/meta.json"


def create_or_update_dataset(company_name):
    """
    Create or update the dataset in CKAN under the specified organization.
    """
    #### Sanitize the dataset name to meet CKAN naming rules ####
    dataset_name = company_name.lower()
    dataset_name = re.sub(r'[^a-z0-9-_]', '-', dataset_name)  #### Replace invalid characters with '-' ####

    #### Ensure the dataset name does not exceed 100 characters ####
    if len(dataset_name) > 100:
        dataset_name = dataset_name[:100].rstrip('-')#### Truncate and avoid trailing '-'####

    try:
        print(f"Checking if dataset '{dataset_name}' exists.")
        #### Check if the package exists ####
        package = ckan.action.package_show(id=dataset_name)
        print(f"Dataset '{dataset_name}' exists.")
    except ckanapi.errors.NotFound:
        print(f"Dataset '{dataset_name}' does not exist. Creating a new one.")
        package = ckan.action.package_create(
            name=dataset_name,
            title=company_name[:100],  #### Truncate title if needed ####
            owner_org=CKAN_ORGANIZATION_ID,
        )
    return package

def upload_or_update_resource(company_name, package_id, json_file_path):
    """
    Upload or update the resource in the dataset with the local JSON file.
    """
    #### Check if the resource already exists ####
    existing_resource = None
    try:
        package = ckan.action.package_show(id=package_id)
        for resource in package.get("resources", []):
            if resource.get("name") == company_name:
                existing_resource = resource
                break
    except Exception as e:
        print(f"Error checking resources: {e}")

    #### Prepare the resource data ####
    with open(json_file_path, "rb") as file_obj:
        resource_data = {
            "package_id": package_id,
            "name": company_name,
            "format": "JSON",
            "url": "upload",  #### Needed to pass validation ####
        }
        if existing_resource:
            print(f"Updating existing resource '{company_name}' in the dataset.")
            resource_data["id"] = existing_resource["id"]
            action = "resource_update"
        else:
            print(f"Creating new resource '{company_name}' in the dataset.")
            action = "resource_create"

        #### Upload or update the resource ####
        response = requests.post(
            f"{CKAN_URL}/api/action/{action}",
            data=resource_data,
            headers={"Authorization": API_KEY},
            files={"upload": file_obj},
            verify=False,  #### Disable SSL verification ####
        )

        if response.status_code == 200:
            resource_info = response.json()["result"]
            resource_id = resource_info["id"]
            print(f"Resource '{company_name}' successfully {action.replace('_', 'ed')}.")
            resource_url = generate_resource_url(package_id, resource_id)
            print(f"Resource URL: {resource_url}")
            return resource_url ####Return the generated URL ####
        else:
            print(f"Error while {action.replace('_', 'ing')} resource: {response.content}")
            return None

def main():
    #### Connect to the database ####
    connection = connect_to_db()
    if connection is None:
        print("Failed to establish a database connection. Exiting...")
        return

    #### Retrieve company names from the database ####
    company_names = get_package_names_from_db(connection)
    if not company_names:
        print("No company names found in the database. Exiting...")
        close_db_connection(connection)
        return

    #### Loop through each company name and process the corresponding data ####
    for company_name in company_names:
        print(f"Processing company: {company_name}")

        #### Assuming the meta.json file is named after the company and located in the respective folder ####
        folder_path = os.path.join(LOCAL_JSON_FOLDER, LOCAL_JSON_FILE)
        meta_json_path = os.path.join(folder_path, company_name, 'meta.json')

        if os.path.exists(meta_json_path):
            print(f"Found meta.json for {company_name}.")
            try:
                with open(meta_json_path, 'r', encoding='utf-8') as file:
                    meta_data = json.load(file)
                    company_name_from_json = meta_data.get('company_name')
                    website_url = meta_data.get('website_url')
                    emails = meta_data.get('email', [])

                #### Create or update the dataset (package) for this company ####
                package = create_or_update_dataset(company_name)

                #### Upload or update the resource with the meta.json file ####
                resource_url = upload_or_update_resource(company_name, package["id"], meta_json_path)

                #### Save the website and email data to the database ####
                if resource_url:
                    save_website_and_email(company_name_from_json, website_url, emails, resource_url, connection)
                else:
                    print(f"Skipping database update for {company_name} due to resource upload failure.")

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Error processing meta.json for {company_name}: {e}")
        else:
            print(f"No meta.json found for {company_name}")

    close_db_connection(connection)

if __name__ == "__main__":
    main()