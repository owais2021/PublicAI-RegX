############################################################
#                                                          #
#         Code implemented by Owais Khan                   #
#         Version: 1.0                                     #
#         Description: Finds official company websites     #
#                      using SERPAPI, scrapes internal     #
#                      pages for meta data and emails, and #
#                      saves aggregated information for    #
#                      each company.                       #
#                                                          #
############################################################

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin
from dotenv import load_dotenv
import logging
import time
###### Load environment variables ######
load_dotenv()

###### Environment variable setup ######
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY is missing in environment variables.")

PARSED_CKAN_DATA_FILE = os.getenv("PARSED_CKAN_DATA_FILE")
#PARSED_CKAN_DATA_FILE = "/srv/app/src_extensions/ckanext-regx/ckanext/regx/lib/parse-data/all_datasets_data.json"
if not PARSED_CKAN_DATA_FILE:
    raise ValueError("PARSED_CKAN_DATA_FILE is missing in environment variables.")

output_dir = os.getenv("COMPANY_DETAILS_FILE", "/srv/app/src_extensions/ckanext-regx/ckanext/regx/lib/scrape-data")
#output_dir="/srv/app/src_extensions/ckanext-regx/ckanext/regx/scripts/scrape-data"

###### Set up logging ######
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

###### Define Functions ######
def find_company_website_with_serpapi(company_name, api_key):
    """Use SerpAPI to find the official website of the company."""
    query = f"{company_name} official site"
    url = "https://serpapi.com/search.json"

    params = {
        "q": query,
        "hl": "en",
        "api_key": api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()

        if "organic_results" not in results:
            log.error(f"No 'organic_results' in SerpAPI response for {company_name}: {json.dumps(results, indent=2)}")
            return None

        for result in results.get("organic_results", []):
            link = result.get("link")
            if link:
                log.info(f"Found link for {company_name}: {link}")
                return link

        log.warning(f"No valid links found for {company_name}.")
    except requests.exceptions.RequestException as e:
        log.error(f"Error finding website for {company_name}: {e}")
    except Exception as e:
        log.error(f"Unexpected error for {company_name}: {e}")

    return None

def get_all_internal_links(base_url):
    """Get all unique internal links from the base URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        links = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            if base_url in full_url:
                links.add(full_url)

        log.info(f"Total internal links found: {len(links)}")
        return list(links)
    except requests.exceptions.RequestException as e:
        log.error(f"Error getting internal links from {base_url}: {e}")
        return []
        


def extract_emails(text):
    """Extract all email addresses from the given text."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(email_pattern, text)


def scrape_pages(links, visited_urls, pause_event, progress=None):
    """Scrape all unique links provided and extract emails."""
    scraped_data = []
    for link in links:
        pause_event.wait()
        if link in visited_urls:
            continue
        time.sleep(5)

        visited_urls.add(link)

        if progress:
            progress['current'] += 1
            log.info(f"Scraping page {progress['current']} of {progress['total']} | {link}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
            }
            response = requests.get(link, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            raw_text = soup.get_text(separator="\n", strip=True)
            text_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

            title = soup.title.string if soup.title else "No title found"
            meta_description = soup.find("meta", attrs={"name": "description"})
            meta_description = meta_description["content"] if meta_description else "No description found"

            ####### Extract emails from the page ######
            emails = list(set(extract_emails(response.text)))

            scraped_data.append({
                "url": link,
                "title": title,
                "meta_description": meta_description,
                "all_text": text_lines,
                "emails": emails
            })
        except requests.exceptions.RequestException as e:
            log.error(f"Error scraping {link}: {e}")
        except Exception as e:
            log.error(f"Unexpected error scraping {link}: {e}")

    return scraped_data


def process_companies(parsed_data_file, output_dir, api_key, pause_event):
    """Process each company, find its official URL, and scrape the website."""
    try:
        
        with open(parsed_data_file, "r", encoding="utf-8") as file:
            parsed_data = json.load(file)

        os.makedirs(output_dir, exist_ok=True)

        for company in parsed_data:
            pause_event.wait()
            company_name = company.get("legalName")
            if not company_name:
                log.warning("Skipping entry with missing legalName.")
                continue

            log.info(f"Processing company: {company_name}")
            
            ####### Find the website URL using SerpAPI ######
            website_url = find_company_website_with_serpapi(company_name, api_key)
            
            if not website_url:
                log.warning(f"No website URL found for {company_name}. Skipping.")
                continue

            log.info(f"Found website: {website_url}")

            ####### Get internal links ######
            links = get_all_internal_links(website_url)

            if not links:
                log.warning(f"No internal links found for {company_name}. Skipping.")
                continue

            ####### Track progress ######
            progress = {'current': 0, 'total': len(links)}

            ####### Set up the visited URLs set ######
            visited_urls = set()

            ####### Scrape the pages ######
            scraped_data = scrape_pages(links, visited_urls, pause_event, progress)

            ####### Aggregate emails ######
            all_emails = set()
            for page in scraped_data:
                all_emails.update(page["emails"])

            ####### Create a sanitized folder for the company ######
            sanitized_name = re.sub(r'[\\/*?:"<>|]', "_", company_name.strip())
            company_folder = os.path.join(output_dir, sanitized_name)
            os.makedirs(company_folder, exist_ok=True)

            ####### Save the meta information in meta.json ######
            meta_info = {
                "company_name": company_name,
                "website_url": website_url,
                "email": list(all_emails),  # Collect aggregated emails
                "links_scraped": len(scraped_data),
                "scraped_data": scraped_data
            }

            meta_file_path = os.path.join(company_folder, "meta.json")
            with open(meta_file_path, "w", encoding="utf-8") as meta_file:
                json.dump(meta_info, meta_file, indent=4, ensure_ascii=False)

            log.info(f"Meta data for '{company_name}' saved to '{meta_file_path}'")
    
    except Exception as e:
        log.error(f"An error occurred: {e}")
        


###### Main function ######
def fetch_additional_info_via_google_main(pause_event):
    """Main function to call the process_companies method."""
    process_companies(PARSED_CKAN_DATA_FILE, output_dir, SERPAPI_API_KEY, pause_event)

