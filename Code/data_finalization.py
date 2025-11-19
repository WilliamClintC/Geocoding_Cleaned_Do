"""
Data Finalization - Final Processing

This script performs the final data processing step by:
1. Loading the complete processed dataset with final coordinates
2. Filtering to keep only essential columns for the final output
3. Creating a clean, finalized dataset for analysis

This is the final step in the data cleaning pipeline.
"""

import pandas as pd
import os

def process_notebooks_10_workflow(input_path, output_dir):
    """
    Process the Notebooks\10 workflow which performs final data filtering
    and creates the clean finalized dataset.
    
    This function:
    1. Loads the complete processed dataset with final coordinates
    2. Defines essential columns to keep for the final output
    3. Filters the DataFrame to include only existing essential columns
    4. Saves the finalized dataset and supplementary dataset
    
    Parameters:
    -----------
    input_path : str
        Path to the input dataset (9_complete.csv)
    output_dir : str
        Directory to save the final output
    
    Returns:
    --------
    tuple
        (df_final, df_supplementary): The finalized DataFrame and supplementary DataFrame
    """
    print("Processing Notebooks\\10 workflow - Final data filtering and finalization...")
    
    # Load the complete processed dataset
    print(f"Loading complete dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path)
        print(f"Dataset loaded successfully with shape: {df.shape}")
    except FileNotFoundError:
        print(f"ERROR: Dataset not found at {input_path}")
        return None, None
    
    # Define the essential columns to keep in the final output (original list)
    columns_to_keep_final = [
        'clean_line1',
        'clean_line2', 
        'line3',
        'city',
        'zip_code',
        'label',
        'phone',
        'year',
        'major_city',
        'state',
        'chain',
        'Address_Type',
        'Exit_Number',
        'Exit_From_Address',
        'Exit_From_Label',
        'Main_Road',
        'Secondary_Road',
        'Exit_Number_2',
        'Exit_Number_3',
        'Tertiary_Road',
        'Scraped_phone_match_rate',
        'Yelp_phone_match_rate',
        'place_identifier(year)',
        'Yellowbook_phone_match_rate',
        'Webscraped_Phone_full_url',
        'Webscraped_PlacedMatched_full_url',
        'Yelp_URL',
        'YellowPages_SEARCH_URL',
        'Match_Comments',
        'Final_Lat',
        'Final_Long'
    ]
    
    # Define the supplementary columns list
    columns_to_keep_supplementary = [
        'clean_line1',
        'clean_line2',
        'line3',
        'city',
        'zip_code',
        'label',
        'phone',
        'year',
        'major_city',
        'state',
        'chain',
        'address_standardized_ON_parenthesis',
        'address_standardized_OFF_parenthesis',
        'Address_Type',
        'Exit_Number',
        'Main_Road',
        'Secondary_Road',
        'Exit_Number_2',
        'Exit_Number_3',
        'Tertiary_Road',
        'Scraped_zipcode_to_label_match_rate',
        'Scraped_phone_match_rate',
        'Yelp_phone_match_rate',
        'place_identifier(year)',
        'Flag_Place_Change',
        'Flag_Place_Change_Year',
        'Similarity_Score',
        'Chain_Match',
        'Previous_Year_Label',
        'Previous_Year_Chain',
        'Yellowbook_phone_match_rate',
        'Webscraped_Phone_state_id',
        'Webscraped_Phone_state',
        'Webscraped_Phone_name',
        'Webscraped_Phone_href',
        'Webscraped_Phone_full_url',
        'Webscraped_Phone_stop_type',
        'Webscraped_Phone_Chain',
        'Webscraped_Phone_Latitude',
        'Webscraped_Phone_Longitude',
        'Webscraped_Phone_LD_URL',
        'Webscraped_Phone_LD_Latitude',
        'Webscraped_Phone_LD_Longitude',
        'Webscraped_Phone_Highway',
        'Webscraped_Phone_Exit',
        'Webscraped_Phone_Street Address',
        'Webscraped_Phone_City',
        'Webscraped_Phone_State',
        'Webscraped_Phone_Postal Code',
        'Webscraped_Phone_Phone',
        'Webscraped_Phone_Fax',
        'Webscraped_Phone_# of Parking Spots',
        'Webscraped_Phone_# of Reserved Parking Spots',
        'Webscraped_Phone_# of Paid Parking Spots',
        'Webscraped_Phone_# of Fuel Lanes',
        'Webscraped_Phone_# of Showers',
        'Webscraped_Phone_# of Men\'s Showers',
        'Webscraped_Phone_# of Truck Service Bays',
        'Webscraped_Phone_Phone 2',
        'Webscraped_Phone_Unleaded',
        'Webscraped_Phone_Diesel',
        'Webscraped_Phone_Bulk Def',
        'Webscraped_Phone_Phone 3',
        'Webscraped_Phone_Phone 4',
        'Webscraped_Phone_Propane',
        'Webscraped_Phone_Phone 5',
        'Webscraped_Phone_Mile Marker',
        'Webscraped_Phone_Road Name',
        'Webscraped_Phone_Hours of Operation',
        'Webscraped_Phone_https',
        'Webscraped_Phone_http',
        'Webscraped_PlacedMatched_state_id',
        'Webscraped_PlacedMatched_state',
        'Webscraped_PlacedMatched_name',
        'Webscraped_PlacedMatched_href',
        'Webscraped_PlacedMatched_full_url',
        'Webscraped_PlacedMatched_stop_type',
        'Webscraped_PlacedMatched_Chain',
        'Webscraped_PlacedMatched_Latitude',
        'Webscraped_PlacedMatched_Longitude',
        'Webscraped_PlacedMatched_LD_URL',
        'Webscraped_PlacedMatched_LD_Latitude',
        'Webscraped_PlacedMatched_LD_Longitude',
        'Webscraped_PlacedMatched_Highway',
        'Webscraped_PlacedMatched_Exit',
        'Webscraped_PlacedMatched_Street Address',
        'Webscraped_PlacedMatched_City',
        'Webscraped_PlacedMatched_State',
        'Webscraped_PlacedMatched_Postal Code',
        'Webscraped_PlacedMatched_Phone',
        'Webscraped_PlacedMatched_Fax',
        'Webscraped_PlacedMatched_# of Parking Spots',
        'Webscraped_PlacedMatched_# of Reserved Parking Spots',
        'Webscraped_PlacedMatched_# of Paid Parking Spots',
        'Webscraped_PlacedMatched_# of Fuel Lanes',
        'Webscraped_PlacedMatched_# of Showers',
        'Webscraped_PlacedMatched_# of Men\'s Showers',
        'Webscraped_PlacedMatched_# of Truck Service Bays',
        'Webscraped_PlacedMatched_Phone 2',
        'Webscraped_PlacedMatched_Unleaded',
        'Webscraped_PlacedMatched_Diesel',
        'Webscraped_PlacedMatched_Bulk Def',
        'Webscraped_PlacedMatched_Phone 3',
        'Webscraped_PlacedMatched_Phone 4',
        'Webscraped_PlacedMatched_Propane',
        'Webscraped_PlacedMatched_Phone 5',
        'Webscraped_PlacedMatched_Mile Marker',
        'Webscraped_PlacedMatched_Road Name',
        'Webscraped_PlacedMatched_Hours of Operation',
        'Webscraped_PlacedMatched_https',
        'Webscraped_PlacedMatched_http',
        'Yelp_Original_Phone',
        'Yelp_Name',
        'Yelp_Rating',
        'Yelp_Review_Count',
        'Yelp_Address',
        'Yelp_City',
        'Yelp_State',
        'Yelp_Zip_Code',
        'Yelp_Phone',
        'Yelp_Categories',
        'Yelp_Latitude',
        'Yelp_Longitude',
        'Yelp_Price',
        'Yelp_Is_Closed',
        'Yelp_URL',
        'YellowPages_ADDRESS',
        'YellowPages_AKA',
        'YellowPages_BUSINESS_NAME',
        'YellowPages_BUSINESS_URL',
        'YellowPages_CATEGORIES',
        'YellowPages_EXTRA_PHONES',
        'YellowPages_FORMATTED_PHONE',
        'YellowPages_JSONLD_CITY_1',
        'YellowPages_JSONLD_LAT_1',
        'YellowPages_JSONLD_LNG_1',
        'YellowPages_JSONLD_NAME_1',
        'YellowPages_JSONLD_PHONE_1',
        'YellowPages_JSONLD_STATE_1',
        'YellowPages_JSONLD_STREET_1',
        'YellowPages_JSONLD_ZIP_1',
        'YellowPages_ORIGINAL_PHONE',
        'YellowPages_PHONE',
        'YellowPages_SCRAPED_AT',
        'YellowPages_SEARCH_URL',
        'YellowPages_STATUS',
        'YellowPages_WEBSITE',
        'min_distance_miles',
        'min_distance_sources',
        'Match_Comments',
        'Final_Lat',
        'Final_Long'
    ]
    
    print(f"Processing FINAL dataset...")
    print(f"Target columns for final: {len(columns_to_keep_final)}")
    
    # Filter the DataFrame for final dataset
    existing_columns_final = [col for col in columns_to_keep_final if col in df.columns]
    missing_columns_final = [col for col in columns_to_keep_final if col not in df.columns]
    df_final = df[existing_columns_final].copy()
    
    print(f"Processing SUPPLEMENTARY dataset...")
    print(f"Target columns for supplementary: {len(columns_to_keep_supplementary)}")
    
    # Filter the DataFrame for supplementary dataset
    existing_columns_supp = [col for col in columns_to_keep_supplementary if col in df.columns]
    missing_columns_supp = [col for col in columns_to_keep_supplementary if col not in df.columns]
    df_supplementary = df[existing_columns_supp].copy()
    
    # Report filtering results
    print(f"\nOriginal DataFrame shape: {df.shape}")
    print(f"Final DataFrame shape: {df_final.shape}")
    print(f"Supplementary DataFrame shape: {df_supplementary.shape}")
    print(f"Final columns kept: {len(existing_columns_final)} out of {len(columns_to_keep_final)} requested")
    print(f"Supplementary columns kept: {len(existing_columns_supp)} out of {len(columns_to_keep_supplementary)} requested")
    
    if missing_columns_final:
        print(f"Missing columns in FINAL dataset: {missing_columns_final}")
    if missing_columns_supp:
        print(f"Missing columns in SUPPLEMENTARY dataset: {missing_columns_supp}")
    
    # Save both datasets
    final_output_path = os.path.join(output_dir, '10_final.csv')
    supp_output_path = os.path.join(output_dir, '10_supplementary.csv')
    
    df_final.to_csv(final_output_path, index=False)
    df_supplementary.to_csv(supp_output_path, index=False)
    
    print(f"Final dataset saved to: {final_output_path}")
    print(f"Supplementary dataset saved to: {supp_output_path}")
    
    # Display summary statistics
    print(f"\nFinal dataset summary:")
    print(f"  Total rows: {len(df_final)}")
    print(f"  Total columns: {len(df_final.columns)}")
    
    print(f"\nSupplementary dataset summary:")
    print(f"  Total rows: {len(df_supplementary)}")
    print(f"  Total columns: {len(df_supplementary.columns)}")
    
    print(f"\nData completeness for key fields:")
    # Check completeness of critical fields
    key_fields = ['Final_Lat', 'Final_Long', 'phone', 'label', 'place_identifier(year)']
    for field in key_fields:
        if field in df_supplementary.columns:
            non_null_count = df_supplementary[field].notna().sum()
            completeness = (non_null_count / len(df_supplementary)) * 100
            print(f"    {field}: {non_null_count}/{len(df_supplementary)} ({completeness:.1f}%)")
    
    return df_final, df_supplementary

def main():
    """
    Main function to execute the data finalization workflow.
    """
    print("="*60)
    print("DATA FINALIZATION PIPELINE")
    print("="*60)
    
    # Define paths
    input_path = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Processed_Intermediate\9_complete.csv'
    output_dir = r'C:\Users\clint\Desktop\Geocoding_Cleaned_Documentation\Data\Processed_Final'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Process the final workflow
    df_final, df_supplementary = process_notebooks_10_workflow(input_path, output_dir)
    
    if df_final is not None and df_supplementary is not None:
        print("\n" + "="*60)
        print("DATA FINALIZATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Final outputs created:")
        print("  - 10_final.csv: Clean finalized dataset with essential columns")
        print(f"    Shape: {df_final.shape}")
        print(f"    Location: {os.path.join(output_dir, '10_final.csv')}")
        print("  - 10_supplementary.csv: Extended dataset with detailed analysis columns")
        print(f"    Shape: {df_supplementary.shape}")
        print(f"    Location: {os.path.join(output_dir, '10_supplementary.csv')}")
        print("\nThe datasets are now ready for analysis:")
        print("\n10_final.csv contains:")
        print("  - Core address and location information")
        print("  - Exit numbers and road information") 
        print("  - External data source URLs for verification")
        print("  - Match rates from different data sources")
        print("  - Final consolidated coordinates")
        print("  - Place identifiers for time series analysis")
        print("\n10_supplementary.csv additionally contains:")
        print("  - Place change detection flags and analysis")
        print("  - Detailed web scraped facility information")
        print("  - Complete Yelp business data")
        print("  - Full Yellow Pages information")
        print("  - Address standardization variants")
        print("  - Comprehensive match rate details")
        print("  - Distance calculations and geocoding metadata")
    else:
        print("ERROR: Data finalization failed!")

if __name__ == "__main__":
    main()
