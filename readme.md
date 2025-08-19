# Truck Stop Geocoding Data Processing Pipeline

**Project completed under Prof. Ron Yang and Sarah Armitage**

## Table of Contents

- [Truck Stop Geocoding Data Processing Pipeline](#truck-stop-geocoding-data-processing-pipeline)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Challenges](#challenges)
  - [Final Output](#final-output)
    - [Original Data Fields](#original-data-fields)
    - [Processed Data Fields](#processed-data-fields)
    - [Match Rate Fields](#match-rate-fields)
    - [Temporal Consistency Field](#temporal-consistency-field)
    - [Reference URLs](#reference-urls)
    - [Manual Verification Field](#manual-verification-field)
    - [Final Coordinates](#final-coordinates)
  - [Data Sources and Collection Timeline](#data-sources-and-collection-timeline)
    - [1. Truck Stops and Services and RVers and Travellers Website Scraping](#1-truck-stops-and-services-and-rvers-and-travellers-website-scraping)
    - [2. Yellow Pages Scraping](#2-yellow-pages-scraping)
    - [3. Yelp API Integration](#3-yelp-api-integration)
  - [Project Structure](#project-structure)
  - [Usage](#usage)

## Overview

This study utilizes a truck stop directory dataset (The Trucker's Friend: National Truck Stop Directory) containing information about individual truck stops. Notably, the original dataset does not include geographic coordinates (latitude and longitude). The  objective of this project is to systematically extract and assign accurate geographic coordinates to each truck stop entry.

This README provides an overview of the project. More details on the matching processes and the intermediate/raw files are available at: https://github.com/WilliamClintC/Geocoding_Documentation/blob/main/6.pdf


## Challenges

A significant challenge encountered in this process stems from the inconsistent formatting of address information. While some entries provide complete street addresses, others list only road names, highway exits, or mile markers. This lack of standardization complicates the process of automated geocoding and necessitates additional data processing steps.

Furthermore, the dataset required extensive cleaning. 

## Final Output 

The final output is `Data\Processed_Final\10_final.csv`, which contains the following columns:

### Original Data Fields

**`clean_line1`, `clean_line2`, `line3`**  
These contain the original OCR-read data from the Truckers Friend truck stop directory. This is the "original" data without geocoordinates.

**`city`, `zip_code`, `label`, `phone`, `year`, `major_city`, `state`, `chain`**  
These fields came from the original data as well:
- `label`: Name of the truck stop
- `year`: Year of the truck stop directory where the data was sourced
- `chain`: Truck stop chain (some truck stops are independent while others are nationwide franchises or chains)
- Other fields are self-explanatory

### Processed Data Fields

**`Address_Type`, `Exit_Number`, `Main_Road`, `Secondary_Road`, `Exit_Number_2`, `Exit_Number_3`, `Tertiary_Road`**  
These fields were created to analyze the data and improve the matching process:

- **`Address_Type`**: Categorizes addresses into three types:
  - `Exit`: Address containing only highway and exit number
  - `Proper`: Standard address with number and road name
  - `Empty`: Any other format that doesn't fit the above categories

- **`Main_Road`, `Secondary_Road`**: Extract road information
  - For standard address "1234 Sesame and Elmer Street": `Main_Road` = "Sesame Street", `Secondary_Road` = "Elmer Street"
  - For highway address "I-90 exit 25": `Main_Road` = "I-90", `Exit_Number` = "25"
  - For complex highways "I-90 and I-25 exit 25": `Secondary_Road` = "I-25"

- **`Exit_Number_2/3`**: Additional exit numbers when present
- **`Tertiary_Road`**: Third road when applicable

### Match Rate Fields

**`Scraped_phone_match_rate`, `Yelp_phone_match_rate`, `Yellowbook_phone_match_rate`**  
Binary variables indicating phone number matches in associated sources:
- `Scraped_phone_match_rate`: True if phone number matches in RVers and Travellers or Truck Stops and Services
- `Yelp_phone_match_rate`: True if phone number matches in Yelp API
- `Yellowbook_phone_match_rate`: True if phone number matches in Yellow Pages

### Temporal Consistency Field

**`place_identifier(year)`**  
This variable identifies consecutive entries of the same truck stop across different years. For example, if we have data for a truck stop in 2006, 2007, 2008, 2014, 2015, and 2016, this identifier helps handle inconsistencies due to OCR errors, data cleaning errors, or genuine changes.

If geocoordinates are missing for 2007 but available for 2006 and 2008, and the place identifier confirms it's the same truck stop, we can reasonably impute the 2007 coordinates using data from adjacent years.

### Reference URLs

**`Webscraped_Phone_full_url`, `Webscraped_PlacedMatched_full_url`, `Yelp_URL`, `YellowPages_SEARCH_URL`**  
These contain URLs associated with scraped data and API data, useful for debugging and manually verifying entries to spot discrepancies.

### Manual Verification Field

**`Match_Comments`**  
A comment field used for manually matching entries. When manual matching was required due to lack of automated matches, or when problematic entries needed review and correction, this field indicates that coordinates were manually corrected or verified. It contains specific details about how the match was verified and the source of the "correct" geocoordinate match.

### Final Coordinates

**`Final_Lat`, `Final_Long`**  
The primary output of this project containing the geocoordinates (latitude and longitude) of each truck stop entry.

## Data Sources and Collection Timeline

The project utilized three sources to gather truck stop information and geographic coordinates:

### 1. Truck Stops and Services and RVers and Travellers Website Scraping
**Date Scraped: June 13, 2025**

- **RVers and Travellers**: http://www.rvandtravelers.com/
- **Truck Stops and Services**: https://www.truckstopsandservices.com/

These two websites share similar formatting but with slightly different availability of stop availability and information. RVers and Travellers is geared towards RV users but still contains relevant truck stops. While Truck Stops and Services is specifically geared towards trucks.

![Truck Stops and Services Website](Images/Screenshot%202025-07-16%20001757.png)
*Example of Truck Stops and Services website scraped*

![RVers and Travellers Website](Images/Screenshot%202025-07-16%20002154.png)
*Example of RVers and Travellers website scraped*

### 2. Yellow Pages Scraping
**Date Scraped: July 6, 2025**

- **Yellow Pages**: https://www.yellowpages.com/

Yellow Pages was scraped to gather additional truck stop business information.

![Yellow Pages Search Results](Images/Screenshot%202025-07-16%20011959.png)
*Yellow Pages website scraped*

![Yellow Pages Business Listings](Images/Screenshot%202025-07-16%20012037.png)
*Yellow Pages  website scraped*

### 3. Yelp API Integration
**Date Accessed: June 25, 2025**

- **Yelp API**: https://www.yelp.com/

The Yelp API was utilized to query truck stop phone numbers. 

![Yelp API Data](Images/Screenshot%202025-07-16%20013928.png)
*Example of Yelp API website*

## Project Structure

```
├── main.py                     # Master execution script
├── Code/
│   ├── data_cleaning.py        # Data cleaning and processing
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
