from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hiddenworld.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    username = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    if username:
        session['username'] = username
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    topics = Topic.query.order_by(Topic.created_at.desc()).all()
    messages = Message.query.order_by(Message.created_at.desc()).limit(100).all()
    return render_template('dashboard.html', 
                         username=session['username'],
                         topics=topics, 
                         messages=messages)


@app.route('/api/messages', methods=['POST'])
def post_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    message = Message(
        username=session['username'],
        content=data['content']
    )
    db.session.add(message)
    db.session.commit()
    return jsonify({'success': True, 'message': {
        'id': message.id,
        'content': message.content,
        'user': message.username,
        'created_at': message.created_at.isoformat()
    }})


@app.route('/api/messages')
def get_messages():
    messages = Message.query.order_by(Message.created_at.desc()).limit(100).all()
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'user': m.username,
        'created_at': m.created_at.isoformat()
    } for m in messages])


@app.route('/api/topics', methods=['POST'])
def create_topic():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    topic = Topic(
        title=data['title'],
        description=data.get('description', ''),
        username=session['username']
    )
    db.session.add(topic)
    db.session.commit()
    return jsonify({'success': True, 'topic': {
        'id': topic.id,
        'title': topic.title,
        'user': topic.username
    }})


@app.route('/api/topics')
def get_topics():
    topics = Topic.query.order_by(Topic.created_at.desc()).all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'user': t.username,
        'created_at': t.created_at.isoformat()
    } for t in topics])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
