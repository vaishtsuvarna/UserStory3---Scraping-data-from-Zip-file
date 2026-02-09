import sys
import logging
import requests
import pandas as pd
import io
from typing import Optional
import zipfile
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger=logging.getLogger(__name__)

URL='https://www.thespreadsheetguru.com/wp-content/uploads/2022/12/EmployeeSampleData.zip'
EXPECTED_FIELDS = ['eeid', 'first name', 'last name', 'job title', 'department','business unit', 'gender', 'ethnicity', 'age', 'hire date', 'annual salary', 'bonus %', 'country', 'city', 'exit date']

def downld_extract_zip(URL: str, max_retries: int = 3) -> Optional[bytes]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt+1}/{max_retries}")
            resp = requests.get(URL, timeout=30, headers=headers)
            logger.info(f"HTTP {resp.status_code}, {len(resp.content)} bytes")
            
            if resp.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                   
                    csv_files = [f for f in z.namelist() 
                                if f.endswith('.csv') 
                                and not f.startswith('__MACOSX')]
                    if not csv_files:
                        logger.error("No CSV files found in zip")
                        return None
                    csv_files.sort()
                    first_csv = csv_files[0]
                    logger.info(f"Extracting: {first_csv}")
                    
                    return z.read(first_csv)         
            else:
                logger.warning(f"HTTP {resp.status_code}")
                
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    logger.critical(f"Download FAILED after {max_retries} attempts")
    return None

def parse_data(content: bytes):
    try:
        df = pd.read_csv(io.BytesIO(content))
        logger.info(f"CSV parsed: {df.shape[0]} rows, {len(df.columns)} cols")
    except Exception as e:
        logger.error(f"Parse failed: {e}")
        return None, None

    df.columns = [str(c).lower().strip() for c in df.columns]

    if len(df.columns) <= 1:
        logger.error("Invalid file format: garbage or unstructured data")
        return None, None
    col_map = {}
    for field in EXPECTED_FIELDS:
        match = next(
            (c for c in df.columns if any(k in c for k in field.split())),
            None
        )
        col_map[field] = match

    return df, col_map

def validate_csv(df: pd.DataFrame) -> bool:
    if df.empty:
        logger.error("CSV is empty")
        return False
    if len(df.columns) <= 1:
        logger.error("CSV file has invalid structure")
        return False
    
    required_columns = ['eeid', 'full name', 'job title', 'department','business unit', 'gender', 'ethnicity', 'age', 'hire date', 'annual salary', 'bonus %', 'country', 'city', 'exit date']
    
    df_columns_lower = [col.lower() for col in df.columns]
    for col in required_columns:
        if col not in df_columns_lower:
            logger.error(f"Missing required column: {col}")
            return False
    logger.info("CSV validation passed")
    return True

def process_clean_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    try:
        logger.info("Starting data cleaning")
      
        df_clean = df.copy()
        
        if 'full name' in df_clean.columns:
            df_clean[['first name', 'last name']] = df_clean['full name'].str.split(' ', n=1, expand=True)
            
            df_clean['last name'] = df_clean['last name'].fillna('')

            df_clean = df_clean.drop(columns=['full name'])

        else:
            logger.warning("'full name' column not found, skipping split")
     
        if 'hire date' in df_clean.columns:
            df_clean['hire date'] = pd.to_datetime(df_clean['hire date'], errors='coerce')
            
            invalid_count = df_clean['hire date'].isna().sum()
            if invalid_count > 0:
                logger.warning(f"{invalid_count} records have invalid 'hire date'")
        else:
            logger.warning("'hire date' column not found")
        
        if 'exit date' in df_clean.columns:
            df_clean['exit date'] = pd.to_datetime(df_clean['exit date'], errors='coerce')
            
            invalid_count = df_clean['exit date'].isna().sum()
        else:
            logger.warning("'exit date' column not found")

        column_order = [
            'eeid', 'first name','last name','job title','department','business unit','gender','ethnicity','age','hire date','annual salary','bonus %','country','city','exit date' ]
        
        final_columns = [col for col in column_order if col in df_clean.columns]
        
        remaining = [col for col in df_clean.columns if col not in final_columns]
        final_columns.extend(remaining)
        
        df_clean = df_clean[final_columns]
        return df_clean
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        return None


def main():
    logger.info("Starting employee data scraper")
    
    content = downld_extract_zip(URL)
    if content:
        df = pd.read_csv(io.BytesIO(content), encoding='latin-1')
        df.columns = [col.lower().strip() for col in df.columns]
    
        if validate_csv(df):
            df_clean = process_clean_data(df)
            
            if df_clean is not None:
                df_clean.to_csv('employees_cleaned.csv', index=False)
                logger.info("Sucess: employees_cleaned.csv saved")
    
    logger.info("Scraper complete")

if __name__ == "__main__":
    main()


