from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

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


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer)
    sender = db.Column(db.String(100))
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

    return jsonify({"message": "Registered"})


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
            "email": user.email,  # ✅ FIX
            "phone": user.phone,
            "college": user.college,
            "skills": user.skills,
            "status": user.status,
            "profileCompleted": True
        })

    return jsonify({"error": "Invalid"}), 401


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
        user = User.query.get(i.userId)

        result.append({
            "id": i.id,
            "title": i.title,
            "description": i.description,
            "skills": i.skills,
            "userId": i.userId,
            "userName": user.name if user else "Unknown"
        })

    return jsonify(result)


# =========================
# 👥 REQUESTS
# =========================

@app.route("/api/request/join", methods=["POST"])
def join():
    data = request.json

    req = Request(
        ideaId=data["ideaId"],
        userId=data["userId"]
    )

    db.session.add(req)
    db.session.commit()

    return jsonify({"message": "Request sent"})


@app.route("/api/request/incoming/<int:user_id>", methods=["GET"])
def incoming(user_id):
    ideas = Idea.query.filter_by(userId=user_id).all()
    ids = [i.id for i in ideas]

    requests = Request.query.filter(Request.ideaId.in_(ids)).all()

    result = []
    for r in requests:
        user = User.query.get(r.userId)

        result.append({
            "requestId": r.id,
            "userName": user.name,
            "status": r.status
        })

    return jsonify(result)


@app.route("/api/request/update/<int:id>", methods=["PUT"])
def update_req(id):
    data = request.json

    req = Request.query.get(id)
    req.status = data["status"]

    db.session.commit()

    return jsonify({"message": "Updated"})


# =========================
# 👤 PROFILE
# =========================

@app.route("/api/user/<int:id>", methods=["GET"])
def profile(id):
    user = User.query.get(id)

    return jsonify({
        "name": user.name,
        "email": user.email,   # ✅ FIX
        "phone": user.phone,
        "college": user.college,
        "skills": user.skills,
        "status": user.status
    })


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
    user.email = data.get("email", user.email)  # ✅ FIX
    user.phone = data.get("phone", user.phone)
    user.college = data.get("college", user.college)
    user.skills = data.get("skills", user.skills)
    user.status = data.get("status", user.status)

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})


# =========================
# 💬 PRIVATE CHAT
# =========================

@app.route("/api/chat/send", methods=["POST"])
def send():
    data = request.json

    msg = Chat(
        sender=data["from"],
        receiver=data["to"],
        message=data["message"]
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Sent"})


@app.route("/api/chat/<u1>/<u2>", methods=["GET"])
def chat(u1, u2):
    msgs = Chat.query.filter(
        ((Chat.sender == u1) & (Chat.receiver == u2)) |
        ((Chat.sender == u2) & (Chat.receiver == u1))
    ).all()

    return jsonify([
        {"from": m.sender, "message": m.message}
        for m in msgs
    ])


# =========================
# 👥 GROUP CHAT
# =========================

@app.route("/api/group/create", methods=["POST"])
def create_group():
    data = request.json

    g = Group(name=data["name"])
    db.session.add(g)
    db.session.commit()

    return jsonify({"groupId": g.id})


@app.route("/api/group/send", methods=["POST"])
def group_send():
    data = request.json

    msg = GroupMessage(
        groupId=data["groupId"],
        sender=data["sender"],
        message=data["message"]
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Sent"})


@app.route("/api/group/<int:id>", methods=["GET"])
def group_chat(id):
    msgs = GroupMessage.query.filter_by(groupId=id).all()

    return jsonify([
        {"sender": m.sender, "message": m.message}
        for m in msgs
    ])


# =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)