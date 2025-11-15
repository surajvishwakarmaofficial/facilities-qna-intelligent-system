import os
import dotenv
dotenv.load_dotenv()

# Predefined users configuration
PREDEFINED_USERS = [
    {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "email": os.getenv("ADMIN_EMAIL", "admin@yopmail.com"),
        "full_name": os.getenv("ADMIN_FULL_NAME", "System Administrator"),
        "password": os.getenv("ADMIN_PASSWORD", "admin2025"),
    },
    {
        "username": "hr",
        "email": "hr@yopmail.com",
        "full_name": "HR Manager",
        "password": "hrmanager2025",
    },
    {
        "username": "staff",
        "email": "staff@yopmail.com",
        "full_name": "Staff Member",
        "password": "staff2025",
    },
    {
        "username": "it",
        "email": "it@yopmail.com",
        "full_name": "IT Support",
        "password": "itsupport2025",
    },
    {
        "username": "user",
        "email": "user@yopmail.com",
        "full_name": "Regular User",
        "password": "user2025",
    },

]
