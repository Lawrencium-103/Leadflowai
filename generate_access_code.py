"""
Access Code Generator for LeadFlow AI
Generates unique access codes for Pro users
"""
import sqlite3
import secrets
import string

def generate_code(length=12):
    """Generate a secure random access code"""
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    # Format as XXXX-XXXX-XXXX for readability
    return f"{code[:4]}-{code[4:8]}-{code[8:]}"

def add_access_code(code=None, description=""):
    """Add a new access code to the database"""
    if code is None:
        code = generate_code()
    
    conn = sqlite3.connect('leadflow.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_codes (
            code TEXT PRIMARY KEY,
            used INTEGER DEFAULT 0,
            used_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')
    
    try:
        cursor.execute(
            'INSERT INTO access_codes (code, description) VALUES (?, ?)',
            (code, description)
        )
        conn.commit()
        print(f"[OK] Access Code Generated: {code}")
        if description:
            print(f"   Description: {description}")
        return code
    except sqlite3.IntegrityError:
        print(f"[ERROR] Code already exists: {code}")
        return None
    finally:
        conn.close()

def list_access_codes():
    """List all access codes and their status"""
    conn = sqlite3.connect('leadflow.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT code, used, used_by, created_at, description 
            FROM access_codes 
            ORDER BY created_at DESC
        ''')
        codes = cursor.fetchall()
        
        if not codes:
            print("No access codes found.")
            return
        
        print("\n" + "="*80)
        print("ACCESS CODES")
        print("="*80)
        for code, used, used_by, created_at, description in codes:
            status = "[USED]" if used else "[AVAILABLE]"
            print(f"\n{status} | {code}")
            print(f"   Created: {created_at}")
            if description:
                print(f"   Description: {description}")
            if used_by:
                print(f"   Used by: {used_by}")
        print("="*80 + "\n")
    except sqlite3.OperationalError:
        print("[ERROR] Access codes table doesn't exist yet.")
    finally:
        conn.close()

def generate_multiple(count=5, description=""):
    """Generate multiple access codes"""
    print(f"\nGenerating {count} access codes...\n")
    codes = []
    for i in range(count):
        desc = f"{description} #{i+1}" if description else f"Batch code #{i+1}"
        code = add_access_code(description=desc)
        if code:
            codes.append(code)
    
    print(f"\nGenerated {len(codes)} codes successfully!")
    return codes

if __name__ == "__main__":
    import sys
    
    print("\nLeadFlow AI - Access Code Generator\n")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_access_codes()
        elif command == "generate":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            description = sys.argv[3] if len(sys.argv) > 3 else ""
            if count == 1:
                add_access_code(description=description)
            else:
                generate_multiple(count, description)
        else:
            print("Usage:")
            print("  python generate_access_code.py list")
            print("  python generate_access_code.py generate [count] [description]")
    else:
        # Interactive mode
        print("1. Generate single code")
        print("2. Generate multiple codes")
        print("3. List all codes")
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            desc = input("Description (optional): ").strip()
            add_access_code(description=desc)
        elif choice == "2":
            count = int(input("How many codes? ").strip())
            desc = input("Description (optional): ").strip()
            generate_multiple(count, desc)
        elif choice == "3":
            list_access_codes()
        else:
            print("Invalid option")
