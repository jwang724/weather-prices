# weather-prices
Python backend that uses Selenium to scrape data from ERCOT https://www.ercot.com/mp/data-products/data-product-details?id=np6-905-cd and collects and processes that data combined with React and Typescript frontend dashboard to visualize relationship between weather and energy prices.
Fetches weather data from Visual Crossing API to fetch info like wind speed, temperature, etc.

# Setup instructions

## 1. Clone Repo
```
git clone https://github.com/jwang724/weather-prices.git
cd weather-prices
```
## 2. Install dependencies
```
pip install pandas requests selenium
```
## 3. Run Python Script to gather and process data
```
cd src/services
python3 app.py # This generates a json file to the processed data so the frontend could use
```
## 4. React Setup
```
npm install # Install dependencies
npm run start # Runs the app and available to use at http://localhost:3000
```

# Approach
Used Selenium to programmatically scrape ERCOT data since table from website was dynamically loaded
Used Visual Crossing API to fetch weather data. Had to cache the data since was receiving rate limits on the API request, so data may be stale/old.
Only parsed three major settlement points ("LZ_HOUSTON", "LZ_NORTH", "LZ_AEN"), matched the location of weather with each of these regions
Export the proccessed dataset as JSON file for the React frontend.
Used Material UI, and Recharts graph library for building the frontend dashboard.
Frontend Dashboard includes a timeseries graph plotting Price vs Windspeed over time and a Scatter plot of windspeed vs price correlation.

# Screenshots
![Screenshot 2025-04-20 at 10 53 17 PM](https://github.com/user-attachments/assets/f196d5b2-106c-4006-b1cc-79ba5072f6f5)

![Screenshot 2025-04-20 at 10 43 10 PM](https://github.com/user-attachments/assets/69ee3e9c-0d3d-4b8c-9810-a19fac8a9362)
