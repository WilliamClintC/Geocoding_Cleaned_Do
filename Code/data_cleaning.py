"""
Address Data Cleaning - Initial Processing

This script performs the initial cleaning and standardization of address data 
from the raw unbalanced panel dataset. It handles:

1. Standardizing interstate highway references (e.g., "I 80", "1-80" to "I-80")
2. Removing unnecessary columns
3. Saving the cleaned data for further processing

This is the first step in the data cleaning pipeline.
"""

import pandas as pd
import numpy as np
import re
import os
import random
import ast

def standardize_interstate_format_final(text):
    """
    Standardizes interstate highway naming to I-NUMBER format
    
    Handles these specific variations:
    - I - NUMBER (with spaces, e.g., I - 80)
    - I -NUMBER  
    - I- NUMBER (space after dash, e.g., I- 80)
    - I-NUMBER (e.g., I-80) [already correct]
    - 1 - NUMBER (with spaces, e.g., 1 - 80)
    - 1 -NUMBER
    - 1- NUMBER (space after dash, e.g., 1- 80)
    
    Does NOT match: "1 NUMBER" (space, no dash like "1 80")
    """
    if pd.isna(text) or not isinstance(text, str):
        return text
    
    # Multiple patterns to handle specific cases
    patterns = [
        # I with dash variations (spaces around dash)
        r'\bI\s*-\s*(\d+)\b',           # I - 80, I -80, I- 80, I-80
        # I with no dash but with space  
        r'\bI\s+(\d+)\b',               # I 80
        # 1 with dash variations (spaces around dash)
        r'\b1\s*-\s*(\d+)\b',           # 1 - 80, 1 -80, 1- 80, 1-80
        # Note: Intentionally excluding r'\b1\s+(\d+)\b' which would match "1 80"
    ]
    
    def replace_interstate(match):
        number = match.group(1)
        return f'I-{number}'
    
    result = text
    for pattern in patterns:
        result = re.sub(pattern, replace_interstate, result, flags=re.IGNORECASE)
    
    return result

def extract_address_components(df):
    """
    Extract address components by splitting on parentheses.
    Creates two new columns:
    - address_standardized_ON_parenthesis: Everything from "(" onwards
    - address_standardized_OFF_parenthesis: Everything before "("
    """
    print("Extracting address components based on parentheses...")
    
    # Extract everything from "(" onwards (ON portion)
    df['address_standardized_ON_parenthesis'] = df['address'].str.extract(r'(\(.*)', expand=False)
    
    # Extract everything before "(" (OFF portion)
    df['address_standardized_OFF_parenthesis'] = df['address'].str.extract(r'(.*?)(?=\(|$)', expand=False)
    
    print("Address component extraction completed!")
    return df

def classify_address_types(df):
    """
    Create an Address_Type column and classify addresses as 'Exit' based on patterns.
    Sets "Address_Type" to "Exit" if address contains exit-related patterns.
    """
    print("Classifying address types...")
    
    # Create a new column called "Address_Type" - initially empty
    df['Address_Type'] = 'empty'
    
    # Set "Address_Type" to "Exit" if address contains exit patterns
    # This will catch patterns like "Exit", "I-15 Exit 10", "I-710 Ex 1 B SB", etc.
    exit_pattern = r'([EÉeé]?xit|Ex\s+\d+|Ex$|\bEx\b|\bX\s+\d+)'
    df.loc[df['address_standardized_OFF_parenthesis'].str.contains(exit_pattern, case=False, na=False, regex=True), 'Address_Type'] = 'Exit'
    
    exit_count = (df['Address_Type'] == 'Exit').sum()
    print(f"Classified {exit_count} addresses as 'Exit' type")
    
    return df

def remove_zipcode_from_all_rows(df):
    """
    Remove zip codes from address strings for all rows in the DataFrame.
    Handles ZIP codes both with and without leading zeros (e.g., both "1105" and "01105").
    
    Args:
        df: DataFrame containing the data
    
    Returns:
        DataFrame with updated addresses
    """
    print("Removing zip codes from addresses...")
    rows_processed = 0
    rows_updated = 0
    
    for index in range(len(df)):
        zip_code = str(df.iloc[index]['zip_code'])
        current_address = str(df.iloc[index]['address_standardized_OFF_parenthesis'])
        
        if zip_code != 'nan' and zip_code.strip():
            # Clean the zip code and ensure it's numeric
            zip_code_clean = zip_code.strip()
            
            # Create both versions of the ZIP code (with and without leading zero)
            zip_codes_to_remove = set()
            
            if zip_code_clean.isdigit():
                # Add the original ZIP code
                zip_codes_to_remove.add(zip_code_clean)
                
                # If it's 4 digits, add the 5-digit version with leading zero
                if len(zip_code_clean) == 4:
                    zip_codes_to_remove.add('0' + zip_code_clean)
                
                # If it's 5 digits and starts with 0, add the version without leading zero
                elif len(zip_code_clean) == 5 and zip_code_clean.startswith('0'):
                    zip_codes_to_remove.add(zip_code_clean[1:])
            
            # Check if any version of the ZIP code exists in the address
            address_updated = False
            updated_address = current_address
            
            for zip_to_remove in zip_codes_to_remove:
                if zip_to_remove in updated_address:
                    # Remove the zip code from the address string
                    updated_address = updated_address.replace(zip_to_remove, '').strip()
                    address_updated = True
            
            if address_updated:
                # Clean up multiple spaces and trailing/leading commas
                updated_address = ' '.join(updated_address.split())  # Remove multiple spaces
                updated_address = updated_address.replace(' ,', ',')  # Fix space before comma
                updated_address = updated_address.replace(', ,', ',')  # Fix double commas
                updated_address = updated_address.strip(' ,')  # Remove leading/trailing spaces and commas
                
                # Update the DataFrame
                df.iloc[index, df.columns.get_loc('address_standardized_OFF_parenthesis')] = updated_address
                rows_updated += 1
        
        rows_processed += 1
    
    print(f"Processed {rows_processed} rows, updated {rows_updated} addresses")
    return df

def clean_leading_dashes(df):
    """
    Remove leading "-" characters from address_standardized_OFF_parenthesis column
    Example: "- 43859 N Sierra " becomes "43859 N Sierra "
    """
    print("Cleaning leading dashes from address_standardized_OFF_parenthesis column...")
    
    # Count how many entries have leading dashes
    leading_dash_count = df['address_standardized_OFF_parenthesis'].str.startswith('- ', na=False).sum()
    print(f"Found {leading_dash_count} entries with leading dashes")
    
    # Remove leading "- " from the addresses
    df['address_standardized_OFF_parenthesis'] = df['address_standardized_OFF_parenthesis'].str.replace(r'^- ', '', regex=True)
    
    print("Cleaning completed!")
    return df

def identify_proper_addresses(df):
    """
    Function to identify proper addresses and update Address_Type column.
    Only processes rows where Address_Type is currently "empty".
    For these rows:
    1. Removes any instances of ")" and "<U+00D8>" from address_standardized_OFF_parenthesis
    2. Checks if the cleaned address starts with a number sequence (proper address)
    3. Updates Address_Type to "Proper" if criteria is met
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the address data
    
    Returns:
    pandas.DataFrame: DataFrame with updated Address_Type column and cleaned addresses
    """
    print("Identifying proper addresses...")
    
    # Create a copy to avoid modifying the original dataframe
    df_copy = df.copy()
    
    # Ensure Address_Type column exists
    if 'Address_Type' not in df_copy.columns:
        df_copy['Address_Type'] = ''
    
    # Only iterate through rows where Address_Type is "empty"
    empty_rows = df_copy[df_copy['Address_Type'] == 'empty']
    proper_count = 0
    
    for index, row in empty_rows.iterrows():
        address = row['address_standardized_OFF_parenthesis']
        
        # Check if address is not null/empty
        if pd.notna(address) and str(address).strip():
            # Convert to string and strip whitespace
            address_str = str(address).strip()
            
            # Remove any instances of ")" and "<U+00D8>" from the address
            cleaned_address = address_str.replace(')', '').replace('<U+00D8>', '')
            
            # Update the address column with the cleaned version
            df_copy.at[index, 'address_standardized_OFF_parenthesis'] = cleaned_address
            
            # Check if cleaned address starts with a number sequence followed by a space
            # This pattern matches one or more digits followed by a space
            if re.match(r'^\d+\s', cleaned_address):
                df_copy.at[index, 'Address_Type'] = 'Proper'
                proper_count += 1
    
    print(f"Identified {proper_count} proper addresses")
    return df_copy

def remove_city_prefix(df):
    """
    Remove "City," prefix from address_standardized_OFF_parenthesis entries
    that start with this pattern.
    """
    print("Removing 'City,' prefix from addresses...")
    
    # Create a copy to avoid modifying the original dataframe
    df_copy = df.copy()
    
    # Find entries that start with "City,"
    city_mask = df_copy['address_standardized_OFF_parenthesis'].str.startswith('City,', na=False)
    
    print(f"Found {city_mask.sum()} entries starting with 'City,'")
    
    if city_mask.sum() > 0:
        # Remove "City," prefix (including the comma and any following space)
        df_copy.loc[city_mask, 'address_standardized_OFF_parenthesis'] = (
            df_copy.loc[city_mask, 'address_standardized_OFF_parenthesis']
            .str.replace('^City,\s*', '', regex=True)
        )
        
        print(f"Successfully cleaned {city_mask.sum()} entries")
    
    return df_copy

def rename_ocr_columns(df):
    """
    Rename columns to remove OCR_ prefix.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the data
    
    Returns:
    pandas.DataFrame: DataFrame with renamed columns
    """
    print("Renaming columns to remove OCR_ prefix...")
    
    # Find all columns that start with 'OCR_'
    ocr_columns = [col for col in df.columns if col.startswith('OCR_')]
    
    if ocr_columns:
        # Create rename dictionary
        rename_dict = {col: col.replace('OCR_', '') for col in ocr_columns}
        
        print(f"Renaming {len(ocr_columns)} columns:")
        for old_name, new_name in rename_dict.items():
            print(f"  {old_name} -> {new_name}")
        
        # Rename the columns
        df = df.rename(columns=rename_dict)
        
        print("Column renaming completed!")
    else:
        print("No columns with OCR_ prefix found.")
    
    return df

def clean_exit_parenthesis(df):
    """
    Remove ')' characters from address_standardized_OFF_parenthesis for entries
    where Address_Type='Exit'.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the data
    
    Returns:
    pandas.DataFrame: DataFrame with cleaned exit addresses
    """
    print("Cleaning parenthesis characters from exit addresses...")
    
    # Create a copy of the dataframe to modify
    df_cleaned = df.copy()
    
    # Find entries with Address_Type='Exit'
    exit_mask = (df_cleaned['Address_Type'] == 'Exit')
    exit_count = exit_mask.sum()
    print(f"Found {exit_count} entries with Address_Type='Exit'")
    
    if exit_count > 0:
        # Check which exit entries contain ')' characters
        exit_with_parenthesis = df_cleaned[exit_mask & 
                                         df_cleaned['address_standardized_OFF_parenthesis'].str.contains('\)', na=False)]
        
        parenthesis_count = len(exit_with_parenthesis)
        print(f"Found {parenthesis_count} exit entries containing ')' character")
        
        if parenthesis_count > 0:
            # Remove ')' characters from entries where Address_Type='Exit'
            df_cleaned.loc[exit_mask, 'address_standardized_OFF_parenthesis'] = (
                df_cleaned.loc[exit_mask, 'address_standardized_OFF_parenthesis']
                .str.replace(')', '', regex=False)
            )
            
            print(f"Successfully cleaned {parenthesis_count} exit entries")
        else:
            print("No exit entries with ')' characters found")
    
    return df_cleaned

def extract_exit_number(address_text, label_text=None):
    """
    Extract exit number from OCR address text and label text with comprehensive pattern matching.
    
    Handles formats like:
    - "I-80 Exit 162"
    - "I-710 Ex 13" (treats 'Ex' as 'Exit')
    - "US 101 X 326 B" (treats 'X' as 'Exit')
    - "I-710 X 15" (treats 'X' as 'Exit')
    - "Everett Tpke X 10" (treats 'X' as 'Exit')
    - "Garden State Pkwy X 157" (treats 'X' as 'Exit')
    - "I-40 <U+00C9>xit 325" (handles Unicode OCR errors)
    - "Speedy's I - 10 Exit 114 # 501 ( Miller Rd S )" (Exit in middle of text)
    
    Args:
        address_text (str): The address text containing exit information
        label_text (str): Optional label text to also search for exit information
        
    Returns:
        str or None: The extracted exit number, or None if not found
    """
    def _extract_from_text(text):
        if pd.isna(text) or text == '':
            return None
        
        text = str(text)
        
        # Pattern 1: Standard "Exit ###" format (anywhere in text)
        pattern1 = r'Exit\s+(\d+[A-Za-z]?)'
        match1 = re.search(pattern1, text, re.IGNORECASE)
        if match1:
            return match1.group(1)
        
        # Pattern 2: "Ex ###" format (abbreviation)
        pattern2 = r'\bEx\s+(\d+[A-Za-z]?)'
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            return match2.group(1)
        
        # Pattern 3: Unicode OCR error patterns (e.g., "I-40 <U+00C9>xit 325")
        # Handles Unicode characters that represent corrupted "Exit" text
        pattern3 = r'<U\+[0-9A-Fa-f]+>xit\s+(\d+[A-Za-z]?)'
        match3 = re.search(pattern3, text, re.IGNORECASE)
        if match3:
            return match3.group(1)
        
        # Pattern 4: Accented character patterns (É, È, etc.) for "Exit"
        # Handles cases where OCR misreads E as accented characters
        pattern4 = r'[ÉÈÊËéèêë]xit\s+(\d+[A-Za-z]?)'
        match4 = re.search(pattern4, text, re.IGNORECASE)
        if match4:
            return match4.group(1)
        
        # Pattern 5: "X ###" format with interstate/US highways
        # Matches patterns like "US 101 X 326" or "I-710 X 15"
        pattern5 = r'(?:US\s+\d+|I-\d+|SR\s+\d+|CA\s+\d+|State\s+Route\s+\d+)\s+X\s+(\d+[A-Za-z]?)'
        match5 = re.search(pattern5, text, re.IGNORECASE)
        if match5:
            return match5.group(1)
        
        # Pattern 6: "X ###" format with highway/route keywords
        # This catches other highway formats followed by X and a number
        pattern6 = r'(?:Highway|Hwy|Route|Rt)\s+\d+\s+X\s+(\d+[A-Za-z]?)'
        match6 = re.search(pattern6, text, re.IGNORECASE)
        if match6:
            return match6.group(1)
        
        # Pattern 7: "X ###" format with turnpikes, parkways, and named highways
        # Handles "Everett Tpke X 10", "Garden State Pkwy X 157", etc.
        pattern7 = r'(?:\w+\s+)?(?:Tpke|Turnpike|Pkwy|Parkway|Expwy|Expressway|Fwy|Freeway)\s+X\s+(\d+[A-Za-z]?)'
        match7 = re.search(pattern7, text, re.IGNORECASE)
        if match7:
            return match7.group(1)
        
        # Pattern 8: "X ###" format with named highways (e.g., "Garden State X 157")
        # More general pattern for named highways followed by X
        pattern8 = r'(?:\w+\s+\w+)\s+X\s+(\d+[A-Za-z]?)'
        match8 = re.search(pattern8, text, re.IGNORECASE)
        if match8:
            return match8.group(1)
        
        # Pattern 9: Standalone "X ###" format (most cautious approach)
        # Only matches if there's a numeric highway identifier before the X
        pattern9 = r'(?:\d{1,3}(?:-\d+)?)\s+X\s+(\d+[A-Za-z]?)'
        match9 = re.search(pattern9, text, re.IGNORECASE)
        if match9:
            return match9.group(1)
        
        return None
    
    # Try extracting from address text first
    result = _extract_from_text(address_text)
    if result:
        return result
    
    # If not found in address text, try label text
    if label_text is not None:
        result = _extract_from_text(label_text)
        if result:
            return result
    
    return None

def is_unclear_ocr_address(address_text, address_type):
    """
    Identify unclear OCR addresses based on patterns that indicate poor OCR quality.
    Only applies unclear patterns if the address_type is 'Exit'.
    
    Args:
        address_text (str): The address text to check
        address_type (str): The Address_Type value
    
    Returns:
        bool: True if unclear OCR is detected, False otherwise
    """
    if pd.isna(address_text) or address_text == '':
        return False
    
    # Only apply unclear patterns to Exit type addresses
    if address_type != 'Exit':
        return False
    
    text = str(address_text).strip()
    
    # Pattern indicators of unclear OCR
    unclear_patterns = [
        r'^\d{4,}',  # Starts with 4+ digits like "81191-15-80"
        r'.+,.+,.+',  # Multiple comma-separated fragments
        r'[A-Za-z][0-9]+-[0-9]+-[0-9]+',  # Letters followed by number patterns
        r'D[A-Z][a-z]+\s+[A-Z][a-z]+\s+City',  # "DSalt Lake City" pattern
        r'[A-Z][a-z]+\sJ\s[A-Z][a-z]+',  # Fragmented "Flying J Travel"
    ]
    
    # Check for unclear patterns
    for pattern in unclear_patterns:
        if re.search(pattern, text):
            return True
    
    # Check for specific problematic phrases
    problematic_phrases = ['81191-15-80', 'DSalt Lake City', 'nemucca,', 'Flying I-', 'Eagle\'s I-']
    for phrase in problematic_phrases:
        if phrase in text:
            return True
    
    return False

def apply_exit_number_extraction(df):
    """
    Apply exit number extraction using both address and label columns.
    Also performs OCR quality assessment and flagging.
    """
    print("Extracting exit numbers from addresses...")
    
    # Apply exit number extraction using both columns
    df['Exit_Number'] = df.apply(lambda row: extract_exit_number(
        row['address_standardized_OFF_parenthesis'], 
        row.get('label', None)
    ), axis=1)
    
    # Report extraction statistics
    total_rows = len(df)
    exits_found = df['Exit_Number'].notna().sum()
    
    print(f"Exit number extraction results:")
    print(f"Total rows: {total_rows}")
    print(f"Exit numbers extracted: {exits_found}")
    print(f"Success rate: {(exits_found / total_rows * 100):.1f}%")
    
    # Ensure Flagged and Flag_Reason columns exist
    if 'Flagged' not in df.columns:
        df['Flagged'] = False
    if 'Flag_Reason' not in df.columns:
        df['Flag_Reason'] = ''
    
    # Apply unclear OCR detection and flagging - only for Exit type addresses
    print("Performing OCR quality assessment...")
    df['Is_Unclear_OCR'] = df.apply(lambda row: is_unclear_ocr_address(
        row['address_standardized_OFF_parenthesis'], 
        row['Address_Type']
    ), axis=1)
    
    unclear_mask = df['Is_Unclear_OCR']
    df.loc[unclear_mask, 'Flagged'] = True
    df.loc[unclear_mask, 'Flag_Reason'] = 'unclear address_standardized_OFF_parenthesis'
    
    exit_type_count = (df['Address_Type'] == 'Exit').sum()
    unclear_flagged = (df['Is_Unclear_OCR'] & (df['Address_Type'] == 'Exit')).sum()
    
    print(f"OCR quality assessment results:")
    print(f"Total Exit type rows checked: {exit_type_count}")
    print(f"Exit type rows flagged as unclear: {unclear_flagged}")
    
    # Report pattern statistics
    ex_pattern_count = df['address_standardized_OFF_parenthesis'].str.contains(r'\bEx\s+\d+', case=False, na=False).sum()
    x_pattern_count = df['address_standardized_OFF_parenthesis'].str.contains(r'\sX\s+\d+', case=False, na=False).sum()
    print(f"'Ex' pattern addresses found: {ex_pattern_count}")
    print(f"'X' pattern addresses found: {x_pattern_count}")
    
    return df

