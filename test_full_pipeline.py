"""Full pipeline test - directly calls the workflow, not via HTTP."""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.workflow import run_full_pipeline

def main():
    print("=" * 60)
    print("TEST: Full Pipeline (Story -> Audio -> Video -> Compositor)")
    print("=" * 60)
    
    run_full_pipeline(
        job_id="test-run",
        prompt="A spy thriller in a rainy Tokyo alleyway",
        num_scenes=2,
    )
    
    # Check result
    import json
    with open("data/temp/test-run.json") as f:
        status = json.load(f)
    print(f"\nFinal status: {status}")
    
    if status.get("status") == "completed":
        print("\nFull pipeline completed successfully!")
        
        if os.path.exists("data/outputs/final_output.mp4"):
            size = os.path.getsize("data/outputs/final_output.mp4")
            print(f"Final video size: {size / 1024:.1f} KB")
        
        for f in os.listdir("data/outputs/audio"):
            print(f"Audio: data/outputs/audio/{f}")
    else:
        print(f"\nPipeline result: {status}")

if __name__ == "__main__":
    main()
