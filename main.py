from flask import Flask, render_template, request, redirect, session, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect, generate_csrf
from user_agents import parse

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


friends_association = db.Table(
    'friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('accepted', db.Boolean, default=False)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_online = db.Column(db.Boolean, default=False)

    # 생성한 채팅방
    created_chats = db.relationship('Chat', backref='creator', lazy=True)

    # 친구 관계
    friends = db.relationship(
        'User',
        secondary=friends_association,
        primaryjoin=id == friends_association.c.user_id,
        secondaryjoin=id == friends_association.c.friend_id,
        backref='friend_of'
    )

    def get_friends(self):
        return [f for f in self.friends if self.is_friend_accepted(f)]

    def is_friend_accepted(self, other_user):
        conn = db.session.query(friends_association).filter_by(user_id=self.id, friend_id=other_user.id).first()
        return conn and conn.accepted

    def __repr__(self):
        return f'<User {self.username}>'



chat_members = db.Table('chat_members',
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                        db.Column('chat_id', db.Integer, db.ForeignKey('chat.id'), primary_key=True),
                        db.Column('is_admin', db.Boolean, default=False)
                        )


def isMobile():
    user_agent = request.headers.get('User-Agent')
    mobile_keywords = ['iphone', 'ipod', 'android', 'blackberry',
                       'windows phone', 'nokia', 'samsung', 'mobile']

    is_mobile = any(keyword in user_agent.lower() for keyword in mobile_keywords)

    return any(keyword in user_agent for keyword in mobile_keywords)


@app.context_processor
def inject_csrf():
    return {'csrf_token': generate_csrf()}


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    messages = db.relationship('Message', backref='chat', lazy=True)
    members = db.relationship('User', secondary=chat_members, backref=db.backref('chats', lazy='dynamic'))

    def is_member(self, user):
        """Check if user is a member of this chat"""
        return db.session.query(chat_members).filter_by(
            chat_id=self.id,
            user_id=user.id
        ).count() > 0

    def __repr__(self):
        return f'<Chat {self.name} (ID: {self.id})>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User')


# ========== 데코레이터 ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def chat_member_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        chat = Chat.query.get(kwargs.get('chat_id'))

        if not chat:
            abort(404)

        # 관리자는 모든 채팅방 접근 가능
        if user.role == 'admin':
            return f(*args, **kwargs)

        # 채팅방 멤버 확인
        if user not in chat.members and chat.is_private:
            abort(403)

        return f(*args, **kwargs)

    return decorated_function

def is_mobile(user_agent):
    return parse(user_agent).is_mobile

# ========== 라우트 ==========
@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent', '')
    """
    if 'username' in session:
        if is_mobile(user_agent):
            return redirect(url_for('moi'))
        else:
            return redirect(url_for('home'))
    return redirect(url_for('login'))
"""
    if is_mobile(user_agent):
        if 'username' in session:
            return redirect(url_for('moi'))
        else:
            return redirect(url_for('login'))
    else:
        if 'username' in session:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return redirect(url_for(('home.html')))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            user.is_online = True
            session['username'] = user.username
            return redirect(url_for('home'))
        return '로그인 실패. 사용자명 또는 비밀번호가 틀렸습니다.'
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return '이미 존재하는 사용자입니다.'
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/moi', methods=['GET', 'POST'])
def moi():
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('logout'))
    selected_chat_id = request.args.get('chat_id')
    selected_chat = Chat.query.get(selected_chat_id) if selected_chat_id else None
    return render_template('mobile.html',
                           username=user.username,
                           chats=user.chats.all(),
                           selected_chat=selected_chat)


@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('logout'))
    selected_chat_id = request.args.get('chat_id')
    selected_chat = Chat.query.get(selected_chat_id) if selected_chat_id else None
    return render_template('home.html',
                         username=user.username,
                         chats=user.chats.all(),
                         selected_chat=selected_chat)

@app.route('/fd')
@login_required
def fd():
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('logout'))
    selected_chat_id = request.args.get('chat_id')
    selected_chat = Chat.query.get(selected_chat_id) if selected_chat_id else None
    return render_template('fd.html',
                         username=user.username,
                         chats=user.chats.all(),
                         selected_chat=selected_chat)


@app.route('/chat/<int:chat_id>')
@chat_member_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    user = User.query.filter_by(username=session['username']).first()

    # 사용자가 채팅방 관리자인지 확인
    is_admin = db.session.query(
        chat_members.c.is_admin
    ).filter_by(
        user_id=user.id,
        chat_id=chat.id
    ).scalar() or user.role == 'admin'

    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
    return render_template('home.html',
                           chat=chat,
                           messages=messages,
                           is_admin=is_admin,
                           members=chat.members)


