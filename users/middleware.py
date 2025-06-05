from django.http import JsonResponse
from rest_framework import status
import jwt
from django.conf import settings
from .mongo import mongo_db
from bson import ObjectId

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude authentication for login and register endpoints
        if request.path in ['/api/users/login/', '/api/users/register/']:
            return self.get_response(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {"error": "No token provided"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Extract token
            token = auth_header.split(' ')[1]
            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Verify user exists
            user = mongo_db.users.find_one({"_id": ObjectId(payload['user_id'])})
            if not user:
                return JsonResponse(
                    {"error": "User not found"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Add user info to request
            request.user = user
            return self.get_response(request)

        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {"error": "Token has expired"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {"error": "Invalid token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            ) 