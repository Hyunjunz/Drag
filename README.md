# Flask Chat Service

## language
- [한국어](#한국어)

A full-featured real-time chat application built using Flask and Flask-SocketIO — created entirely by a solo 15-year-old developer.

## ✨ Features
- 🧑‍💬 User registration and login (with password hashing)
- 🧑‍🤝‍🧑 Friend request system with accept/reject
- 💬 Real-time chat using WebSocket (Socket.IO)
- 🛏️ Chat room creation and management
- ✅ Online status tracking
- 🔐 CSRF protection and session management
- 📱 Frontend with HTML/CSS/JS
- 🐍 Python backend with SQLite DB

## 🧠 Tech Stack
- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Other**: CSRFProtect, Werkzeug, user_agents

## 📂 Folder Structure
```
chat_project/
├── main.py # Main Flask app executable
├── static/ # Static files directory
│ ├── style.css # CSS stylesheet
│ ├── profileIMG/
│ │ ├── default.png # Default user profile image

├── templates/ # HTML templates (login, chat, home, etc.)
│ ├── login.html
│ ├── register.html
│ ├── fd.html
│ ├── mobile.html
│ └── home.html
├── requirements.txt # List of project dependencies

```


## 🛣️ Future Plans

- [ ] Profile picture upload feature
- [ ] Show whether chat messages have been read
- [ ] Chat room notification sound settings
- [ ] Message deletion and editing feature
- [ ] Admin-only chat room



## 한국어
## 소개
Flask Chat Service는 Flask와 Flask-SocketIO를 활용하여 개발된 실시간 채팅 웹 애플리케이션입니다.
이 프로젝트는 15세 개발자 혼자서 설계하고 구현한 것으로, 사용자 인증부터 친구 요청 시스템, 실시간 채팅, 채팅방 관리 기능까지 포함된 풀스택 웹 서비스입니다.

## 🎯 주요 기능
 - 🧑‍💻 회원가입 및 로그인: 비밀번호는 안전하게 해시 처리되며, 세션 기반으로 사용자 인증을 유지합니다.
 - 🧑‍🤝‍🧑 친구 요청 시스템: 친구 요청을 보내고 수락/거절할 수 있습니다.
 - 💬 실시간 채팅: Flask-SocketIO와 WebSocket을 활용한 실시간 메시지 송수신이 가능합니다.
 - 🛏️ 채팅방 생성 및 관리: 사용자들이 새로운 채팅방을 만들고, 초대하여 대화를 나눌 수 있습니다.
 - 🟢 온라인 상태 표시: 로그인한 사용자의 온라인 여부를 실시간으로 추적합니다.
 - 🔐 보안 기능: CSRF 보호, 세션 관리, 비밀번호 해싱 등 웹 보안 요소를 충실히 구현하였습니다.
 - 🌐 웹 기반 프론트엔드: HTML, CSS, JavaScript로 구성된 직관적이고 반응형 UI 제공.

## 🧰 사용 기술
 - 백엔드: Python, Flask, Flask-SocketIO, SQLAlchemy
 - 프론트엔드: HTML, CSS, JavaScript
 - 데이터베이스: SQLite
 - 보안 및 기타: CSRFProtect, Werkzeug, user_agents

## 📁 프로젝트 구조
  ```
chat_project/
├── main.py               # 메인 Flask 앱 실행 파일
├── static/               # 정적 파일 디렉토리
│   ├── style.css         # CSS 스타일 시트
│   ├── profileIMG/
│   │   ├── default.png   # 기본 유저 프로필 이미지     
├── templates/            # HTML 템플릿 (로그인, 채팅, 홈 등)
│   ├── login.html
│   ├── register.html    
│   ├── fd.html
│   ├── mobile.html
│   └── home.html
├── requirements.txt      # 프로젝트 의존성 목록
  ```


## 🛣️ 향후 계획

- [ ] 프로필 사진 업로드 기능
- [ ] 채팅 메시지 읽음 여부 표시
- [ ] 채팅방 알림 음 설정
- [ ] 메시지 삭제 및 수정 기능
- [ ] 관리자 전용 채팅방
