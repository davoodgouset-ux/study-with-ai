# ==============================================================================
# File: create_my_jwt.py
# Purpose: Step-by-step demonstration of how a JWT is assembled.
# ==============================================================================

import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

print("=" * 65)
print("       STEP-BY-STEP: HOW A JWT IS BORN INSIDE PYTHON")
print("=" * 65)

# STEP 1: The Header
# Tells the world what algorithm we use to sign the token
header_dict = {"alg": "HS256", "typ": "JWT"}
header_json = json.dumps(header_dict, separators=(",", ":")).encode("utf-8")
# Convert to URL-safe Base64 (removes '=' padding)
header_b64 = base64.urlsafe_b64encode(header_json).decode("utf-8").rstrip("=")

print("\n[STEP 1] THE HEADER:")
print("  Plain JSON :", header_dict)
print("  Base64     :", header_b64)

# STEP 2: The Payload (User Data + Expiration)
# Contains the user information and valid expiration date
expire_time = int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
payload_dict = {
    "sub": "davoodgouset@gmil.com",
    "name": "David Gouse",
    "role": "Student",
    "exp": expire_time
}
payload_json = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")

print("\n[STEP 2] THE PAYLOAD (Your Identity):")
print("  Plain JSON :", payload_dict)
print("  Base64     :", payload_b64)

# STEP 3: The Secret Key (Only known to our backend server)
SECRET_KEY = "study_with_ai_super_secret_jwt_key_2026_cse_final_year_project_secure"

# STEP 4: Creating the Signature (The Wax Seal)
# Combines Header + Payload and signs it with the SECRET_KEY using HMAC-SHA256
message_to_sign = f"{header_b64}.{payload_b64}".encode("utf-8")
signature_bytes = hmac.new(SECRET_KEY.encode("utf-8"), message_to_sign, hashlib.sha256).digest()
signature_b64 = base64.urlsafe_b64encode(signature_bytes).decode("utf-8").rstrip("=")

print("\n[STEP 3] THE SIGNATURE (Cryptographic Wax Seal):")
print("  Generated using HMAC-SHA256 + Secret Key")
print("  Signature  :", signature_b64)

# STEP 5: Stitching all 3 parts together with dots (.)
final_jwt = f"{header_b64}.{payload_b64}.{signature_b64}"

print("\n" + "=" * 65)
print("FINAL COMPLETE JWT TOKEN:")
print("=" * 65)
print(final_jwt)
print("=" * 65)
