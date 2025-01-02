from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect("database/chat_history.db")
    conn.row_factory = sqlite3.Row
    return conn

# Get all messages
@app.route('/messages', methods=['GET'])
def get_messages():
    protocol = request.args.get('protocol')
    conn = get_db_connection()
    
    if protocol:
        messages = conn.execute('SELECT * FROM messages WHERE protocol = ?', (protocol,)).fetchall()
    else:
        messages = conn.execute('SELECT * FROM messages').fetchall()
        
    conn.close()
    return jsonify([dict(row) for row in messages])

# Add a new message
@app.route('/messages', methods=['POST'])
def add_message():
    data = request.json
    protocol = data['protocol']
    sender = data['sender']
    recipient = data['recipient']
    message = data['message']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO messages (protocol, sender, recipient, message) VALUES (?, ?, ?, ?)',
        (protocol, sender, recipient, message)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

if __name__ == "__main__":
    app.run(debug=True)
