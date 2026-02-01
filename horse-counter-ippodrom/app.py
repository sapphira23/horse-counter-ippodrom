import os
from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, date
from yolo_model import Model
import pandas as pd
from flask import send_file
from logger import Logger
import json
from history_manager import HistoryManager

data_logger = Logger()
model = Model()
history_manager = HistoryManager()

app = Flask(__name__)

RESULT_DIR = os.path.join('static', 'results')
os.makedirs(RESULT_DIR, exist_ok=True)


REPORT_FOLDER = os.path.join(os.getcwd(), 'reports')
os.makedirs(REPORT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    recent_history = history_manager.update_table()
    return render_template('index.html', history=recent_history)


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return "Файл не найден", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400

    if file:
        filename = secure_filename(file.filename)
        today = str(date.today())

        target_dir = os.path.join(RESULT_DIR, today)
        os.makedirs(target_dir, exist_ok=True)
        
        source_path = os.path.join(target_dir, filename)
        file.save(source_path)

        horse_count = model.get_processed_images(source_path, target_dir, False)

        data_logger.log(filename, horse_count)
        recent_history = history_manager.update_table()
        
        return render_template('index.html', 
                               image_path=f"results/{today}/{filename}", 
                               count=horse_count,
                               history=recent_history)


@app.route('/download/<format>')
def download_report(format):
    if format == 'json':
        return send_file('history.json', as_attachment=True)
    
    if format == 'excel':

        with open('history.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        excel_path = f'reports/history_report_{str(date.today())}_{datetime.now().strftime("%H-%M-%S")}.xlsx'
        df.to_excel(excel_path, index=False)

        return send_file(excel_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
