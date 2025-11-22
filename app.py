from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'forum-4j-class-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///class_4j_forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    theme = db.Column(db.String(10), default='light')
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_type = db.Column(db.String(20), default='news')
    status = db.Column(db.String(20), default='published')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.String(50))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref=db.backref('homeworks', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('chat_messages', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user and user.is_banned:
        return None
    return user

# Добавляем проверку бана перед каждым запросом
@app.before_request
def check_ban():
    if current_user.is_authenticated and current_user.is_banned:
        logout_user()
        flash('Ваш аккаунт заблокирован', 'error')
        return redirect(url_for('login'))

# Welcome страница
@app.route('/welcome')
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('welcome.html')

# Главная страница - редирект на welcome для неавторизованных
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('welcome'))

@app.route('/forum')
@login_required
def index():
    posts = Post.query.filter_by(post_type='news', status='published').order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        password = request.form['password']
        
        existing_user = User.query.filter_by(first_name=first_name, last_name=last_name).first()
        if existing_user:
            flash('Пользователь с таким именем уже зарегистрирован', 'error')
            return redirect(url_for('register'))
        
        user = User(first_name=first_name, last_name=last_name)
        user.set_password(password)
        
        if first_name.lower() == 'марк' and last_name.lower() == 'габдрахимов':
            user.role = 'admin'
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        password = request.form['password']
        
        user = User.query.filter_by(first_name=first_name, last_name=last_name).first()
        
        if user and user.check_password(password):
            if user.is_banned:
                flash('Ваш аккаунт заблокирован', 'error')
                return redirect(url_for('login'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверные данные', 'error')
    
    return render_template('login.html')

@app.route('/homework')
@login_required
def homework():
    homeworks = Homework.query.order_by(Homework.created_at.desc()).all()
    return render_template('homework.html', homeworks=homeworks)

@app.route('/add_homework', methods=['POST'])
@login_required
def add_homework():
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    subject = request.json.get('subject')
    content = request.json.get('content')
    due_date = request.json.get('due_date')
    
    homework = Homework(
        subject=subject,
        content=content,
        due_date=due_date,
        author_id=current_user.id
    )
    db.session.add(homework)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/info')
@login_required
def info():
    info_posts = Post.query.filter_by(post_type='info', status='published').order_by(Post.created_at.desc()).all()
    return render_template('info.html', info_posts=info_posts)

@app.route('/add_info', methods=['POST'])
@login_required
def add_info():
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    title = request.json.get('title')
    content = request.json.get('content')
    
    post = Post(
        title=title,
        content=content,
        post_type='info',
        author_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/chat')
@login_required
def chat():
    if request.args.get('check_new'):
        last_message_id = request.args.get('last_id', 0, type=int)
        new_messages = ChatMessage.query.filter(
            ChatMessage.id > last_message_id,
            ChatMessage.user_id != current_user.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        messages_data = []
        for msg in new_messages:
            messages_data.append({
                'id': msg.id,
                'user_id': msg.user_id,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%H:%M')
            })
        
        return jsonify({'new_messages': messages_data})
    
    messages = ChatMessage.query.order_by(ChatMessage.created_at.asc()).all()
    return render_template('chat.html', messages=messages)

@app.route('/send_chat', methods=['POST'])
@login_required
def send_chat():
    content = request.json.get('content')
    
    if not content.strip():
        return jsonify({'error': 'Пустое сообщение'}), 400
    
    message = ChatMessage(
        content=content,
        user_id=current_user.id
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/messages')
@login_required
def messages():
    users = User.query.filter(User.id != current_user.id, User.is_banned == False).all()
    return render_template('messages.html', users=users)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')
    
    if not content.strip():
        return jsonify({'error': 'Пустое сообщение'}), 400
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/get_messages/<int:user_id>')
@login_required
def get_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%H:%M'),
            'is_my': msg.sender_id == current_user.id
        })
    
    return jsonify(messages_data)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Нет доступа', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    suggested_posts = Post.query.filter_by(status='suggested').all()
    return render_template('admin.html', users=users, suggested_posts=suggested_posts)

@app.route('/add_news', methods=['POST'])
@login_required
def add_news():
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    title = request.json.get('title')
    content = request.json.get('content')
    
    if not title.strip() or not content.strip():
        return jsonify({'error': 'Заполните все поля'}), 400
    
    post = Post(
        title=title,
        content=content,
        post_type='news',
        author_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/suggest_news', methods=['POST'])
@login_required
def suggest_news():
    title = request.json.get('title')
    content = request.json.get('content')
    
    if not title.strip() or not content.strip():
        return jsonify({'error': 'Заполните все поля'}), 400
    
    post = Post(
        title=title,
        content=content,
        post_type='info',
        status='suggested',
        author_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/ban_user/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    user = User.query.get(user_id)
    if user:
        user.is_banned = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Пользователь не найден'}), 404

@app.route('/unban_user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    user = User.query.get(user_id)
    if user:
        user.is_banned = False
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Пользователь не найден'}), 404

@app.route('/publish_post/<int:post_id>', methods=['POST'])
@login_required
def publish_post(post_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    post = Post.query.get(post_id)
    if post:
        post.status = 'published'
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Пост не найден'}), 404

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Нет прав'}), 403
    
    post = Post.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Пост не найден'}), 404

@app.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.json.get('theme')
    current_user.theme = theme
    db.session.commit()
    return jsonify({'success': True})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('welcome'))

# Обработчик 404 ошибки
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# Обработчик 500 ошибки
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Запуск на всех интерфейсах (0.0.0.0) для доступа из сети
    app.run(debug=True, host='0.0.0.0', port=5000)