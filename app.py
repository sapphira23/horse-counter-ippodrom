import os
import json
import cv2
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from ultralytics import YOLO
from PIL import Image
import io
from fpdf import FPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['HISTORY_FILE'] = 'history.json'

# Создаём папки
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['RESULT_FOLDER']).mkdir(parents=True, exist_ok=True)

# Загружаем предобученную модель
model = YOLO('yolov8n.pt')

# Инициализируем историю
if not os.path.exists(app.config['HISTORY_FILE']):
    with open(app.config['HISTORY_FILE'], 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_history():
    with open(app.config['HISTORY_FILE'], 'r', encoding='utf-8') as f:
        return json.load(f)

def save_history(entry):
    history = load_history()
    history.append(entry)
    with open(app.config['HISTORY_FILE'], 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не загружен'}), 400
    
    file = request.files['file']
    input_type = request.form.get('type', 'image')  # image, video, stream
    
    if file.filename == '':
        return jsonify({'error': 'Пустое имя файла'}), 400
    
    # Сохраняем файл
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Обрабатываем изображение
    img = cv2.imread(filepath)
    results = model(img, classes=[17])  # класс 17 = horse
    
    horse_count = 0
    for r in results:
        horse_count += len(r.boxes)
        annotated_img = r.plot()
        result_path = os.path.join(app.config['RESULT_FOLDER'], f"result_{filename}")
        cv2.imwrite(result_path, annotated_img)
    
    # Сохраняем в историю
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'input_type': input_type,
        'filename': filename,
        'result_filename': f"result_{filename}",
        'horse_count': horse_count,
        'boxes': [
            {
                'x1': float(box.xyxy[0][0]),
                'y1': float(box.xyxy[0][1]),
                'x2': float(box.xyxy[0][2]),
                'y2': float(box.xyxy[0][3]),
                'confidence': float(box.conf[0])
            }
            for r in results for box in r.boxes
        ]
    }
    save_history(entry)
    
    return jsonify({
        'success': True,
        'horse_count': horse_count,
        'result_url': f"/{result_path}",
        'history_id': entry['id']
    })

@app.route('/history')
def get_history():
    return jsonify(load_history())

@app.route('/report/pdf')
def generate_pdf_report():
    history = load_history()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)  # для кириллицы
    pdf.set_font('DejaVu', '', 14)
    
    pdf.cell(0, 10, 'Отчёт по учёту лошадей на ипподроме', 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font('DejaVu', '', 12)
    for i, entry in enumerate(history[-10:], 1):  # последние 10 записей
        dt = datetime.fromisoformat(entry['timestamp'])
        pdf.cell(0, 8, f"{i}. {dt.strftime('%d.%m.%Y %H:%M:%S')} — лошадей: {entry['horse_count']}", 0, 1)
    
    pdf_output = 'report.pdf'
    pdf.output(pdf_output)
    return send_file(pdf_output, as_attachment=True)

@app.route('/report/excel')
def generate_excel_report():
    import pandas as pd
    history = load_history()
    
    df = pd.DataFrame([
        {
            'Дата': datetime.fromisoformat(h['timestamp']).strftime('%d.%m.%Y %H:%M:%S'),
            'Тип': h['input_type'],

'Количество лошадей': h['horse_count'],
            'Файл': h['filename']
        }
        for h in history
    ])
    
    excel_path = 'report.xlsx'
    df.to_excel(excel_path, index=False, engine='openpyxl')
    return send_file(excel_path, as_attachment=True)

if name == '__main__':
    app.run(debug=True)