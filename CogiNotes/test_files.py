import os, sys
sys.path.insert(0, os.getcwd())
from database import db

BASE_DIR = os.getcwd()
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

def load_uploaded_files():
    try:
        meta = db.get_all_file_metadata()
        if meta is None:
            meta = {}
    except Exception as e:
        print(f"Error loading file metadata: {e}")
        meta = {}
    
    files = []
    try:
        for fname in sorted(os.listdir(UPLOADS_DIR)):
            fpath = os.path.join(UPLOADS_DIR, fname)
            if os.path.isfile(fpath):
                ext  = os.path.splitext(fname)[1].lower().lstrip(".")
                info = meta.get(fname, {})
                # Only show approved files to regular users
                if info.get("status") == "approved" or not info:
                    files.append({
                        "name":    fname,
                        "type":    ext.upper(),
                        "path":    fpath,
                        "course":  info.get("course", ""),
                        "topic":   info.get("topic", ""),
                        "program": info.get("program", ""),
                        "uploader": info.get("uploader", ""),
                        "date":    info.get("date", ""),
                    })
    except Exception as e:
        print(f"Error loading files: {e}")
    
    return files

files = load_uploaded_files()
print(f"Found {len(files)} approved files:")
for f in files:
    print(f"  - {f['name']} ({f['type']})")
