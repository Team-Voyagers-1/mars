from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import os
import uuid
import string
import random
from users.mongo import mongo_db
import datetime

def generate_handle(name):
    base = name.lower().replace(' ', '-')
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{base}-{random_str}"

def is_text_file(filename):
    # List of supported text file extensions
    text_extensions = {
        '.txt', '.csv', '.json', '.md', '.py', '.js', 
        '.html', '.css', '.xml', '.yaml', '.yml', 
        '.ini', '.conf', '.log', '.env'
    }
    return os.path.splitext(filename)[1].lower() in text_extensions

class FeatureView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        user_id = "test_user_123"
        
        name = request.data.get('name')
        if not name:
            return Response({"error": "Feature name is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Check if files were uploaded
        files = request.FILES.getlist('files')
        if not files:
            return Response({"error": "No files uploaded"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        handle = generate_handle(name)
        feature_id = str(uuid.uuid4())
        file_details = []
        unsupported_files = []
        
        for file in files:
            if not is_text_file(file.name):
                unsupported_files.append(file.name)
                continue

            try:
                # Try to read and decode file content
                content = file.read().decode('utf-8')
                file_details.append({
                    'name': file.name,
                    'content': content
                })
            except UnicodeDecodeError:
                unsupported_files.append(file.name)
                continue

        # If no valid files were processed
        if not file_details:
            error_msg = "No valid text files were uploaded. "
            if unsupported_files:
                error_msg += f"Unsupported files: {', '.join(unsupported_files)}"
            return Response({"error": error_msg}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Create feature document in MongoDB
        features = mongo_db.features
        feature = {
            'id': feature_id,
            'name': name,
            'handle': handle,
            'user_id': user_id,
            'files': file_details,
            'created_at': datetime.datetime.utcnow()
        }
        
        features.insert_one(feature)

        # Prepare response
        response_data = {
            'id': feature_id,
            'name': name,
            'handle': handle,
            'files': file_details
        }

        # Add warning about unsupported files if any
        if unsupported_files:
            response_data['warnings'] = {
                'unsupported_files': unsupported_files,
                'message': 'Some files were not processed because they are not supported text files'
            }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user_id = "test_user_123"
        features = mongo_db.features
        
        user_features = list(features.find({'user_id': user_id}))
        
        # Convert ObjectId to string
        for feature in user_features:
            feature['_id'] = str(feature['_id'])
        
        return Response(user_features)