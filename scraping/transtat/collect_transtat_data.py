
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options as FirefoxOptions

def setup_webdriver(download_dir):
    """Sets up and returns a WebDriver instance with download directory configured."""
    try:
        geckodriver_path = "/home/stochastic1017/.wdm/drivers/geckodriver/linux64/v0.35.0/geckodriver"
        service = FirefoxService(executable_path=geckodriver_path)
        options = FirefoxOptions()
        options.add_argument("--headless") 
        options.set_preference("browser.download.folderList", 2) 
        options.set_preference("browser.download.dir", download_dir) 
        options.set_preference("browser.download.manager.showWhenStarting", False) 
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip") 
        options.set_preference("pdfjs.disabled", True)
        
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except Exception as e:
        raise Exception(f"Failed to setup WebDriver: {str(e)}")

# Set up the download directory
download_dir = "/home/stochastic1017/Downloads"

# Set up the WebDriver
driver = setup_webdriver(download_dir)
driver.get("https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGK&QO_fu146_anzr=b0-gvzr")

print("\n")
print("clicking checkboxes...")

driver.find_element(By.ID, "chkDownloadZip").click()
driver.find_element(By.ID, "chkshowNull").click()

# Find all the checkboxes on the page and select them
checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
for checkbox in checkboxes:
    if "chk" not in checkbox.get_attribute('name') and not checkbox.is_selected():
        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)  # Scroll into view
        checkbox.click()

# Scroll back up
driver.execute_script("window.scrollTo(0, 0);")  # Scrolls back to the top

print("\n")
print("Begin Downloading Data Chunks...")

# Find the dropdown element by its ID
dropdown_years = Select(driver.find_element(By.ID, 'cboYear'))
dropdown_months = Select(driver.find_element(By.ID, 'cboPeriod'))

total_start = time.time()
for year in dropdown_years.options:
    start_year = time.time()

    print("\n")
    print(f"Currently at year: {year.text}")
    dropdown_years.select_by_visible_text(year.text)

    for month in dropdown_months.options:
        start_month = time.time()
        print("\n")
        print(f"Currently at Month: {month.text}")
        dropdown_months.select_by_visible_text(month.text)

        try:
            # Click the download button
            driver.find_element(By.ID, "btnDownload").click()

            # Wait for the file to be downloaded and renamed
            print("\n")
            print(f"Downloading Data for: {year.text} <-> {month.text}.")
            print(f"Total time: {time.time() - total_start}")
            print(f"Year time: {time.time() - start_year}")
            print(f"Month time: {time.time() - start_month}")
    
        except Exception as e:
            print("Error:", e)
            print(f"Unable to process: {year.text} <-> {month.text}.")

        time.sleep(5)

driver.quit()
