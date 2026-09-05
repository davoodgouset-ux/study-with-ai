# ==============================================================================
# File: test_jwt.py
# Purpose: Visual breakdown of how JWT tokens are built and decoded.
# ==============================================================================

from app.core.security import create_access_token, decode_access_token

# 1. Create a JWT for user David Gouse
token = create_access_token(data={"sub": "davoodgouset@gmil.com", "user_id": 5, "role": "Student"})

print("=" * 70)
print("FULL JWT TOKEN (Sent in HTTP Headers):")
print(token)
print("=" * 70)

# 2. Split into the 3 parts separated by dots
parts = token.split(".")
print("\nTHE 3 PARTS SEPARATED BY DOTS:")
print("1. HEADER    (Algorithm) :", parts[0])
print("2. PAYLOAD   (User Data) :", parts[1])
print("3. SIGNATURE (Wax Seal)  :", parts[2])
print("=" * 70)

# 3. Decode the token back to Python data
decoded = decode_access_token(token)
print("\nDECODED DATA INSIDE THE TOKEN:")
print("User Email  :", decoded.get("sub"))
print("User ID     :", decoded.get("user_id"))
print("User Role   :", decoded.get("role"))
print("Expires At  :", decoded.get("exp"), "(Unix timestamp)")
print("=" * 70)
