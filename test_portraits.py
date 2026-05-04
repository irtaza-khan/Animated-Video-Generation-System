import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.tools.vision_tools.image_gen_tool import generate_character_portrait

def main():
    print("=" * 60)
    print("TEST: Character Portrait Generation")
    print("=" * 60)
    
    char_name = "Agent Alpha"
    desc = "A man in a sharp black suit with sunglasses"
    print(f"\nCharacter: {char_name}")
    print(f"Description: {desc}")
    
    path = generate_character_portrait(char_name, desc)
    
    if path and os.path.exists(path):
        print(f"\nPortrait saved to: {path}")
        print(f"File size: {os.path.getsize(path)} bytes")
    else:
        print("\nFailed to generate portrait.")

if __name__ == "__main__":
    main()
