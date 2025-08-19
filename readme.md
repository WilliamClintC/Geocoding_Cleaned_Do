# Truck Stop Geocoding Data Processing Pipeline

**Project completed under Prof. Ron Yang and Sarah Armitage**

## Overview

This study utilizes a comprehensive truck stop directory dataset containing information about individual truck stops. Notably, the original dataset does not include geographic coordinates (latitude and longitude). The  objective of this project is to systematically extract and assign accurate geographic coordinates to each truck stop entry.

## Challenges

A significant challenge encountered in this process stems from the inconsistent formatting of address information. While some entries provide complete street addresses, others list only road names, highway exits, or mile markers. This lack of standardization complicates the process of automated geocoding and necessitates additional data processing steps.

Furthermore, the dataset required extensive cleaning. 

## Data Sources and Collection Timeline

The project utilized three sources to gather truck stop information and geographic coordinates:

### 1. Truck Stops and Services and RVers and Travellers Website Scraping
**Date: June 13, 2025**

- **RVers and Travellers**: http://www.rvandtravelers.com/
- **Truck Stops and Services**: https://www.truckstopsandservices.com/

These two websites share similar formatting but with slightly different availability of stop availability and information. RVers and Travellers is geared towards RV users but still contains relevant truck stops. While Truck Stops and Services is specifically geared towards trucks.

![Truck Stops and Services Website](Images/Screenshot%202025-07-16%20001757.png)
*Example of Truck Stops and Services website scraped*

![RVers and Travellers Website](Images/Screenshot%202025-07-16%20002154.png)
*Example of RVers and Travellers website scraped*

### 2. Yellow Pages Scraping
**Date: July 6, 2025**

- **Yellow Pages**: https://www.yellowpages.com/

Yellow Pages was scraped to gather additional truck stop business information.

![Yellow Pages Search Results](Images/Screenshot%202025-07-16%20011959.png)
*Yellow Pages search results page*

![Yellow Pages Business Listings](Images/Screenshot%202025-07-16%20012037.png)
*Yellow Pages business listing details*

### 3. Yelp API Integration
**Date: June 25, 2025**

- **Yelp API**: https://www.yelp.com/

The Yelp API was utilized to query truck stop phone numbers. 

![Yelp API Data](Images/Screenshot%202025-07-16%20013928.png)
*Example of Yelp API website*

## Project Structure

```
├── main.py                     # Master pipeline execution script
├── Code/
│   ├── data_cleaning.py        # Data cleaning and preprocessing
│   └── data_finalization.py    # Final data processing and output
├── Data/
│   ├── Raw/                    # Original source data
│   ├── Processed_Intermediate/ # Intermediate processing files
│   └── Processed_Final/        # Final cleaned and geocoded data
└── Images/                     # Documentation screenshots
```

## Usage

Execute the complete data processing pipeline by running:

```bash
python main.py
```

This master script orchestrates the entire workflow from raw data ingestion through final geocoded output generation.
