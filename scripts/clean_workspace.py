import os
import glob
import shutil

def cleanup():
    # 1. Delete templates in data/templates
    template_files = glob.glob("data/templates/*.json")
    for f in template_files:
        try:
            os.remove(f)
            print(f"Removed template: {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")

    # 2. Clean temporary files in .local_data/worlds and .local_data/screens
    world_files = glob.glob(".local_data/worlds/*.json")
    for f in world_files:
        try:
            os.remove(f)
        except Exception as e:
            pass
    print(f"Cleaned {len(world_files)} temporary files in .local_data/worlds/")

    screen_files = glob.glob(".local_data/screens/*.json")
    for f in screen_files:
        try:
            os.remove(f)
        except Exception as e:
            pass
    print(f"Cleaned {len(screen_files)} temporary files in .local_data/screens/")

if __name__ == "__main__":
    cleanup()
