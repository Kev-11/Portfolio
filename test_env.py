from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("ADMIN_USERNAME")
password = os.getenv("ADMIN_PASSWORD")

print(f"Username: [{username}]")
print(f"Username repr: {repr(username)}")
print(f"Username stripped: [{username.strip()}]")
print(f"Password repr: {repr(password)}")
print(f"Password stripped: [{password.strip()}]")
