import os
import sqlite3
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from deepface import DeepFace

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
DB_PATH = 'database/persons.db'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('database', exist_ok=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        location TEXT,
        photo TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/database', methods=['GET', 'POST'])
def database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        photo = request.files['photo']
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

        # Insert into database
        c.execute("INSERT INTO persons (name, age, gender, location, photo) VALUES (?, ?, ?, ?, ?)",
                  (name, age, gender, location, filename))
        conn.commit()

    # Fetch all persons
    c.execute("SELECT * FROM persons")
    persons = c.fetchall()
    conn.close()
    return render_template('database.html', persons=persons)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    result = None
    if request.method == 'POST':
        uploaded_file = request.files['image']
        if uploaded_file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
            uploaded_file.save(path)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM persons")
            persons = c.fetchall()
            conn.close()

            found = False
            for person in persons:
                known_image_path = os.path.join(app.config['UPLOAD_FOLDER'], person[5])
                try:
                    comparison = DeepFace.verify(img1_path=path, img2_path=known_image_path, enforce_detection=False)
                    if comparison["verified"]:
                        result = {
                            'name': person[1],
                            'age': person[2],
                            'gender': person[3],
                            'location': person[4],
                            'photo': person[5]
                        }
                        found = True
                        break
                except Exception as e:
                    print("Error comparing faces:", e)
                    continue

            if not found:
                result = 'Person not found in database.'

    return render_template('dashboard.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
