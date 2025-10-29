# app.py — Flask backend for Missing Person Identification System

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import face_recognition

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
DB_PATH = 'database/persons.db'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    # Handle new person form submission
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        photo = request.files['photo']
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Insert into database
        c.execute("INSERT INTO persons (name, age, gender, location, photo) VALUES (?, ?, ?, ?, ?)",
                  (name, age, gender, location, filename))
        conn.commit()

    # Fetch all registered persons
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

            # Load uploaded image and extract face encoding
            unknown_image = face_recognition.load_image_file(path)
            unknown_encoding = face_recognition.face_encodings(unknown_image)

            if unknown_encoding:
                unknown_encoding = unknown_encoding[0]

                # Compare with known faces in database
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM persons")
                persons = c.fetchall()
                conn.close()

                for person in persons:
                    known_image_path = os.path.join(app.config['UPLOAD_FOLDER'], person[5])
                    known_image = face_recognition.load_image_file(known_image_path)
                    known_encoding = face_recognition.face_encodings(known_image)

                    if known_encoding and face_recognition.compare_faces([known_encoding[0]], unknown_encoding)[0]:
                        result = {
                            'name': person[1],
                            'age': person[2],
                            'gender': person[3],
                            'location': person[4],
                            'photo': person[5]
                        }
                        break

                if not result:
                    result = 'Person not found in database.'
            else:
                result = 'No face detected in uploaded image.'
    return render_template('dashboard.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
