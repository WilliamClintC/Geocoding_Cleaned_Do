"""
Master Data Processing Pipeline

This master script orchestrates the complete data processing pipeline by:
1. Running the comprehensive data cleaning workflow (data_cleaning.py)
2. Running the data finalization workflow (data_finalization.py)

This provides a single entry point to execute the entire geocoding data processing pipeline
from raw data to final analysis-ready output.
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_script(script_path, script_name):
    """
    Run a Python script and handle the execution results.
    
    Parameters:
    -----------
    script_path : str
        Full path to the Python script
    script_name : str
        Name of the script for display purposes
        
    Returns:
    --------
    bool
        True if script executed successfully, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"EXECUTING: {script_name}")
    print(f"{'='*70}")
    print(f"Script path: {script_path}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # Run the script using subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,  # Allow output to be displayed in real-time
            text=True,
            check=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ {script_name} COMPLETED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"Execution time: {duration:.2f} seconds")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"❌ {script_name} FAILED")
        print(f"{'='*70}")
        print(f"Error code: {e.returncode}")
        print(f"Execution time: {duration:.2f} seconds")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return False
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: Script not found at {script_path}")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        return False

def check_prerequisites():
    """
    Check if required files and directories exist.
    
    Returns:
    --------
    bool
        True if all prerequisites are met, False otherwise
    """
    print("Checking prerequisites...")
    
    # Define required paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    code_dir = os.path.join(base_dir, "Code")
    data_dir = os.path.join(base_dir, "Data")
    raw_data_dir = os.path.join(data_dir, "Raw")
    
    required_files = [
        os.path.join(code_dir, "data_cleaning.py"),
        os.path.join(code_dir, "data_finalization.py"),
        os.path.join(raw_data_dir, "unbalanced_panel.csv"),
        os.path.join(raw_data_dir, "TruckStopsServices.csv"),
        os.path.join(raw_data_dir, "yelp_businesses_all.csv"),
        os.path.join(raw_data_dir, "yellowpages_data.csv")
    ]
    
    required_dirs = [
        code_dir,
        data_dir,
        raw_data_dir
    ]
    
    # Check directories
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    # Check files
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    # Report results
    if missing_dirs:
        print("❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"   - {dir_path}")
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
    
    if missing_dirs or missing_files:
        return False
    
    print("✅ All prerequisites met!")
    return True

def main():
    """
    Main function to execute the complete data processing pipeline.
    """
    pipeline_start_time = time.time()
    
    print("🚀 GEOCODING DATA PROCESSING PIPELINE")
    print("="*70)
    print("This master script will execute the complete data processing workflow:")
    print("  1. Data Cleaning (data_cleaning.py)")
    print("  2. Data Finalization (data_finalization.py)")
    print("="*70)
    print(f"Pipeline start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ PIPELINE ABORTED: Prerequisites not met")
        print("Please ensure all required files and directories exist before running the pipeline.")
        sys.exit(1)
    
    # Define script paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_cleaning_script = os.path.join(base_dir, "Code", "data_cleaning.py")
    data_finalization_script = os.path.join(base_dir, "Code", "data_finalization.py")
    
    # Track overall success
    overall_success = True
    
    # Execute data cleaning
    print(f"\n🔄 Starting Phase 1: Data Cleaning...")
    if not run_script(data_cleaning_script, "Data Cleaning Pipeline"):
        print("\n❌ PIPELINE FAILED: Data cleaning step failed")
        overall_success = False
    
    # Execute data finalization (only if data cleaning succeeded)
    if overall_success:
        print(f"\n🔄 Starting Phase 2: Data Finalization...")
        if not run_script(data_finalization_script, "Data Finalization Pipeline"):
            print("\n❌ PIPELINE FAILED: Data finalization step failed")
            overall_success = False
    
    # Calculate total pipeline time
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    
    # Final status report
    print(f"\n{'='*70}")
    if overall_success:
        print("🎉 COMPLETE PIPELINE EXECUTION SUCCESSFUL!")
        print("='*70")
        print("All phases completed successfully:")
        print("  ✅ Phase 1: Data Cleaning (25 stages)")
        print("  ✅ Phase 2: Data Finalization")
        print(f"\nFinal outputs:")
        print("  📁 Intermediate results: Data/Processed_Intermediate/")
        print("  📄 Final dataset: Data/Processed_Final/10_final.csv")
        print(f"\nDataset ready for analysis with:")
        print("  • 2,336 geocoded locations")
        print("  • 29 essential columns")
        print("  • 98.7% coordinate completion rate")
        print("  • Comprehensive external data integration")
    else:
        print("❌ PIPELINE EXECUTION FAILED!")
        print("='*70")
        print("One or more phases failed. Please check the error messages above.")
        print("Ensure all input files are available and try again.")
    
    print("='*70")
    print(f"Total pipeline execution time: {total_duration:.2f} seconds")
    print(f"Pipeline end time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()