def extract_single_road(road_text):
    """
    Helper function to extract a single road from text
    """
    if not road_text or road_text.strip() == '':
        return ''
    
    road_text = road_text.strip()
    
    # Priority patterns - highways and numbered routes first
    highway_patterns = [
        r'\b(Hwy\s+\d+(?:\s+[NSEW])?)',          # Hwy 67, Hwy 65 W
        r'\b(US\s+\d+)',                         # US 101
        r'\b(CA\s+\d+(?:-\d+)?)',               # CA 152, CA 29-175
        r'\b(I-\d+(?:-\d+)?)',                  # I-15, I-15-84
        r'\b(SR\s+\d+)',                        # SR 99
        r'\b(UT\s+\d+)',                        # UT routes
        r'\b(NV\s+\d+)',                        # NV routes
        r'\b(AZ\s+\d+)',                        # AZ routes
    ]
    
    # Check for highway patterns first
    for pattern in highway_patterns:
        match = re.search(pattern, road_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Pattern for abbreviated roads with numbers (like "Rd 4", "St 5") - check BEFORE numbered streets
    abbrev_road_pattern = r'\b((?:Rd|St|Ave|Blvd|Dr|Ln|Way|Pkwy)\s+\w+)\b'
    abbrev_match = re.search(abbrev_road_pattern, road_text, re.IGNORECASE)
    if abbrev_match:
        return abbrev_match.group(1).strip()
    
    # Pattern for numbered streets/avenues (like "4th St", "12th Ave")
    numbered_street_pattern = r'\b(\d+(?:st|nd|rd|th)\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard))\b'
    numbered_match = re.search(numbered_street_pattern, road_text, re.IGNORECASE)
    if numbered_match:
        return numbered_match.group(1).strip()
    
    # Pattern for named streets/roads (like "Main St", "Riverford Rd")
    street_pattern = r'\b([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway)\b'
    street_match = re.search(street_pattern, road_text, re.IGNORECASE)
    if street_match:
        street_name = street_match.group(1).strip()
        suffix = street_match.group(2).strip()
        return f"{street_name} {suffix}"
    
    # If no specific pattern found, try to extract meaningful content
    # Clean up common non-essential words
    exclude_words = {'exit', 'jct', 'junction', 'at', 'near', 'and', 'the', 'on', 'off', 'to', 'from'}
    
    # Split into words and filter
    words = re.findall(r'\b\w+\b', road_text)
    filtered_words = [word for word in words if word.lower() not in exclude_words and word.strip()]
    
    if filtered_words:
        # Return the full filtered content for short cases (like single names)
        if len(filtered_words) <= 2:
            return ' '.join(filtered_words)
        # For longer cases, take the first 2 words
        else:
            return ' '.join(filtered_words[:2])
    
    return ''

def extract_road_info_fixed(address):
    """
    Extract main road and secondary road information from address text.
    Places main road in Main_Road and secondary road in Secondary_Road.
    If only one road exists, puts it in Main_Road and leaves Secondary_Road blank.
    """
    if pd.isna(address) or address == '':
        return '', ''
    
    # Clean the address - remove extra spaces and convert to string
    address = str(address).strip()
    
    # Initialize output variables
    main_road = ''
    secondary_road = ''
    
    # Handle hyphenated roads first (like CA 29-175)
    hyphen_pattern = r'\b((?:CA|US|I-|Hwy|SR)\s*\d+[-]\d+)\b'
    hyphen_match = re.search(hyphen_pattern, address, re.IGNORECASE)
    if hyphen_match and '&' not in address:
        main_road = hyphen_match.group(1).strip()
        return main_road, secondary_road
    
    # Pattern for roads with & separator (two roads)
    if '&' in address:
        parts = address.split('&', 1)  # Split only on first &
        first_part = parts[0].strip()
        second_part = parts[1].strip()
        
        # Extract main road from first part
        main_road = extract_single_road(first_part)
        
        # Extract secondary road from second part
        secondary_road = extract_single_road(second_part)
        
    else:
        # Single road - extract main road only
        main_road = extract_single_road(address)
    
    return main_road, secondary_road

def apply_road_extraction(df):
    """
    Apply road information extraction to the DataFrame.
    Creates Main_Road and Secondary_Road columns.
    """
    print("Extracting road information from addresses...")
    
    # Apply the function to extract road information
    road_info = df['address_standardized_OFF_parenthesis'].apply(extract_road_info_fixed)
    
    # Update the columns with the extraction results
    df['Main_Road'] = [info[0] for info in road_info]
    df['Secondary_Road'] = [info[1] for info in road_info]
    
    # Report extraction statistics
    main_road_count = (df['Main_Road'] != '').sum()
    secondary_road_count = (df['Secondary_Road'] != '').sum()
    
    print(f"Road extraction complete!")
    print(f"Records with main road extracted: {main_road_count}")
    print(f"Records with secondary road extracted: {secondary_road_count}")
    
    return df

def clean_chain_name(chain_name):
    """
    Clean chain names based on specified rules and additional patterns
    """
    if pd.isna(chain_name):
        return chain_name
    
    # Convert to string and strip whitespace
    cleaned = str(chain_name).strip()
    
    # Convert to lowercase for processing
    cleaned_lower = cleaned.lower()
    
    # Apply specific rules mentioned by user
    if cleaned_lower.startswith('bp-'):
        return 'bp'
    elif cleaned_lower.startswith('shell_'):
        return 'shell'
    elif 'circle_k' in cleaned_lower and '_' in cleaned_lower:
        return 'circle_k'
    elif cleaned_lower == '66gas':
        return '66 gas'
    elif 'gulf_oil' in cleaned_lower:
        return 'gulf oil'
    elif cleaned_lower.startswith('flying-j-') or cleaned_lower == 'flying-j':
        return 'flying j'
    
    # Additional cleaning patterns based on common issues
    # Remove trailing underscores and numbers
    cleaned = re.sub(r'_+\d*$', '', cleaned)
    
    # Remove leading/trailing dashes
    cleaned = re.sub(r'^-+|-+$', '', cleaned)
    
    # Replace underscores with spaces (for general cases)
    cleaned = re.sub(r'_+', ' ', cleaned)
    
    # Replace multiple dashes with single space
    cleaned = re.sub(r'-+', ' ', cleaned)
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Handle specific common gas station chains
    if cleaned_lower in ['76', '76_gas', '76gas']:
        return '76'
    elif cleaned_lower in ['chevron', 'chevron_gas']:
        return 'chevron'
    elif cleaned_lower in ['exxon', 'exxonmobil', 'exxon_mobil']:
        return 'exxon'
    elif cleaned_lower in ['mobil', 'mobil_gas']:
        return 'mobil'
    elif cleaned_lower in ['texaco', 'texaco_gas']:
        return 'texaco'
    elif cleaned_lower in ['arco', 'arco_gas']:
        return 'arco'
    elif cleaned_lower in ['valero', 'valero_gas']:
        return 'valero'
    elif cleaned_lower in ['sunoco', 'sunoco_gas']:
        return 'sunoco'
    elif cleaned_lower in ['citgo', 'citgo_gas']:
        return 'citgo'
    elif cleaned_lower in ['marathon', 'marathon_gas']:
        return 'marathon'
    elif cleaned_lower in ['speedway', 'speedway_gas']:
        return 'speedway'
    elif cleaned_lower in ['wawa', 'wawa_gas']:
        return 'wawa'
    elif cleaned_lower in ['sheetz', 'sheetz_gas']:
        return 'sheetz'
    elif cleaned_lower in ['quicktrip', 'qt', 'quiktrip']:
        return 'quicktrip'
    elif cleaned_lower in ['casey\'s', 'caseys', 'casey_s']:
        return 'casey\'s'
    elif cleaned_lower in ['holiday', 'holiday_gas']:
        return 'holiday'
    elif cleaned_lower in ['kum_go', 'kum go', 'kumgo']:
        return 'kum & go'
    elif cleaned_lower in ['pilot', 'pilot_gas', 'pilot travel center']:
        return 'pilot'
    elif cleaned_lower in ['loves', 'love\'s', 'loves_gas']:
        return 'love\'s'
    elif cleaned_lower in ['ta', 'ta_gas', 'travelcenters']:
        return 'ta TravelCenters Travel Centers'
    elif cleaned_lower in ['petro', 'petro_gas']:
        return 'petro'
    elif cleaned_lower in ['sinclair', 'sinclair_gas']:
        return 'sinclair'
    elif cleaned_lower in ['conoco', 'conoco_gas', 'conocophillips']:
        return 'conoco'
    elif cleaned_lower in ['phillips_66', 'phillips66', 'phillips 66']:
        return 'phillips 66'
    
    return cleaned

def process_truck_stops_data():
    """
    Process the TruckStopsServices.csv file to clean chain names.
    This function loads, cleans, and saves the truck stops data separately.
    """
    print("Processing TruckStopsServices data...")
    
    # Load the truck stops dataset
    truck_stops_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\TruckStopsServices.csv'
    df_truck_stops = pd.read_csv(truck_stops_path)
    
    print(f"TruckStopsServices data loaded with shape: {df_truck_stops.shape}")
    
    # Check if Chain column exists
    if 'Chain' not in df_truck_stops.columns:
        print("Warning: 'Chain' column not found in TruckStopsServices data")
        print(f"Available columns: {list(df_truck_stops.columns)}")
        return df_truck_stops
    
    # Show original chain statistics
    original_unique = df_truck_stops['Chain'].nunique()
    print(f"Original unique chain values: {original_unique}")
    
    # Apply chain name cleaning
    print("Cleaning chain names...")
    df_truck_stops['Chain_cleaned'] = df_truck_stops['Chain'].apply(clean_chain_name)
    
    # Show cleaning results
    cleaned_unique = df_truck_stops['Chain_cleaned'].nunique()
    print(f"Cleaned unique chain values: {cleaned_unique}")
    print(f"Reduction in unique values: {original_unique - cleaned_unique}")
    
    # Show rows where Chain was actually modified
    modified_rows = df_truck_stops[df_truck_stops['Chain'] != df_truck_stops['Chain_cleaned']][['Chain', 'Chain_cleaned']].drop_duplicates()
    if len(modified_rows) > 0:
        print(f"\nChain names that were modified ({len(modified_rows)} unique changes):")
        for _, row in modified_rows.head(10).iterrows():  # Show first 10 changes
            print(f"  '{row['Chain']}' -> '{row['Chain_cleaned']}'")
        if len(modified_rows) > 10:
            print(f"  ... and {len(modified_rows) - 10} more changes")
    
    # Replace the original Chain column with the cleaned version
    df_truck_stops['Chain'] = df_truck_stops['Chain_cleaned']
    df_truck_stops.drop('Chain_cleaned', axis=1, inplace=True)
    
    # Show top chains after cleaning
    print(f"\nTop 10 most common chains after cleaning:")
    top_chains = df_truck_stops['Chain'].value_counts().head(10)
    for chain, count in top_chains.items():
        print(f"  {chain}: {count}")
    
    # Create output directory if it doesn't exist
    output_dir = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Processed_Intermediate'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the cleaned truck stops data
    output_path = os.path.join(output_dir, 'scraped_4_7.csv')
    df_truck_stops.to_csv(output_path, index=False)
    print(f"Cleaned TruckStopsServices data saved to: {output_path}")
    
    return df_truck_stops

def process_add_1_workflow(df_main, df_truck_stops):
    """
    Process the Add_1 workflow which combines and filters both datasets.
    Performs state filtering and manual corrections.
    """
    print("Processing Add_1 workflow...")
    
    # Filter both dataframes to include only CA, UT, NV, and AZ states
    states_to_keep = ['CA', 'UT', 'NV', 'AZ']
    
    print(f"Filtering main dataset for states: {states_to_keep}")
    original_main_count = len(df_main)
    df_main_filtered = df_main[df_main['state'].isin(states_to_keep)]
    filtered_main_count = len(df_main_filtered)
    print(f"Main dataset: {original_main_count} -> {filtered_main_count} rows ({filtered_main_count/original_main_count*100:.1f}% retained)")
    
    print(f"Filtering truck stops dataset for states: {states_to_keep}")
    original_truck_count = len(df_truck_stops)
    
    # Check if truck stops dataset has 'State' or 'state' column
    state_column = None
    if 'State' in df_truck_stops.columns:
        state_column = 'State'
    elif 'state' in df_truck_stops.columns:
        state_column = 'state'
    else:
        print("Warning: No 'State' or 'state' column found in truck stops dataset")
        print(f"Available columns: {list(df_truck_stops.columns)}")
        df_truck_stops_filtered = df_truck_stops  # Keep all data if no state column
        filtered_truck_count = len(df_truck_stops_filtered)
    
    if state_column:
        df_truck_stops_filtered = df_truck_stops[df_truck_stops[state_column].isin(states_to_keep)]
        filtered_truck_count = len(df_truck_stops_filtered)
        print(f"Truck stops dataset: {original_truck_count} -> {filtered_truck_count} rows ({filtered_truck_count/original_truck_count*100:.1f}% retained)")
    
    # Drop specific columns from truck stops dataset
    columns_to_drop = [
        "Hours of Operation", 
        "# of Parking Spots", 
        "# of Reserved Parking Spots", 
        "# of Paid Parking Spots", 
        "# of Fuel Lanes", 
        "# of Showers", 
        "# of Truck Service Bays", 
        "Unleaded", 
        "Diesel", 
        "Bulk Def", 
        "Propane", 
        "# of Men's Showers",
        "href"
    ]
    
    # Filter columns to only drop those that actually exist
    existing_columns_to_drop = [col for col in columns_to_drop if col in df_truck_stops_filtered.columns]
    if existing_columns_to_drop:
        print(f"Dropping {len(existing_columns_to_drop)} columns from truck stops dataset: {existing_columns_to_drop}")
        df_truck_stops_filtered = df_truck_stops_filtered.drop(columns=existing_columns_to_drop)
    else:
        print("No specified columns found to drop from truck stops dataset")
    
    # Make manual correction for specific address pattern
    print("Applying manual corrections...")
    mask = df_main_filtered['address_standardized_ON_parenthesis'] == "( MM 30 ) & NV 373"
    correction_count = mask.sum()
    
    if correction_count > 0:
        print(f"Found {correction_count} rows where address_standardized_ON_parenthesis = '( MM 30 ) & NV 373'")
        print("Setting Secondary_Road to 'NV 373' for these rows")
        df_main_filtered.loc[mask, 'Secondary_Road'] = "NV 373"
    else:
        print("No rows found matching the correction pattern")
    
    # Drop the original 'address' column from main dataset if it exists
    if 'address' in df_main_filtered.columns:
        print("Dropping original 'address' column from main dataset")
        df_main_filtered = df_main_filtered.drop(columns=['address'])
    
    return df_main_filtered, df_truck_stops_filtered

def extract_road_and_exit_info(row):
    """
    Extract secondary and tertiary road and exit information from complex address strings,
    specifically tailored to the patterns observed in the actual data.
    
    This version preserves any existing values in the relevant columns.
    
    Parameters:
        row: DataFrame row containing address_standardized_OFF_parenthesis and possibly existing values
        
    Returns:
        Dictionary with Exit_Number_2, Exit_Number_3, Secondary_Road, and Tertiary_Road.
    """
    # Initialize with existing values from the row (or None if they don't exist)
    result = {
        'Exit_Number_2': row.get('Exit_Number_2'), 
        'Exit_Number_3': row.get('Exit_Number_3'),
        'Secondary_Road': row.get('Secondary_Road'),
        'Tertiary_Road': row.get('Tertiary_Road')
    }
    
    # Get the address string
    address_string = row['address_standardized_OFF_parenthesis']
    
    # Skip processing if no address or no slash
    if pd.isna(address_string) or not isinstance(address_string, str) or '/' not in address_string:
        return result
    
    # Split the address by '/'
    parts = [part.strip() for part in address_string.split('/')]
    
    # Process second part (if exists)
    if len(parts) > 1:
        second_part = parts[1]
        
        # More flexible road pattern - look for common highway prefixes
        if result['Secondary_Road'] is None:  # Only update if no existing value
            road_match = re.search(r'\b(I|US|SR|UT|CA|NV|AZ|NM)[-\s]?(\d+)', second_part)
            if road_match:
                prefix = road_match.group(1)
                number = road_match.group(2)
                result['Secondary_Road'] = f"{prefix}-{number}"
        
        if result['Exit_Number_2'] is None:  # Only update if no existing value
            # Try to match "Exit 123", "X 123", or "Xt 123" pattern first
            exit_match = re.search(r'[XE](?:xit|t)?\s*(\d+)', second_part)
            if exit_match:
                result['Exit_Number_2'] = exit_match.group(1)
            else:
                # If no explicit exit, just look for any number
                num_match = re.search(r'\b(\d+)\b', second_part)
                if num_match:
                    result['Exit_Number_2'] = num_match.group(1)
    
    # Process third part (if exists)
    if len(parts) > 2:
        third_part = parts[2]
        
        # More flexible road pattern
        if result['Tertiary_Road'] is None:  # Only update if no existing value
            road_match = re.search(r'\b(I|US|SR|UT|CA|NV|AZ|NM)[-\s]?(\d+)', third_part)
            if road_match:
                prefix = road_match.group(1)
                number = road_match.group(2)
                result['Tertiary_Road'] = f"{prefix}-{number}"
        
        if result['Exit_Number_3'] is None:  # Only update if no existing value
            # Try to match exit pattern first
            exit_match = re.search(r'[XE](?:xit|t)?\s*(\d+)', third_part)
            if exit_match:
                result['Exit_Number_3'] = exit_match.group(1)
            else:
                # If no explicit exit, look for any number
                num_match = re.search(r'\b(\d+)\b', third_part)
                if num_match:
                    result['Exit_Number_3'] = num_match.group(1)
    
    return result

def extract_secondary_road(row):
    """Extract Secondary_Road while preserving existing data"""
    # If there's already a value, keep it
    if pd.notna(row.get('Secondary_Road')):
        return row['Secondary_Road']
        
    address = row['address_standardized_OFF_parenthesis']
    if pd.isna(address) or '/' not in address:
        return None
    
    parts = address.split('/')
    if len(parts) < 2:
        return None
    
    second_part = parts[1].strip()
    # Look for road pattern (I-80, UT 201, etc.)
    road_match = re.search(r'\b(I|US|SR|UT|CA|NV|AZ|NM)[-\s]?(\d+)', second_part)
    if road_match:
        prefix = road_match.group(1)
        number = road_match.group(2)
        return f"{prefix}-{number}"
    
    return None

def extract_exit_number_2(row):
    """Extract Exit_Number_2 while preserving existing data"""
    # If there's already a value, keep it
    if pd.notna(row.get('Exit_Number_2')):
        return row['Exit_Number_2']
        
    address = row['address_standardized_OFF_parenthesis']
    if pd.isna(address) or '/' not in address:
        return None
    
    parts = address.split('/')
    if len(parts) < 2:
        return None
    
    second_part = parts[1].strip()
    # Look for exit pattern - now includes Xt as well
    exit_match = re.search(r'[XE](?:xit|t)?\s*(\d+)', second_part)
    if exit_match:
        return exit_match.group(1)
    
    # If no explicit exit marker, look for any number
    num_match = re.search(r'\b(\d+)\b', second_part)
    if num_match:
        return num_match.group(1)
    
    return None

def extract_tertiary_road(row):
    """Extract Tertiary_Road while preserving existing data"""
    # If there's already a value, keep it
    if pd.notna(row.get('Tertiary_Road')):
        return row['Tertiary_Road']
        
    address = row['address_standardized_OFF_parenthesis']
    if pd.isna(address) or '/' not in address:
        return None
    
    parts = address.split('/')
    if len(parts) < 3:
        return None
    
    third_part = parts[2].strip()
    # Look for road pattern
    road_match = re.search(r'\b(I|US|SR|UT|CA|NV|AZ|NM)[-\s]?(\d+)', third_part)
    if road_match:
        prefix = road_match.group(1)
        number = road_match.group(2)
        return f"{prefix}-{number}"
    
    return None

def process_add_1_5_workflow(df_main, df_truck_stops):
    """
    Process the Add_1_5 workflow which performs advanced address parsing
    to extract secondary and tertiary road/exit information.
    """
    print("Processing Add_1_5 workflow - Advanced address parsing...")
    
    # Ensure all necessary columns exist
    for col in ['Exit_Number_2', 'Exit_Number_3', 'Secondary_Road', 'Tertiary_Road']:
        if col not in df_main.columns:
            df_main[col] = None
    
    print("Extracting road and exit information from complex address strings...")
    
    # Apply comprehensive extraction function
    results = df_main.apply(extract_road_and_exit_info, axis=1)
    extracted_df = pd.DataFrame(results.tolist(), index=df_main.index)
    
    # Update df_main using masks - safer approach
    for col in extracted_df.columns:
        mask = extracted_df[col].notna()
        if mask.any():
            df_main.loc[mask, col] = extracted_df.loc[mask, col]
    
    # Apply individual extraction functions for additional coverage
    print("Applying individual extraction functions...")
    
    # Extract Secondary_Road
    secondary_road_series = df_main.apply(extract_secondary_road, axis=1)
    secondary_mask = secondary_road_series.notna()
    if secondary_mask.any():
        df_main.loc[secondary_mask, 'Secondary_Road'] = secondary_road_series[secondary_mask]
    
    # Extract Exit_Number_2
    exit_number_2_series = df_main.apply(extract_exit_number_2, axis=1)
    exit_2_mask = exit_number_2_series.notna()
    if exit_2_mask.any():
        df_main.loc[exit_2_mask, 'Exit_Number_2'] = exit_number_2_series[exit_2_mask]
    
    # Extract Tertiary_Road
    tertiary_road_series = df_main.apply(extract_tertiary_road, axis=1)
    tertiary_mask = tertiary_road_series.notna()
    if tertiary_mask.any():
        df_main.loc[tertiary_mask, 'Tertiary_Road'] = tertiary_road_series[tertiary_mask]
    
    # Clean Exit_Number_2 to remove decimal points
    if 'Exit_Number_2' in df_main.columns:
        df_main['Exit_Number_2'] = df_main['Exit_Number_2'].astype(str).str.replace('.0', '', regex=False)
        # Replace 'nan' strings with actual NaN
        df_main['Exit_Number_2'] = df_main['Exit_Number_2'].replace('nan', pd.NA)
    
    # Report extraction statistics
    print(f"Advanced address parsing complete!")
    print(f"Rows with Exit_Number_2: {df_main['Exit_Number_2'].notna().sum()}")
    print(f"Rows with Secondary_Road: {df_main['Secondary_Road'].notna().sum()}")
    print(f"Rows with Exit_Number_3: {df_main['Exit_Number_3'].notna().sum()}")
    print(f"Rows with Tertiary_Road: {df_main['Tertiary_Road'].notna().sum()}")
    
    return df_main, df_truck_stops

def compare_random_rows(dataframe, n=2, columns=None, seed=None, address_type=None):
    """
    Compare random rows from a dataframe.
    
    Parameters:
    -----------
    dataframe : pandas.DataFrame
        The dataframe to sample rows from
    n : int, default 2
        Number of random rows to compare
    columns : list, default None
        List of columns to include in comparison. If None, all columns are used.
    seed : int, default None
        Random seed for reproducibility
    address_type : str or list, default None
        Filter rows by specific address type(s). If None, all address types are considered.
        Can be a single string or a list of address types.
    
    Returns:
    --------
    pandas.DataFrame
        A dataframe with the randomly selected rows
    """
    import numpy as np
    
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    # Filter by address type if specified
    if address_type is not None:
        if 'Address_Type' in dataframe.columns:
            # Handle both single string and list of address types
            if isinstance(address_type, str):
                filtered_df = dataframe[dataframe['Address_Type'] == address_type]
            else:  # Assume it's a list or other iterable
                filtered_df = dataframe[dataframe['Address_Type'].isin(address_type)]
                
            if filtered_df.empty:
                raise ValueError(f"No rows found with address type(s): {address_type}")
        else:
            raise ValueError("'Address_Type' column not found in the dataframe")
    else:
        filtered_df = dataframe
    
    # Randomly sample n rows
    if n > len(filtered_df):
        print(f"Warning: Requested {n} rows but only {len(filtered_df)} rows available. Using all available rows.")
        n = len(filtered_df)
    
    random_indices = np.random.choice(filtered_df.index, size=n, replace=False)
    
    # Get the selected columns or use all if None
    if columns is None:
        columns = dataframe.columns
    
    # Return the sampled rows with the selected columns
    return dataframe.loc[random_indices, columns]

def get_comprehensive_common_words_filter():
    """
    Returns a comprehensive set of common words that should be filtered out
    across all matching algorithms to prevent false matches.
    """
    common_words = {
        # Basic English stop words
        'the', 'of', 'and', 'to', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 'this', 'with',
        'i', 'you', 'it', 'at', 'be', 'or', 'an', 'are', 'as', 'be', 'been', 'by',
        'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'but', 'not', 'all', 'can', 'had', 'her', 'his',
        'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'way', 'may', 'say',
        
        # Symbols and special characters (as words)
        '#', '&', '@', 'and', 'or', 'vs', 'inc', 'llc', 'ltd', 'corp', 'co',
        
        # Business/location related common words
        'gas', 'station', 'service', 'store', 'shop', 'center', 'mart', 'market',
        'fuel', 'food', 'auto', 'car', 'truck', 'travel', 'stop', 'plaza',
        
        # Street types and directionals
        'st', 'street', 'ave', 'avenue', 'blvd', 'boulevard', 'rd', 'road', 'ln', 'lane',
        'dr', 'drive', 'way', 'pkwy', 'parkway', 'hwy', 'highway', 'expwy', 'expressway',
        'ct', 'court', 'cir', 'circle', 'pl', 'place', 'ter', 'terrace', 'trl', 'trail',
        'route', 'rte', 'miles', 'mile', 'mi', 'km', 'exit', 'interchange',
        
        # Directionals
        'n', 's', 'e', 'w', 'north', 'south', 'east', 'west', 'ne', 'nw', 'se', 'sw',
        'northeast', 'northwest', 'southeast', 'southwest', 'northern', 'southern',
        'eastern', 'western',
        
        # Geographic terms
        'city', 'town', 'village', 'county', 'state', 'country', 'usa', 'us', 'america',
        'united', 'states',
        
        # Numbers as words (common ones that might appear in addresses)
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth',
        'ninth', 'tenth', 'hundred', 'thousand',
        
        # Time-related words
        'am', 'pm', 'hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months',
        'year', 'years', 'open', 'close', 'closed',
        
        # Size/quantity descriptors
        'big', 'small', 'large', 'little', 'mini', 'super', 'mega', 'giant', 'express',
        'quick', 'fast', 'speed', 'rapid',
        
        # Common business suffixes/prefixes
        'old', 'new', 'fresh', 'best', 'good', 'great', 'quality', 'family', 'local',
        'discount', 'cheap', 'budget', 'premium', 'deluxe'
    }
    
    return common_words

def clean_ordinal_suffixes(text_str):
    """
    Removes ordinal suffixes from numbers in text.
    Examples: "66th" → "66", "2nd" → "2", "1st" → "1"
    """
    if pd.isna(text_str):
        return ''
    
    # Remove ordinal suffixes from numbers
    cleaned = re.sub(r'(\d+)(?:st|nd|rd|th)\b', r'\1', str(text_str).lower())
    return cleaned

def clean_phone_number(phone_str):
    """Function to clean phone numbers by removing non-numeric characters"""
    if pd.isna(phone_str):
        return ''
    # Extract only digits from the phone number
    digits_only = re.sub(r'\D', '', str(phone_str))
    # If we have at least 7 digits, consider it a valid phone number
    if len(digits_only) >= 7:
        return digits_only
    return ''

def clean_zip_code(zip_str):
    """Function to clean ZIP codes by ensuring they're strings and removing extra spaces"""
    if pd.isna(zip_str):
        return ''
    # Convert to string and strip any leading/trailing spaces
    zip_clean = str(zip_str).strip()
    # Take only the first 5 digits for US ZIP codes
    zip_clean = re.sub(r'[^0-9]', '', zip_clean)[:5]
    return zip_clean

def clean_city(city_str):
    """Function to clean and tokenize city names"""
    if pd.isna(city_str):
        return []
    
    # Convert to lowercase, remove special characters
    city_clean = re.sub(r'[^a-zA-Z0-9\s]', '', str(city_str).lower()).strip()
    
    # Remove ordinal suffixes
    city_clean = clean_ordinal_suffixes(city_clean)
    
    # Split into words and filter using centralized common words filter
    words = city_clean.split()
    common_words = get_comprehensive_common_words_filter()
    
    # Filter out common words and keep meaningful city name parts
    filtered_words = []
    for word in words:
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        if (clean_word not in common_words and 
            len(clean_word) > 1 and 
            not clean_word.isdigit()):
            filtered_words.append(clean_word)
    
    return filtered_words

def extract_exit_numbers_for_matching(exit_str):
    """Function to extract exit numbers from text for matching purposes"""
    if pd.isna(exit_str):
        return []
    
    # Convert to string
    exit_str = str(exit_str)
    
    # Extract numeric portions that might represent exit numbers
    exit_numbers = []
    
    # Find all numbers in the string
    number_matches = re.findall(r'\d+', exit_str)
    exit_numbers.extend(number_matches)
    
    # Special handling for compound exits like "160 EB/164 WB"
    if '/' in exit_str:
        parts = exit_str.split('/')
        for part in parts:
            part_numbers = re.findall(r'\d+', part)
            if part_numbers:
                exit_numbers.extend(part_numbers)
    
    # Remove duplicates
    return list(set(exit_numbers))

def clean_state(state_str):
    """Function to clean state names/abbreviations"""
    if pd.isna(state_str):
        return ''
    # Convert to uppercase and remove spaces/special characters
    return re.sub(r'[^A-Z]', '', str(state_str).upper())

def extract_road_tokens(road_str):
    """Function to extract road identifiers and names"""
    if pd.isna(road_str):
        return set()
    
    road_str = str(road_str).lower()
    tokens = set()
    
    # Extract basic road name with ordinal suffixes cleaned
    basic_name = re.sub(r'[^a-z0-9\s]', ' ', road_str)
    basic_name = clean_ordinal_suffixes(basic_name)
    
    tokens.update(basic_name.split())
    
    # Extract route numbers (e.g., US 60-70, I-10, NV 604)
    route_numbers = re.findall(r'(\d+)(?:\s*-\s*(\d+))?', road_str)
    for match in route_numbers:
        tokens.add(match[0])  # Add first number
        if match[1]:  # Add second number if it exists (e.g., "60-70" → add both "60" and "70")
            tokens.add(match[1])
    
    # Handle interstate notation
    interstate_match = re.search(r'i\s*[-]?\s*(\d+)', road_str)
    if interstate_match:
        tokens.add(interstate_match.group(1))  # Add just the number
    
    # Handle state routes (e.g., "NV 604" → add "604")
    state_route_match = re.search(r'[a-z]{2}\s*[-]?\s*(\d+)', road_str)
    if state_route_match:
        tokens.add(state_route_match.group(1))  # Add just the number
    
    # Handle compound routes with slashes (e.g., "NV 604/574" → add both "604" and "574")
    if '/' in road_str:
        slash_parts = road_str.split('/')
        for part in slash_parts:
            numbers = re.findall(r'\d+', part)
            tokens.update(numbers)
    
    # Filter using centralized common words filter
    words = road_str.split()
    filtered_words = []
    common_words = get_comprehensive_common_words_filter()
    
    for word in words:
        # Remove ordinal suffixes from individual words
        clean_word = clean_ordinal_suffixes(word)
        clean_word = re.sub(r'[^a-z0-9]', '', clean_word)
        
        if (clean_word not in common_words and 
            not (len(clean_word) == 1 and clean_word.isalpha()) and  # Skip single letters like N, S, E, W
            len(clean_word) > 0):  # Skip empty strings
            filtered_words.append(clean_word)
    
    tokens.update(filtered_words)
    
    # Remove common words using centralized filter
    tokens = tokens - common_words
    
    return tokens

def standardize_chain(chain_str):
    """Function to standardize chain names for better matching"""
    if pd.isna(chain_str):
        return set()
    
    chain_str = str(chain_str).lower()
    tokens = set()
    
    # Standard mapping of chain variations to canonical forms
    chain_mappings = {
        'sinclair': ['sinclair', 'sinclair oil'],
        'travelcenters': ['ta', 'taexpress', 'talogo'],
        'eleven': ['11', '7-11', 'seven', 'eleven', '7 eleven', '7eleven'],
        "love's": ['love', 'loves', "love's"],
        'speedway': ['speedway', 'speedwaygas'],
        'chevron': ['chevron'],
        'flying j': ['flying j'],
        'tesoro': ['tesoro'],
        'shell': ['shell'],
        'texaco': ['texaco'],
        'exxon': ['exxon'],
        'pilot': ['pilot'],
        'conoco': ['conoco'],
        'shamrock': ['shamrock'],
        'valero': ['valero'],
        'bp': ['bp'],
        'mobil': ['mobil'],
        'circle k': ['circle_k', 'circle k'],
        'citgo': ['citgo'],
        '76': ['76', 'union 76']
    }
    
    # Add the original chain text
    tokens.add(chain_str)
    
    # Add individual words
    words = re.sub(r'[^a-z0-9\s]', ' ', chain_str).split()
    tokens.update(words)
    
    # Add known variations based on mapping
    for canonical, variations in chain_mappings.items():
        for variation in variations:
            if variation in chain_str:
                tokens.add(canonical)
                tokens.update(variations)
    
    # Specific handling for "7-Eleven" / "Eleven" because it appears in different formats
    if any(term in chain_str for term in ['11', 'seven', 'eleven']):
        tokens.update(['11', '7-11', 'seven', 'eleven', '7 eleven', '7eleven'])
    
    return tokens

def extract_label_words(label_str):
    """Function to extract meaningful words from labels"""
    if pd.isna(label_str):
        return set()
    
    # Convert to lowercase and remove special characters
    clean_label = re.sub(r'[^a-z0-9\s]', ' ', str(label_str).lower())
    
    # Remove ordinal suffixes using centralized function
    clean_label = clean_ordinal_suffixes(clean_label)
    
    # Split into words
    words = clean_label.split()
    
    # Use centralized common words filter
    common_words = get_comprehensive_common_words_filter()
    
    meaningful_words = set()
    for word in words:
        # Clean and remove ordinal suffixes from individual words
        clean_word = clean_ordinal_suffixes(word)
        clean_word = re.sub(r'[^a-z0-9]', '', clean_word)
        
        # Skip if it's a common word, single digit, or too short
        if (clean_word not in common_words and 
            not (clean_word.isdigit() and len(clean_word) == 1) and 
            len(clean_word) > 1):
            meaningful_words.add(clean_word)
            
            # Handle special case for "7-Eleven" type stores
            if clean_word == '7' and any(eleven_word in words for eleven_word in ['eleven', '11']):
                meaningful_words.add('7-eleven')
            if clean_word == 'loves':
                meaningful_words.add("love's")
    
    return meaningful_words

def str_to_list(str_val):
    """Convert string representations of lists to actual lists"""
    if pd.isna(str_val):
        return []
    try:
        # Try to evaluate the string as a literal Python expression
        return eval(str_val)
    except:
        # If that fails, return an empty list
        return []

def process_add_3_workflow(df_main, df_truck_stops):
    """
    Process the Add_3 workflow which performs comprehensive data matching
    between the main dataset and scraped dataset using 8 different criteria:
    1. Phone number matching
    2. ZIP code matching  
    3. City name matching
    4. Exit number matching
    5. State matching
    6. Road name matching
    7. Chain name matching
    8. Label text matching
    """
    print("Processing Add_3 workflow - Comprehensive data matching...")
    
    # Reset indices to ensure they're sequential
    df_main = df_main.reset_index(drop=True)
    df_truck_stops = df_truck_stops.reset_index(drop=True)
    
    print(f"Main dataset (df1) shape: {df_main.shape}")
    print(f"Scraped dataset (df2) shape: {df_truck_stops.shape}")
    
    # STEP 1: Match by phone number
    print("Step 1: Phone number matching...")
    df_main['phone_scraped_matches_row_ids'] = None
    
    # Clean phone numbers in df_main
    df1_clean_phones = df_main['phone'].apply(clean_phone_number) if 'phone' in df_main.columns else pd.Series([''] * len(df_main))
    
    # Initialize the phone columns to check in df_truck_stops
    phone_columns = ['Phone', 'Phone 2', 'Phone 3', 'Phone 4', 'Phone 5', 'Fax']
    
    # Create cleaned versions of all phone columns in df_truck_stops
    df2_clean_phones = {}
    for col in phone_columns:
        if col in df_truck_stops.columns:
            df2_clean_phones[col] = df_truck_stops[col].apply(clean_phone_number)
        else:
            print(f"Warning: Column '{col}' not found in scraped dataset")
    
    # Match phone numbers and store row IDs
    for i, phone in enumerate(df1_clean_phones):
        if phone:  # If phone number is not empty
            matches = []
            for col, clean_phones in df2_clean_phones.items():
                # Find all rows where this phone number matches
                matching_idx = clean_phones[clean_phones == phone].index.tolist()
                matches.extend(matching_idx)
            
            # Remove duplicates and store the matches
            if matches:
                df_main.at[i, 'phone_scraped_matches_row_ids'] = str(list(set(matches)))
    
    # Count how many rows got matches
    matched_count = df_main['phone_scraped_matches_row_ids'].notna().sum()
    print(f"Phone number matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 2: Match by ZIP code
    print("Step 2: ZIP code matching...")
    df_main['ZIP_scraped_matches_row_ids'] = None
    
    # Clean ZIP codes in df_main
    df1_clean_zips = df_main['zip_code'].apply(clean_zip_code) if 'zip_code' in df_main.columns else pd.Series([''] * len(df_main))
    
    # Clean ZIP codes in df_truck_stops
    df2_clean_zips = df_truck_stops['Postal Code'].apply(clean_zip_code) if 'Postal Code' in df_truck_stops.columns else pd.Series([''] * len(df_truck_stops))
    
    # If Postal Code column doesn't exist, alert the user
    if 'Postal Code' not in df_truck_stops.columns:
        print("Warning: 'Postal Code' column not found in scraped dataset")
    
    # Match ZIP codes and store row IDs
    for i, zip_code in enumerate(df1_clean_zips):
        if zip_code:  # If ZIP code is not empty
            # Find all rows where this ZIP code matches
            matching_idx = df2_clean_zips[df2_clean_zips == zip_code].index.tolist()
            
            # Store the matches
            if matching_idx:
                df_main.at[i, 'ZIP_scraped_matches_row_ids'] = str(matching_idx)
    
    # Count how many rows got matches
    matched_count = df_main['ZIP_scraped_matches_row_ids'].notna().sum()
    print(f"ZIP code matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 3: Match by city name with permissive matching
    print("Step 3: City name matching...")
    df_main['City_scraped_matches_row_ids'] = None
    
    # Clean and tokenize city names in df_main
    df1_city_tokens = df_main['city'].apply(clean_city) if 'city' in df_main.columns else pd.Series([[] for _ in range(len(df_main))])
    df1_major_city_tokens = df_main['major_city'].apply(clean_city) if 'major_city' in df_main.columns else pd.Series([[] for _ in range(len(df_main))])
    
    # Clean and tokenize city names in df_truck_stops
    if 'City' in df_truck_stops.columns:
        df2_city_tokens = df_truck_stops['City'].apply(clean_city)
    else:
        print("Warning: 'City' column not found in scraped dataset")
        df2_city_tokens = pd.Series([[] for _ in range(len(df_truck_stops))])
    
    # Match cities using the permissive criteria
    for i in range(len(df_main)):
        matches = []
        
        # Combine tokens from city and major_city
        all_tokens = set(df1_city_tokens.iloc[i] + df1_major_city_tokens.iloc[i])
        
        # Skip if no tokens to match
        if not all_tokens:
            continue
        
        # For each row in df_truck_stops
        for j, df2_tokens in enumerate(df2_city_tokens):
            # Check for partial matches
            if any(token in df2_tokens for token in all_tokens) or any(token in all_tokens for token in df2_tokens):
                matches.append(j)
        
        # Store the matches
        if matches:
            df_main.at[i, 'City_scraped_matches_row_ids'] = str(matches)
    
    # Count how many rows got matches
    matched_count = df_main['City_scraped_matches_row_ids'].notna().sum()
    print(f"City matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 4: Match by exit number with permissive matching
    print("Step 4: Exit number matching...")
    df_main['Exit_scraped_matches_row_ids'] = None
    
    # Extract exit numbers from all relevant columns in df_main
    exit_columns = ['Exit_Number', 'Exit_From_Address', 'Exit_From_Label', 'Exit_Number_2', 'Exit_Number_3']
    df1_exit_numbers = {}
    
    for col in exit_columns:
        if col in df_main.columns:
            df1_exit_numbers[col] = df_main[col].apply(extract_exit_numbers_for_matching)
        else:
            print(f"Warning: '{col}' column not found in df_main")
    
    # Extract exit numbers from df_truck_stops
    if 'Exit' in df_truck_stops.columns:
        df2_exit_numbers = df_truck_stops['Exit'].apply(extract_exit_numbers_for_matching)
    else:
        print("Warning: 'Exit' column not found in scraped dataset")
        df2_exit_numbers = pd.Series([[] for _ in range(len(df_truck_stops))])
    
    # Match exit numbers
    for i in range(len(df_main)):
        matches = []
        
        # Collect all exit numbers from this df_main row
        all_exit_numbers = []
        for col, exit_nums in df1_exit_numbers.items():
            if i < len(exit_nums):  # Ensure index is in range
                all_exit_numbers.extend(exit_nums.iloc[i])
        
        # Skip if no exit numbers to match
        if not all_exit_numbers:
            continue
        
        # For each row in df_truck_stops
        for j, df2_nums in enumerate(df2_exit_numbers):
            # Check for matches
            if any(num in df2_nums for num in all_exit_numbers):
                matches.append(j)
        
        # Store the matches
        if matches:
            df_main.at[i, 'Exit_scraped_matches_row_ids'] = str(matches)
    
    # Count how many rows got matches
    matched_count = df_main['Exit_scraped_matches_row_ids'].notna().sum()
    print(f"Exit number matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 5: Match by state
    print("Step 5: State matching...")
    df_main['State_scraped_matches_row_ids'] = None
    
    # Clean states in df_main
    df1_clean_states = df_main['state'].apply(clean_state) if 'state' in df_main.columns else pd.Series([''] * len(df_main))
    
    # Clean states in df_truck_stops
    df2_clean_states = df_truck_stops['State'].apply(clean_state) if 'State' in df_truck_stops.columns else pd.Series([''] * len(df_truck_stops))
    
    # If state column doesn't exist in either dataframe, alert the user
    if 'state' not in df_main.columns:
        print("Warning: 'state' column not found in df_main")
    if 'State' not in df_truck_stops.columns:
        print("Warning: 'State' column not found in df_truck_stops")
    
    # Match states and store row IDs
    for i, state in enumerate(df1_clean_states):
        if state:  # If state is not empty
            # Find all rows where this state matches
            matching_idx = df2_clean_states[df2_clean_states == state].index.tolist()
            
            # Store the matches
            if matching_idx:
                df_main.at[i, 'State_scraped_matches_row_ids'] = str(matching_idx)
    
    # Count how many rows got matches
    matched_count = df_main['State_scraped_matches_row_ids'].notna().sum()
    print(f"State matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 6: Match by road name with permissive matching
    print("Step 6: Road name matching...")
    df_main['Road_scraped_matches_row_ids'] = None
    
    # Get road tokens from df_main
    road_columns = ['Main_Road', 'Secondary_Road', 'Tertiary_Road']
    df1_road_tokens = {}
    
    for col in road_columns:
        if col in df_main.columns:
            df1_road_tokens[col] = df_main[col].apply(extract_road_tokens)
        else:
            print(f"Warning: '{col}' column not found in df_main")
    
    # Get road tokens from df_truck_stops
    df2_road_columns = ['Highway', 'Street Address', 'Mailing Address', 'Road Name']
    df2_road_tokens = {}
    
    for col in df2_road_columns:
        if col in df_truck_stops.columns:
            df2_road_tokens[col] = df_truck_stops[col].apply(extract_road_tokens)
        else:
            print(f"Warning: '{col}' column not found in df_truck_stops")
    
    # Match roads and store row IDs
    for i in range(len(df_main)):
        matches = []
        
        # Collect all road tokens from this df_main row
        all_road_tokens = set()
        for col, tokens_series in df1_road_tokens.items():
            if i < len(tokens_series):  # Ensure index is in range
                all_road_tokens.update(tokens_series.iloc[i])
        
        # Skip if no road tokens to match
        if not all_road_tokens:
            continue
        
        # For each row in df_truck_stops
        for j in range(len(df_truck_stops)):
            # Collect all road tokens from this df_truck_stops row
            df2_all_tokens = set()
            for col, tokens_series in df2_road_tokens.items():
                if j < len(tokens_series):  # Ensure index is in range
                    df2_all_tokens.update(tokens_series.iloc[j])
            
            # Check for matches
            if any(token in df2_all_tokens for token in all_road_tokens):
                matches.append(j)
        
        # Store the matches
        if matches:
            df_main.at[i, 'Road_scraped_matches_row_ids'] = str(matches)
    
    # Count how many rows got matches
    matched_count = df_main['Road_scraped_matches_row_ids'].notna().sum()
    print(f"Road name matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 7: Match by gas station chain with permissive matching
    print("Step 7: Chain name matching...")
    df_main['Chain_scraped_matches_row_ids'] = None
    
    # Get chain tokens from df_main
    if 'chain' in df_main.columns:
        df1_chain_tokens = df_main['chain'].apply(standardize_chain)
    else:
        print("Warning: 'chain' column not found in df_main")
        df1_chain_tokens = pd.Series([set() for _ in range(len(df_main))])
    
    # Get chain tokens from df_truck_stops
    if 'Chain' in df_truck_stops.columns:
        df2_chain_tokens = df_truck_stops['Chain'].apply(standardize_chain)
    else:
        print("Warning: 'Chain' column not found in df_truck_stops")
        df2_chain_tokens = pd.Series([set() for _ in range(len(df_truck_stops))])
    
    # Match chains and store row IDs
    for i in range(len(df_main)):
        df1_tokens = df1_chain_tokens.iloc[i]
        
        # Skip if no tokens to match
        if not df1_tokens:
            continue
        
        matches = []
        for j, df2_tokens in enumerate(df2_chain_tokens):
            # Check if any token matches between the two sets
            if df1_tokens.intersection(df2_tokens):
                matches.append(j)
        
        # Store the matches
        if matches:
            df_main.at[i, 'Chain_scraped_matches_row_ids'] = str(matches)
    
    # Count how many rows got matches
    matched_count = df_main['Chain_scraped_matches_row_ids'].notna().sum()
    print(f"Chain matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # STEP 8: Match by label text
    print("Step 8: Label text matching...")
    df_main['Label_scraped_matches_row_ids'] = None
    
    # Get label tokens from df_main
    if 'label' in df_main.columns:
        df1_label_tokens = df_main['label'].apply(extract_label_words)
    else:
        print("Warning: 'label' column not found in df_main")
        df1_label_tokens = pd.Series([set() for _ in range(len(df_main))])
    
    # Get name and chain tokens from df_truck_stops
    if 'name' in df_truck_stops.columns:
        df2_name_tokens = df_truck_stops['name'].apply(extract_label_words)
    else:
        print("Warning: 'name' column not found in df_truck_stops")
        df2_name_tokens = pd.Series([set() for _ in range(len(df_truck_stops))])
    
    if 'Chain' in df_truck_stops.columns:
        df2_chain_tokens_for_label = df_truck_stops['Chain'].apply(extract_label_words)
    else:
        print("Warning: 'Chain' column not found in df_truck_stops")
        df2_chain_tokens_for_label = pd.Series([set() for _ in range(len(df_truck_stops))])
    
    # Match labels to name/chain and store row IDs
    for i in range(len(df_main)):
        df1_tokens = df1_label_tokens.iloc[i]
        
        # Skip if no tokens to match
        if not df1_tokens:
            continue
        
        matches = []
        for j in range(len(df_truck_stops)):
            # Combine name and chain tokens from df_truck_stops
            df2_combined_tokens = df2_name_tokens.iloc[j].union(df2_chain_tokens_for_label.iloc[j])
            
            # Check if any token matches
            if df1_tokens.intersection(df2_combined_tokens):
                matches.append(j)
        
        # Store the matches
        if matches:
            df_main.at[i, 'Label_scraped_matches_row_ids'] = str(matches)
    
    # Count how many rows got matches
    matched_count = df_main['Label_scraped_matches_row_ids'].notna().sum()
    print(f"Label text matching complete: {matched_count} rows in df_main have matches in df_truck_stops")
    
    # FINAL STEP: Summarize matches and create combined matches column
    print("Finalizing matches and creating summary...")
    
    # Convert string representations of lists to actual lists
    match_columns = [
        'phone_scraped_matches_row_ids',
        'ZIP_scraped_matches_row_ids',
        'City_scraped_matches_row_ids',
        'Exit_scraped_matches_row_ids',
        'State_scraped_matches_row_ids',
        'Road_scraped_matches_row_ids',
        'Chain_scraped_matches_row_ids',
        'Label_scraped_matches_row_ids'
    ]
    
    for col in match_columns:
        if col in df_main.columns:
            df_main[col] = df_main[col].apply(str_to_list)
    
    # Create a new column that combines all matches
    df_main['all_matches'] = df_main.apply(
        lambda row: list(set().union(*[row[col] for col in match_columns if col in df_main.columns and isinstance(row[col], list)])),
        axis=1
    )
    
    # Count matches by type
    match_summary = {
        'Total rows in df_main': len(df_main),
        'Total rows in df_truck_stops': len(df_truck_stops)
    }
    
    for col in match_columns:
        if col in df_main.columns:
            match_summary[f'Rows with {col}'] = sum(df_main[col].apply(lambda x: len(x) > 0))
    
    match_summary['Rows with any match'] = sum(df_main['all_matches'].apply(lambda x: len(x) > 0))
    match_summary['Rows with no matches'] = sum(df_main['all_matches'].apply(lambda x: len(x) == 0))
    
    # Calculate percentage of rows matched
    match_summary['Percentage matched'] = (match_summary['Rows with any match'] / match_summary['Total rows in df_main']) * 100
    
    # Display the summary
    print("\n" + "="*50)
    print("MATCHING SUMMARY:")
    print("="*50)
    for key, value in match_summary.items():
        if 'Percentage' in key:
            print(f"{key}: {value:.2f}%")
        else:
            print(f"{key}: {value}")
    
    return df_main, df_truck_stops

def safe_eval(s):
    """
    Function to safely evaluate string representation of lists.
    Used for parsing match column data.
    """
    import ast
    try:
        if isinstance(s, str):
            return ast.literal_eval(s)
        return s
    except (ValueError, SyntaxError):
        return []

def determine_match_success(row):
    """
    Function to determine match success rate based on hierarchical sequence:
    1. ZIP/State
    2. City/Exit  
    3. Road
    4. Label
    5. Chain
    """
    # Start with ZIP/State
    match_set = set()
    match_set.update(row['ZIP_scraped_matches_row_ids_parsed'])
    match_set.update(row['State_scraped_matches_row_ids_parsed'])
    
    if not match_set:
        return "0/6 successful match"
    
    # Check City/Exit
    city_exit_set = set()
    city_exit_set.update(row['City_scraped_matches_row_ids_parsed'])
    city_exit_set.update(row['Exit_scraped_matches_row_ids_parsed'])
    
    # Find common elements between match_set and city_exit_set
    match_set = match_set.intersection(city_exit_set) if city_exit_set else match_set
    
    if not match_set:
        return "2/6 successful match"  # Only ZIP/State matched
    
    # Check Road
    road_set = set(row['Road_scraped_matches_row_ids_parsed'])
    match_set = match_set.intersection(road_set) if road_set else match_set
    
    if not match_set:
        return "4/6 successful match"  # ZIP/State and City/Exit matched
    
    # Check Label
    label_set = set(row['Label_scraped_matches_row_ids_parsed'])
    match_set = match_set.intersection(label_set) if label_set else match_set
    
    if not match_set:
        return "5/6 successful match"  # ZIP/State, City/Exit, and Road matched
    
    # Finally check Chain
    chain_set = set(row['Chain_scraped_matches_row_ids_parsed'])
    match_set = match_set.intersection(chain_set) if chain_set else match_set
    
    if not match_set:
        return "6/6 successful match"  # ZIP/State, City/Exit, Road, and Label matched
    
    return "7/6 successful match"  # All components matched

def process_add_4_workflow(df_main, df_truck_stops):
    """
    Process the Add_4 workflow which performs comprehensive analysis
    of matching results from Add_3, including:
    1. Phone number match analysis
    2. Match success hierarchy analysis using address components
    3. Success rate classification
    """
    print("Processing Add_4 workflow - Match success analysis...")
    
    print(f"Total rows in dataset: {len(df_main)}")
    
    # 1️⃣ Phone number match analysis
    print("Step 1: Phone number match analysis...")
    
    # Apply the safe_eval function to phone_scraped_matches_row_ids column
    df_main['phone_matches'] = df_main['phone_scraped_matches_row_ids'].apply(safe_eval)
    
    # Check if the list is empty or not
    df_main['has_phone_match'] = df_main['phone_matches'].apply(lambda x: len(x) > 0)
    
    # Count rows with and without phone matches
    rows_with_phone = df_main['has_phone_match'].sum()
    rows_without_phone = len(df_main) - rows_with_phone
    
    # Calculate percentages
    total_rows = len(df_main)
    percent_with_phone = (rows_with_phone / total_rows) * 100
    percent_without_phone = (rows_without_phone / total_rows) * 100
    
    print(f"Rows with phone matches: {rows_with_phone} ({percent_with_phone:.2f}%)")
    print(f"Rows without phone matches: {rows_without_phone} ({percent_without_phone:.2f}%)")
    print(f"Total rows: {total_rows}")
    
    # 2️⃣ Match success using address components
    print("Step 2: Address component match analysis...")
    
    # Apply safe_eval to all match columns
    match_columns = [
        'ZIP_scraped_matches_row_ids',
        'State_scraped_matches_row_ids', 
        'City_scraped_matches_row_ids',
        'Exit_scraped_matches_row_ids',
        'Road_scraped_matches_row_ids',
        'Label_scraped_matches_row_ids',
        'Chain_scraped_matches_row_ids'
    ]
    
    for col in match_columns:
        if col in df_main.columns:
            df_main[col + '_parsed'] = df_main[col].apply(safe_eval)
        else:
            print(f"Warning: Column '{col}' not found in dataset")
            df_main[col + '_parsed'] = [[]] * len(df_main)
    
    # Apply the hierarchical matching function to each row
    print("Determining match success rates using hierarchical approach...")
    df_main['Success_Match_Rate'] = df_main.apply(determine_match_success, axis=1)
    
    # Add Phone Success Match Rate column
    df_main['Phone_Success_Match_Rate'] = df_main['has_phone_match']
    
    # Show distribution of match success rates
    success_counts = df_main['Success_Match_Rate'].value_counts().sort_index()
    print("\nDistribution of Match Success Rates:")
    for rate, count in success_counts.items():
        percentage = (count / len(df_main) * 100)
        print(f"  {rate}: {count} rows ({percentage:.2f}%)")
    
    # Define success level descriptions for better understanding
    success_levels = {
        '0/6 successful match': 'No match',
        '2/6 successful match': 'ZIP/State only',
        '4/6 successful match': 'ZIP/State + City/Exit',
        '5/6 successful match': 'ZIP/State + City/Exit + Road',
        '6/6 successful match': 'ZIP/State + City/Exit + Road + Label',
        '7/6 successful match': 'All components'
    }
    
    print("\nMatch Success Level Descriptions:")
    for level, description in success_levels.items():
        if level in success_counts.index:
            count = success_counts[level]
            percentage = (count / len(df_main) * 100)
            print(f"  {description}: {count} rows ({percentage:.2f}%)")
    
    # Analyze relationship between phone matches and address component success rates
    print("\nAnalyzing relationship between phone matches and address component success...")
    
    # Create crosstab analysis
    phone_vs_component = pd.crosstab(df_main['has_phone_match'], df_main['Success_Match_Rate'], normalize='index') * 100
    
    print("\nPercentage of Success Match Rates by Phone Match Status:")
    print("=" * 60)
    for phone_status in [False, True]:
        status_label = "With Phone Match" if phone_status else "Without Phone Match"
        print(f"\n{status_label}:")
        if phone_status in phone_vs_component.index:
            for success_rate in phone_vs_component.columns:
                percentage = phone_vs_component.loc[phone_status, success_rate]
                if percentage > 0:
                    description = success_levels.get(success_rate, success_rate)
                    print(f"  {description}: {percentage:.2f}%")
    
    # Summary statistics
    print(f"\nSummary Statistics:")
    print(f"  Total unique success rates: {df_main['Success_Match_Rate'].nunique()}")
    print(f"  Most common success rate: {df_main['Success_Match_Rate'].mode().iloc[0]}")
    print(f"  Phone match availability: {percent_with_phone:.1f}% have phone matches")
    
    # Clean up temporary columns (keep parsed columns for potential future use)
    print("Cleaning up temporary analysis columns...")
    if 'phone_matches' in df_main.columns:
        df_main.drop('phone_matches', axis=1, inplace=True)
    
    print("Match success analysis completed!")
    
    return df_main, df_truck_stops

def process_add_2_workflow(df_main, df_truck_stops):
    """
    Process the Add_2 workflow which performs data type conversions,
    manual corrections, and data quality improvements.
    """
    print("Processing Add_2 workflow - Data type conversions and manual corrections...")
    
    # Convert Exit_Number_2 and Exit_Number_3 to nullable integer, then to string
    print("Converting exit number columns to proper data types...")
    
    if 'Exit_Number_2' in df_main.columns:
        # Convert to numeric first, then to nullable integer, then to string
        df_main['Exit_Number_2'] = pd.to_numeric(df_main['Exit_Number_2'], errors='coerce', downcast='integer').astype('Int64')
        df_main['Exit_Number_2'] = df_main['Exit_Number_2'].astype(str)
        # Replace 'nan' strings with actual NaN
        df_main['Exit_Number_2'] = df_main['Exit_Number_2'].replace(['nan', '<NA>', 'None'], pd.NA)
    
    if 'Exit_Number_3' in df_main.columns:
        # Convert to numeric first, then to nullable integer, then to string
        df_main['Exit_Number_3'] = pd.to_numeric(df_main['Exit_Number_3'], errors='coerce', downcast='integer').astype('Int64')
        df_main['Exit_Number_3'] = df_main['Exit_Number_3'].astype(str)
        # Replace 'nan' strings with actual NaN
        df_main['Exit_Number_3'] = df_main['Exit_Number_3'].replace(['nan', '<NA>', 'None'], pd.NA)
    
    # Apply manual corrections for rows where place_identifier(year) == 13.0
    print("Applying manual corrections for place_identifier(year) == 13.0 ...")
    if 'place_identifier(year)' in df_main.columns:
        mask = df_main['place_identifier(year)'] == 13.0
        rows_to_update = df_main.index[mask].tolist()
        if rows_to_update:
            # Ensure columns exist
            if 'Exit_Number_3' not in df_main.columns:
                df_main['Exit_Number_3'] = pd.NA
            if 'Exit_Number_2' not in df_main.columns:
                df_main['Exit_Number_2'] = pd.NA
            if 'Tertiary_Road' not in df_main.columns:
                df_main['Tertiary_Road'] = pd.NA
            if 'Main_Road' not in df_main.columns:
                df_main['Main_Road'] = pd.NA
            correction_count = 0
            for row in rows_to_update:
                df_main.at[row, 'Main_Road'] = 'I-15-80'
                df_main.at[row, 'Tertiary_Road'] = 'UT 201'
                df_main.at[row, 'Exit_Number_2'] = '122'
                df_main.at[row, 'Exit_Number_3'] = '17'
                correction_count += 1
            print(f"Applied manual corrections to {correction_count} rows where place_identifier(year) == 13.0")
        else:
            print("No rows found with place_identifier(year) == 13.0 for manual corrections.")
    else:
        print("Column 'place_identifier(year)' not found in dataframe. Skipping manual corrections.")
    
    # Report data types after conversion
    print("Data type conversions completed:")
    if 'Exit_Number_2' in df_main.columns:
        print(f"Exit_Number_2: {df_main['Exit_Number_2'].dtype}")
    if 'Exit_Number_3' in df_main.columns:
        print(f"Exit_Number_3: {df_main['Exit_Number_3'].dtype}")
    
    # Report data quality statistics
    print("\nData quality statistics:")
    if 'Exit_Number_2' in df_main.columns:
        exit_2_count = df_main['Exit_Number_2'].notna().sum()
        print(f"Rows with Exit_Number_2: {exit_2_count}")
    if 'Exit_Number_3' in df_main.columns:
        exit_3_count = df_main['Exit_Number_3'].notna().sum()
        print(f"Rows with Exit_Number_3: {exit_3_count}")
    
    return df_main, df_truck_stops

def normalize_phone(phone_num):
    """
    Function to normalize phone numbers to a standard format for Yelp matching.
    """
    if pd.isna(phone_num):
        return None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', str(phone_num))
    
    # If it's a 10-digit number, add '1' prefix for US numbers
    if len(digits_only) == 10:
        return '1' + digits_only
    
    # If it already has 11 digits starting with 1, return as is
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return digits_only
    
    # Return whatever we have if it doesn't fit the expected patterns
    return digits_only

def process_yelp_4_workflow(df_main):
    """
    Process the Yelp_Lookup 4 workflow which performs phone number matching
    between the main dataset and Yelp businesses dataset.
    
    This function:
    1. Loads the Yelp businesses dataset
    2. Performs phone number normalization and matching
    3. Creates Phone_Yelp_matches_row_ids column with matched Yelp row IDs
    4. Only matches with Yelp businesses that have non-missing Name values
    """
    print("Processing Yelp_Lookup 4 workflow - Phone number matching with Yelp data...")
    
    # Load the Yelp businesses dataset
    yelp_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\yelp_businesses_all.csv'
    print(f"Loading Yelp businesses dataset from: {yelp_path}")
    
    try:
        df_yelp = pd.read_csv(yelp_path)
        print(f"Yelp dataset loaded with shape: {df_yelp.shape}")
    except FileNotFoundError:
        print(f"ERROR: Yelp businesses file not found at: {yelp_path}")
        print("Skipping Yelp matching workflow...")
        return df_main
    
    # Check for required columns in Yelp dataset
    if 'Name' not in df_yelp.columns:
        print("ERROR: 'Name' column not found in Yelp dataset")
        print(f"Available columns: {df_yelp.columns.tolist()}")
        return df_main
    
    if 'Original_Phone' not in df_yelp.columns:
        print("ERROR: 'Original_Phone' column not found in Yelp dataset")
        print(f"Available columns: {df_yelp.columns.tolist()}")
        return df_main
    
    # Check for missing names in Yelp data
    missing_names = df_yelp['Name'].isna().sum()
    print(f"Yelp dataset: {missing_names} rows have missing Name values")
    
    # Check for duplicate phone numbers in Yelp data
    if 'Original_Phone' in df_yelp.columns:
        duplicate_mask = df_yelp['Original_Phone'].duplicated(keep=False)
        duplicate_count = duplicate_mask.sum()
        print(f"Yelp dataset: {duplicate_count} rows have non-unique phone numbers")
    
    # Create a new column for the matching row ids
    df_main['Phone_Yelp_matches_row_ids'] = None
    
    # Normalize the phone numbers in both dataframes
    print("Normalizing phone numbers for matching...")
    df_main['normalized_phone'] = df_main['phone'].apply(normalize_phone) if 'phone' in df_main.columns else pd.Series([None] * len(df_main))
    df_yelp['normalized_phone'] = df_yelp['Original_Phone'].apply(normalize_phone)
    
    # Create a dictionary mapping normalized phone numbers to their row indices in df_yelp
    # But only include rows where df_yelp['Name'] is not missing
    phone_to_indices = {}
    valid_yelp_count = 0
    
    for idx, row in df_yelp.iterrows():
        phone = row['normalized_phone']
        # Only include rows where Name is not missing
        if phone is not None and not pd.isna(row['Name']):
            valid_yelp_count += 1
            if phone not in phone_to_indices:
                phone_to_indices[phone] = []
            phone_to_indices[phone].append(idx)
    
    print(f"Found {valid_yelp_count} Yelp businesses with valid phone numbers and names")
    print(f"Unique phone numbers in Yelp data: {len(phone_to_indices)}")
    
    # For each row in df_main, find matching rows in df_yelp
    match_count = 0
    for idx, row in df_main.iterrows():
        if row['normalized_phone'] is not None:
            # Check if the normalized phone exists in our mapping
            if row['normalized_phone'] in phone_to_indices:
                df_main.at[idx, 'Phone_Yelp_matches_row_ids'] = phone_to_indices[row['normalized_phone']]
                match_count += 1
    
    # Clean up by removing the temporary normalized_phone column
    df_main.drop('normalized_phone', axis=1, inplace=True)
    df_yelp.drop('normalized_phone', axis=1, inplace=True)
    
    # Display the number of matches found
    print(f"Phone number matching complete!")
    print(f"Number of rows in main dataset with matching phone numbers in Yelp data: {match_count}")
    
    # Show some sample matches for verification
    if match_count > 0:
        matched_df = df_main[df_main['Phone_Yelp_matches_row_ids'].notna()]
        sample_size = min(3, match_count)  # Show up to 3 matches
        
        print(f"\nSample of {sample_size} matched phone numbers:")
        for i, (idx, row) in enumerate(matched_df.head(sample_size).iterrows()):
            print(f"\nMatch {i+1} (main dataset row {idx}):")
            
            # Display main dataset info
            if 'label' in df_main.columns:
                print(f"  Main dataset - Label: {row['label']}")
            print(f"  Main dataset - Phone: {row['phone']}")
            
            # Get the matched row ids from df_yelp
            matched_ids = row['Phone_Yelp_matches_row_ids']
            if isinstance(matched_ids, list):
                print(f"  Found {len(matched_ids)} matches in Yelp data:")
                for match_id in matched_ids[:2]:  # Show first 2 matches
                    matched_row = df_yelp.iloc[match_id]
                    print(f"    Yelp row {match_id} - Name: {matched_row['Name']}, Phone: {matched_row['Original_Phone']}")
                if len(matched_ids) > 2:
                    print(f"    ... and {len(matched_ids) - 2} more matches")
            else:
                # In case there's only one match and it's not stored as a list
                matched_row = df_yelp.iloc[matched_ids]
                print(f"  Found 1 match in Yelp data:")
                print(f"    Yelp row {matched_ids} - Name: {matched_row['Name']}, Phone: {matched_row['Original_Phone']}")
    else:
        print("No matches found between main dataset and Yelp data where Yelp Name is not missing.")
    
    return df_main

def process_yelp_6_workflow(df_main):
    """
    Process the Yelp_Lookup 6 workflow which performs column renaming
    and creates additional match rate indicators.
    
    This function:
    1. Renames match rate columns for better clarity
    2. Creates Yelp_phone_match_rate based on Phone_Yelp_matches_row_ids
    """
    print("Processing Yelp_Lookup 6 workflow - Column renaming and match rate indicators...")
    
    # Rename columns for better clarity
    print("Renaming match rate columns...")
    rename_mapping = {
        'Success_Match_Rate': 'Scraped_zipcode_to_label_match_rate',
        'Phone_Success_Match_Rate': 'Scraped_phone_match_rate'
    }
    
    # Only rename columns that actually exist
    existing_renames = {old: new for old, new in rename_mapping.items() if old in df_main.columns}
    
    if existing_renames:
        df_main.rename(columns=existing_renames, inplace=True)
        print(f"Renamed columns: {existing_renames}")
    else:
        print("No columns to rename found")
    
    # Create the Yelp_phone_match_rate column based on Phone_Yelp_matches_row_ids
    print("Creating Yelp_phone_match_rate indicator...")
    if 'Phone_Yelp_matches_row_ids' in df_main.columns:
        df_main['Yelp_phone_match_rate'] = df_main['Phone_Yelp_matches_row_ids'].notna()
        
        # Report statistics
        total_rows = len(df_main)
        yelp_matches = df_main['Yelp_phone_match_rate'].sum()
        yelp_percentage = (yelp_matches / total_rows) * 100
        
        print(f"Yelp phone match statistics:")
        print(f"  Total rows: {total_rows}")
        print(f"  Rows with Yelp phone matches: {yelp_matches}")
        print(f"  Yelp phone match percentage: {yelp_percentage:.2f}%")
    else:
        print("WARNING: 'Phone_Yelp_matches_row_ids' column not found")
        df_main['Yelp_phone_match_rate'] = False
    
    # Display column summary
    print(f"\nColumn summary after Yelp 6 workflow:")
    print(f"  Total columns: {len(df_main.columns)}")
    print(f"  Dataset shape: {df_main.shape}")
    
    # Show the new/renamed columns
    match_rate_columns = [col for col in df_main.columns if 'match_rate' in col.lower()]
    if match_rate_columns:
        print(f"  Match rate columns: {match_rate_columns}")
    
    return df_main

def process_yelp_7_5_workflow(df_main):
    """
    Process the Yelp_Lookup 7_5 workflow which performs specific row reordering.
    
    This function:
    1. Moves row 1588 to just before row 1585
    2. This appears to be a specific data correction operation
    """
    print("Processing Yelp_Lookup 7_5 workflow - Row reordering operation...")
    
    # Check if the dataframe has enough rows for this operation
    if len(df_main) <= 1588:
        print(f"WARNING: DataFrame has only {len(df_main)} rows, but operation requires row 1588")
        print("Skipping row reordering operation...")
        return df_main
    
    print(f"Original DataFrame shape: {df_main.shape}")
    print("Moving row 1588 to just before row 1585...")
    
    # Extract the row we want to move (row 1588)
    row_to_move = df_main.iloc[1588:1589].copy()
    print(f"Row to move (original row 1588): {row_to_move.index[0]}")
    
    # Remove the row from its original position
    df_temp = df_main.drop(df_main.index[1588]).reset_index(drop=True)
    
    # Insert the row at the new position (before what will be row 1585 after the removal)
    # Since we removed one row, the target position is now 1585
    df_reordered = pd.concat([
        df_temp.iloc[:1585],  # All rows before position 1585
        row_to_move.reset_index(drop=True),  # The row we're moving
        df_temp.iloc[1585:]   # All rows from position 1585 onwards
    ], ignore_index=True)
    
    print("Row movement completed!")
    print(f"Reordered DataFrame shape: {df_reordered.shape}")
    
    # Verify the operation by checking rows around the moved position
    if len(df_reordered) > 1587:
        print("\nRows around the moved position (1584-1587):")
        preview_rows = df_reordered.iloc[1584:1588]
        print(f"Row 1584: Label = {preview_rows.iloc[0]['label'] if 'label' in preview_rows.columns else 'N/A'}")
        print(f"Row 1585: Label = {preview_rows.iloc[1]['label'] if 'label' in preview_rows.columns else 'N/A'} (moved row)")
        print(f"Row 1586: Label = {preview_rows.iloc[2]['label'] if 'label' in preview_rows.columns else 'N/A'}")
        print(f"Row 1587: Label = {preview_rows.iloc[3]['label'] if 'label' in preview_rows.columns else 'N/A'}")
    
    # Verify data integrity
    original_row_count = len(df_main)
    reordered_row_count = len(df_reordered)
    
    if original_row_count == reordered_row_count:
        print(f"✓ Data integrity verified: Row count maintained ({original_row_count} rows)")
    else:
        print(f"⚠ WARNING: Row count changed from {original_row_count} to {reordered_row_count}")
    
    return df_reordered

def process_yelp_8_workflow(df_main):
    """
    Process the Yelp_Lookup 8 workflow which creates sequential place identifiers
    based on year patterns.
    
    This function:
    1. Creates place_identifier(year) column based on target sequence [2006, 2007, 2008, 2014, 2015, 2016]
    2. Groups rows that follow this year sequence pattern
    3. Analyzes completeness of place identifier groups
    4. Provides detailed statistics on missing years for incomplete groups
    """
    print("Processing Yelp_Lookup 8 workflow - Sequential place identifier creation...")
    
    # Check if year column exists
    if 'year' not in df_main.columns:
        print("ERROR: 'year' column not found in dataset")
        print(f"Available columns: {df_main.columns.tolist()}")
        return df_main
    
    print(f"Original DataFrame shape: {df_main.shape}")
    
    # Target sequence to follow
    target_sequence = [2006, 2007, 2008, 2014, 2015, 2016]
    print(f"Target year sequence: {target_sequence}")
    
    # Initialize variables for place identifier assignment
    n = 1
    group_ids = [None] * len(df_main)
    i = 0  # Current index in df_main
    
    print("Creating sequential place identifiers...")
    
    while i < len(df_main):
        # Process one row at a time
        current_year = df_main.at[i, 'year']
        
        # Check if current year is in target sequence (can start with any year)
        if current_year in target_sequence:
            # Find where this year appears in the sequence
            seq_idx = target_sequence.index(current_year)
            
            # Start a new group
            group_ids[i] = n
            seq_idx += 1
            i += 1
            
            # Continue building this group while we find matching years
            while i < len(df_main) and seq_idx < len(target_sequence):
                current_year = df_main.at[i, 'year']
                
                # If we find the next expected year, add to current group
                if current_year == target_sequence[seq_idx]:
                    group_ids[i] = n
                    seq_idx += 1
                    i += 1
                else:
                    # If we don't find the expected year, break out and start new group
                    break
            
            # Move to next group after completing or breaking current group
            n += 1
        else:
            # If current row doesn't match any year in sequence, skip it (no group assignment)
            i += 1
    
    # Assign the place identifiers to the dataframe
    df_main['place_identifier(year)'] = group_ids
    
    print(f"Place identifier creation completed!")
    print(f"Total unique place identifiers created: {n - 1}")
    
    # Analyze the place identifier groups
    print("\nAnalyzing place identifier completeness...")
    
    # Count entries for each place identifier
    place_counts = df_main['place_identifier(year)'].value_counts().sort_index()
    
    # Find place identifiers that don't have exactly 6 entries
    not_six_entries = place_counts[place_counts != 6]
    
    # Summary statistics
    total_places = df_main['place_identifier(year)'].nunique()
    places_with_6_entries = (place_counts == 6).sum()
    places_without_6_entries = (place_counts != 6).sum()
    nan_count = df_main['place_identifier(year)'].isnull().sum()
    
    print(f"\nPLACE IDENTIFIER ANALYSIS:")
    print(f"  Total unique place identifiers: {total_places}")
    print(f"  Place identifiers with exactly 6 entries: {places_with_6_entries}")
    print(f"  Place identifiers WITHOUT exactly 6 entries: {places_without_6_entries}")
    print(f"  Rows with no place identifier (NaN): {nan_count}")
    print(f"  Total rows in dataset: {len(df_main)}")
    
    # Show distribution of entry counts
    print(f"\nDistribution of entry counts:")
    count_distribution = place_counts.value_counts().sort_index()
    for count, freq in count_distribution.items():
        print(f"  {freq} place identifiers have {count} entries each")
    
    # Detailed analysis of incomplete groups
    if len(not_six_entries) > 0:
        print(f"\nDETAILED ANALYSIS OF INCOMPLETE GROUPS:")
        print(f"Found {len(not_six_entries)} place identifiers with incomplete year sequences:")
        
        for entry_count in sorted(not_six_entries.value_counts().index):
            places_with_this_count = not_six_entries[not_six_entries == entry_count].index.tolist()
            print(f"\n  Places with {entry_count} entries ({len(places_with_this_count)} places):")
            
            for place_id in places_with_this_count[:3]:  # Show first 3 examples
                place_subset = df_main[df_main['place_identifier(year)'] == place_id]
                years = sorted(place_subset['year'].tolist())
                
                # Calculate missing years
                target_set = set(target_sequence)
                present_years = set(years)
                missing_years = sorted(list(target_set - present_years))
                
                print(f"    Place ID {place_id}: Years = {years}")
                if missing_years:
                    print(f"      → Missing years: {missing_years}")
            
            if len(places_with_this_count) > 3:
                print(f"    ... and {len(places_with_this_count) - 3} more places with {entry_count} entries")
    else:
        print("\n✓ All place identifiers have exactly 6 entries!")
    
    # Final verification
    print(f"\nFinal dataset shape: {df_main.shape}")
    print(f"New column added: 'place_identifier(year)'")
    
    return df_main

def extract_keywords(label):
    """Extract meaningful keywords from a label, excluding common stop words"""
    if pd.isna(label) or label == '':
        return set(), set()
    
    # Convert to lowercase and remove special characters
    cleaned = re.sub(r'[^\w\s]', ' ', str(label).lower())
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'across',
        'behind', 'beyond', 'plus', 'except', 'but', 'until', 'unless',
        'n', 'rd', 'st', 'ave', 'blvd', 'dr', 'ln', 'way', 'ct', 'pl', 'exit',
        'truck', 'stop', 'travel', 'plaza', 'fuel', 'station', 'gas'
    }
    
    # Business-specific stop words (common but less distinctive)
    business_common = {
        'truck', 'stop', 'travel', 'plaza', 'fuel', 'station', 'gas', 'exit',
        'chevron', 'shell', 'exxon', 'mobil', 'bp', 'texaco', 'citgo'
    }
    
    # Split into words and filter out stop words and short words
    words = [word.strip() for word in cleaned.split() if len(word.strip()) > 1]
    
    # Separate distinctive vs common keywords
    distinctive_keywords = set()
    common_keywords = set()
    
    for word in words:
        if word not in stop_words and len(word) > 2:
            if word in business_common:
                common_keywords.add(word)
            else:
                distinctive_keywords.add(word)
        elif word.isdigit() and len(word) >= 2:  # Keep numbers (like store numbers)
            distinctive_keywords.add(word)
    
    return distinctive_keywords, common_keywords

def calculate_similarity(label1, label2):
    """Calculate similarity between two labels using keyword matching and string similarity"""
    if pd.isna(label1) or pd.isna(label2) or label1 == '' or label2 == '':
        return 0.0
    
    # Extract keywords from both labels
    distinctive1, common1 = extract_keywords(label1)
    distinctive2, common2 = extract_keywords(label2)
    
    # If either has no keywords, use string similarity only
    if (not distinctive1 and not common1) or (not distinctive2 and not common2):
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str(label1).lower(), str(label2).lower()).ratio()
    
    # Calculate distinctive keyword overlap (more important)
    distinctive_intersection = distinctive1.intersection(distinctive2)
    distinctive_union = distinctive1.union(distinctive2)
    distinctive_similarity = len(distinctive_intersection) / len(distinctive_union) if distinctive_union else 0
    
    # Calculate common keyword overlap (less important)
    common_intersection = common1.intersection(common2)
    common_union = common1.union(common2)
    common_similarity = len(common_intersection) / len(common_union) if common_union else 0
    
    # Calculate string similarity
    from difflib import SequenceMatcher
    string_similarity = SequenceMatcher(None, str(label1).lower(), str(label2).lower()).ratio()
    
    # Special boost for distinctive keyword matches
    distinctive_boost = 0
    if len(distinctive_intersection) > 0:
        # Give significant bonus for each distinctive keyword match
        distinctive_boost = min(0.4, len(distinctive_intersection) * 0.2)
        
        # Extra bonus if we have multiple distinctive keywords matching
        if len(distinctive_intersection) >= 2:
            distinctive_boost += 0.1
    
    # If we have at least one distinctive keyword match, be more generous
    if len(distinctive_intersection) > 0:
        # Primary scoring when we have distinctive matches
        combined_similarity = (
            distinctive_similarity * 0.4 +   # Base distinctive similarity
            string_similarity * 0.3 +        # String context
            common_similarity * 0.1 +        # Common words context
            distinctive_boost                 # Bonus for matches
        )
    else:
        # Fallback scoring when no distinctive matches
        combined_similarity = (
            common_similarity * 0.5 + 
            string_similarity * 0.5
        )
    
    return min(1.0, combined_similarity)  # Cap at 1.0

def check_chain_match(chain1, chain2):
    """Check if chain values match, handling NaN values more permissively"""
    # Convert to string and handle various NaN representations
    chain1_str = str(chain1).lower().strip() if not pd.isna(chain1) else 'nan'
    chain2_str = str(chain2).lower().strip() if not pd.isna(chain2) else 'nan'
    
    # If either is NaN (including string 'nan'), consider it a match (ignore chain mismatches to/from NaN)
    if chain1_str == 'nan' or chain2_str == 'nan' or chain1_str == 'none' or chain2_str == 'none':
        return True
    
    # Both have real values, check if they match
    return chain1_str == chain2_str

def analyze_place_changes(df, similarity_threshold=0.5):
    """
    Analyze place changes across years for each place_identifier
    
    Parameters:
    df: DataFrame with columns 'place_identifier(year)', 'label', 'chain', 'year'
    similarity_threshold: Minimum similarity score to consider a match (0.5 = 50%)
    """
    
    # Add new columns to track changes
    df['Flag_Place_Change'] = False
    df['Flag_Place_Change_Year'] = None
    df['Similarity_Score'] = None
    df['Chain_Match'] = None
    df['Previous_Year_Label'] = None
    df['Previous_Year_Chain'] = None
    
    # Use the place_identifier(year) column as the base identifier and the separate 'year' column for year info
    df['place_id_base'] = df['place_identifier(year)'].astype(str)
    
    # Convert year to numeric, handling any non-numeric values
    df['year_numeric'] = pd.to_numeric(df['year'], errors='coerce')
    
    # Group by base place identifier
    grouped = df.groupby('place_id_base')
    
    changes_detected = []
    
    print(f"Found {len(grouped)} unique place identifiers to analyze")
    year_range = df['year_numeric'].dropna()
    if len(year_range) > 0:
        print(f"Year range: {year_range.min():.0f} to {year_range.max():.0f}")
    else:
        print("No valid years found")
    
    for place_id, group in grouped:
        if len(group) < 2:  # Skip if only one record
            continue
        
        # Filter out records without valid years
        group_with_years = group.dropna(subset=['year_numeric'])
        
        if len(group_with_years) < 2:  # Skip if less than 2 records with valid years
            continue
            
        # Sort by year
        group_sorted = group_with_years.sort_values('year_numeric').reset_index()
        
        # Compare consecutive years
        for i in range(1, len(group_sorted)):
            current_idx = group_sorted.loc[i, 'index']
            previous_idx = group_sorted.loc[i-1, 'index']
            
            current_label = group_sorted.loc[i, 'label']
            previous_label = group_sorted.loc[i-1, 'label']
            current_chain = group_sorted.loc[i, 'chain']
            previous_chain = group_sorted.loc[i-1, 'chain']
            current_year = group_sorted.loc[i, 'year_numeric']
            previous_year = group_sorted.loc[i-1, 'year_numeric']
            
            # Calculate label similarity
            similarity = calculate_similarity(current_label, previous_label)
            
            # Check chain match
            chain_match = check_chain_match(current_chain, previous_chain)
            
            # Update dataframe with comparison results
            df.loc[current_idx, 'Similarity_Score'] = similarity
            df.loc[current_idx, 'Chain_Match'] = chain_match
            df.loc[current_idx, 'Previous_Year_Label'] = previous_label
            df.loc[current_idx, 'Previous_Year_Chain'] = previous_chain
            
            # Determine if this represents a place change
            # A change is flagged if BOTH label similarity is low AND chain doesn't match
            # OR if similarity is extremely low (< 0.2) regardless of chain
            is_change = (
                (similarity < similarity_threshold and not chain_match) or  # Both conditions
                (similarity < 0.2)  # Extremely low similarity regardless of chain
            )
            
            if is_change:
                df.loc[current_idx, 'Flag_Place_Change'] = True
                df.loc[current_idx, 'Flag_Place_Change_Year'] = current_year
                
                change_info = {
                    'place_identifier': place_id,
                    'change_year': current_year,
                    'previous_year': previous_year,
                    'previous_label': previous_label,
                    'current_label': current_label,
                    'previous_chain': previous_chain,
                    'current_chain': current_chain,
                    'similarity_score': similarity,
                    'chain_match': chain_match,
                    'change_reason': []
                }
                
                if similarity < similarity_threshold:
                    change_info['change_reason'].append(f'Low label similarity ({similarity:.2f})')
                if not chain_match:
                    change_info['change_reason'].append('Chain mismatch')
                
                change_info['change_reason'] = '; '.join(change_info['change_reason'])
                changes_detected.append(change_info)
    
    # Clean up temporary columns
    df.drop(['place_id_base', 'year_numeric'], axis=1, inplace=True)
    
    return df, changes_detected

def process_yelp_10_workflow(df_main):
    """
    Process the Yelp_Lookup 10 workflow which performs sophisticated place change analysis
    across years using advanced label similarity and chain matching algorithms.
    
    This function:
    1. Implements advanced keyword extraction and weighted similarity matching
    2. Analyzes place changes across years for each place_identifier
    3. Flags potential business changes based on label similarity and chain matching
    4. Provides detailed statistics on detected changes
    """
    print("Processing Yelp_Lookup 10 workflow - Advanced place change analysis...")
    
    # Check for required columns
    required_columns = ['place_identifier(year)', 'label', 'chain', 'year']
    missing_columns = [col for col in required_columns if col not in df_main.columns]
    
    if missing_columns:
        print(f"ERROR: Required columns missing: {missing_columns}")
        print(f"Available columns: {df_main.columns.tolist()}")
        return df_main
    
    print(f"Original DataFrame shape: {df_main.shape}")
    
    # Run the place change analysis
    print("Starting place change analysis...")
    print(f"Analyzing {len(df_main)} records...")
    
    # Run the analysis with similarity threshold of 0.5 (50%)
    df_analyzed, detected_changes = analyze_place_changes(df_main.copy(), similarity_threshold=0.5)
    
    # Display summary statistics
    print(f"\n=== PLACE CHANGE ANALYSIS SUMMARY ===")
    print(f"Total changes detected: {len(detected_changes)}")
    print(f"Records with changes: {df_analyzed['Flag_Place_Change'].sum()}")
    print(f"Records without changes: {(~df_analyzed['Flag_Place_Change']).sum()}")
    print(f"Percentage of records with changes: {df_analyzed['Flag_Place_Change'].sum()/len(df_analyzed)*100:.2f}%")
    
    # Show distribution of similarity scores
    similarity_scores = df_analyzed['Similarity_Score'].dropna()
    if len(similarity_scores) > 0:
        print(f"\nSimilarity Score Distribution:")
        print(f"  Mean: {similarity_scores.mean():.3f}")
        print(f"  Median: {similarity_scores.median():.3f}")
        print(f"  Min: {similarity_scores.min():.3f}")
        print(f"  Max: {similarity_scores.max():.3f}")
    
    # Show chain match statistics
    chain_matches = df_analyzed['Chain_Match'].dropna()
    if len(chain_matches) > 0:
        print(f"\nChain Match Statistics:")
        print(f"  Chain matches: {chain_matches.sum()}")
        print(f"  Chain mismatches: {(~chain_matches).sum()}")
        print(f"  Chain match rate: {chain_matches.sum()/len(chain_matches)*100:.1f}%")
    
    # Show changes by year if any were detected
    if detected_changes:
        changes_df = pd.DataFrame(detected_changes)
        print(f"\nChanges by year:")
        year_counts = changes_df['change_year'].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"  {year}: {count} changes")
        
        # Show a few examples of detected changes
        print(f"\nExample changes detected:")
        for i, change in enumerate(changes_df.head(3).iterrows()):
            change_data = change[1]
            print(f"\n  Example {i+1}:")
            print(f"    Place ID: {change_data['place_identifier']}")
            print(f"    Year: {change_data['previous_year']} → {change_data['change_year']}")
            print(f"    Label: '{change_data['previous_label']}' → '{change_data['current_label']}'")
            print(f"    Reason: {change_data['change_reason']}")
    
    # Final dataset info
    print(f"\nFinal dataset shape: {df_analyzed.shape}")
    new_columns = ['Flag_Place_Change', 'Flag_Place_Change_Year', 'Similarity_Score', 
                   'Chain_Match', 'Previous_Year_Label', 'Previous_Year_Chain']
    print(f"New columns added: {new_columns}")
    
    return df_analyzed

def process_yellowpages_1_workflow(df_main):
    """
    Process the YellowPages_scraper 1 workflow which performs phone number matching
    between the main dataset and YellowPages data.
    
    This function:
    1. Loads the YellowPages data
    2. Performs phone number format analysis and matching
    3. Creates Phone_Yellowpages_matches_row_ids column with matched YellowPages row IDs
    4. Creates Yellowbook_phone_match_rate column based on STATUS validation
    5. Only matches with YellowPages entries that have valid phone numbers
    """
    print("Processing YellowPages_scraper 1 workflow - Phone number matching with YellowPages data...")
    
    # Load the YellowPages dataset
    yellowpages_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\yellowpages_data.csv'
    print(f"Loading YellowPages dataset from: {yellowpages_path}")
    
    try:
        df_yellowpages = pd.read_csv(yellowpages_path)
        print(f"YellowPages dataset loaded successfully with shape: {df_yellowpages.shape}")
    except FileNotFoundError:
        print(f"ERROR: YellowPages dataset not found at {yellowpages_path}")
        return df_main
    
    # Check for required columns in YellowPages dataset
    print(f"YellowPages columns: {df_yellowpages.columns.tolist()}")
    
    # Find the best phone column in YellowPages dataset
    phone_col_yellowpages = None
    
    # Check each column for phone number patterns
    for col in df_yellowpages.columns:
        if df_yellowpages[col].dtype == 'object':
            # Check if this column contains phone numbers in the format XXX-XXX-XXXX
            sample_non_null = df_yellowpages[col].dropna()
            if len(sample_non_null) > 0:
                # Convert to string and check format
                sample_str = sample_non_null.astype(str).head(100)
                phone_pattern_count = sum(1 for x in sample_str if len(x) == 12 and x.count('-') == 2)
                
                if phone_pattern_count > 0:
                    print(f"Column '{col}' contains {phone_pattern_count} phone-like values out of {len(sample_str)} sampled")
                    # If this looks like a phone column, use it
                    if phone_col_yellowpages is None or phone_pattern_count > 50:
                        phone_col_yellowpages = col
    
    if phone_col_yellowpages is None:
        print("ERROR: Could not find a suitable phone column in YellowPages dataset")
        print("Available columns:", df_yellowpages.columns.tolist())
        return df_main
    
    print(f"Selected phone column from YellowPages: {phone_col_yellowpages}")
    
    # Check for phone column in main dataset
    if 'phone' not in df_main.columns:
        print("ERROR: 'phone' column not found in main dataset")
        return df_main
    
    # Check for STATUS column in YellowPages dataset
    status_col = None
    for col in df_yellowpages.columns:
        if 'status' in col.lower():
            status_col = col
            break
    
    if status_col is None:
        print("WARNING: No STATUS column found in YellowPages dataset")
    else:
        print(f"Using STATUS column: {status_col}")
    
    # Initialize the new columns
    df_main['Phone_Yellowpages_matches_row_ids'] = None
    df_main['Yellowbook_phone_match_rate'] = True
    
    # Convert phone columns to string and handle NaN values
    df_main['phone'] = df_main['phone'].astype(str)
    df_yellowpages[phone_col_yellowpages] = df_yellowpages[phone_col_yellowpages].astype(str)
    
    # Create a dictionary for faster lookup from YellowPages dataset
    phone_to_indices = {}
    for idx, phone in enumerate(df_yellowpages[phone_col_yellowpages]):
        if phone not in ['nan', '', 'None']:
            if phone not in phone_to_indices:
                phone_to_indices[phone] = []
            phone_to_indices[phone].append(idx)
    
    print(f"Created phone lookup dictionary with {len(phone_to_indices)} unique phone numbers")
    
    # Show some sample phones for verification
    print("\nSample phones from main dataset:")
    main_phones_sample = df_main['phone'].dropna().head(5).tolist()
    print(main_phones_sample)
    print(f"\nSample phones from YellowPages dataset:")
    yp_phones_sample = df_yellowpages[phone_col_yellowpages].dropna().head(5).tolist()
    print(yp_phones_sample)
    
    # Process each row in main dataset
    rows_with_matches = 0
    rows_with_invalid_status = 0
    
    for df_idx, row in df_main.iterrows():
        phone = row['phone']
        
        # Skip if phone is NaN or empty
        if phone in ['nan', '', 'None']:
            df_main.at[df_idx, 'Phone_Yellowpages_matches_row_ids'] = []
            df_main.at[df_idx, 'Yellowbook_phone_match_rate'] = True
            continue
        
        # Find matching indices in YellowPages dataset
        if phone in phone_to_indices:
            matching_indices = phone_to_indices[phone]
            df_main.at[df_idx, 'Phone_Yellowpages_matches_row_ids'] = matching_indices
            rows_with_matches += 1
            
            # Check if any of the matching rows have STATUS == "no_results_found"
            match_rate = True
            if status_col is not None:
                for match_idx in matching_indices:
                    if df_yellowpages.iloc[match_idx][status_col] == 'no_results_found':
                        match_rate = False
                        rows_with_invalid_status += 1
                        break
            
            df_main.at[df_idx, 'Yellowbook_phone_match_rate'] = match_rate
        else:
            # No matches found
            df_main.at[df_idx, 'Phone_Yellowpages_matches_row_ids'] = []
            df_main.at[df_idx, 'Yellowbook_phone_match_rate'] = True
    
    # Report matching statistics
    total_rows = len(df_main)
    rows_without_matches = total_rows - rows_with_matches
    match_percentage = (rows_with_matches / total_rows) * 100
    
    print(f"\nYellowPages phone matching results:")
    print(f"Total rows processed: {total_rows}")
    print(f"Rows with matches: {rows_with_matches} ({match_percentage:.2f}%)")
    print(f"Rows without matches: {rows_without_matches}")
    print(f"Rows with invalid status: {rows_with_invalid_status}")
    print(f"Rows with Yellowbook_phone_match_rate = False: {(df_main['Yellowbook_phone_match_rate'] == False).sum()}")
    
    # Show some examples of matches
    matched_rows = df_main[df_main['Phone_Yellowpages_matches_row_ids'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
    if len(matched_rows) > 0:
        print(f"\nSample matched rows (first 3):")
        sample_matched = matched_rows.head(3)[['phone', 'Phone_Yellowpages_matches_row_ids', 'Yellowbook_phone_match_rate']]
        for idx, row in sample_matched.iterrows():
            print(f"Phone: {row['phone']}, Matches: {row['Phone_Yellowpages_matches_row_ids']}, Valid: {row['Yellowbook_phone_match_rate']}")
    else:
        print("\nNo matches found - analyzing potential format issues...")
        # Check for format mismatches
        main_phones = set(df_main['phone'].dropna().astype(str))
        yp_phones = set(df_yellowpages[phone_col_yellowpages].dropna().astype(str))
        exact_matches = main_phones & yp_phones
        print(f"Exact matches between phone sets: {len(exact_matches)}")
    
    print("YellowPages phone matching completed!")
    return df_main

def process_notebooks_5_workflow(df_main):
    """
    Process the Notebooks_5 workflow which performs coordinate analysis and distance calculations.
    This function:
    
    1. Analyzes coordinates from multiple data sources (Webscraped, Yelp, YellowPages)
    2. Calculates distances between coordinate pairs from different sources
    3. Handles duplicate coordinates within single sources
    4. Prioritizes Webscraped data comparisons when available
    5. Calculates midpoints between closest coordinate pairs
    6. Provides both constrained and unconstrained distance metrics
    """
    print("Processing Notebooks_5 workflow - Coordinate analysis and distance calculations...")
    
    # Import required libraries for distance calculations
    import numpy as np
    from math import radians, cos, sin, asin, sqrt
    
    # Define the columns and their labels - treating Webscraped sources as one
    columns_info = [
        # Combine both webscraped sources into one "Webscraped" category
        ([('Webscraped_Phone_LD_Latitude', 'Webscraped_Phone_LD_Longitude'),
          ('Webscraped_PlacedMatched_LD_Latitude', 'Webscraped_PlacedMatched_LD_Longitude')], 'Webscraped'),
        ([('Yelp_Latitude', 'Yelp_Longitude')], 'Yelp (Phone)'),
        ([('YellowPages_JSONLD_LAT_1', 'YellowPages_JSONLD_LNG_1')], 'YellowPages (Phone)')
    ]
    
    def parse_coords(lat_str, lon_str):
        """Parse coordinate strings into coordinate pairs"""
        exclude = {'nan', '', 'None', 'removed'}
        try:
            lats = [float(x) for x in str(lat_str).split(';') if x.strip() not in exclude]
            lons = [float(x) for x in str(lon_str).split(';') if x.strip() not in exclude]
            return list(zip(lats, lons))
        except (ValueError, AttributeError):
            return []
    
    def remove_duplicate_coords(coords):
        """Remove duplicate coordinates and return unique coordinates"""
        unique_coords = []
        for coord in coords:
            if coord not in unique_coords:
                unique_coords.append(coord)
        return unique_coords
    
    def get_single_coordinate_from_duplicates(coords):
        """Extract single coordinate from duplicate entries"""
        if len(coords) == 1:
            lat, lon = coords[0]
            return lat, lon
        
        # Check if we have duplicate coordinates that represent the same location
        unique_coords = remove_duplicate_coords(coords)
        if len(unique_coords) == 1:
            lat, lon = unique_coords[0]
            return lat, lon
        
        return None
    
    def haversine(lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points on Earth"""
        R = 3958.8  # Earth radius in miles
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c
    
    def calculate_midpoint(lat1, lon1, lat2, lon2):
        """Calculate the midpoint between two coordinates"""
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        return mid_lat, mid_lon
    
    # Initialize result lists
    max_distances = []
    max_distance_sources = []
    min_distances = []
    min_distance_sources = []
    min_distances_unconstrained = []
    min_distance_sources_unconstrained = []
    mid_lats = []
    mid_longs = []
    
    print(f"Analyzing coordinates for {len(df_main)} records...")
    
    for idx, row in df_main.iterrows():
        # Collect coordinates from each data source
        source_coords = {}
        
        for column_pairs, label in columns_info:
            all_coords = []
            
            # Collect coordinates from all column pairs for this source
            for lat_col, lon_col in column_pairs:
                if lat_col in row and lon_col in row:
                    coords = parse_coords(row[lat_col], row[lon_col])
                    if coords:
                        all_coords.extend(coords)
            
            if all_coords:
                # Remove duplicate coordinates within the same source
                unique_coords = remove_duplicate_coords(all_coords)
                source_coords[label] = unique_coords
        
        # Check if we have only one data source with coordinates
        if len(source_coords) == 1:
            source_name = list(source_coords.keys())[0]
            coords = source_coords[source_name]
            
            # Try to get a single coordinate from potential duplicates
            single_coord = get_single_coordinate_from_duplicates(coords)
            if single_coord:
                lat, lon = single_coord
                max_distances.append(0)
                max_distance_sources.append(f"Single source: {source_name}")
                min_distances.append(0)
                min_distance_sources.append(f"Single source: {source_name}")
                min_distances_unconstrained.append(0)
                min_distance_sources_unconstrained.append(f"Single source: {source_name}")
                mid_lats.append(lat)
                mid_longs.append(lon)
            else:
                # Multiple different coordinates in single source - leave without midpoint
                max_distances.append(0)
                max_distance_sources.append(f"Single source (multiple coords): {source_name}")
                min_distances.append(0)
                min_distance_sources.append(f"Single source (multiple coords): {source_name}")
                min_distances_unconstrained.append(0)
                min_distance_sources_unconstrained.append(f"Single source (multiple coords): {source_name}")
                mid_lats.append(None)
                mid_longs.append(None)
            continue
        
        # Compare coordinates across different data sources
        max_dist = 0
        min_dist_unconstrained = float('inf')
        max_source_pair = ""
        min_source_pair_unconstrained = ""
        min_coord_pair_unconstrained = None
        source_names = list(source_coords.keys())
        
        # UNCONSTRAINED: Original logic for all comparisons
        for i in range(len(source_names)):
            for j in range(i+1, len(source_names)):
                # Get coordinates from two different sources
                source1_coords = source_coords[source_names[i]]
                source2_coords = source_coords[source_names[j]]
                
                # Compare all coordinates from source1 with all coordinates from source2
                for lat1, lon1 in source1_coords:
                    for lat2, lon2 in source2_coords:
                        dist = haversine(lat1, lon1, lat2, lon2)
                        if dist > max_dist:
                            max_dist = dist
                            max_source_pair = f"{source_names[i]} vs {source_names[j]}"
                        if dist < min_dist_unconstrained:
                            min_dist_unconstrained = dist
                            min_source_pair_unconstrained = f"{source_names[i]} vs {source_names[j]}"
                            min_coord_pair_unconstrained = ((lat1, lon1), (lat2, lon2))
        
        # CONSTRAINED: Prioritize Webscraped comparisons
        min_dist_constrained = float('inf')
        min_source_pair_constrained = ""
        min_coord_pair_constrained = None
        
        # First, try to find comparisons involving Webscraped
        webscraped_found = False
        if 'Webscraped' in source_coords:
            webscraped_coords = source_coords['Webscraped']
            
            for source_name in source_names:
                if source_name != 'Webscraped':
                    other_coords = source_coords[source_name]
                    
                    for lat1, lon1 in webscraped_coords:
                        for lat2, lon2 in other_coords:
                            dist = haversine(lat1, lon1, lat2, lon2)
                            if dist < min_dist_constrained:
                                min_dist_constrained = dist
                                min_source_pair_constrained = f"Webscraped vs {source_name}"
                                min_coord_pair_constrained = ((lat1, lon1), (lat2, lon2))
                                webscraped_found = True
        
        # If no Webscraped comparisons found, fall back to other comparisons
        if not webscraped_found:
            # Compare non-Webscraped sources
            for i in range(len(source_names)):
                for j in range(i+1, len(source_names)):
                    if source_names[i] != 'Webscraped' and source_names[j] != 'Webscraped':
                        source1_coords = source_coords[source_names[i]]
                        source2_coords = source_coords[source_names[j]]
                        
                        for lat1, lon1 in source1_coords:
                            for lat2, lon2 in source2_coords:
                                dist = haversine(lat1, lon1, lat2, lon2)
                                if dist < min_dist_constrained:
                                    min_dist_constrained = dist
                                    min_source_pair_constrained = f"{source_names[i]} vs {source_names[j]}"
                                    min_coord_pair_constrained = ((lat1, lon1), (lat2, lon2))
        
        max_distances.append(max_dist)
        max_distance_sources.append(max_source_pair)
        
        # Handle unconstrained results
        if min_dist_unconstrained == float('inf'):
            min_dist_unconstrained = 0
            min_source_pair_unconstrained = ""
            mid_lat_unconstrained = None
            mid_lon_unconstrained = None
        else:
            # Calculate midpoint for unconstrained minimum distance
            (lat1, lon1), (lat2, lon2) = min_coord_pair_unconstrained
            mid_lat_unconstrained, mid_lon_unconstrained = calculate_midpoint(lat1, lon1, lat2, lon2)
        
        min_distances_unconstrained.append(min_dist_unconstrained)
        min_distance_sources_unconstrained.append(min_source_pair_unconstrained)
        
        # Handle constrained results
        if min_dist_constrained == float('inf'):
            min_dist_constrained = 0
            min_source_pair_constrained = ""
            mid_lat = None
            mid_lon = None
        else:
            # Calculate midpoint for constrained minimum distance
            (lat1, lon1), (lat2, lon2) = min_coord_pair_constrained
            mid_lat, mid_lon = calculate_midpoint(lat1, lon1, lat2, lon2)
        
        min_distances.append(min_dist_constrained)
        min_distance_sources.append(min_source_pair_constrained)
        mid_lats.append(mid_lat)
        mid_longs.append(mid_lon)
    
    # Update dataframe with new columns
    df_main['max_distance_miles'] = max_distances
    df_main['max_distance_sources'] = max_distance_sources
    df_main['min_distance_miles'] = min_distances
    df_main['min_distance_sources'] = min_distance_sources
    df_main['min_distance_miles_unconstrained'] = min_distances_unconstrained
    df_main['min_distance_sources_unconstrained'] = min_distance_sources_unconstrained
    df_main['Mid_Lat'] = mid_lats
    df_main['Mid_Long'] = mid_longs
    
    # Report analysis results
    filtered_df = df_main[df_main['min_distance_miles'] > 0]
    single_source_df = df_main[df_main['min_distance_sources'].str.contains('Single source', na=False)]
    webscraped_priority_df = df_main[df_main['min_distance_sources'].str.contains('Webscraped vs', na=False)]
    
    print(f"Coordinate analysis complete!")
    print(f"Total records processed: {len(df_main)}")
    print(f"Records with distance comparisons: {len(filtered_df)}")
    print(f"Records with single data source: {len(single_source_df)}")
    print(f"Records with Webscraped-prioritized comparisons: {len(webscraped_priority_df)}")
    
    if len(filtered_df) > 0:
        print(f"Distance statistics (excluding zeros):")
        print(f"  Min distance: {filtered_df['min_distance_miles'].min():.6f} miles")
        print(f"  Max distance: {filtered_df['min_distance_miles'].max():.6f} miles")
        print(f"  Mean distance: {filtered_df['min_distance_miles'].mean():.6f} miles")
        print(f"  Median distance: {filtered_df['min_distance_miles'].median():.6f} miles")
    
    return df_main

def process_notebooks_8_workflow(df_main):
    """
    Process the Notebooks_8 workflow which adds manual matching information and coordinates.
    This function:
    
    1. Creates new columns for manual data entry
    2. Adds manual matches and coordinates for specific place identifiers
    3. Provides match comments for quality control
    4. Updates locations with verified external sources (TruckStops, YellowPages, Yelp)
    """
    print("Processing Notebooks_8 workflow - Manual matching and coordinate updates...")
    
    # Create new columns for manual matching information
    df_main['Match_Comments'] = ''
    df_main['Manual_Match'] = ''
    df_main['Manual_Lat'] = ''
    df_main['Manual_Long'] = ''
    
    print("Adding manual matches and coordinates for specific place identifiers...")
    
    # Manual updates for specific place identifiers
    manual_updates = [
        # TruckStops and Services matches
        (92, 'https://www.truckstopsandservices.com/location_details.php?id=10277', 34.728256, -114.315187, ''),
        (89, 'https://www.truckstopsandservices.com/location_details.php?id=2214', 35.17617, -113.785941, ''),
        (485, 'https://www.truckstopsandservices.com/location_details.php?id=10342', 39.00122, -122.893987, ''),
        (340, 'https://www.truckstopsandservices.com/location_details.php?id=11836', 37.365133, -115.159914, ''),
        
        # YellowPages matches
        (460, 'https://www.yellowpages.com/madera-ca/mip/valero-473794351', 36.923553, -120.02618, ''),
        (499, 'https://www.yellowpages.com/dunnigan-ca/mip/united-travel-plaza-566494439', 38.860195, -121.95684, ''),
        (277, 'https://www.yellowpages.com/ogden-ut/mip/chevron-452413503', 41.229145, -112.006584, ''),
        
        # Yelp matches
        (253, 'https://www.yelp.com/biz/cottonwood-chevron-cottonwood?adjust_creative=xElCeMfmOucjLmXEMhJkIg&utm_campaign=yelp_api_v3&utm_medium=api_v3_phone_search&utm_source=xElCeMfmOucjLmXEMhJkIg', 40.370251, -122.283625, ''),
        
        # RV and Travelers match
        (10, 'http://www.rvandtravelers.com/location_details.php?id=789', 40.739716, -111.944625, ''),
    ]
    
    # Apply manual updates
    for place_id, manual_match, manual_lat, manual_long, comment in manual_updates:
        mask = df_main['place_identifier(year)'] == place_id
        if mask.any():
            df_main.loc[mask, 'Manual_Match'] = manual_match
            df_main.loc[mask, 'Manual_Lat'] = manual_lat
            df_main.loc[mask, 'Manual_Long'] = manual_long
            if comment:
                df_main.loc[mask, 'Match_Comments'] = comment
    
    # Manual coordinate updates (coordinate-only updates)
    coordinate_updates = [
        (275, 41.7110875414374, -112.179749917386, ''),
        (135, 33.774475, -118.25391, ''),
        (273, 41.886516471518895, -112.16742385741813, ''),
        (247, 39.740034472254365, -122.20339906976407, ''),
        (283, 38.99387382027033, -112.32482061895016, ''),
        (477, 37.92484259805216, -121.22885038154168, ''),
        (284, 40.05483507466554, -111.731102394095, 'made a guess match at https://maps.app.goo.gl/yTptgiDPUwDGgGPQ6'),
        (291, 37.0443227914404, -112.5258575028404, 'mapquest match 217 S 100 E\nKanab, UT 84741'),
        (364, 39.53457785486948, -119.78380942956993, ''),
        (389, 32.850239558484, -116.95126512698407, 'mapquest match, 11427 Woodside Ave\nSantee, CA 92071'),
        (430, 34.220795746324455, -119.14231239911598, 'guess'),
        (439, 36.086868117908715, -119.03872700108509, 'truckmap search , https://maps.app.goo.gl/oe8AFnV3CViEC6p67'),
        (443, 35.353927148875115, -118.91178276010221, 'mapquest, 8311 E Brundage Ln\nBakersfield, CA 93307'),
    ]
    
    # Apply coordinate updates
    for place_id, manual_lat, manual_long, comment in coordinate_updates:
        mask = df_main['place_identifier(year)'] == place_id
        if mask.any():
            df_main.loc[mask, 'Manual_Lat'] = manual_lat
            df_main.loc[mask, 'Manual_Long'] = manual_long
            if comment:
                df_main.loc[mask, 'Match_Comments'] = comment
    
    # Special comment-only updates
    comment_updates = [
        (359, 'Both places with similar names and same area'),
        (164, 'Too close already'),
    ]
    
    # Apply comment updates
    for place_id, comment in comment_updates:
        mask = df_main['place_identifier(year)'] == place_id
        if mask.any():
            df_main.loc[mask, 'Match_Comments'] = comment
    
    # Report update statistics
    manual_match_count = (df_main['Manual_Match'] != '').sum()
    manual_coords_count = ((df_main['Manual_Lat'] != '') & (df_main['Manual_Long'] != '')).sum()
    comments_count = (df_main['Match_Comments'] != '').sum()
    
    print(f"Manual matching workflow completed!")
    print(f"Records with manual matches: {manual_match_count}")
    print(f"Records with manual coordinates: {manual_coords_count}")
    print(f"Records with match comments: {comments_count}")
    
    # Show breakdown by source type
    truckstops_matches = df_main['Manual_Match'].str.contains('truckstopsandservices.com', na=False).sum()
    yellowpages_matches = df_main['Manual_Match'].str.contains('yellowpages.com', na=False).sum()
    yelp_matches = df_main['Manual_Match'].str.contains('yelp.com', na=False).sum()
    other_matches = manual_match_count - truckstops_matches - yellowpages_matches - yelp_matches
    
    print(f"Manual match source breakdown:")
    print(f"  TruckStops and Services: {truckstops_matches}")
    print(f"  YellowPages: {yellowpages_matches}")
    print(f"  Yelp: {yelp_matches}")
    print(f"  Other sources: {other_matches}")
    
    return df_main

def process_notebooks_9_workflow(df_main):
    """
    Process the Notebooks\9 workflow which performs final coordinate consolidation
    by creating Final_Lat and Final_Long columns using Manual coordinates first,
    then Mid coordinates as fallback, and filling missing coordinates from nearby rows.
    """
    print("Processing Notebooks\\9 workflow - Final coordinate consolidation...")
    
    # Initialize the Final columns
    df_main['Final_Lat'] = np.nan
    df_main['Final_Long'] = np.nan
    
    # Check if the required columns exist
    required_cols = ['Manual_Lat', 'Manual_Long', 'Mid_Lat', 'Mid_Long']
    missing_cols = [col for col in required_cols if col not in df_main.columns]
    
    if missing_cols:
        print(f"WARNING: Missing columns: {missing_cols}")
        print("Initializing missing columns with NaN values...")
        for col in missing_cols:
            df_main[col] = np.nan
    
    # Convert string representations to numeric values
    for col in ['Manual_Lat', 'Manual_Long', 'Mid_Lat', 'Mid_Long']:
        if col in df_main.columns:
            # Convert empty strings to NaN, then to numeric
            df_main[col] = df_main[col].replace('', np.nan)
            df_main[col] = pd.to_numeric(df_main[col], errors='coerce')
    
    # Apply the logic: Manual first, then Mid as fallback
    print("Step 1: Using Manual coordinates where available...")
    manual_mask = df_main['Manual_Lat'].notna() & df_main['Manual_Long'].notna()
    df_main.loc[manual_mask, 'Final_Lat'] = df_main.loc[manual_mask, 'Manual_Lat']
    df_main.loc[manual_mask, 'Final_Long'] = df_main.loc[manual_mask, 'Manual_Long']
    
    print("Step 2: Using Mid coordinates as fallback...")
    mid_mask = df_main['Final_Lat'].isna() & df_main['Mid_Lat'].notna() & df_main['Mid_Long'].notna()
    df_main.loc[mid_mask, 'Final_Lat'] = df_main.loc[mid_mask, 'Mid_Lat']
    df_main.loc[mid_mask, 'Final_Long'] = df_main.loc[mid_mask, 'Mid_Long']
    
    # Report initial results
    print("Initial coordinate assignment results:")
    print(f"Total rows: {len(df_main)}")
    print(f"Rows with Manual coordinates used: {manual_mask.sum()}")
    print(f"Rows with Mid coordinates used: {mid_mask.sum()}")
    print(f"Rows with Final coordinates: {df_main['Final_Lat'].notna().sum()}")
    
    # Fill missing coordinates from nearby rows with same place_identifier
    def fill_missing_coordinates_from_nearby(df):
        """Fill missing Final_Lat and Final_Long by looking for nearby rows with the same place_identifier(year)"""
        filled_count = 0
        
        # Find rows with missing Final coordinates
        missing_mask = df['Final_Lat'].isna() | df['Final_Long'].isna()
        missing_indices = df[missing_mask].index.tolist()
        
        print(f"Found {len(missing_indices)} rows with missing Final coordinates")
        
        for idx in missing_indices:
            # Get the place_identifier for this row
            if 'place_identifier(year)' not in df.columns:
                continue
                
            place_id = df.loc[idx, 'place_identifier(year)']
            
            if pd.isna(place_id):
                continue
                
            # Find all rows with the same place_identifier that have valid coordinates
            same_place_mask = (df['place_identifier(year)'] == place_id) & \
                             (df['Final_Lat'].notna()) & \
                             (df['Final_Long'].notna())
            
            same_place_indices = df[same_place_mask].index.tolist()
            
            if not same_place_indices:
                continue
                
            # Find the nearest row(s) by index distance
            distances = [(abs(idx - other_idx), other_idx) for other_idx in same_place_indices]
            distances.sort()  # Sort by distance
            
            # Use the nearest row with valid coordinates
            nearest_distance, nearest_idx = distances[0]
            
            # Copy coordinates from the nearest row
            df.loc[idx, 'Final_Lat'] = df.loc[nearest_idx, 'Final_Lat']
            df.loc[idx, 'Final_Long'] = df.loc[nearest_idx, 'Final_Long']
            
            filled_count += 1
        
        return filled_count
    
    print("\nStep 3: Filling missing coordinates from nearby rows with same place_identifier...")
    filled = fill_missing_coordinates_from_nearby(df_main)
    
    # Final summary
    final_missing = (df_main['Final_Lat'].isna() | df_main['Final_Long'].isna()).sum()
    total_rows = len(df_main)
    rows_with_final_coords = (df_main['Final_Lat'].notna() & df_main['Final_Long'].notna()).sum()
    
    print(f"\nFinal coordinate consolidation completed!")
    print(f"Coordinates filled from nearby rows: {filled}")
    print(f"Total rows in dataset: {total_rows}")
    print(f"Rows with Final coordinates: {rows_with_final_coords}")
    print(f"Rows still missing coordinates: {final_missing}")
    print(f"Completion rate: {(rows_with_final_coords/total_rows)*100:.1f}%")
    
    if final_missing > 0:
        print(f"\nSample of rows still missing coordinates:")
        still_missing = df_main[df_main['Final_Lat'].isna() | df_main['Final_Long'].isna()]
        if 'clean_line1' in df_main.columns and 'place_identifier(year)' in df_main.columns:
            sample_missing = still_missing[['clean_line1', 'place_identifier(year)']].head(5)
            print(sample_missing.to_string(index=False))
    
    return df_main

def process_notebooks_1_workflow(df_main):
    """
    Process the Notebooks 1 workflow which performs comprehensive data enrichment
    by joining data from multiple sources (webscraped data, Yelp data, and YellowPages data)
    based on matching row IDs.
    
    This function:
    1. Loads webscraped, Yelp, and YellowPages datasets
    2. Extracts and joins webscraped data using Phone_scraped_matches_row_ids
    3. Computes Webscraped_Place_Match based on complex matching logic
    4. Extracts and joins place-matched webscraped data
    5. Extracts and joins Yelp data using Phone_Yelp_matches_row_ids
    6. Extracts and joins YellowPages data using Phone_Yellowpages_matches_row_ids
    """
    print("Processing Notebooks 1 workflow - Comprehensive data enrichment...")
    
    # Load the webscraped dataset (scraped truck stops data)
    webscraped_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Processed_Intermediate\scraped_4_7.csv'
    print(f"Loading webscraped dataset from: {webscraped_path}")
    
    try:
        webscraped_df = pd.read_csv(webscraped_path)
        print(f"Webscraped dataset loaded successfully with shape: {webscraped_df.shape}")
    except FileNotFoundError:
        print(f"ERROR: Webscraped dataset not found at {webscraped_path}")
        return df_main
    
    # Load the Yelp dataset
    yelp_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\yelp_businesses_all.csv'
    print(f"Loading Yelp dataset from: {yelp_path}")
    
    try:
        yelp_df = pd.read_csv(yelp_path)
        print(f"Yelp dataset loaded successfully with shape: {yelp_df.shape}")
    except FileNotFoundError:
        print(f"ERROR: Yelp dataset not found at {yelp_path}")
        return df_main
    
    # Load the YellowPages dataset
    yellowpages_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\yellowpages_data.csv'
    print(f"Loading YellowPages dataset from: {yellowpages_path}")
    
    try:
        yellowpages_df = pd.read_csv(yellowpages_path)
        print(f"YellowPages dataset loaded successfully with shape: {yellowpages_df.shape}")
    except FileNotFoundError:
        print(f"ERROR: YellowPages dataset not found at {yellowpages_path}")
        return df_main
    
    # Helper function to parse string representations of lists
    def parse_list(val):
        try:
            if isinstance(val, str):
                import ast
                out = ast.literal_eval(val)
            else:
                out = val
            return out if isinstance(out, list) else []
        except:
            return []
    
    # STEP 1: Extract and join webscraped data using Phone_scraped_matches_row_ids
    print("Step 1: Extracting webscraped data using phone matches...")
    
    def get_webscraped_data(row):
        try:
            idx_list = parse_list(row.get('phone_scraped_matches_row_ids', []))
            if not idx_list:
                return pd.Series()
            
            # Extract rows from webscraped_df by index
            selected = webscraped_df.iloc[idx_list]
            
            # Prefix columns and flatten (if multiple, join with ';')
            prefixed = {}
            for col in webscraped_df.columns:
                values = selected[col].astype(str).tolist()
                prefixed['Webscraped_Phone_' + col] = '; '.join(values)
            
            return pd.Series(prefixed)
        except Exception as e:
            return pd.Series()
    
    print("Applying webscraped data extraction...")
    webscraped_cols = df_main.apply(get_webscraped_data, axis=1)
    df_main = pd.concat([df_main, webscraped_cols], axis=1)
    
    webscraped_phone_cols = len([col for col in df_main.columns if col.startswith('Webscraped_Phone_')])
    print(f"Added {webscraped_phone_cols} webscraped phone-matched columns")
    
    # STEP 2: Compute Webscraped_Place_Match based on complex matching logic
    print("Step 2: Computing webscraped place matches...")
    
    def get_place_match(row):
        # Read all match lists and convert to sets
        zip_list = set(parse_list(row.get('ZIP_scraped_matches_row_ids', [])))
        state_list = set(parse_list(row.get('State_scraped_matches_row_ids', [])))
        city_list = set(parse_list(row.get('City_scraped_matches_row_ids', [])))
        exit_list = set(parse_list(row.get('Exit_scraped_matches_row_ids', [])))
        road_list = set(parse_list(row.get('Road_scraped_matches_row_ids', [])))
        label_list = set(parse_list(row.get('Label_scraped_matches_row_ids', [])))
        
        # Union ZIP and State
        base = zip_list.union(state_list)
        
        # Eliminate numbers not found in City or Exit
        city_exit = city_list.union(exit_list)
        filtered = base.intersection(city_exit)
        
        # Keep only those found in both Road and Label
        final = [x for x in filtered if x in road_list and x in label_list]
        
        return final
    
    df_main['Webscraped_Place_Match'] = df_main.apply(get_place_match, axis=1)
    
    place_matches = df_main['Webscraped_Place_Match'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).sum()
    print(f"Computed place matches for {place_matches} rows")
    
    # STEP 3: Extract and join place-matched webscraped data
    print("Step 3: Extracting webscraped place-matched data...")
    
    def get_webscraped_place_matched_data(row):
        try:
            idx_list = row.get('Webscraped_Place_Match', [])
            if not isinstance(idx_list, list) or not idx_list:
                return pd.Series()
            
            selected = webscraped_df.iloc[idx_list]
            prefixed = {}
            for col in webscraped_df.columns:
                values = selected[col].astype(str).tolist()
                prefixed['Webscraped_PlacedMatched_' + col] = '; '.join(values)
            
            return pd.Series(prefixed)
        except Exception as e:
            return pd.Series()
    
    webscraped_place_matched_cols = df_main.apply(get_webscraped_place_matched_data, axis=1)
    df_main = pd.concat([df_main, webscraped_place_matched_cols], axis=1)
    
    place_matched_cols = len([col for col in df_main.columns if col.startswith('Webscraped_PlacedMatched_')])
    print(f"Added {place_matched_cols} webscraped place-matched columns")
    
    # STEP 4: Extract and join Yelp data using Phone_Yelp_matches_row_ids
    print("Step 4: Extracting Yelp data using phone matches...")
    
    def get_yelp_data(row):
        try:
            idx_list = parse_list(row.get('Phone_Yelp_matches_row_ids', []))
            if not idx_list:
                return pd.Series()
            
            selected = yelp_df.iloc[idx_list]
            prefixed = {}
            for col in yelp_df.columns:
                values = selected[col].astype(str).tolist()
                prefixed['Yelp_' + col] = '; '.join(values)
            
            return pd.Series(prefixed)
        except Exception as e:
            return pd.Series()
    
    yelp_cols = df_main.apply(get_yelp_data, axis=1)
    df_main = pd.concat([df_main, yelp_cols], axis=1)
    
    yelp_added_cols = len([col for col in df_main.columns if col.startswith('Yelp_')])
    print(f"Added {yelp_added_cols} Yelp columns")
    
    # STEP 5: Extract and join YellowPages data using Phone_Yellowpages_matches_row_ids
    print("Step 5: Extracting YellowPages data using phone matches...")
    
    def get_yellowpages_data(row):
        try:
            idx_list = parse_list(row.get('Phone_Yellowpages_matches_row_ids', []))
            if not idx_list:
                return pd.Series()
            
            selected = yellowpages_df.iloc[idx_list]
            prefixed = {}
            for col in yellowpages_df.columns:
                values = selected[col].astype(str).tolist()
                prefixed['YellowPages_' + col] = '; '.join(values)
            
            return pd.Series(prefixed)
        except Exception as e:
            return pd.Series()
    
    yellowpages_cols = df_main.apply(get_yellowpages_data, axis=1)
    df_main = pd.concat([df_main, yellowpages_cols], axis=1)
    
    yellowpages_added_cols = len([col for col in df_main.columns if col.startswith('YellowPages_')])
    print(f"Added {yellowpages_added_cols} YellowPages columns")
    
    # Report final statistics
    print(f"\nData enrichment completed!")
    print(f"Final dataset shape: {df_main.shape}")
    print(f"Total columns added: {webscraped_phone_cols + place_matched_cols + yelp_added_cols + yellowpages_added_cols}")
    
    # Show sample of enrichment status
    has_webscraped = df_main[[col for col in df_main.columns if col.startswith('Webscraped_Phone_')]].notna().any(axis=1).sum()
    has_yelp = df_main[[col for col in df_main.columns if col.startswith('Yelp_')]].notna().any(axis=1).sum()
    has_yellowpages = df_main[[col for col in df_main.columns if col.startswith('YellowPages_')]].notna().any(axis=1).sum()
    
    print(f"Enrichment summary:")
    print(f"  Rows with webscraped data: {has_webscraped}")
    print(f"  Rows with Yelp data: {has_yelp}")
    print(f"  Rows with YellowPages data: {has_yellowpages}")
    
    return df_main

def main():
    """Main function to execute the data cleaning process."""
    
    # Load the original unbalanced panel dataset
    print("Loading the original unbalanced panel dataset...")
    df = pd.read_csv(r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Raw\unbalanced_panel.csv')
    print(f"Dataset loaded with shape: {df.shape}")
    
    # Standardize interstate highway formats
    print("Overwriting string columns with standardized interstate formats...")
    
    for column in df.columns:
        if df[column].dtype == 'object':  # String columns
            print(f"Processing column: {column}")
            df[column] = df[column].apply(standardize_interstate_format_final)
    
    print("Interstate standardization complete! All string columns have been overwritten.")
    
    # Drop specified columns
    columns_to_drop = [
        'Unnamed: 0', 
        'filename', 
        'record_num', 
        'parking', 
        'gray_parking', 
        'identifier', 
        'panel', 
        'p_identifier', 
        'identifier2', 
        'identifier3'
    ]
    
    # Filter list to only include columns that actually exist in the dataframe
    columns_to_drop = [col for col in columns_to_drop if col in df.columns]
    
    if columns_to_drop:
        print(f"Dropping columns: {columns_to_drop}")
        df.drop(columns=columns_to_drop, inplace=True)
        print(f"Remaining columns: {list(df.columns)}")
    else:
        print("None of the specified columns exist in the dataframe.")
    
    # Create output directory if it doesn't exist
    output_dir = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Processed_Intermediate'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the initial cleaned data (equivalent to 1.csv)
    output_path_1 = os.path.join(output_dir, '1.csv')
    df.to_csv(output_path_1, index=False)
    print(f"Initial cleaned data saved to: {output_path_1}")
    print(f"Initial dataset shape: {df.shape}")
    
    # Continue with additional processing steps from 3_5.ipynb
    print("\n" + "="*50)
    print("Starting additional processing steps (3_5 workflow)...")
    print("="*50)
    
    # Extract address components based on parentheses
    df = extract_address_components(df)
    
    # Classify address types (identify exits)
    df = classify_address_types(df)
    
    # Remove zip codes from addresses
    df = remove_zipcode_from_all_rows(df)
    
    # Clean leading dashes from addresses
    df = clean_leading_dashes(df)
    
    # Save the fully processed data (equivalent to 3_5.csv)
    output_path_3_5 = os.path.join(output_dir, '3_5.csv')
    df.to_csv(output_path_3_5, index=False)
    print(f"Fully processed data saved to: {output_path_3_5}")
    print(f"Dataset shape after 3_5 processing: {df.shape}")
    
    # Continue with additional processing steps from 3_7.ipynb
    print("\n" + "="*50)
    print("Starting additional processing steps (3_7 workflow)...")
    print("="*50)
    
    # Identify proper addresses and clean special characters
    df = identify_proper_addresses(df)
    
    # Remove "City," prefix from addresses
    df = remove_city_prefix(df)
    
    # Save the final processed data (equivalent to 3_7.csv)
    output_path_3_7 = os.path.join(output_dir, '3_7.csv')
    df.to_csv(output_path_3_7, index=False)
    print(f"Final processed data saved to: {output_path_3_7}")
    print(f"Dataset shape after 3_7 processing: {df.shape}")
    
    # Continue with additional processing steps from 4.ipynb
    print("\n" + "="*50)
    print("Starting additional processing steps (4 workflow)...")
    print("="*50)
    
    # Rename columns to remove OCR_ prefix
    df = rename_ocr_columns(df)
    
    # Clean parenthesis characters from exit addresses
    df = clean_exit_parenthesis(df)
    
    # Save the final processed data (equivalent to 4.csv)
    output_path_4 = os.path.join(output_dir, '4.csv')
    df.to_csv(output_path_4, index=False)
    print(f"Final processed data saved to: {output_path_4}")
    print(f"Dataset shape after 4 processing: {df.shape}")
    
    # Continue with additional processing steps from 4_5.ipynb
    print("\n" + "="*50)
    print("Starting additional processing steps (4_5 workflow)...")
    print("="*50)
    
    # Apply exit number extraction and OCR quality assessment
    df = apply_exit_number_extraction(df)
    
    # Save the final processed data (equivalent to 4_5.csv)
    output_path_4_5 = os.path.join(output_dir, '4_5.csv')
    df.to_csv(output_path_4_5, index=False)
    print(f"Final processed data saved to: {output_path_4_5}")
    print(f"Dataset shape after 4_5 processing: {df.shape}")
    
    # Continue with additional processing steps from 4_6.ipynb
    print("\n" + "="*50)
    print("Starting additional processing steps (4_6 workflow)...")
    print("="*50)
    
    # Apply road information extraction
    df = apply_road_extraction(df)
    
    # Save the final processed data (equivalent to 4_6.csv)
    output_path_4_6 = os.path.join(output_dir, '4_6.csv')
    df.to_csv(output_path_4_6, index=False)
    print(f"Final processed data saved to: {output_path_4_6}")
    print(f"Final dataset shape: {df.shape}")
    
    # Process TruckStopsServices data (4_7 workflow)
    print("\n" + "="*50)
    print("Starting TruckStopsServices data processing (4_7 workflow)...")
    print("="*50)
    
    # Process the truck stops data separately
    df_truck_stops = process_truck_stops_data()
    
    # Process Add_1 workflow (filtering and combining datasets)
    print("\n" + "="*50)
    print("Starting Add_1 workflow processing...")
    print("="*50)
    
    # Apply Add_1 workflow processing
    df_main_filtered, df_truck_stops_filtered = process_add_1_workflow(df, df_truck_stops)
    
    # Save the filtered and processed datasets
    output_path_add_1 = os.path.join(output_dir, 'Add_1.csv')
    df_main_filtered.to_csv(output_path_add_1, index=False)
    print(f"Filtered main dataset saved to: {output_path_add_1}")
    print(f"Filtered main dataset shape: {df_main_filtered.shape}")
    
    output_path_add_1_scraped = os.path.join(output_dir, 'Add_1_scraped.csv')
    df_truck_stops_filtered.to_csv(output_path_add_1_scraped, index=False)
    print(f"Filtered truck stops dataset saved to: {output_path_add_1_scraped}")
    print(f"Filtered truck stops dataset shape: {df_truck_stops_filtered.shape}")
    
    # Process Add_1_5 workflow (advanced address parsing)
    print("\n" + "="*50)
    print("Starting Add_1_5 workflow processing...")
    print("="*50)
    
    # Apply Add_1_5 workflow processing (advanced address parsing)
    df_main_advanced, df_truck_stops_final = process_add_1_5_workflow(df_main_filtered, df_truck_stops_filtered)
    
    # Save the final processed datasets with advanced parsing
    output_path_add_1_5 = os.path.join(output_dir, 'Add_1_5.csv')
    df_main_advanced.to_csv(output_path_add_1_5, index=False)
    print(f"Advanced parsed main dataset saved to: {output_path_add_1_5}")
    print(f"Advanced parsed main dataset shape: {df_main_advanced.shape}")
    
    output_path_add_1_5_scraped = os.path.join(output_dir, 'Add_1_5_scraped.csv')
    df_truck_stops_final.to_csv(output_path_add_1_5_scraped, index=False)
    print(f"Final truck stops dataset saved to: {output_path_add_1_5_scraped}")
    print(f"Final truck stops dataset shape: {df_truck_stops_final.shape}")
    
    # Process Add_2 workflow (data type conversions and manual corrections)
    print("\n" + "="*50)
    print("Starting Add_2 workflow processing...")
    print("="*50)
    
    # Apply Add_2 workflow processing (data type conversions and corrections)
    df_main_final, df_truck_stops_final = process_add_2_workflow(df_main_advanced, df_truck_stops_final)
    
    # Save the final corrected datasets
    output_path_add_2 = os.path.join(output_dir, 'Add_2.csv')
    df_main_final.to_csv(output_path_add_2, index=False)
    print(f"Final corrected main dataset saved to: {output_path_add_2}")
    print(f"Final corrected main dataset shape: {df_main_final.shape}")
    
    output_path_add_2_scraped = os.path.join(output_dir, 'Add_2_scraped.csv')
    df_truck_stops_final.to_csv(output_path_add_2_scraped, index=False)
    print(f"Final corrected truck stops dataset saved to: {output_path_add_2_scraped}")
    print(f"Final corrected truck stops dataset shape: {df_truck_stops_final.shape}")
    
    # Process Add_3 workflow (comprehensive data matching)
    print("\n" + "="*50)
    print("Starting Add_3 workflow processing...")
    print("="*50)
    
    # Apply Add_3 workflow processing (comprehensive data matching)
    df_main_matched, df_truck_stops_matched = process_add_3_workflow(df_main_final, df_truck_stops_final)
    
    # Save the final matched datasets
    output_path_add_3 = os.path.join(output_dir, 'Add_3.csv')
    df_main_matched.to_csv(output_path_add_3, index=False)
    print(f"Final matched main dataset saved to: {output_path_add_3}")
    print(f"Final matched main dataset shape: {df_main_matched.shape}")
    
    # Process Add_4 workflow (match success analysis)
    print("\n" + "="*50)
    print("Starting Add_4 workflow processing...")
    print("="*50)
    
    # Apply Add_4 workflow processing (match success analysis)
    df_main_analyzed, df_truck_stops_final = process_add_4_workflow(df_main_matched, df_truck_stops_matched)
    
    # Save the final analyzed dataset
    output_path_add_4 = os.path.join(output_dir, 'Add_4.csv')
    df_main_analyzed.to_csv(output_path_add_4, index=False)
    print(f"Final analyzed main dataset saved to: {output_path_add_4}")
    print(f"Final analyzed main dataset shape: {df_main_analyzed.shape}")
    
    # Continue with Yelp lookup workflow
    print("\n" + "="*50)
    print("Starting Yelp lookup workflow (4 workflow)...")
    print("="*50)
    
    # Apply Yelp 4 workflow processing (phone number matching with Yelp data)
    df_main_yelp = process_yelp_4_workflow(df_main_analyzed)
    
    # Save the dataset with Yelp matches
    output_path_yelp_4 = os.path.join(output_dir, '4.csv')
    df_main_yelp.to_csv(output_path_yelp_4, index=False)
    print(f"Dataset with Yelp matches saved to: {output_path_yelp_4}")
    print(f"Dataset with Yelp matches shape: {df_main_yelp.shape}")
    
    # Continue with Yelp 6 workflow processing
    print("\n" + "="*50)
    print("Starting Yelp lookup workflow (6 workflow)...")
    print("="*50)
    
    # Apply Yelp 6 workflow processing (column renaming and match rate indicators)
    df_main_yelp_final = process_yelp_6_workflow(df_main_yelp)
    
    # Save the final dataset with enhanced Yelp information
    output_path_yelp_6 = os.path.join(output_dir, '6.csv')
    df_main_yelp_final.to_csv(output_path_yelp_6, index=False)
    print(f"Final dataset with enhanced Yelp information saved to: {output_path_yelp_6}")
    print(f"Final dataset shape: {df_main_yelp_final.shape}")
    
    # Continue with Yelp 7_5 workflow processing
    print("\n" + "="*50)
    print("Starting Yelp lookup workflow (7_5 workflow)...")
    print("="*50)
    
    # Apply Yelp 7_5 workflow processing (row reordering operation)
    df_main_yelp_reordered = process_yelp_7_5_workflow(df_main_yelp_final)
    
    # Save the final reordered dataset
    output_path_yelp_7_5 = os.path.join(output_dir, '7_5.csv')
    df_main_yelp_reordered.to_csv(output_path_yelp_7_5, index=False)
    print(f"Final reordered dataset saved to: {output_path_yelp_7_5}")
    print(f"Final reordered dataset shape: {df_main_yelp_reordered.shape}")
    
    # Continue with Yelp 8 workflow processing
    print("\n" + "="*50)
    print("Starting Yelp lookup workflow (8 workflow)...")
    print("="*50)
    
    # Apply Yelp 8 workflow processing (sequential place identifier creation)
    df_main_yelp_place_ids = process_yelp_8_workflow(df_main_yelp_reordered)
    
    # Save the final dataset with place identifiers
    output_path_yelp_8 = os.path.join(output_dir, '8.csv')
    df_main_yelp_place_ids.to_csv(output_path_yelp_8, index=False)
    print(f"Final dataset with place identifiers saved to: {output_path_yelp_8}")
    print(f"Final dataset shape: {df_main_yelp_place_ids.shape}")
    
    # Continue with Yelp 10 workflow processing
    print("\n" + "="*50)
    print("Starting Yelp lookup workflow (10 workflow)...")
    print("="*50)
    
    # Apply Yelp 10 workflow processing (advanced place change analysis)
    df_main_yelp_changes = process_yelp_10_workflow(df_main_yelp_place_ids)
    
    # Save the final dataset with place change analysis
    output_path_yelp_10 = os.path.join(output_dir, '10.csv')
    df_main_yelp_changes.to_csv(output_path_yelp_10, index=False)
    print(f"Final dataset with place change analysis saved to: {output_path_yelp_10}")
    print(f"Final dataset shape: {df_main_yelp_changes.shape}")
    
    # Apply YellowPages 1 workflow processing (phone number matching with YellowPages data)
    df_main_yellowpages = process_yellowpages_1_workflow(df_main_yelp_changes)
    
    # Save the dataset with YellowPages matching
    output_path_yellowpages_1 = os.path.join(output_dir, '1_yellowpages.csv')
    df_main_yellowpages.to_csv(output_path_yellowpages_1, index=False)
    print(f"Dataset with YellowPages phone matching saved to: {output_path_yellowpages_1}")
    print(f"YellowPages matched dataset shape: {df_main_yellowpages.shape}")
    
    # Apply Notebooks 1 workflow processing (comprehensive data enrichment)
    df_main_enriched = process_notebooks_1_workflow(df_main_yellowpages)
    
    # Save the enriched dataset
    output_path_notebooks_1 = os.path.join(output_dir, '1_enriched.csv')
    df_main_enriched.to_csv(output_path_notebooks_1, index=False)
    print(f"Enriched dataset saved to: {output_path_notebooks_1}")
    print(f"Enriched dataset shape: {df_main_enriched.shape}")
    
    # Apply Notebooks 5 workflow processing (coordinate analysis and distance calculations)
    print("\n" + "="*50)
    print("Starting Notebooks 5 workflow processing...")
    print("="*50)
    
    df_main_final = process_notebooks_5_workflow(df_main_enriched)
    
    # Save the dataset with coordinate analysis
    output_path_notebooks_5 = os.path.join(output_dir, '5_final.csv')
    df_main_final.to_csv(output_path_notebooks_5, index=False)
    print(f"Dataset with coordinate analysis saved to: {output_path_notebooks_5}")
    print(f"Dataset shape: {df_main_final.shape}")
    
    # Apply Notebooks 8 workflow processing (manual matching and coordinate updates)
    print("\n" + "="*50)
    print("Starting Notebooks 8 workflow processing...")
    print("="*50)
    
    df_main_complete = process_notebooks_8_workflow(df_main_final)
    
    # Save the dataset with manual updates
    output_path_notebooks_8 = os.path.join(output_dir, '8_complete.csv')
    df_main_complete.to_csv(output_path_notebooks_8, index=False)
    print(f"Dataset with manual updates saved to: {output_path_notebooks_8}")
    print(f"Dataset shape: {df_main_complete.shape}")
    
    # Apply Notebooks 9 workflow processing (final coordinate consolidation)
    print("\n" + "="*50)
    print("Starting Notebooks 9 workflow processing...")
    print("="*50)
    
    df_main_final_coords = process_notebooks_9_workflow(df_main_complete)
    
    # Save the final complete dataset with final coordinates
    output_path_notebooks_9 = os.path.join(output_dir, '9_complete.csv')
    df_main_final_coords.to_csv(output_path_notebooks_9, index=False)
    print(f"Final complete dataset with final coordinates saved to: {output_path_notebooks_9}")
    print(f"Final complete dataset shape: {df_main_final_coords.shape}")
    
    print("\n" + "="*50)
    print("Data cleaning pipeline completed successfully!")
    print("="*50)
    print("Output files created:")
    print("  - 1.csv: Initial cleaning")
    print("  - 3_5.csv: Enhanced cleaning with address parsing")
    print("  - 3_7.csv: Advanced cleaning with proper address identification")
    print("  - 4.csv: Dataset with Yelp phone number matches")
    print("  - 4_5.csv: Exit number extraction and OCR quality flags")
    print("  - 4_6.csv: Complete road information extraction")
    print("  - 6.csv: Dataset with enhanced Yelp match rate indicators")
    print("  - 7_5.csv: Dataset with row reordering corrections")
    print("  - 8.csv: Dataset with sequential place identifiers")
    print("  - 10.csv: Final dataset with advanced place change analysis")
    print("  - 1_yellowpages.csv: Dataset with YellowPages phone number matching")
    print("  - 1_enriched.csv: Comprehensive dataset with all external data sources")
    print("  - 5_final.csv: Dataset with coordinate analysis and distance calculations")
    print("  - 8_complete.csv: Dataset with manual matching and coordinate updates")
    print("  - 9_complete.csv: Final dataset with consolidated coordinates")
    print("  - scraped_4_7.csv: Cleaned TruckStopsServices data with standardized chain names")
    print("  - Add_1.csv: Filtered main dataset (CA, UT, NV, AZ only)")
    print("  - Add_1_scraped.csv: Filtered truck stops dataset (CA, UT, NV, AZ only)")
    print("  - Add_1_5.csv: Advanced parsed main dataset with secondary/tertiary roads")
    print("  - Add_1_5_scraped.csv: Final truck stops dataset")
    print("  - Add_2.csv: Main dataset with data type corrections and manual fixes")
    print("  - Add_2_scraped.csv: Final truck stops dataset")
    print("  - Add_3.csv: Main dataset with comprehensive data matching columns")
    print("  - Add_4.csv: Main dataset with match success analysis and hierarchical matching")
    print("  - FINAL OUTPUT: 9_complete.csv contains complete processing with final coordinate consolidation")
    print("    using Manual coordinates first, then Mid coordinates as fallback, plus coordinate filling")
    print("    from nearby rows with the same place identifier.")
    print("\nTotal stages completed: 25")
    print("Pipeline includes: initial cleaning, address parsing, data matching, external source integration,")
    print("coordinate analysis, manual verification, and final coordinate consolidation.")

if __name__ == "__main__":
    main()