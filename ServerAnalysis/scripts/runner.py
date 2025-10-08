import requests
import time
from datetime import datetime, timedelta
import json

def get_august_dates():
    """Generate all dates for August 2025"""
    start_date = datetime(2025,7, 1)
    end_date = datetime(2025, 7, 31)
    
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    return dates

def run_august_analysis():
    """Run analysis for all days of August 2025"""
    base_url = "http://localhost:8000"
    endpoint = "/api/analysis/daily"
    
    august_dates = get_august_dates()
    
    print(f"Starting analysis for {len(august_dates)} days in August 2025...")
    print(f"Endpoint: {base_url}{endpoint}")
    print("-" * 50)
    
    # Start total runtime timer
    start_time = time.perf_counter()
    
    for i, date in enumerate(august_dates, 1):
        payload = {"date": date}
        
        try:
            print(f"[{i:2d}/{len(august_dates)}] Processing date: {date}")
            
            response = requests.post(
                f"{base_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"Success - Status: {response.status_code}")
                if response.text:
                    try:
                        result = response.json()
                        print(f"Response: {json.dumps(result, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Response: {response.text}")
            else:
                print(f"Error - Status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"    Request failed: {e}")
        
        # Wait 2 seconds before next request (except for the last one)
        if i < len(august_dates):
            print("Waiting 8 seconds...")
            time.sleep(8)
        
        print()
    
    # Calculate and print total runtime
    elapsed_seconds = time.perf_counter() - start_time
    elapsed_td = timedelta(seconds=int(elapsed_seconds))
    elapsed_ms = int((elapsed_seconds - int(elapsed_seconds)) * 1000)
    print("=" * 50)
    print(f"Total time: {elapsed_td}.{elapsed_ms:03d}")
    print("August analysis complete!")

if __name__ == "__main__":
    run_august_analysis()
