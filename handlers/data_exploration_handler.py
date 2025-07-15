import pandas as pd
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, List
import io
from pathlib import Path

# Define a maximum file size limit (e.g., 10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def handle_explore_data_from_file(
    file_path: Path, page: int, page_size: int
) -> Dict[str, Any]:
    """
    Reads a CSV file from a given path, paginates the data, and returns it.
    """
    try:
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds the limit of {MAX_FILE_SIZE / 1024 / 1024} MB."
            )

        df = pd.read_csv(file_path)

        total_records = len(df)
        total_pages = (total_records + page_size - 1) // page_size
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_df = df.iloc[start_index:end_index]

        # Convert DataFrame to a list of dictionaries for JSON serialization
        data_list = paginated_df.to_dict(orient='records')

        return {
            "data": data_list,
            "total_pages": total_pages,
            "current_page": page,
            "total_records": total_records,
            "error": None,
        }
    except HTTPException as e:
        # Re-raise HTTPException to keep its status code and detail
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {e}")
