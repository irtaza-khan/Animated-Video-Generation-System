"""Full pipeline test - verify Gender/Visual consistency."""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.workflow import run_full_pipeline

def main():
    print("=" * 60)
    print("TEST: Gender/Visual Consistency (Agent A=Male, Agent B=Female)")
    print("=" * 60)
    
    # Run a test with a prompt that triggers a conversation
    run_full_pipeline(
        job_id="gender-fix-run",
        prompt="A tense conversation between a male detective and a female suspect",
        num_scenes=1,
    )
    
    import json
    with open("data/temp/gender-fix-run.json") as f:
        status = json.load(f)
    print(f"\nFinal status: {status}")
    
    if status.get("status") == "completed":
        print("\nPipeline completed! Please check 'data/outputs/final_output.mp4' to verify:")
        print("1. Agent A has a male voice and Agent B has a female voice.")
        print("2. The visual prompt (check console) included 'mysterious woman'.")
        print("3. Lips only move for the active speaker segment.")

if __name__ == "__main__":
    main()
