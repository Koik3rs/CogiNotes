import sys
import os

# Redirect output to file
log_file = open("app_debug.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

print("Starting app...")
sys.stdout.flush()

# Now run the app
os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open("study_buddy.py", "r", encoding="utf-8") as f:
    exec(f.read())
