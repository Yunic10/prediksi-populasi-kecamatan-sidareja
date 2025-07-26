from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    password = "admin123"
    hashed = generate_password_hash(password)
    print(f"Hash untuk 'admin123':\n{hashed}") 