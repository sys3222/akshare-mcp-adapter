import logging
import os
import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from google.generativeai import GenerativeModel, configure
from google.generativeai.types import GenerationConfig, Tool, FunctionDeclaration, HarmCategory, HarmBlockThreshold

from handlers.mcp_handler import _get_and_normalize_akshare_data
from core.security import get_current_active_user
from models.schemas import User

# --- Constants and Configuration ---

# Configure the Gemini API with the key from environment variables
try:
    configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    raise RuntimeError("GEMINI_API_KEY environment variable not set.")

# Define the model and generation configuration
MODEL_NAME = "gemini-1.5-pro-latest"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- Tool Definition ---

def load_akshare_tool_definitions() -> List[Dict[str, Any]:
    """Loads AkShare interface definitions from the JSON file."""
    try:
        with open("akshare_interfaces.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading AkShare tool definitions: {e}")
        return []

# Define the primary tool for the LLM to use
GET_AKSHARE_DATA_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="get_akshare_data",
            description=(
                "Fetches various types of Chinese financial market data using the AkShare library. "
                "Use this tool to get information about stocks, futures, funds, bonds, forex, and economic indicators from China."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "The specific AkShare data interface (function name) to call.",
                    },
                    "params": {
                        "type": "object",
                        "description": "A dictionary of parameters to pass to the AkShare interface.",
                        "properties": {},  # Parameters are dynamic based on the interface
                    },
                },
                "required": ["interface", "params"],
            },
        )
    ]
)

# --- Router Setup ---

router = APIRouter()
logger = logging.getLogger("mcp-unified-service")

# --- System Instructions and Prompts ---

def get_system_instructions() -> str:
    """
    Generates the system instruction prompt for the LLM, including the list of available tools.
    """
    akshare_tools = load_akshare_tool_definitions()
    tool_descriptions = "\n".join(
        f"- `{tool['name']}`: {tool['description']}" for tool in akshare_tools
    )
    
    return f"""
You are a powerful financial data assistant specializing in the Chinese market. 
Your role is to help users by fetching data using the `get_akshare_data` tool.

**Instructions:**
1.  **Analyze the user's request** to identify the specific financial data they need.
2.  **Select the most appropriate AkShare interface** from the list below to fulfill the request.
3.  **Construct the `params` dictionary** needed for the chosen interface.
4.  **Call the `get_akshare_data` tool** with the correct `interface` and `params`.
5.  If the tool returns data, present it clearly to the user.
6.  If the tool returns an error or you cannot fulfill the request, inform the user clearly.

**Available AkShare Interfaces:**
{tool_descriptions}
"""

# --- Core Logic ---

@router.post("/chat/completions", tags=["LLM"])
async def llm_chat_completions(
    prompt: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Handles a user's natural language query, uses the LLM to decide which tool to call,
    executes the tool, and returns the final response from the LLM.
    """
    try:
        model = GenerativeModel(
            MODEL_NAME,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
            tools=[GET_AKSHARE_DATA_TOOL],
            system_instruction=get_system_instructions(),
        )
        
        chat_session = model.start_chat()
        
        # Send the user's prompt to the model
        response = chat_session.send_message(prompt)
        
        # Check if the model decided to call a tool
        if response.function_calls:
            tool_call = response.function_calls[0]
            
            if tool_call.name == "get_akshare_data":
                interface = tool_call.args.get("interface")
                params = tool_call.args.get("params", {})
                
                if not interface:
                    raise HTTPException(status_code=400, detail="LLM did not provide an interface.")
                
                # Execute the backend function to get data
                api_response_data = await _get_and_normalize_akshare_data(interface, params)
                
                # Send the tool's result back to the model
                response = chat_session.send_message(
                    Part.from_function_response(
                        name="get_akshare_data",
                        response={"data": api_response_data},
                    )
                )

        return {"response": response.text}

    except Exception as e:
        logger.error(f"Error in LLM chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
