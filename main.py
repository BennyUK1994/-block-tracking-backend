
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = 'block_tracking.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS staff (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        staff_id INTEGER,
                        date TEXT,
                        blocks_cut INTEGER,
                        FOREIGN KEY (staff_id) REFERENCES staff(id))''')
        conn.commit()

init_db()

@app.route('/staff', methods=['GET'])
def get_staff():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM staff")
        staff = c.fetchall()
    return jsonify([{'id': s[0], 'name': s[1]} for s in staff])

@app.route('/staff', methods=['POST'])
def add_staff():
    data = request.get_json()
    name = data['name']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO staff (name) VALUES (?)", (name,))
        conn.commit()
    return jsonify({'message': 'Staff added successfully'})

@app.route('/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
        conn.commit()
    return jsonify({'message': 'Staff deleted successfully'})

@app.route('/entry', methods=['POST'])
def add_entry():
    data = request.get_json()
    staff_id = data['staff_id']
    date = data['date']
    blocks_cut = data['blocks_cut']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO entries (staff_id, date, blocks_cut) VALUES (?, ?, ?)",
                  (staff_id, date, blocks_cut))
        conn.commit()
    return jsonify({'message': 'Entry added successfully'})

@app.route('/entries', methods=['GET'])
def get_entries():
    staff_id = request.args.get('staff_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if staff_id:
            c.execute("SELECT entries.id, staff.name, date, blocks_cut FROM entries JOIN staff ON staff.id = entries.staff_id WHERE staff.id = ?", (staff_id,))
        else:
            c.execute("SELECT entries.id, staff.name, date, blocks_cut FROM entries JOIN staff ON staff.id = entries.staff_id")
        entries = c.fetchall()
    return jsonify([{'id': e[0], 'staff': e[1], 'date': e[2], 'blocks_cut': e[3]} for e in entries])

@app.route('/entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
    return jsonify({'message': 'Entry deleted successfully'})

@app.route('/reset', methods=['POST'])
def reset_data():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM entries")
        c.execute("DELETE FROM staff")
        conn.commit()
    return jsonify({'message': 'All data reset successfully'})

@app.route('/export', methods=['GET'])
def export_data():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT staff.name, date, blocks_cut FROM entries JOIN staff ON staff.id = entries.staff_id")
        rows = c.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Staff Name', 'Date', 'Blocks Cut'])
    writer.writerows(rows)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'block_data_export_{datetime.now().strftime("%Y%m%d")}.csv')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
