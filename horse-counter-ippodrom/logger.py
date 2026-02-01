import json
import os
from datetime import datetime, date

class Logger:
    def __init__(self, filename='history.json'):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def log(self, original_name, count):
        new_entry = {
            "date": str(date.today()),
            "time": datetime.now().strftime("%H:%M:%S"),
            "filename": original_name,
            "horse_count": count
        }
        
        with open(self.filename, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data.append(new_entry)
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.truncate()
