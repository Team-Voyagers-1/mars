from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .mongo import mongo_db
import hashlib
import jwt
from django.conf import settings
from datetime import datetime, timedelta

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_jwt_token(user_data):
    payload = {
        'user_id': str(user_data['_id']),
        'username': user_data['username'],
        'role': user_data.get('role', 'user'),
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

class RegisterView(APIView):
    def post(self, request):
        users = mongo_db.users
        username = request.data.get("username")
        password = request.data.get("password")
        role = request.data.get("role", "user")

        if users.find_one({"username": username}):
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        users.insert_one({
            "username": username,
            "password": hash_password(password),
            "role": role
        })

        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        users = mongo_db.users
        username = request.data.get("username")
        password = request.data.get("password")

        user = users.find_one({
            "username": username,
            "password": hash_password(password)
        })

        if user:
#             token = generate_jwt_token(user)
            return Response({
                "message": "Login successful",
#                 "token": token,
                "user_id": str(user["_id"]),
                "username": user["username"],
                "role": user.get("role", "user")
            })
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
