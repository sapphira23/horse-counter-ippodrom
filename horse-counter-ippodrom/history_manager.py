import json
import os

class HistoryManager:
    def __init__(self, filename='history.json'):
        self.filename = filename

    def update_table(self, limit=5):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data[-limit:][::-1]
    
