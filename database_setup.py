import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# ===== Users table =====
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    location TEXT
)
""")

# ===== Skills table =====
c.execute("""
CREATE TABLE IF NOT EXISTS skills(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    description TEXT,
    category TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# ===== Requests table =====
c.execute("""
CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER,
    requester_id INTEGER,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(skill_id) REFERENCES skills(id),
    FOREIGN KEY(requester_id) REFERENCES users(id)
)
""")

# ===== Reviews table =====
c.execute("""
CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER,
    reviewer_id INTEGER,
    rating INTEGER,
    comment TEXT,
    FOREIGN KEY(skill_id) REFERENCES skills(id),
    FOREIGN KEY(reviewer_id) REFERENCES users(id)
)
""")

conn.commit()
conn.close()
print("✅ Database created successfully!")