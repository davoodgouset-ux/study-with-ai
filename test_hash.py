# ==============================================================================
# File: test_hash.py
# Purpose: Quick visual test to see how bcrypt hashes any password.
# ==============================================================================

from app.core.security import hash_password, verify_password

password = "my_secret_code_123"

# 1. Hash the password
hashed = hash_password(password)

print("=" * 60)
print("PLAIN PASSWORD :", password)
print("BCRYPT HASH    :", hashed)
print("=" * 60)

# 2. Test verification
is_correct = verify_password("my_secret_code_123", hashed)
is_wrong = verify_password("wrong_password", hashed)

print("Verification with correct password :", is_correct)  # True
print("Verification with wrong password   :", is_wrong)    # False
print("=" * 60)
