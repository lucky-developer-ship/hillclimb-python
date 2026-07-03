import os
import subprocess
import sys


def main():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(src_dir)

    if not os.path.exists("PressStart2P-Regular.ttf"):
        print("WARNING: PressStart2P-Regular.ttf not found in source folder.")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name",
        "HillClimbRacing",
        "--add-data",
        f"PressStart2P-Regular.ttf{os.pathsep}.",
        "--add-data",
        f"hillclimb_save.json{os.pathsep}.",
        "main.py",
    ]

    print("Running PyInstaller...")
    subprocess.check_call(cmd)
    print(f"\nBuild complete! Executable in: {os.path.join(src_dir, 'dist', 'HillClimbRacing.exe')}")


if __name__ == "__main__":
    main()
