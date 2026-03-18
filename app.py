from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

# ✅ SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///startup.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# 🧠 MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    college = db.Column(db.String(100))
    skills = db.Column(db.String(200))
    status = db.Column(db.String(50))
    profileCompleted = db.Column(db.Boolean, default=True)


class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    skills = db.Column(db.String(200))
    userId = db.Column(db.Integer)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ideaId = db.Column(db.Integer)
    userId = db.Column(db.Integer)
    status = db.Column(db.String(50), default="pending")


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100))
    receiver = db.Column(db.String(100))
    message = db.Column(db.String(500))


# =========================
# 🔐 AUTH
# =========================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        phone=data.get("phone"),
        college=data.get("college"),
        skills=data.get("skills"),
        status=data.get("status"),
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(
        email=data["email"],
        password=data["password"]
    ).first()

    if user:
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "college": user.college,
            "skills": user.skills,
            "status": user.status,
            "profileCompleted": user.profileCompleted
        })
    else:
        return jsonify({"error": "Invalid login"}), 401


# =========================
# 💡 IDEAS
# =========================

@app.route("/api/idea/create", methods=["POST"])
def create_idea():
    data = request.json

    idea = Idea(
        title=data["title"],
        description=data["description"],
        skills=data["skills"],
        userId=data["userId"]
    )

    db.session.add(idea)
    db.session.commit()

    return jsonify({"message": "Idea created"})


@app.route("/api/idea/all", methods=["GET"])
def get_ideas():
    ideas = Idea.query.all()

    result = []
    for i in ideas:
        result.append({
            "id": i.id,
            "title": i.title,
            "description": i.description,
            "skills": i.skills,
            "userId": i.userId
        })

    return jsonify(result)


# =========================
# 🔍 SEARCH USERS
# =========================

@app.route("/api/user/search", methods=["GET"])
def search_users():
    skill = request.args.get("skill", "")

    users = User.query.filter(User.skills.like(f"%{skill}%")).all()

    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "skills": u.skills
        })

    return jsonify(result)


# =========================
# 👥 JOIN REQUEST
# =========================

@app.route("/api/request/join", methods=["POST"])
def request_join():
    data = request.json

    req = Request(
        ideaId=data["ideaId"],
        userId=data["userId"]
    )

    db.session.add(req)
    db.session.commit()

    return jsonify({"message": "Request sent"})


# =========================
# 💬 CHAT
# =========================

@app.route("/api/chat/send", methods=["POST"])
def send_message():
    data = request.json

    msg = Chat(
        sender=data["from"],
        receiver=data["to"],
        message=data["message"]
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Message sent"})


@app.route("/api/chat/<user1>/<user2>", methods=["GET"])
def get_chat(user1, user2):
    messages = Chat.query.filter(
        ((Chat.sender == user1) & (Chat.receiver == user2)) |
        ((Chat.sender == user2) & (Chat.receiver == user1))
    ).all()

    result = []
    for m in messages:
        result.append({
            "from": m.sender,
            "to": m.receiver,
            "message": m.message
        })

    return jsonify(result)

# =========================
# ✏️ UPDATE PROFILE
# =========================

@app.route("/api/user/update/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    user.name = data.get("name", user.name)
    user.phone = data.get("phone", user.phone)
    user.college = data.get("college", user.college)
    user.skills = data.get("skills", user.skills)
    user.status = data.get("status", user.status)

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)