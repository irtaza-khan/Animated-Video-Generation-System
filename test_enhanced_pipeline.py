"""Full pipeline test - includes Portraits and LipSync."""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.workflow import run_full_pipeline

def main():
    print("=" * 60)
    print("TEST: Full Pipeline (Enhanced with Characters & LipSync)")
    print("=" * 60)
    
    # Using 1 scene to verify the workflow logic without waiting 20 mins
    run_full_pipeline(
        job_id="enhanced-run",
        prompt="A secret meeting between two spies in a dimly lit cafe",
        num_scenes=1,
    )
    
    import json
    with open("data/temp/enhanced-run.json") as f:
        status = json.load(f)
    print(f"\nFinal status: {status}")
    
    if status.get("status") == "completed":
        print("\nEnhanced pipeline completed!")
        
        # Verify portraits
        if os.path.exists("data/outputs/characters"):
            print(f"Portraits: {os.listdir('data/outputs/characters')}")
            
        # Verify synced video
        if os.path.exists("data/outputs/synced"):
            print(f"Synced Videos: {os.listdir('data/outputs/synced')}")

if __name__ == "__main__":
    main()
