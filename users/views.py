from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .mongo import mongo_db
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class RegisterView(APIView):
    def post(self, request):
        users = mongo_db.users
        username = request.data.get("username")
        password = request.data.get("password")

        if users.find_one({"username": username}):
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        users.insert_one({
            "username": username,
            "password": hash_password(password)
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
            return Response({"message": "Login successful", "user_id": str(user["_id"])})
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
