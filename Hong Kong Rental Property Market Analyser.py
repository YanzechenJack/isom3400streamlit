from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import json
import pandas as pd
from datetime import datetime

class HongKongRentalAnalyser:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://www.squarefoot.com.hk/en/rent"
        self.data = []

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print("WebDriver initialized. ")

    def navigate_to_site(self):
        self.driver.get(self.base_url)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

    def apply_filter(self, field, value):
        if not value or value.lower() in ["all", ""]:
            return

        try:
            if field == "Location":
                district_map = {"hong kong island": "a1", "kowloon": "a2", "new territories": "a3", "outlying islands": "a170"}
                code = district_map.get(value.lower())
                if code:
                    selector = f'a[href$="{code}"]'
                    link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    link.click()
                    time.sleep(3)

            elif field == "Type":
                
                banner = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[attr-field-name="Type"]')))

                # Mapping based on your provided data-id
                type_id_map = {
                    "apartment": "1",
                    "carpark": "2",
                    "office": "3",
                    "shop": "4"
                }
                data_id = type_id_map.get(value.lower())

                if data_id:
                    option = banner.find_element(By.CSS_SELECTOR, f'[data-id="{data_id}"]')
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                    self.driver.execute_script("arguments[0].click();", option)
                    time.sleep(4)
                    print(f"✓ Applied Type: {value}")
                    return

                print(f"Type '{value}' not found in banner.")


            elif field in ["Price", "Area", "Bedrooms"]:
                field_map = {"Price": "Price", "Area": "Area", "Bedrooms": "Bedrooms"}
                banner_selector = f'[attr-field-name="{field_map[field]}"]'
                banner = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, banner_selector)))
                option = banner.find_element(By.CSS_SELECTOR, f'[data-id="{value}"]')
                self.driver.execute_script("arguments[0].click();", option)
                time.sleep(3)
                print(f"✓ Applied {field}: {value}")

        except Exception as e:
            print(f"Failed to apply {field}='{value}': {str(e)[:100]}")

    def perform_search(self):
        print("\nPlease select filters (press Enter for All)")
        # --- Input Validation for District ---
        while True:
            district = input("Location (Hong Kong Island / Kowloon / New Territories / Outlying Islands): ").strip()
            if district.lower() == "" or district.lower() in ["hong kong island", "kowloon", "new territories", "outying islands"]:
                break
            print("Invalid input. Please enter Hong Kong Island / Kowloon / New Territories / Outlying Islands.")
        # --- Input Validation for Property Type ---
        
        while True:
            ptype = input("Property Type (Apartment / Carpark / Office / Shop): ").strip()
            if ptype.lower() == "" or ptype.lower() in ["apartment", "carpark", "office", "shop"]:
                break
            print("Invalid input. Please enter Apartment / Carpark / Office / Shop.")
        # --- Input Validation for Budget ---
        while True:
            price = input("Budget (input number as shown: 1=Below 10000, 2=10000-20000, 3=20000-40000, 4=40000-600000, 5=60000-80000, 6=Above 80000): ").strip()
            if price.lower() == "" or (price.isdigit() and 1 <= int(price) <= 6):
                break
            print("Invalid input. Please enter 1-6.")

        # --- Input Validation for Area ---
        while True:
            area = input("Area (input number as shown: 1=Saleable Area, 2=Gross Area): ").strip()
            if area.lower() == "" or area in ["1", "2"]:
                break
            print("Invalid input. Please enter 1 or 2.")

        # --- Input Validation for Bedrooms ---
        while True:
            bedrooms = input("Bedrooms (input number as shown: 1=Studio, 2=1 bedroom, 3=2 bedrooms, 4=3 bedrooms, 5=4 bedrooms, 6=5+ bedrooms): ").strip()
            if bedrooms.lower() == "" or (bedrooms.isdigit() and 1 <= int(bedrooms) <= 6):
                break
            print("Invalid input. Please enter 1-6")
        
        print("\nApplying filters...")
        self.driver.get(self.base_url)
        time.sleep(3)

        self.apply_filter("Location", district)
        self.apply_filter("Type", ptype)
        self.apply_filter("Price", price)
        self.apply_filter("Area", area)
        self.apply_filter("Bedrooms", bedrooms)

        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item.property_item")))
        print("Search completed.\n")
        return True

    def extract_properties(self):
        self.data = []
        try:
            print("Extracting properties...")

            images = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.desktop_myimage.detail_page, img.desktop_myimage.detail_page_others"))
            )

            print(f"Found {len(images)} listings on page.")

            for img in images[:15]:
                try:
                    card = img.find_element(By.XPATH, "./ancestor::div[contains(@class, 'listing') or contains(@class, 'item') or contains(@class, 'property')][1]")

                    prop = {}

                    try:
                        header = card.find_element(By.CSS_SELECTOR, ".header.cat")
                        header_html = header.get_attribute("innerHTML")
                        parts = header_html.split('<span class="separation"></span>')
                        prop['District'] = parts[0].strip()
                        prop['Property Name'] = parts[1].strip()
                    except:
                        prop['District'] = "N/A"
                        prop['Property Name'] = "N/A"

                    try:
                        prop['Street Address'] = card.find_element(By.CSS_SELECTOR, ".meta").text.strip()
                    except:
                        prop['Street Address'] = "N/A"

                    try:
                        prop['Monthly Rental Price (HKD)'] = card.find_element(By.CSS_SELECTOR, ".priceDesc, .rentDesc, .price").text.strip()
                    except:
                        prop['Monthly Rental Price (HKD)'] = "N/A"

                    try:
                        headers = card.find_elements(By.CSS_SELECTOR, ".header")
                        for h in headers:
                            if "cat" in h.get_attribute("class"): 
                                continue  
                            t = h.text.strip()
                            tokens = t.split()
                        prop['Saleable Area (ft²)'] = " ".join(tokens[0:2]) if len(tokens) >= 2 else "N/A"
                        prop['Number of Bedrooms'] = tokens[2] if len(tokens) >= 3 else "N/A" 
                        prop['Number of Bathrooms'] = tokens[3] if len(tokens) >= 4 else "N/A" 
                    except:
                        prop['Saleable Area (ft²)'] = "N/A"
                        prop['Number of Bedrooms'] = "N/A"
                        prop['Number of Bathrooms'] = "N/A"

                    prop['Property URL'] = img.get_attribute("href") or "N/A"

                    self.data.append(prop)

                except:
                    continue

            print(f"Extracted {len(self.data)} properties.")
            return self.data

        except Exception as e:
            print(f"Extraction error: {e}")
            return []

    # === Export Functions ===
    def save_to_csv(self, filename):
        if not self.data: 
            print("No data.")
            return
        fieldnames = ['District', 'Property Name', 'Street Address', 'Monthly Rental Price (HKD)',
                      'Saleable Area (ft²)', 'Number of Bedrooms', 'Number of Bathrooms', 'Property URL']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        print(f"Saved CSV: {filename}")

    def export_to_json(self, filename):
        if not self.data: return
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print(f"Saved JSON: {filename}")

    def export_to_excel(self, filename):
        if not self.data: return
        pd.DataFrame(self.data).to_excel(filename, index=False)
        print(f"Saved Excel: {filename}")

    def view_search_results_count(self):
        count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.item.property_item"))
        print(f"Properties on current page: {count}")

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    # Menu and main()
    def display_menu(self):
            print("\n" + "="*65)
            print("Hong Kong Rental Property Market Analyser")
            print("="*65)
            print("1. Search for properties using filters")
            print("2. View search results count")
            print("3. Extract property data to CSV files")
            print("4. Exit")
            print("="*65)

    def main(self):
            print("Starting Hong Kong Rental Property Market Analyser...")
            self.setup_driver()
            self.navigate_to_site()

            while True:
                self.display_menu()
                choice = input("Enter your choice (1-4): ").strip()

                if choice == "1":
                    self.perform_search()
                elif choice == "2":
                    self.view_search_results_count()
                elif choice == "3":
                    self.extract_properties()
                    if self.data:
                        ts = datetime.now().strftime("%Y%m%d_%H%M")
                        self.save_to_csv(f"rental_properties_{ts}.csv")
                        # Optional additional export
                        
                        while True:
                            extra = input("Export to JSON and Excel too? (y/n): ").strip().lower()
                            if extra == 'y':
                                self.export_to_json(f"rental_properties_{ts}.json")
                                self.export_to_excel(f"rental_properties_{ts}.xlsx")
                                break
                            elif extra == 'n':
                                break
                            else:
                                print("Invalid input. Please enter y/n")
                    else:
                        print("No property data is available to be extracted.")
                elif choice == "4":
                    print("Thank you for using the program. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-4.")

                input("\nPress Enter to continue...")

            self.close_driver()


if __name__ == "__main__":
    app = HongKongRentalAnalyser()
    try:
        app.main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        app.close_driver()
    except Exception as e:
        print(f"Error: {e}")
        app.close_driver()
