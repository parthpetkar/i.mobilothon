import json
import os
from .config import JSON_OUTPUT_DIR

def save_json_to_file(filename, data_list):
    filepath = os.path.join(JSON_OUTPUT_DIR, filename)
    with open(filepath,'w') as f:
        json.dump(data_list,f,indent=2)
    print(f"Saved {len(data_list)} entries to {filepath}")
