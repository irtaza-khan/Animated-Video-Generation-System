import sys
import os
import time
from fastapi.testclient import TestClient

# Add current dir to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

def main():
    client = TestClient(app)
    
    print("Sending request to /api/generate...")
    
    payload = {
        "story": {
            "scenes": [
                {
                    "id": 1,
                    "visual_prompt": "A beautiful fast test scene",
                    "dialogue": "Let's go fast.",
                    "characters": []
                }
            ]
        }
    }
    
    response = client.post("/api/generate", json=payload)
    data = response.json()
    print(f"Response: {data}")
    
    job_id = data.get("job_id")
    if not job_id:
        print("Failed to get job_id")
        return
        
    print(f"\nPolling status for job {job_id}...")
    for _ in range(15):
        status_res = client.get(f"/api/status/{job_id}")
        s_data = status_res.json()
        print(f"Status: {s_data}")
        
        if s_data.get("status") == "completed":
            print("\nJob completed successfully!")
            break
        elif "error" in s_data.get("status", ""):
            print(f"\nJob failed: {s_data}")
            break
            
        time.sleep(1)

if __name__ == "__main__":
    main()