@app.route('/add_chat', methods=['POST'])
@login_required
def add_chat():
    chat_name = request.form.get('chat_name')
    is_private = request.form.get('is_private') == 'on'
    user = User.query.filter_by(username=session['username']).first()

    if chat_name and user:
        new_chat = Chat(
            name=chat_name,
            creator_id=user.id,
            is_private=is_private
        )
        db.session.add(new_chat)
        db.session.commit()

        # 채팅방 생성자를 관리자로 추가
        db.session.execute(chat_members.insert().values(
            user_id=user.id,
            chat_id=new_chat.id,
            is_admin=True
        ))
        db.session.commit()

    return redirect(url_for('home'))


@app.route('/chat/<int:chat_id>/add_member', methods=['POST'])
@chat_member_required
def add_member(chat_id):
    username = request.form.get('username')
    user_to_add = User.query.filter_by(username=username).first()
    chat = Chat.query.get(chat_id)

    if user_to_add and chat:
        # 이미 멤버인지 확인
        if user_to_add not in chat.members:
            db.session.execute(chat_members.insert().values(
                user_id=user_to_add.id,
                chat_id=chat.id,
                is_admin=False
            ))
            db.session.commit()
    print(f"username={username}, user_to_add={user_to_add}, chat={chat}")

    return redirect(url_for('view_chat', chat_id=chat_id))


@socketio.on('send_message')
def handle_send_message(data):
    try:
        if 'username' not in session:
            emit('error', {'message': '로그인이 필요합니다'})
            return

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            emit('error', {'message': '사용자를 찾을 수 없습니다'})
            return

        chat = db.session.get(Chat, data['chat_id'])
        if not chat:
            emit('error', {'message': '채팅방을 찾을 수 없습니다'})
            return

        # 권한 확인
        if chat.is_private and not any(m.id == user.id for m in chat.members):
            emit('error', {'message': '접근 권한이 없습니다'})
            return

        # 메시지 저장
        new_message = Message(
            content=data['message'],
            chat_id=chat.id,
            sender_id=user.id
        )
        db.session.add(new_message)
        db.session.commit()

        # 모든 클라이언트에 브로드캐스트
        emit('new_message', {
            'chat_id': chat.id,
            'message': data['message'],
            'sender': user.username,
            'timestamp': new_message.timestamp.isoformat()
        }, include_self=False)

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': f'서버 오류: {str(e)}'})


@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(username=session['username']).first()
    return render_template('profile/index.html',
                           username=user.username,
                           status="■",
                           role=user.role)

@app.route('/license')
@login_required
def lic():
    user = User.query.filter_by(username=session['username']).first()
    return render_template('setting/license.html',
                           username=user.username,
                           status="■",
                           role=user.role)

@app.route('/license-DCLA')
def licDCLA():
    return render_template('license/dcla.html')


@app.route('/mprofile')
@login_required
def mprofile():
    user = User.query.filter_by(username=session['username']).first()
    return render_template('profile/mobile.html',
                           username=user.username,
                           status="■",
                           role=user.role)



@app.route('/audioVideo')
@login_required
def audioVideo():
    user = User.query.filter_by(username=session['username']).first()
    return render_template('setting/audioVideo.html',
                           username=user.username,
                           status="■",
                           role=user.role)


@app.route('/logout')
def logout():
    user = User.query.filter_by(username=session.get('username')).first()
    if user:
        user.is_online = False
        db.session.commit()
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/changeName', methods=['GET', 'POST'])
@login_required
def changeName():
    if request.method == 'POST':
        new_username = request.form.get('new_username')
        if not new_username:
            return '닉네임이 전송되지 않았습니다.', 400
        if User.query.filter_by(username=new_username).first():
            return '이미 존재하는 사용자 이름입니다.'
        current_user = User.query.filter_by(username=session['username']).first()
        current_user.username = new_username
        db.session.commit()
        session['username'] = new_username
        return redirect(url_for('profile'))
    return render_template('change_username.html')


@app.route('/api/chat/<int:chat_id>/messages')
def get_chat_messages(chat_id):
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    chat = Chat.query.get_or_404(chat_id)

    if chat.creator_id != user.id and not chat.is_member(user):
        return jsonify({'error': 'Forbidden'}), 403

    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    return jsonify({
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender': m.sender.username,
            'timestamp': m.timestamp.isoformat()
        } for m in messages]
    })


# 관리자 전용: 모든 사용자 조회
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


