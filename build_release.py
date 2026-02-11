"""Build helper for one-click desktop binaries using PyInstaller.

Usage:
    python build_release.py
"""

import subprocess
import sys


def run(cmd):
    print(" ".join(cmd))
    subprocess.check_call(cmd)


def main():
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "gymratHD",
        "gymratHD.py",
    ])
    print("\nBuild complete. Check dist/gymratHD")


if __name__ == "__main__":
    main()
