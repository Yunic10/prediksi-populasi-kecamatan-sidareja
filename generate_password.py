import bcrypt

def generate_password_hash(password):
    """Generate password hash menggunakan bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    # Contoh penggunaan
    password = "admin123"
    hashed = generate_password_hash(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    
    # Test verifikasi
    test_result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    print(f"Verifikasi berhasil: {test_result}")
    
    # Untuk menambahkan user baru ke config.yaml
    print("\nUntuk menambahkan user baru, copy hash di atas ke config.yaml")
    print("Contoh:")
    print("  newuser:")
    print("    email: newuser@example.com")
    print("    name: New User")
    print(f"    password: {hashed}") 