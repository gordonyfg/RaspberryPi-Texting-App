from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'database/chat_history.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.route('/messages', methods=['GET'])
def get_messages():
    protocol = request.args.get('protocol')
    db = get_db()
    try:
        if protocol:
            messages = db.execute(
                'SELECT * FROM messages WHERE protocol = ? ORDER BY timestamp',
                [protocol]
            ).fetchall()
        else:
            messages = db.execute(
                'SELECT * FROM messages ORDER BY timestamp'
            ).fetchall()
        return jsonify([dict(msg) for msg in messages])
    finally:
        db.close()

@app.route('/messages', methods=['POST'])
def add_message():
    try:
        data = request.get_json()
        
        # Check for required fields
        required_fields = ['protocol', 'sender', 'recipient', 'message']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO messages (protocol, sender, recipient, message)
            VALUES (?, ?, ?, ?)
        ''', [data['protocol'], data['sender'], data['recipient'], data['message']])
        
        message_id = cursor.lastrowid
        db.commit()
        db.close()
        
        return jsonify({'id': message_id}), 201
        
    except (TypeError, ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid JSON data', 'details': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
