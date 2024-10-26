
import re
import time
from selenium.webdriver.support.ui import Select
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
import sys
from multiprocessing import Pool
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

def setup_logging(year):
    """
    Sets up logging configuration for a specific year.
    """
    log_base_dir = 'logs'
    info_dir = os.path.join(log_base_dir, year, 'info')
    error_dir = os.path.join(log_base_dir, year, 'error')
    os.makedirs(info_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Set up info logger
    info_logger = logging.getLogger(f'info_logger_{year}')
    info_logger.setLevel(logging.INFO)

    # File handler for info logs
    info_handler = RotatingFileHandler(
        os.path.join(info_dir, f'info_{timestamp}.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    info_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(info_formatter)

    # Stream handler for terminal output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(info_formatter)

    # Add both handlers to the info logger
    info_logger.addHandler(info_handler)
    info_logger.addHandler(stream_handler)

    # Set up error logger
    error_logger = logging.getLogger(f'error_logger_{year}')
    error_logger.setLevel(logging.ERROR)

    # File handler for error logs
    error_handler = RotatingFileHandler(
        os.path.join(error_dir, f'error_{timestamp}.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n')
    error_handler.setFormatter(error_formatter)

    # Stream handler for terminal output (for errors)
    error_stream_handler = logging.StreamHandler()
    error_stream_handler.setFormatter(error_formatter)

    # Add both handlers to the error logger
    error_logger.addHandler(error_handler)
    error_logger.addHandler(error_stream_handler)

    return info_logger, error_logger

def setup_webdriver():
    """
    Sets up and returns a headless Chrome WebDriver instance.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver
    except Exception as e:
        raise Exception(f"Failed to setup WebDriver: {str(e)}")

def set_entries_to_n(driver, n):
    """
    Sets the entries dropdown to 100 to show more items on the page.
    """
    try:
        # Locate the dropdown element by its name attribute
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "tb-s3objects_length"))
        )
        
        # Use Select to set the dropdown value to 100
        select = Select(select_element)
        select.select_by_value(f"{n}")
        
        # Optional wait to ensure the page refreshes after changing the dropdown
        time.sleep(2)
        logging.info(f"Set entries per page to {n}.")
    except Exception as e:
        logging.error(f"Failed to set entries per page to 100: {str(e)}")

def get_number_of_pages_and_entries(driver, info_logger, error_logger):
    """Returns the number of pages and total entries for a particular year."""
    try:
        time.sleep(1)
        pagination_info = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.dataTables_info"))
        ).text
        
        # Replace commas with an empty string to ignore them during integer parsing
        total_entries = int(pagination_info.split('of')[-1].split('entries')[0].strip().replace(',', ''))
        entries_per_page = int(pagination_info.split('to')[1].split('of')[0].strip().replace(',', ''))
        
        total_pages = (total_entries // entries_per_page) + (total_entries % entries_per_page > 0)
        
        info_logger.info(f"Total entries: {total_entries}, Entries per page: {entries_per_page}, Total pages: {total_pages}")
        return total_pages, total_entries
    except Exception as e:
        error_logger.error(f"Error calculating pages and entries: {str(e)}")
        return 1, 0

def collect_csv_links(driver, url, info_logger, error_logger):
    """
    Collects all downloadable CSV file links from all pages.
    """
    info_logger.info(f"Navigating to {url}")
    driver.get(url)

    time.sleep(15)
    
    # Set entries to 100 to show more links per page
    set_entries_to_n(driver, n=100)
    
    total_pages, _ = get_number_of_pages_and_entries(driver, info_logger, error_logger)
    regex = r".*\.csv$"
    all_csv_links = []

    for page in range(1, total_pages + 1):
        info_logger.info(f"Processing page {page} of {total_pages}")
        if page > 1:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, str(page)))
            ).click()
            time.sleep(1)

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        hyperlinks = driver.find_elements(By.TAG_NAME, "a")

        page_links = [link.get_attribute('href') for link in hyperlinks if link.get_attribute('href') and re.search(regex, link.get_attribute('href'))]
        info_logger.info(f"Found {len(page_links)} CSV links on page {page}")

        all_csv_links.extend(page_links)

    info_logger.info(f"Total CSV links collected: {len(all_csv_links)}")
    return all_csv_links

def download_csv_file(csv_link, output_folder, info_logger):
    """
    Downloads a CSV file using wget with retries.
    """
    file_name = csv_link.split('/')[-1]
    output_path = os.path.join(output_folder, file_name)
    retry_count = 10

    for attempt in range(retry_count):
        try:
            subprocess.run(['wget', '-O', output_path, csv_link], check=True, capture_output=True, text=True)
            info_logger.info(f"Downloaded {file_name} successfully.")
            break
        except subprocess.CalledProcessError as e:
            info_logger.error(f"Attempt {attempt + 1} failed to download {file_name}: {str(e)}")
            if attempt == retry_count - 1:
                info_logger.error(f"Failed to download {file_name} after {retry_count} attempts.")

def parallel_download(csv_links, output_folder, info_logger):
    """
    Downloads all CSV files in parallel.
    """
    os.makedirs(output_folder, exist_ok=True)
    with Pool(processes=5) as pool:
        for csv_link in csv_links:
            pool.apply_async(download_csv_file, args=(csv_link, output_folder, info_logger))

        pool.close()
        pool.join()

def verify_downloads(csv_links, output_folder, year, info_logger, error_logger):
    """
    Verifies if all CSV files were downloaded. If not, logs missing files to a separate file.
    """
    downloaded_files = set(os.listdir(output_folder))
    missing_files = []

    for csv_link in csv_links:
        file_name = csv_link.split('/')[-1]
        if file_name not in downloaded_files:
            missing_files.append(csv_link)

    if missing_files:
        missing_file_path = os.path.join(output_folder, f'missing_downloads_{year}.txt')
        with open(missing_file_path, 'w') as f:
            for link in missing_files:
                f.write(f"{link}\n")
        
        error_logger.error(f"Download verification failed. {len(missing_files)} files missing. See {missing_file_path} for details.")
    else:
        info_logger.info("All files downloaded successfully. No missing files.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <year>")
        sys.exit(1)

    year = sys.argv[1]
    base_url = f"https://www.ncei.noaa.gov/oa/local-climatological-data/index.html#v2/access/{year}/"
    output_folder = os.path.join('csv_downloads', year)

    info_logger, error_logger = setup_logging(year)
    info_logger.info(f"Starting script for year: {year}")

    try:
        driver = setup_webdriver()
        csv_links = collect_csv_links(driver, base_url, info_logger, error_logger)
        info_logger.info("Starting download of CSV files.")
        parallel_download(csv_links, output_folder, info_logger)
        
        # Verify downloads
        verify_downloads(csv_links, output_folder, year, info_logger, error_logger)
        
        info_logger.info("Download and verification completed.")
    except Exception as e:
        error_logger.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()

    print(f"Script completed for year {year}. Check the logs and download folder for details.")
