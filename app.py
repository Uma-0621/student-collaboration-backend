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


# ---- Chat model uses Integer ids for sender/receiver (recommended) ----
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.Integer)     # integer user id
    receiver = db.Column(db.Integer)   # integer user id
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

    return jsonify({"message": "Registered"}), 201


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
            # 🔥 AUTO CHECK PROFILE
            "profileCompleted": True if user.phone and user.college else False
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
        skills=data.get("skills"),
        userId=int(data["userId"])
    )

    db.session.add(idea)
    db.session.commit()

    return jsonify({"message": "Idea created"}), 201


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
        ideaId=int(data["ideaId"]),
        userId=int(data["userId"])
    )

    db.session.add(req)
    db.session.commit()

    return jsonify({"message": "Request sent"}), 201


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
            "userName": user.name if user else "Unknown",
            "status": r.status
        })

    return jsonify(result)


@app.route("/api/request/update/<int:id>", methods=["PUT"])
def update_req(id):
    data = request.json

    req = Request.query.get(id)
    if not req:
        return jsonify({"error": "Request not found"}), 404

    req.status = data.get("status", req.status)

    db.session.commit()

    return jsonify({"message": "Updated"})


# =========================
# 👤 PROFILE
# =========================

@app.route("/api/user/<int:id>", methods=["GET"])
def profile(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "college": user.college,
        "skills": user.skills,
        "status": user.status,
        # 🔥 keep consistent
        "profileCompleted": True if user.phone and user.college else False
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
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    user.college = data.get("college", user.college)
    user.skills = data.get("skills", user.skills)
    user.status = data.get("status", user.status)

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        # 🔥 return updated user also
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "college": user.college,
            "skills": user.skills,
            "status": user.status,
            "profileCompleted": True if user.phone and user.college else False
        }
    })


# =========================
# 💬 PRIVATE CHAT
# =========================

@app.route("/api/chat/send", methods=["POST"])
def send():
    data = request.json

    # Validate presence
    if "from" not in data or "to" not in data or "message" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    try:
        sender_id = int(data["from"])
        receiver_id = int(data["to"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user ids"}), 400

    # Optional: verify users exist (uncomment if desired)
    # if not User.query.get(sender_id) or not User.query.get(receiver_id):
    #     return jsonify({"error": "User not found"}), 404

    msg = Chat(
        sender=sender_id,
        receiver=receiver_id,
        message=data["message"]
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Sent"}), 201


@app.route("/api/chat/<u1>/<u2>", methods=["GET"])
def chat(u1, u2):
    # Convert to integer IDs (important for querying integer columns)
    try:
        a = int(u1)
        b = int(u2)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user ids"}), 400

    msgs = Chat.query.filter(
        ((Chat.sender == a) & (Chat.receiver == b)) |
        ((Chat.sender == b) & (Chat.receiver == a))
    ).order_by(Chat.id).all()

    return jsonify([
        {
            "id": m.id,
            "from": m.sender,
            "to": m.receiver,
            "message": m.message
        }
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

    return jsonify({"groupId": g.id}), 201


@app.route("/api/group/send", methods=["POST"])
def group_send():
    data = request.json

    msg = GroupMessage(
        groupId=int(data["groupId"]),
        sender=data["sender"],
        message=data["message"]
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Sent"}), 201


@app.route("/api/group/<int:id>", methods=["GET"])
def group_chat(id):
    msgs = GroupMessage.query.filter_by(groupId=id).order_by(GroupMessage.id).all()

    return jsonify([
        {"sender": m.sender, "message": m.message}
        for m in msgs
    ])


# =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":
    with app.app_context():
        # If you're switching from string-based sender/receiver to integers,
        # you MUST reset the DB (drop_all + create_all) to update column types.
        # Uncomment the next line to reset the DB (this will erase existing data):
        # db.drop_all()

        db.create_all()

    app.run(debug=True)