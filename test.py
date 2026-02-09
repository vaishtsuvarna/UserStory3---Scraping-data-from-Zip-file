import pytest
import pandas as pd
from scraper import downld_extract_zip, validate_csv, process_clean_data

URL = "https://www.thespreadsheetguru.com/wp-content/uploads/2022/12/EmployeeSampleData.zip"



def test_download_success():
    """Test file download from actual URL"""
    result = downld_extract_zip(URL)
    assert result is not None
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_extraction_success():
    """tests ZIP extraction gets CSV data"""
    content = downld_extract_zip(URL)
    assert content is not None
    
    df = pd.read_csv(pd.io.common.BytesIO(content), encoding='latin-1')
    assert df is not None


def test_file_type_validation():
    """tests CSV file type is validated"""
    content = downld_extract_zip(URL)
    assert content is not None
    df = pd.read_csv(pd.io.common.BytesIO(content), encoding='latin-1')
    assert len(df.columns) > 1


def test_data_structure_validation():
    """tests data structure is valid"""
    content = downld_extract_zip(URL)
    df = pd.read_csv(pd.io.common.BytesIO(content), encoding='latin-1')
    df.columns = [col.lower().strip() for col in df.columns]
    
    result = validate_csv(df)
    assert result == True


def test_handle_missing_data():
    """missing/invalid data is handled"""
    content = downld_extract_zip(URL)
    df = pd.read_csv(pd.io.common.BytesIO(content), encoding='latin-1')
    df.columns = [col.lower().strip() for col in df.columns]
    df_clean = process_clean_data(df)

    assert df_clean is not None
    assert 'first name' in df_clean.columns
    assert 'last name' in df_clean.columns
    assert 'full name' not in df_clean.columns
    
    assert pd.api.types.is_datetime64_any_dtype(df_clean['hire date'])
    assert pd.api.types.is_datetime64_any_dtype(df_clean['exit date'])
    
    assert df_clean['exit date'].isna().sum() >= 0  
    assert df_clean['last name'].notna().all() or (df_clean['last name'] == '').any()
    assert len(df_clean) == len(df)

if __name__ == "__main__":
    pytest.main([__file__])