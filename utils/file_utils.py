import os
import pandas as pd
from typing import Tuple, Optional

def validate_csv_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a CSV file has the required columns for backtesting
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        df = pd.read_csv(file_path)
        
        # Check for required columns (case insensitive)
        required_cols = ['open', 'high', 'low', 'close']
        lower_cols = [col.lower() for col in df.columns]
        
        missing_cols = [col for col in required_cols if col not in lower_cols]
        
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
        
        return True, None
    except Exception as e:
        return False, f"Error validating CSV file: {str(e)}"