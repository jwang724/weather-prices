import os
import time
import requests
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from weatherFetcher import fetch_weather

ERCOT_URL = "https://www.ercot.com/mp/data-products/data-product-details?id=np6-905-cd"
OUTPUT_DIR = "data/ercot_csvs"
API_KEY = "NVGXZSJ474N64LKUSW796N23Y"

TARGET_POINTS = {
    "LZ_HOUSTON", "LZ_NORTH", "LZ_AEN"
}

CITY_LOCATIONS = {
    "LZ_HOUSTON": "Houston,TX",
    "LZ_NORTH": "Dallas,TX",
    "LZ_AEN": "Austin,TX",
}

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)

def get_file_rows(driver):
    #gets csv files from table
    driver.get(ERCOT_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'doclookupId=')]"))
    )
    return driver.find_elements(By.XPATH, "//table//tr")

def download_and_extract(row):
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) < 2:
        return

    file_title = cells[0].get_attribute("title")
    link_el = row.find_element(By.XPATH, ".//a[contains(@href, 'doclookupId=')]")
    download_url = link_el.get_attribute("href")

    print(f"Downloading: {file_title}")
    response = requests.get(download_url)

    with ZipFile(BytesIO(response.content)) as z:
        for file in z.namelist():
            if file.endswith(".csv"):
                print(f"Extracting: {file}")
                z.extract(file, path=OUTPUT_DIR)

def combine_and_merge():
    print("Combining and filtering ERCOT CSVs")
    all_data = []

    for file in os.listdir(OUTPUT_DIR):
        if file.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(OUTPUT_DIR, file))
                if TARGET_POINTS:
                    df = df[df["SettlementPointName"].isin(TARGET_POINTS)]
                df["timestamp"] = pd.to_datetime(df["DeliveryDate"]) + pd.to_timedelta(df["DeliveryHour"] - 1, unit="h")
                all_data.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")

    if not all_data:
        print("No data to process.")
        return

    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv("data/hourly_filtered_prices.csv", index=False)
    print("Saved hourly_filtered_prices.csv")

    # Average price per hour per point
    pivoted = combined.groupby(["timestamp", "SettlementPointName"])["SettlementPointPrice"].mean().unstack()
    pivoted.to_csv("data/hourly_prices_pivoted.csv")
    print("Saved hourly_prices_pivoted.csv")

    # Fetch and merge weather
    start = combined["timestamp"].min().strftime("%Y-%m-%d")
    end = combined["timestamp"].max().strftime("%Y-%m-%d")

    all_weather = []
    for point in TARGET_POINTS:
        location = CITY_LOCATIONS.get(point)
        if location:
            weather_df = fetch_weather(API_KEY, location, start, end)
            weather_df["timestamp"] = weather_df["timestamp"].dt.tz_localize(None)
            weather_df["SettlementPointName"] = point
            all_weather.append(weather_df)
            #wait between fetches, bc rate limit
            time.sleep(2)

    if all_weather:
        weather_combined = pd.concat(all_weather, ignore_index=True)
        weather_combined.to_csv("data/weather_hourly.csv", index=False)

        merged = pd.merge(combined, weather_combined, on=["timestamp", "SettlementPointName"], how="inner")
        # Keep only rows where SettlementPointType is 'LZ'
        cleaned_df = merged[merged['SettlementPointType'] == 'LZ'].copy()
        cleaned_df.reset_index(drop=True, inplace=True)
        cleaned_df.to_csv("data/ercot_weather_merged.csv", index=False)

        #Ensure unique timestamp + SettlementPointName for reindexing
        grouped_df = cleaned_df.groupby(["timestamp", "SettlementPointName"]).mean(numeric_only=True).reset_index()

        #Create complete time range
        full_range = pd.date_range(grouped_df["timestamp"].min(), grouped_df["timestamp"].max(), freq="H")
        index = pd.MultiIndex.from_product([full_range, grouped_df["SettlementPointName"].unique()], names=["timestamp", "SettlementPointName"])
        grouped_df = grouped_df.set_index(["timestamp", "SettlementPointName"]).reindex(index).reset_index()

        #Handle missing values
        grouped_df[["SettlementPointPrice", "temperature", "windspeed", "solar_irradiance"]] = grouped_df[["SettlementPointPrice", "temperature", "windspeed", "solar_irradiance"]].interpolate()

        #Remove outliers
        grouped_df = grouped_df[(grouped_df["SettlementPointPrice"].between(-1000, 10000))]

        #Correlation per region
        for region in grouped_df["SettlementPointName"].unique():
            subset = grouped_df[grouped_df["SettlementPointName"] == region]
            print(f"\nCorrelation for {region}:")
            print(subset[["SettlementPointPrice", "temperature", "windspeed", "solar_irradiance"]].corr())

    df = pd.read_csv("data/ercot_weather_merged.csv", parse_dates=["timestamp"])
    json_output_path = "../../public/ercot_weather_merged.json"
    df.to_json(json_output_path, orient="records", date_format="iso")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_csvs = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")]

    if existing_csvs:
        print(f"Found {len(existing_csvs)} CSV files, skipping scrape.")
    else:
        #scraping with selenium
        driver = setup_driver()
        rows = get_file_rows(driver)
        print(f"Found {len(rows)} file rows.")
        for row in rows:
            try:
                download_and_extract(row)
            except Exception as e:
                print(f"Error with row: {e}")
        driver.quit()

    # Cleaning and analyzing data from ercot csvs
    combine_and_merge()

    

if __name__ == "__main__":
    main()

