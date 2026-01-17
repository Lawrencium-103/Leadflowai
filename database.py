import sqlite3
import uuid
import hashlib

DB_PATH = "leadflow.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table: Tracks trial uses by machine_id
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (machine_id TEXT PRIMARY KEY, trial_uses INTEGER DEFAULT 0, is_pro INTEGER DEFAULT 0)''')
    
    # Access codes table
    c.execute('''CREATE TABLE IF NOT EXISTS access_codes
                 (code TEXT PRIMARY KEY, is_used INTEGER DEFAULT 0)''')
    
    # Seed 5 secure, random codes if table is empty
    c.execute("SELECT COUNT(*) FROM access_codes")
    if c.fetchone()[0] == 0:
        import secrets
        import string
        def gen_code():
            alphabet = string.ascii_uppercase + string.digits
            part1 = ''.join(secrets.choice(alphabet) for _ in range(4))
            part2 = ''.join(secrets.choice(alphabet) for _ in range(4))
            return f"LFLOW-{part1}-{part2}"
            
        for _ in range(5):
            c.execute("INSERT INTO access_codes (code) VALUES (?)", (gen_code(),))
    
    conn.commit()
    conn.close()

def get_machine_id():
    """Generates a stable machine ID based on environment footprint."""
    import socket
    # Simple fingerprint based on hostname and standard path
    fingerprint = f"{socket.gethostname()}-{uuid.getnode()}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()

def check_user_status(machine_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT trial_uses, is_pro FROM users WHERE machine_id = ?", (machine_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (machine_id) VALUES (?)", (machine_id,))
        conn.commit()
        res = (0, 0)
    conn.close()
    return res # (trial_uses, is_pro)

def increment_trial(machine_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET trial_uses = trial_uses + 1 WHERE machine_id = ?", (machine_id,))
    conn.commit()
    conn.close()

def validate_access_code(machine_id, code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_used FROM access_codes WHERE code = ?", (code,))
    res = c.fetchone()
    if res and res[0] == 0:
        c.execute("UPDATE access_codes SET is_used = 1 WHERE code = ?", (code,))
        c.execute("UPDATE users SET is_pro = 1 WHERE machine_id = ?", (machine_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False