# 초기 관리자 생성 (처음 실행시 한 번만 호출)
def create_admin():
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin = User(username='admin', password_hash=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()


def notify_status_change(user_id):
    socketio.emit('status_update', {'user_id': user_id})


# 서버 코드 수정 (app.py)
@socketio.on('connect')
def handle_connect(_):
    user = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        user.is_online = True
        notify_status_change(user.id)
        db.session.commit()

    if user:
        emit('connection_success', {
            'user': user.username,
            'chats': [{'id': c.id, 'name': c.name} for c in user.chats]
        })
    else:
        emit('redirect', {'url': url_for('login')})

@socketio.on('disconnect')
def on_disconnect():
    user = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        user.is_online = False
        notify_status_change(user.id)
        db.session.commit()

    if user:
        emit('connection_success', {
            'user': user.username,
            'chats': [{'id': c.id, 'name': c.name} for c in user.chats]
        })
    else:
        emit('redirect', {'url': url_for('login')})


@socketio.on('request_messages')
def handle_request_messages(data):
    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        emit('error', {'message': '로그인이 필요합니다'})
        return

    chat = Chat.query.get(data.get('chat_id'))
    if not chat:
        emit('error', {'message': '채팅방을 찾을 수 없습니다'})
        return

    # 생성자이거나 멤버인지 확인
    if chat.creator_id != user.id and not chat.is_member(user):
        emit('error', {'message': '권한이 없습니다'})
        return

    messages = [{
        'id': m.id,
        'content': m.content,
        'sender': m.sender.username,
        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M')
    } for m in chat.messages]

    emit('load_messages', {'messages': messages})

@app.route('/friend/request/<int:friend_id>', methods=['POST'])
@login_required
def send_friend_request(friend_id):
    current_user = User.query.filter_by(username=session['username']).first()
    target_user = User.query.get_or_404(friend_id)

    # 중복 요청 방지
    existing = db.session.query(friends_association).filter_by(
        user_id=current_user.id,
        friend_id=target_user.id
    ).first()

    if existing:
        return '이미 요청을 보냈습니다.', 400

    db.session.execute(friends_association.insert().values(
        user_id=current_user.id,
        friend_id=target_user.id,
        accepted=False
    ))
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/friend/accept/<int:requester_id>', methods=['POST'])
@login_required
def accept_friend_request(requester_id):
    current_user = User.query.filter_by(username=session['username']).first()

    connection = db.session.query(friends_association).filter_by(
        user_id=requester_id, friend_id=current_user.id
    ).first()

    if connection:
        # 친구 요청 수락 처리
        db.session.execute(friends_association.update().where(
            (friends_association.c.user_id == requester_id) &
            (friends_association.c.friend_id == current_user.id)
        ).values(accepted=True))

        # 양방향 친구 관계 추가 (반대 방향)
        db.session.execute(friends_association.insert().values(
            user_id=current_user.id,
            friend_id=requester_id,
            accepted=True
        ))
        db.session.commit()
        return redirect(url_for('profile'))
    else:
        return '요청이 없습니다.', 404


@app.route('/friend/remove/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    current_user = User.query.filter_by(username=session['username']).first()

    db.session.execute(friends_association.delete().where(
        ((friends_association.c.user_id == current_user.id) & (friends_association.c.friend_id == friend_id)) |
        ((friends_association.c.user_id == friend_id) & (friends_association.c.friend_id == current_user.id))
    ))
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/status/<string:status>', methods=['POST'])
@login_required
def update_status(status):
    current_user = User.query.filter_by(username=session['username']).first()

    if status not in ['online', 'offline']:
        return '잘못된 상태입니다.', 400

    current_user.is_online = (status == 'online')
    db.session.commit()
    return '상태가 업데이트되었습니다.', 200


@app.route('/friends')
@login_required
def get_friends():
    current_user = User.query.filter_by(username=session['username']).first()

    # 수락된 친구들
    accepted_friends = current_user.get_friends()

    # 현재 사용자에게 온 친구 요청 (수락 대기 중)
    pending_requests = db.session.query(User).join(
        friends_association,
        (friends_association.c.user_id == User.id)
    ).filter(
        friends_association.c.friend_id == current_user.id,
        friends_association.c.accepted == False
    ).all()

    def status_label(user):
        if getattr(user, 'is_online', False):
            return 'online'
        return 'offline'

    friends_data = [{
        'id': user.id,
        'username': user.username,
        'status': status_label(user),
        'description': user.role
    } for user in accepted_friends]

    requests_data = [{
        'id': user.id,
        'username': user.username,
        'status': status_label(user),
        'description': user.role
    } for user in pending_requests]

    return jsonify({
        'friends': friends_data,
        'requests': requests_data
    })



# ========== 애플리케이션 초기화 ==========
with app.app_context():
    db.create_all()
    create_admin()
    print("사용자 목록:", User.query.all())
    print("채팅방 목록:", Chat.query.all())
    print("메시지 목록:", Message.query.all())

if __name__ == '__main__':
    socketio.run(app,
                host='0.0.0.0',
                port=47989,
                debug=True,
                 use_reloader=True,
                allow_unsafe_werkzeug=True)  # 개발용으로 추가