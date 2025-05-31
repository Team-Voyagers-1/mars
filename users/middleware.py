from django.http import JsonResponse
from rest_framework import status
from users.mongo import mongo_db
from bson import ObjectId

class UserAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip authentication for login and register endpoints
        if request.path in ['/api/login/', '/api/register/']:
            return self.get_response(request)

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return JsonResponse(
                {"error": "Authorization header is missing"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {"error": "Invalid authorization format. Use 'Bearer <token>'"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Convert token string to ObjectId
            object_id = ObjectId(token)
            
            # Find user in MongoDB
            users = mongo_db.users
            user = users.find_one({'_id': object_id})
            
            if not user:
                return JsonResponse(
                    {"error": "Invalid or expired token"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Add user_id to request
            request.user_id = str(user['_id'])
            
            return self.get_response(request)
            
        except Exception:
            return JsonResponse(
                {"error": "Invalid token format"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )