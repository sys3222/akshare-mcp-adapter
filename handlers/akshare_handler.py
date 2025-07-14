import logging
import json
import pandas as pd
import io

from models.schemas import AkShareCodeRequest, AkShareCodeResponse

logger = logging.getLogger("mcp-unified-service")

def handle_execute_akshare_code(request: AkShareCodeRequest) -> AkShareCodeResponse:
    """
    Executes a snippet of AkShare code and returns the result in the specified format.
    """
    try:
        # Prepare the execution namespace
        namespace = {
            "ak": __import__("akshare"),
            "pd": pd,
            "np": __import__("numpy"),
        }
        
        # Execute the user's code
        exec(request.code, namespace)
        
        # Find the result variable in the namespace
        result_var = None
        for var_name, var_value in namespace.items():
            if isinstance(var_value, pd.DataFrame) and var_name not in ["pd", "ak", "np"]:
                result_var = var_value
                break  # Prioritize DataFrame
        
        if result_var is None:
            for var_name, var_value in namespace.items():
                if (isinstance(var_value, (list, dict)) and 
                    var_name not in ["pd", "ak", "np"] and
                    not var_name.startswith("__")):
                    result_var = var_value
                    break

        if result_var is None:
            return AkShareCodeResponse(
                result="No DataFrame, list, or dict found as a result in the executed code.",
                format="text",
                error="No result found"
            )

        # Format the result
        output_format = request.format.lower()
        if output_format == "json":
            if isinstance(result_var, pd.DataFrame):
                result = json.loads(result_var.to_json(orient="records", date_format="iso"))
            else:
                result = result_var
            return AkShareCodeResponse(result=result, format="json")
        
        elif output_format == "csv":
            if isinstance(result_var, pd.DataFrame):
                csv_buffer = io.StringIO()
                result_var.to_csv(csv_buffer, index=False)
                result = csv_buffer.getvalue()
            else:
                result = str(result_var)
            return AkShareCodeResponse(result=result, format="csv")

        elif output_format == "html":
            if isinstance(result_var, pd.DataFrame):
                result = result_var.to_html(index=False, classes='table table-striped text-center', justify='center')
            else:
                result = f"<pre>{str(result_var)}</pre>"
            return AkShareCodeResponse(result=result, format="html")
            
        else:
            return AkShareCodeResponse(
                result=f"Unsupported format: '{request.format}'. Please use 'json', 'csv', or 'html'.",
                format="text",
                error="Unsupported format"
            )

    except Exception as e:
        logger.error(f"Error executing AkShare code: {e}")
        return AkShareCodeResponse(
            result=[],
            format=request.format,
            error=f"Error executing AkShare code: {str(e)}"
        )
