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
    - [Supplementary Fields](#supplementary-fields)
      - [Address Standardization Fields](#address-standardization-fields)
      - [Webscraped Phone Fields](#webscraped-phone-fields)
        - [General Information](#general-information)
        - [Location Details](#location-details)
        - [Contact Information](#contact-information)
        - [Amenities \& Services](#amenities--services)
        - [Fuel Types \& Links](#fuel-types--links)
        - [Place Matching](#place-matching)
        - [Matched Place Details](#matched-place-details)
          - [General Information](#general-information-1)
          - [Location Details](#location-details-1)
          - [Contact Information](#contact-information-1)
          - [Amenities \& Services](#amenities--services-1)
          - [Fuel Types \& Links](#fuel-types--links-1)
      - [Yelp Fields](#yelp-fields)
        - [General Business Information](#general-business-information)
        - [Location Details](#location-details-2)
        - [Contact \& Business Attributes](#contact--business-attributes)
      - [Yellow Pages Fields](#yellow-pages-fields)
        - [General Business Information](#general-business-information-1)
        - [Location Details](#location-details-3)
        - [Contact \& Business Attributes](#contact--business-attributes-1)
      - [Distance Fields](#distance-fields)
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

**`Scraped_zipcode_to_label_match_rate`**  
Binary variables that indicate whether a successful addresses and business names match was found with RVers and Travellers or Truck Stops and Services website.

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
These fields contain URLs associated with scraped data and API data, useful for debugging and manually verifying entries to spot discrepancies.

### Manual Verification Field

**`Match_Comments`**  
A comment field used for manually matching entries. When manual matching was required due to lack of automated matches, or when problematic entries needed review and correction, this field indicates that coordinates were manually corrected or verified. It contains specific details about how the match was verified and the source of the "correct" geocoordinate match.

### Final Coordinates

**`Final_Lat`, `Final_Long`**  
The primary output of this project containing the geocoordinates (latitude and longitude) of each truck stop entry.

### Supplementary Fields

The project also includes a CSV file called `10_supplementary.csv`, which contains supplementary fields. These fields may be helpful but are not necessarily required:

- **`Flag_Place_Change`**: Identifies if a truck stop has changed its name or chain affiliation over the years. Useful for tracking changes in ownership or branding.
- **`Flag_Place_Change_Year`**: Indicates the year of the change.
- **`Similarity_Score`**: Indicates how similar the current truck stop is to the previous year's entry. A high score suggests minimal changes, while a low score indicates potential changes in name or chain affiliation.
- **`Chain_Match`**: Checks if a chain affiliation has changed from the previous year.
- **`Previous_Year_Label`, `Previous_Year_Chain`**: Provide details about the truck stop's label and chain affiliation from the previous year.

#### Address Standardization Fields

- **`address_standardized_ON_parenthesis`**: A human-readable address containing details useful for a trucker that is lost and needs to find a place. This format is not ideal for database matching or geocoding.
- **`address_standardized_OFF_parenthesis`**: The main address used for matching and geocoding.

#### Webscraped Phone Fields

These fields contain details matched with the RVers and Travellers and Truck Stops and Services websites.

##### General Information

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_Phone_state_id`    | State identifier for phone match             |
| `Webscraped_Phone_state`       | State for phone match                        |
| `Webscraped_Phone_name`        | Name of phone-matched place                  |
| `Webscraped_Phone_href`        | Relative URL for phone-matched place         |
| `Webscraped_Phone_full_url`    | Full URL for phone-matched place             |
| `Webscraped_Phone_stop_type`   | Stop type for phone-matched place            |
| `Webscraped_Phone_Chain`       | Chain for phone-matched place                |

##### Location Details

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_Phone_Latitude`    | Website Visual Read Latitude for phone-matched place             |
| `Webscraped_Phone_Longitude`   | Website Visual Read observed Longitude for phone-matched place            |
| `Webscraped_Phone_LD_URL`      | Embedded website data URL for phone-matched place      |
| `Webscraped_Phone_LD_Latitude` | Embedded website data latitude for phone-matched place |
| `Webscraped_Phone_LD_Longitude`| Embedded website data longitude for phone-matched place|
| `Webscraped_Phone_Highway`     | Highway for phone-matched place              |
| `Webscraped_Phone_Exit`        | Exit number for phone-matched place          |
| `Webscraped_Phone_Mile Marker` | Mile marker for phone-matched place          |
| `Webscraped_Phone_Street Address` | Street address for phone-matched place    |
| `Webscraped_Phone_City`        | City for phone-matched place                 |
| `Webscraped_Phone_State`       | State associated with phone-matched place   |
| `Webscraped_Phone_Postal Code` | Postal code for phone-matched place          |
| `Webscraped_Phone_Road Name`   | Road name for phone-matched place            |

##### Contact Information

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_Phone_Phone`       | Main contact number for phone-matched place  |
| `Webscraped_Phone_Phone 2`     | Additional phone for phone-matched place     |
| `Webscraped_Phone_Phone 3`     | Additional phone for phone-matched place     |
| `Webscraped_Phone_Phone 4`     | Additional phone for phone-matched place     |
| `Webscraped_Phone_Phone 5`     | Additional phone for phone-matched place     |
| `Webscraped_Phone_Fax`         | Fax for phone-matched place                  |

##### Amenities & Services

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_Phone_# of Parking Spots`           | Total parking spaces for phone-matched place             |
| `Webscraped_Phone_# of Reserved Parking Spots`  | Reserved spaces for phone-matched place                  |
| `Webscraped_Phone_# of Paid Parking Spots`      | Paid-only spots for phone-matched place                  |
| `Webscraped_Phone_# of Fuel Lanes`              | Fuel lanes for phone-matched place                       |
| `Webscraped_Phone_# of Showers`                 | Showers for phone-matched place                          |
| `Webscraped_Phone_# of Men's Showers`           | Men's showers for phone-matched place                    |
| `Webscraped_Phone_# of Truck Service Bays`      | Truck service bays for phone-matched place               |
| `Webscraped_Phone_Hours of Operation`           | Hours for phone-matched place                            |

##### Fuel Types & Links

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_Phone_Unleaded`    | Whether unleaded gasoline is available        |
| `Webscraped_Phone_Diesel`      | Whether diesel fuel is available              |
| `Webscraped_Phone_Bulk Def`    | Whether DEF (diesel exhaust fluid) is available |
| `Webscraped_Phone_Propane`     | Whether propane is available                  |
| `Webscraped_Phone_https`       | HTTPS URL for phone-matched place             |
| `Webscraped_Phone_http`        | HTTP URL for phone-matched place              |

##### Place Matching

These fields contain details for address and business name matches with the RVers and Travellers and Truck Stops and Services websites.

##### Matched Place Details

###### General Information

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_PlacedMatched_state_id`    | State identifier for matched place           |
| `Webscraped_PlacedMatched_state`       | State for matched place                      |
| `Webscraped_PlacedMatched_name`        | Name of matched place                        |
| `Webscraped_PlacedMatched_href`        | Relative URL for matched place               |
| `Webscraped_PlacedMatched_full_url`    | Full URL for matched place                   |
| `Webscraped_PlacedMatched_stop_type`   | Stop type for matched place                  |
| `Webscraped_PlacedMatched_Chain`       | Chain for matched place                      |

###### Location Details

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_PlacedMatched_Latitude`    | Website Visual Read Latitude for matched place             |
| `Webscraped_PlacedMatched_Longitude`   | Website Visual Read observed Longitude for matched place            |
| `Webscraped_PlacedMatched_LD_URL`      | Embedded website data URL for matched place      |
| `Webscraped_PlacedMatched_LD_Latitude` | Embedded website data latitude for matched place |
| `Webscraped_PlacedMatched_LD_Longitude`| Embedded website data longitude for matched place|
| `Webscraped_PlacedMatched_Highway`     | Highway for matched place              |
| `Webscraped_PlacedMatched_Exit`        | Exit number for matched place          |
| `Webscraped_PlacedMatched_Mile Marker` | Mile marker for matched place          |
| `Webscraped_PlacedMatched_Street Address` | Street address for matched place    |
| `Webscraped_PlacedMatched_City`        | City for matched place                 |
| `Webscraped_PlacedMatched_State`       | State associated with matched place   |
| `Webscraped_PlacedMatched_Postal Code` | Postal code for matched place          |
| `Webscraped_PlacedMatched_Road Name`   | Road name for matched place            |

###### Contact Information

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_PlacedMatched_Phone`       | Main contact number for matched place  |
| `Webscraped_PlacedMatched_Phone 2`     | Additional phone for matched place     |
| `Webscraped_PlacedMatched_Phone 3`     | Additional phone for matched place     |
| `Webscraped_PlacedMatched_Phone 4`     | Additional phone for matched place     |
| `Webscraped_PlacedMatched_Phone 5`     | Additional phone for matched place     |
| `Webscraped_PlacedMatched_Fax`         | Fax for matched place                  |

###### Amenities & Services

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_PlacedMatched_# of Parking Spots`           | Total parking spaces for matched place             |
| `Webscraped_PlacedMatched_# of Reserved Parking Spots`  | Reserved spaces for matched place                  |
| `Webscraped_PlacedMatched_# of Paid Parking Spots`      | Paid-only spots for matched place                  |
| `Webscraped_PlacedMatched_# of Fuel Lanes`              | Fuel lanes for matched place                       |
| `Webscraped_PlacedMatched_# of Showers`                 | Showers for matched place                          |
| `Webscraped_PlacedMatched_# of Men's Showers`           | Men's showers for matched place                    |
| `Webscraped_PlacedMatched_# of Truck Service Bays`      | Truck service bays for matched place               |
| `Webscraped_PlacedMatched_Hours of Operation`           | Hours for matched place                            |

###### Fuel Types & Links

| Column Name | Description |
|:-------------------------------|:---------------------------------------------|
| `Webscraped_PlacedMatched_Unleaded`    | Whether unleaded gasoline is available for matched place        |
| `Webscraped_PlacedMatched_Diesel`      | Whether diesel fuel is available for matched place            |
| `Webscraped_PlacedMatched_Bulk Def`    | Whether DEF (diesel exhaust fluid) is available for matched place |
| `Webscraped_PlacedMatched_Propane`     | Whether propane is available for matched place                  |
| `Webscraped_PlacedMatched_Hours of Operation` | Hours for matched place                   |
| `Webscraped_PlacedMatched_https`       | HTTPS URL for matched place                  |
| `Webscraped_PlacedMatched_http`        | HTTP URL for matched place                   |

#### Yelp Fields

These fields contain details associated with Yelp matches. A notable feature is the ability to observe whether the truck stop is still operational:

##### General Business Information

| Column Name | Description |
|:---------------------|:-----------------------------------------------|
| `Yelp_Original_Phone`| The phone number used as input for the Yelp phone search |
| `Yelp_Name`          | The official name of the business              |
| `Yelp_Rating`        | Yelp rating (e.g., 4.5 stars)                  |
| `Yelp_Review_Count`  | Total number of Yelp reviews                   |
| `Yelp_Is_Closed`     | Boolean indicating if the business is closed   |
| `Yelp_URL`           | Full Yelp business listing URL                 |

##### Location Details

| Column Name | Description |
|:---------------------|:-----------------------------------------------|
| `Yelp_Address`       | Street address of the business                 |
| `Yelp_City`          | City where the business is located             |
| `Yelp_State`         | State (abbreviation)                           |
| `Yelp_Zip_Code`      | Postal or ZIP code                             |
| `Yelp_Latitude`      | Latitude coordinate                            |
| `Yelp_Longitude`     | Longitude coordinate                           |

##### Contact & Business Attributes

| Column Name | Description |
|:---------------------|:-----------------------------------------------|
| `Yelp_Phone`         | Official business phone number returned by Yelp|
| `Yelp_Categories`    | List of categories (e.g., "Coffee & Tea", "Gas Station") |
| `Yelp_Price`         | Price level indicator (`$`, `$$`, etc., if available)    |

#### Yellow Pages Fields

These fields contain details associated with Yellow Pages matches. A notable feature is the AKA field which allows us to observe other names associated with the truck stop.

##### General Business Information

| Column Name | Description |
|:--------------------------|:---------------------------------------------|
| `YellowPages_ADDRESS`     | Full address of the business as listed on Yellow Pages |
| `YellowPages_AKA`         | Alternate names or aliases for the business   |
| `YellowPages_BUSINESS_NAME` | The primary name of the business           |
| `YellowPages_BUSINESS_URL`  | URL to the Yellow Pages business listing    |
| `YellowPages_CATEGORIES`    | Business categories (e.g., "Restaurants", "Auto Repair") |
| `YellowPages_STATUS`        | Business status (e.g., "Open", "Closed")   |
| `YellowPages_WEBSITE`       | Official website of the business, if available |

##### Location Details

| Column Name | Description |
|:--------------------------|:---------------------------------------------|
| `YellowPages_JSONLD_CITY_1`   | City extracted from the embedded structured JSON-LD data |
| `YellowPages_JSONLD_STATE_1`  | State extracted from the embedded structured JSON-LD data |
| `YellowPages_JSONLD_STREET_1` | Street address from JSON-LD                |
| `YellowPages_JSONLD_ZIP_1`    | ZIP code from JSON-LD                      |
| `YellowPages_JSONLD_LAT_1`    | Latitude coordinate from JSON-LD            |
| `YellowPages_JSONLD_LNG_1`    | Longitude coordinate from JSON-LD           |

##### Contact & Business Attributes

| Column Name | Description |
|:--------------------------|:---------------------------------------------|
| `YellowPages_ORIGINAL_PHONE` | Phone number used to initiate the Yellow Pages lookup |
| `YellowPages_FORMATTED_PHONE`| Formatted business phone number as displayed |
| `YellowPages_JSONLD_PHONE_1` | Phone number from the structured JSON-LD data |
| `YellowPages_EXTRA_PHONES`   | Any additional phone numbers found           |
| `YellowPages_PHONE`          | Phone number listed in the primary Yellow Pages HTML content |
| `YellowPages_JSONLD_NAME_1`  | Business name from structured JSON-LD data   |
| `YellowPages_SCRAPED_AT`     | Date/time when the data was scraped          |
| `YellowPages_SEARCH_URL`     | URL used for the Yellow Pages search         |

#### Distance Fields

- **`min_distance_miles`**: Captures the distance between two matches from different sources. For example, if Match A is from Yelp source and Match B is from Yellowpages, this field calculates the distance between the two coordinates.
- **`min_distance_sources`**: Indicates the sources of the matches used for the final match. For example, it shows if Yelp matched onto Yellow Pages or Yelp matched onto Truck Stops and Services (phone), etc. 


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

