from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Home ----------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("home.html")

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    skills = conn.execute("""
        SELECT s.*, u.name,
        COALESCE(AVG(r.rating),0) as avg_rating,
        COUNT(r.id) as review_count
        FROM skills s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN reviews r ON r.skill_id = s.id
        GROUP BY s.id
    """).fetchall()
    conn.close()
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("dashboard.html", skills=skills, time=time)

# ---------------- Register ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(name,email,password,location) VALUES (?,?,?,?)",
                         (name,email,password,location))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered!")
            conn.close()
            return redirect("/register")
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# ---------------- Login ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (email,password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")
    return render_template("login.html")

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- Add Skill ----------------
@app.route("/add_skill", methods=["GET","POST"])
def add_skill():
    if "user_id" not in session:
        return redirect("/login")
    if request.method=="POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        conn = get_db()
        conn.execute("INSERT INTO skills(user_id,title,description,category) VALUES (?,?,?,?)",
                     (session["user_id"], title, description, category))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return render_template("add_skill.html")

# ---------------- Edit Skill ----------------
@app.route("/edit_skill/<id>", methods=["GET","POST"])
def edit_skill(id):
    conn = get_db()
    skill = conn.execute("SELECT * FROM skills WHERE id=? AND user_id=?", (id, session["user_id"])).fetchone()
    if not skill:
        return "Skill not found"
    if request.method=="POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        conn.execute("UPDATE skills SET title=?, description=?, category=? WHERE id=?",
                     (title, description, category, id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    conn.close()
    return render_template("edit_skill.html", skill=skill)

# ---------------- Delete Skill ----------------
@app.route("/delete_skill/<id>")
def delete_skill(id):
    conn = get_db()
    conn.execute("DELETE FROM skills WHERE id=? AND user_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------- Users List ----------------
@app.route("/users")
def users_page():
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("users.html", users=users)

# ---------------- Request Skill ----------------
@app.route("/request/<id>")
def request_skill(id):
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    conn.execute("INSERT INTO requests(skill_id, requester_id) VALUES (?,?)",
                 (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------- My Requests ----------------
@app.route("/requests")
def requests_page():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    requests_list = conn.execute("""
        SELECT r.id, s.title, r.status, s.user_id as owner_id
        FROM requests r
        JOIN skills s ON s.id = r.skill_id
        WHERE r.requester_id=? OR s.user_id=?
    """, (session["user_id"], session["user_id"])).fetchall()
    conn.close()
    return render_template("requests.html", requests=requests_list)

# ---------------- Accept / Reject Requests ----------------
@app.route("/update_request/<int:request_id>/<action>")
def update_request(request_id, action):
    if "user_id" not in session:
        return redirect("/login")
    if action not in ["accept","reject"]:
        return "Invalid action"
    status = "Accepted" if action=="accept" else "Rejected"
    conn = get_db()
    conn.execute("UPDATE requests SET status=? WHERE id=?", (status, request_id))
    conn.commit()
    conn.close()
    return redirect("/incoming_requests")

# ---------------- Mark Completed ----------------
@app.route("/complete/<id>")
def mark_complete(id):
    conn = get_db()
    conn.execute("UPDATE requests SET status='Completed' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/requests")

# ---------------- Leave Review ----------------
@app.route("/review/<skill_id>", methods=["GET","POST"])
def review(skill_id):
    if "user_id" not in session:
        return redirect("/login")
    if request.method=="POST":
        rating = request.form["rating"]
        comment = request.form["comment"]
        conn = get_db()
        conn.execute("INSERT INTO reviews(skill_id, reviewer_id, rating, comment) VALUES (?,?,?,?)",
                     (skill_id, session["user_id"], rating, comment))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return render_template("review.html")

# ---------------- Incoming Requests (for skill owners) ----------------
@app.route("/incoming_requests")
def incoming_requests():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    requests_list = conn.execute("""
        SELECT r.id, s.title, u.name as requester_name, r.status
        FROM requests r
        JOIN skills s ON s.id = r.skill_id
        JOIN users u ON u.id = r.requester_id
        WHERE s.user_id=?
    """, (session["user_id"],)).fetchall()
    conn.close()
    return render_template("incoming_requests.html", requests=requests_list)

# ---------------- Run App ----------------
if __name__=="__main__":
    app.run(debug=True)