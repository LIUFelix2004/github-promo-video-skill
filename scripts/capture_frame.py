#!/usr/bin/env python3
"""Capture a real frame of https://github.com/<user> for the video cover.

Uses the thum.io screenshot service: the first request usually returns a
"please wait" placeholder while the render queues, so we fetch twice with a
pause and keep the real PNG. Alternatives if the service is unavailable:
headless Chrome `--screenshot`, or any screenshot tool — what matters is that
the cover is a REAL captured frame of the profile page (never AI-generated).

Usage: python3 capture_frame.py <github-username> <output.png>
"""
import subprocess, sys, time

def fetch(url, dest):
    subprocess.run(["curl", "-sL", "--max-time", "120", url, "-o", dest], check=True)

def is_png(path):
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"

def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    user, out = sys.argv[1], sys.argv[2]
    url = f"https://image.thum.io/get/width/1600/crop/1000/https://github.com/{user}"
    fetch(url, out)
    if not is_png(out):
        print("first fetch was a placeholder; waiting for the render queue...")
        time.sleep(45)
        fetch(url, out)
    if not is_png(out):
        raise SystemExit("capture did not return a PNG; try again in a minute")
    print(f"saved {out}")

if __name__ == "__main__":
    main()
