#!/bin/bash

# Automated Test Script for LLM API

# --- Configuration ---
BASE_URL="http://127.0.0.1:12001"
TOKEN_URL="${BASE_URL}/api/token"
CHAT_URL="${BASE_URL}/api/llm/chat/completions"
TEST_CASES_FILE="llm_test_cases.json"

# --- Helper Functions ---
function print_header() {
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
}

function check_jq() {
    if ! command -v jq &> /dev/null; then
        echo "Error: 'jq' is not installed. Please install it to run this script."
        exit 1
    fi
}

# --- Main Script ---

# 1. Check for dependencies
check_jq

# 2. Get Access Token
print_header "Attempting to get access token..."
TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=testpassword")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    echo "Error: Failed to retrieve access token."
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi
echo "Successfully retrieved access token."

# 3. Read test cases and run tests
if [ ! -f "$TEST_CASES_FILE" ]; then
    echo "Error: Test cases file not found at '$TEST_CASES_FILE'"
    exit 1
fi

jq -c '.test_cases[]' "$TEST_CASES_FILE" | while read -r test_case; do
    NAME=$(echo "$test_case" | jq -r '.name')
    PROMPT=$(echo "$test_case" | jq -r '.prompt')

    print_header "Running Test: $NAME"
    echo "Prompt: $PROMPT"
    
    # Construct the JSON payload
    JSON_PAYLOAD=$(jq -n --arg prompt "$PROMPT" --arg model "gemini-1.5-flash-latest" \
        '{prompt: $prompt, model: $model}')

    # Make the API call
    API_RESPONSE=$(curl -s -X POST "$CHAT_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$JSON_PAYLOAD")

    # Extract and print the response text
    RESPONSE_TEXT=$(echo "$API_RESPONSE" | jq -r '.response')
    
    echo -e "\n--- LLM Response ---"
    echo "$RESPONSE_TEXT"
    echo -e "--------------------\n"
done

print_header "All tests completed."
