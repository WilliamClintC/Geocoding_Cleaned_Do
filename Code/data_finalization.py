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
    4. Saves the finalized dataset
    
    Parameters:
    -----------
    input_path : str
        Path to the input dataset (9_complete.csv)
    output_dir : str
        Directory to save the final output
    
    Returns:
    --------
    pandas.DataFrame
        The finalized DataFrame with essential columns only
    """
    print("Processing Notebooks\\10 workflow - Final data filtering and finalization...")
    
    # Load the complete processed dataset
    print(f"Loading complete dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path)
        print(f"Dataset loaded successfully with shape: {df.shape}")
    except FileNotFoundError:
        print(f"ERROR: Dataset not found at {input_path}")
        return None
    
    # Define the essential columns to keep in the final output
    columns_to_keep = [
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
    
    print(f"Filtering dataset to essential columns...")
    print(f"Target columns: {len(columns_to_keep)}")
    
    # Filter the DataFrame to keep only existing columns from our target list
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    missing_columns = [col for col in columns_to_keep if col not in df.columns]
    
    # Apply the filter
    df_filtered = df[existing_columns].copy()
    
    # Report filtering results
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Filtered DataFrame shape: {df_filtered.shape}")
    print(f"Columns kept: {len(existing_columns)} out of {len(columns_to_keep)} requested")
    
    if missing_columns:
        print(f"Missing columns (not found in dataset): {missing_columns}")
    
    # Save the finalized dataset
    output_path = os.path.join(output_dir, '10_final.csv')
    df_filtered.to_csv(output_path, index=False)
    print(f"Finalized dataset saved to: {output_path}")
    
    # Display summary statistics
    print(f"\nFinalized dataset summary:")
    print(f"  Total rows: {len(df_filtered)}")
    print(f"  Total columns: {len(df_filtered.columns)}")
    print(f"  Data completeness for key fields:")
    
    # Check completeness of critical fields
    key_fields = ['Final_Lat', 'Final_Long', 'phone', 'label', 'place_identifier(year)']
    for field in key_fields:
        if field in df_filtered.columns:
            non_null_count = df_filtered[field].notna().sum()
            completeness = (non_null_count / len(df_filtered)) * 100
            print(f"    {field}: {non_null_count}/{len(df_filtered)} ({completeness:.1f}%)")
    
    return df_filtered

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
    df_final = process_notebooks_10_workflow(input_path, output_dir)
    
    if df_final is not None:
        print("\n" + "="*60)
        print("DATA FINALIZATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Final output created:")
        print("  - 10_final.csv: Clean finalized dataset with essential columns")
        print(f"    Shape: {df_final.shape}")
        print(f"    Location: {os.path.join(output_dir, '10_final.csv')}")
        print("\nThe dataset is now ready for analysis and contains:")
        print("  ✓ Core address and location information")
        print("  ✓ Exit numbers and road information") 
        print("  ✓ External data source URLs for verification")
        print("  ✓ Match rates from different data sources")
        print("  ✓ Final consolidated coordinates")
        print("  ✓ Place identifiers for time series analysis")
    else:
        print("ERROR: Data finalization failed!")

if __name__ == "__main__":
    main()
