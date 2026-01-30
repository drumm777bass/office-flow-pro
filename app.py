from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Файл с ключами от Google (получите в Google Console)
creds = ServiceAccountCredentials.from_json_keyfile_name("google_creds.json", scope)
client = gspread.authorize(creds)
# Открываем таблицу по названию
sheet = client.open("OfficeFlowDB").sheet1

@app.route('/')
def index():
    # Загружаем данные из таблицы для отображения
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return render_template('index.html', tasks=data)

@app.route('/add', methods=['POST'])
def add_task():
    # Получаем данные из формы на сайте
    task = request.form.get('task')
    user = request.form.get('user')
    priority = request.form.get('priority')
    deadline = request.form.get('deadline')
    
    # Добавляем строку в Google Таблицу
    sheet.append_row([task, user, "🔴 Ожидает", priority, deadline])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
