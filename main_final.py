"""
Hong Kong Rental Property Market Analyser  (final version)
ISOM3400 project - Selenium-based property information extraction

Target site: https://www.squarefoot.com.hk/en/rent

Main flow:
  1. Menu with 4 options
  2. Option 1: choose filters (location / type / budget / area / bedrooms)
  3. System applies filters and reports how many properties are shown
  4. Option 3: extract key information of all properties into CSV,
     optionally also JSON and Excel
  5. Option 4: exit

Changes vs v1:
  1. Fixed: "outlying islands" typo in input validation (Outlying Islands could not be entered)
  2. Fixed: search with no matching results no longer crashes the program
  3. Fixed: filter failures are now reported honestly (per-filter status)
  4. Refactored: District/Property Name extracted via DOM text nodes instead of fragile innerHTML split
  5. Refactored: Area/Bedrooms/Bathrooms located from the header that contains the bed/bath icons
  6. Added: numeric price column (Monthly Rent HKD) cleaned from the raw price text
  7. Efficiency: replaced fixed time.sleep() with WebDriverWait on the site's #search_results_loader
  8. Robustness: unified option-click helper (scrollIntoView + JS click); Area filter disambiguates
     duplicated data-id groups by label text
  9. Exports: written to ./output/, utf-8-sig CSV (Excel-friendly), second-level timestamps,
     friendly Excel error message if openpyxl is missing
  10. UX: menu option 2 warns if no search was done, preview of first 3 rows before export,
      corrected price-range hint text (40000-60000)
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
import csv
import json
import os
from datetime import datetime
import pandas as pd


class HongKongRentalAnalyser:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://www.squarefoot.com.hk/en/rent"
        self.data = []
        self.search_done = False          # whether a successful search has been run
        self.output_dir = "output"

    # ---------------------------------------------------------------
    # Setup & navigation
    # ---------------------------------------------------------------
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print("[OK] WebDriver initialized.")

    def navigate_to_site(self):
        self.driver.get(self.base_url)
        # wait for actual listing content instead of a fixed sleep
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item.property_item")))
        print("[OK] Navigated to rental search page.")

    # ---------------------------------------------------------------
    # Waiting helpers (replace fixed time.sleep)
    # ---------------------------------------------------------------
    def _is_loading(self):
        """The site shows/hides #search_results_loader (Semantic UI dimmer) while refreshing results."""
        try:
            loader = self.driver.find_element(By.CSS_SELECTOR, "#search_results_loader")
            return "active" in (loader.get_attribute("class") or "").split()
        except Exception:
            return False

    def _wait_until_loaded(self, timeout=25):
        """Wait until the loader is done AND results are rendered. Never throws."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: not self._is_loading())
        except TimeoutException:
            pass  # loader may be absent on some pages; fall through
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item.property_item")))
        except TimeoutException:
            pass  # no results is a valid outcome - caller decides

    # ---------------------------------------------------------------
    # Filter helpers
    # ---------------------------------------------------------------
    def _click_option(self, element):
        """Scroll into view, then click via JS (options are <a> tags - JS click is what the site
        responds to reliably). Returns True if the option now looks selected."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.driver.execute_script("arguments[0].click();", element)
        cls = element.get_attribute("class") or ""
        return "active" in cls.split() or "selected" in cls.split()

    def _apply_filter(self, field, value):
        """Apply one filter. Returns (ok: bool, message: str)."""
        if not value or value.lower() in ["all", ""]:
            return True, f"{field}: skipped (All)"

        try:
            if field == "Location":
                district_map = {
                    "hong kong island": "a1",
                    "kowloon": "a2",
                    "new territories": "a3",
                    "outlying islands": "a170",
                }
                code = district_map.get(value.lower())
                if not code:
                    return False, f"{field}: unknown district '{value}'"
                link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[href$="{code}"]')))
                link.click()
                self._wait_until_loaded()
                return True, f"{field}: {value}"

            elif field == "Type":
                banner = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[attr-field-name="Type"]')))
                type_id_map = {"apartment": "1", "carpark": "2", "office": "3", "shop": "4"}
                data_id = type_id_map.get(value.lower())
                if not data_id:
                    return False, f"{field}: '{value}' not supported"
                option = banner.find_element(By.CSS_SELECTOR, f'[data-id="{data_id}"]')
                self._click_option(option)
                self._wait_until_loaded()
                return True, f"{field}: {value}"

            elif field in ["Price", "Area", "Bedrooms"]:
                banner = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f'[attr-field-name="{field}"]')))

                if field == "Area":
                    # The Area panel has TWO groups sharing data-ids (Saleable/Gross AND size ranges).
                    # Disambiguate by matching the option's label text.
                    label_map = {"1": "Saleable", "2": "Gross"}
                    options = banner.find_elements(By.CSS_SELECTOR, f'[data-id="{value}"]')
                    option = next((o for o in options if label_map[value] in (o.text or "")), None)
                    if option is None:
                        return False, f"Area: option '{value}' not found by label"
                else:
                    option = banner.find_element(By.CSS_SELECTOR, f'[data-id="{value}"]')

                self._click_option(option)
                self._wait_until_loaded()
                return True, f"{field}: {value}"

            return False, f"{field}: unsupported filter"

        except Exception as e:
            return False, f"{field}='{value}': {str(e)[:120]}"

    # ---------------------------------------------------------------
    # Search flow
    # ---------------------------------------------------------------
    def perform_search(self):
        print("\n--- Search Filters (press Enter for All) ---")

        while True:
            district = input("Location (Hong Kong Island / Kowloon / New Territories / Outlying Islands): ").strip()
            if district.lower() == "" or district.lower() in ["hong kong island", "kowloon",
                                                               "new territories", "outlying islands"]:
                break
            print("Invalid input. Please enter Hong Kong Island / Kowloon / New Territories / Outlying Islands.")

        while True:
            ptype = input("Property Type (Apartment / Carpark / Office / Shop): ").strip()
            if ptype.lower() == "" or ptype.lower() in ["apartment", "carpark", "office", "shop"]:
                break
            print("Invalid input. Please enter Apartment / Carpark / Office / Shop.")

        while True:
            price = input("Budget (1=Below 10k, 2=10k-20k, 3=20k-40k, 4=40k-60k, 5=60k-80k, 6=Above 80k): ").strip()
            if price.lower() == "" or (price.isdigit() and 1 <= int(price) <= 6):
                break
            print("Invalid input. Please enter 1-6.")

        while True:
            area = input("Area (1=Saleable Area, 2=Gross Area): ").strip()
            if area.lower() == "" or area in ["1", "2"]:
                break
            print("Invalid input. Please enter 1 or 2.")

        while True:
            bedrooms = input("Bedrooms (1=Studio, 2=1, 3=2, 4=3, 5=4, 6=5+): ").strip()
            if bedrooms.lower() == "" or (bedrooms.isdigit() and 1 <= int(bedrooms) <= 6):
                break
            print("Invalid input. Please enter 1-6.")

        print("\nApplying filters...")
        self.driver.get(self.base_url)          # start from a clean search page
        self._wait_until_loaded()

        results = [
            self._apply_filter("Location", district),
            self._apply_filter("Type", ptype),
            self._apply_filter("Price", price),
            self._apply_filter("Area", area),
            self._apply_filter("Bedrooms", bedrooms),
        ]
        for ok, msg in results:
            print(f"  {'[OK]' if ok else '[FAILED]'} {msg}")

        self._wait_until_loaded()
        items = self.driver.find_elements(By.CSS_SELECTOR, "div.item.property_item")
        if not items:
            print("\nNo properties match your filters. Please try different criteria.")
            self.search_done = False
            return False

        print(f"\nSearch completed: {len(items)} properties shown on this page.")
        self.search_done = True
        return True

    # ---------------------------------------------------------------
    # Extraction
    # ---------------------------------------------------------------
    def _text_nodes_of(self, element):
        """Return the trimmed text-node children of an element, in DOM order."""
        return self.driver.execute_script(
            "return Array.from(arguments[0].childNodes)"
            ".filter(n => n.nodeType === Node.TEXT_NODE)"
            ".map(n => n.textContent.trim())"
            ".filter(Boolean);", element)

    def _extract_one_property(self, card):
        prop = {}

        # --- District & Property Name (from .header.cat text nodes) ---
        try:
            header = card.find_element(By.CSS_SELECTOR, ".header.cat")
            parts = self._text_nodes_of(header)
            prop["District"] = parts[0] if len(parts) > 0 else "N/A"
            prop["Property Name"] = parts[1] if len(parts) > 1 else "N/A"
        except Exception:
            prop["District"] = "N/A"
            prop["Property Name"] = "N/A"

        # --- Street address ---
        try:
            prop["Street Address"] = card.find_element(By.CSS_SELECTOR, ".meta").text.strip()
        except Exception:
            prop["Street Address"] = "N/A"

        # --- Price: raw text + cleaned numeric value ---
        raw_price = "N/A"
        try:
            raw_price = card.find_element(By.CSS_SELECTOR, ".priceDesc, .rentDesc, .price").text.strip() or "N/A"
        except Exception:
            pass
        prop["Rental Price Text"] = raw_price
        m = re.search(r"[\d,]+", raw_price)
        prop["Monthly Rent (HKD)"] = int(m.group(0).replace(",", "")) if m else "N/A"

        # --- Area / Bedrooms / Bathrooms: locate the header containing the bed icon ---
        try:
            info_header = card.find_element(
                By.XPATH, ".//div[contains(@class,'header') and .//i[contains(@class,'bed')]]")
            tokens = self._text_nodes_of(info_header)
            prop["Saleable Area (ft\u00b2)"] = tokens[0] if len(tokens) > 0 else "N/A"
            prop["Number of Bedrooms"] = tokens[1] if len(tokens) > 1 else "N/A"
            prop["Number of Bathrooms"] = tokens[2] if len(tokens) > 2 else "N/A"
        except Exception:
            prop["Saleable Area (ft\u00b2)"] = "N/A"
            prop["Number of Bedrooms"] = "N/A"
            prop["Number of Bathrooms"] = "N/A"

        # --- Property URL: the site puts href on the <img>; fall back to nearest <a> ---
        url = "N/A"
        try:
            img = card.find_element(By.CSS_SELECTOR, "img.desktop_myimage[href]")
            url = img.get_attribute("href") or ""
            if not url:
                a = card.find_element(By.XPATH, ".//a[@href]")
                url = a.get_attribute("href") or ""
            if not url:
                url = "N/A"
        except Exception:
            pass
        prop["Property URL"] = url

        return prop

    def extract_properties(self):
        self.data = []
        try:
            print("Extracting properties...")
            cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.item.property_item")))
            print(f"Found {len(cards)} listings on this page.")

            for card in cards:
                try:
                    prop = self._extract_one_property(card)
                    if prop:
                        self.data.append(prop)
                except Exception:
                    continue

            print(f"Extracted {len(self.data)} properties.")
            return self.data

        except Exception as e:
            print(f"Extraction error: {e}")
            return []

    # ---------------------------------------------------------------
    # Export functions
    # ---------------------------------------------------------------
    def _ensure_output_dir(self):
        os.makedirs(self.output_dir, exist_ok=True)

    def save_to_csv(self, filename):
        if not self.data:
            print("No data to save.")
            return False
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        fieldnames = ["District", "Property Name", "Street Address", "Rental Price Text",
                      "Monthly Rent (HKD)", "Saleable Area (ft\u00b2)",
                      "Number of Bedrooms", "Number of Bathrooms", "Property URL"]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.data)
        print(f"[OK] Saved CSV: {path}")
        return True

    def export_to_json(self, filename):
        if not self.data:
            print("No data to save.")
            return False
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print(f"[OK] Saved JSON: {path}")
        return True

    def export_to_excel(self, filename):
        if not self.data:
            print("No data to save.")
            return False
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        try:
            pd.DataFrame(self.data).to_excel(path, index=False)
            print(f"[OK] Saved Excel: {path}")
            return True
        except ImportError:
            print("[!] Excel export needs 'openpyxl'. Run: pip install openpyxl")
            return False
        except Exception as e:
            print(f"[!] Excel export failed: {e}")
            return False

    # ---------------------------------------------------------------
    # Misc / menu / main
    # ---------------------------------------------------------------
    def view_search_results_count(self):
        if not self.search_done:
            print("No search has been performed yet. Please select option 1 first.")
            return
        count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.item.property_item"))
        print(f"Properties on current page: {count}")

    def display_menu(self):
        print("\n" + "=" * 65)
        print("Hong Kong Rental Property Market Analyser")
        print("=" * 65)
        print("1. Search for properties using filters")
        print("2. View search results count")
        print("3. Extract property data to CSV files")
        print("4. Exit")
        print("=" * 65)

    def main(self):
        print("Starting Hong Kong Rental Property Market Analyser...")
        self.setup_driver()
        self.navigate_to_site()

        while True:
            self.display_menu()
            choice = input("Enter your choice (1-4): ").strip()

            if choice == "1":
                if not self.perform_search():
                    print("Try again with different filters.")

            elif choice == "2":
                self.view_search_results_count()

            elif choice == "3":
                if not self.search_done:
                    print("Note: no search has been run yet - extracting whatever is currently on the page.")
                self.extract_properties()
                if self.data:
                    print("\nPreview of first 3 extracted properties:")
                    for p in self.data[:3]:
                        print(f"  - {p.get('Property Name', 'N/A')} | {p.get('District', 'N/A')} | "
                              f"{p.get('Monthly Rent (HKD)', 'N/A')} HKD")

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.save_to_csv(f"rental_properties_{ts}.csv")

                    while True:
                        extra = input("Export to JSON and Excel too? (y/n): ").strip().lower()
                        if extra == "y":
                            self.export_to_json(f"rental_properties_{ts}.json")
                            self.export_to_excel(f"rental_properties_{ts}.xlsx")
                            break
                        elif extra == "n":
                            break
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

    def close_driver(self):
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    app = HongKongRentalAnalyser()
    try:
        app.main()
    except KeyboardInterrupt:
        print("\nStopped by user. Cleaning up...")
        app.close_driver()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("The program will now exit.")
        app.close_driver()
