import requests
import os
import json

def test_backtest_api():
    """Test the backtest API endpoint"""
    
    # API endpoint
    url = "http://localhost:12000/api/backtest"
    
    # Paths to test files
    strategy_file = os.path.join(os.path.dirname(__file__), "sample_strategy.py")
    data_file = os.path.join(os.path.dirname(__file__), "data", "sample_data.csv")
    
    # Strategy parameters
    params = json.dumps({
        "fast_period": 5,
        "slow_period": 20
    })
    
    # Prepare files for upload
    files = {
        "strategy_file": open(strategy_file, "rb"),
        "data_file": open(data_file, "rb")
    }
    
    # Prepare form data
    data = {
        "params": params
    }
    
    try:
        # Make the request
        response = requests.post(url, files=files, data=data)
        
        # Close file handles
        for file in files.values():
            file.close()
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print("Backtest successful!")
            print("\nMetrics:")
            for key, value in result["metrics"].items():
                print(f"  {key}: {value}")
            
            print("\nChart data received (base64 encoded)")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Close file handles in case of exception
        for file in files.values():
            if not file.closed:
                file.close()
        return False

if __name__ == "__main__":
    test_backtest_api()