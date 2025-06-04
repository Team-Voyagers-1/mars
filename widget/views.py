from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils.text import slugify
from functools import wraps
from .mongo import mongo_db, fs
from .models import FeatureDetails
import json
import os
from bson import ObjectId
import csv
from io import StringIO
from .validation_epic import (
    FIELD_VALIDATION_RULES as EPIC_VALIDATION_RULES,
    get_required_fields as get_epic_required_fields,
    get_fields_with_allowed_values as get_epic_allowed_values
)
from .validation_story import (
    FIELD_VALIDATION_RULES as STORY_VALIDATION_RULES,
    get_required_fields as get_story_required_fields,
    get_fields_with_allowed_values as get_story_allowed_values
)
import datetime

# Constants
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'txt', 'docx'}
MIN_FILE_SIZE = 10
CACHE_TIMEOUT = 300  # 5 minutes

def handle_exceptions(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Internal server error'}, status=500)
    return wrapper

def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

def validate_file(uploaded_file):
    if not uploaded_file:
        raise ValueError("No file was uploaded.")
    
    file_extension = os.path.splitext(uploaded_file.name)[1].lower().strip('.')
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}.")
    
    if uploaded_file.size < MIN_FILE_SIZE:
        raise ValueError(f"File is too small. Minimum size is {MIN_FILE_SIZE} bytes.")

def store_file(file, status="uploaded"):
    file_id = fs.put(file, filename=file.name, content_type=file.content_type, status=status)
    return {
        "file_id": str(file_id),
        "filename": file.name
    }

@csrf_exempt
@handle_exceptions
def upload_feature_details(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    name = request.POST.get('name')
    file = request.FILES.get('file')

    if not name or not file:
        return JsonResponse({'error': 'name and file are required'}, status=400)

    validate_file(file)

    existing = mongo_db.feature_details.find_one({"name": name}, {"_id": 1})
    if existing:
        return JsonResponse({'error': 'Feature with this name already exists'}, status=409)

    handle = slugify(name)
    file_detail = store_file(file)

    feature = {
        "name": name,
        "handle": handle,
        "details": [file_detail],
        "story_sheets": [],
        "epic_sheets": []
    }

    result = mongo_db.feature_details.insert_one(feature)
    feature['id'] = str(result.inserted_id)
    del feature['_id']

    return JsonResponse(feature)

@handle_exceptions
def get_feature_details(request):
    handle = request.GET.get('handle')
    if not handle:
        return JsonResponse({"error": "Handle is required"}, status=400)

    cache_key = f'feature_details_{handle}'
    cached_feature = cache.get(cache_key)
    if cached_feature:
        return JsonResponse(cached_feature)

    feature = mongo_db.feature_details.find_one(
        {"handle": handle},
        {"story_sheet": 0, "epic_sheet": 0}
    )
    
    if not feature:
        return JsonResponse({"error": "Feature not found"}, status=404)

    feature_data = {
        "name": feature.get("name"),
        "id": str(feature.get("_id")),
        "handle": feature.get("handle"),
        "details": convert_objectid_to_str(feature.get("details", [])),
        "story_sheets": convert_objectid_to_str(feature.get("story_sheets", [])),
        "epic_sheets": convert_objectid_to_str(feature.get("epic_sheets", []))
    }

    cache.set(cache_key, feature_data, CACHE_TIMEOUT)
    return JsonResponse(feature_data)

@handle_exceptions
def get_all_features(request):
    cache_key = 'all_features'
    cached_features = cache.get(cache_key)
    if cached_features:
        return JsonResponse(cached_features, safe=False)

    features = list(mongo_db.feature_details.find({}, {'name': 1, 'handle': 1, '_id': 0}))
    cache.set(cache_key, features, CACHE_TIMEOUT)
    return JsonResponse(features, safe=False)

@csrf_exempt
@handle_exceptions
def update_feature(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    handle = request.POST.get('handle')
    if not handle:
        return JsonResponse({"error": "Handle is required"}, status=400)

    feature = mongo_db.feature_details.find_one({"handle": handle})
    if not feature:
        return JsonResponse({"error": "Feature not found"}, status=404)

    updates = {}
    file_types = {
        'file': ('details', 'context'),
        'story_sheet': ('story_sheets', None),
        'epic_sheet': ('epic_sheets', None)
    }

    for file_key, (array_field, file_type) in file_types.items():
        if file := request.FILES.get(file_key):
            validate_file(file)
            file_detail = store_file(file)
            if file_type:
                file_detail['type'] = file_type
            
            if array_field not in feature:
                updates[f"$set"] = {**updates.get("$set", {}), array_field: []}
            
            if "$push" not in updates:
                updates["$push"] = {}
            updates["$push"][array_field] = file_detail

    if updates:
        # Remove old single fields if they exist
        updates.setdefault("$unset", {})
        updates["$unset"].update({
            "story_sheet": "",
            "epic_sheet": ""
        })

        mongo_db.feature_details.update_one({"handle": handle}, updates)
        cache.delete(f'feature_details_{handle}')

        updated_feature = mongo_db.feature_details.find_one(
            {"handle": handle},
            {"story_sheet": 0, "epic_sheet": 0}
        )
        return JsonResponse(convert_objectid_to_str(updated_feature))

    return JsonResponse(convert_objectid_to_str(feature))

def fetch_file_from_db(file_id):
    try:
        # Convert string file_id to ObjectId
        file_id = ObjectId(file_id)
        file = fs.get(file_id)
        return file
    except Exception as e:
        raise ValueError(f"File not found in database: {str(e)}")

def read_file_content(file):

    content = []
    file_extension = os.path.splitext(file.filename)[1].lower()

    try:
        if file_extension == '.csv':
            import csv
            from io import StringIO, TextIOWrapper
            # Read CSV file
            csv_content = TextIOWrapper(file, encoding='utf-8')
            csv_reader = csv.reader(csv_content)
            content = list(csv_reader)
        
        elif file_extension == '.txt':
            # Read text file
            content = [line.decode('utf-8').strip().split(',') for line in file]
            
        elif file_extension == '.pdf':
            import PyPDF2
            from io import BytesIO
            # Read PDF file
            pdf_reader = PyPDF2.PdfReader(BytesIO(file.read()))
            content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                content.extend([line.split(',') for line in text.split('\n') if line.strip()])
                
        elif file_extension == '.docx':
            import docx
            from io import BytesIO
            # Read DOCX file
            doc = docx.Document(BytesIO(file.read()))
            content = [paragraph.text.split(',') for paragraph in doc.paragraphs if paragraph.text.strip()]
            
        return content
    except Exception as e:
        raise ValueError(f"Error reading file content: {str(e)}")

def validate_file_content(content, validation_rules):
    if not content or len(content) < 1:
        raise ValueError("File is empty or has no headers")

    # Get headers and data
    headers = content[0]
    data_rows = content[1:] if len(content) > 0 else []
    
    # Validation columns only for fields that have rules
    validation_columns = []
    fields_with_rules = [field for field, rules in validation_rules.items() 
                        if rules.get("is_required") or rules.get("allowed_values")]
    
    # Check if required fields are present in headers
    missing_required_fields = [
        field for field in fields_with_rules 
        if field not in headers and validation_rules[field].get("is_required", False)
    ]
    if missing_required_fields:
        raise ValueError(f"Required fields missing in CSV: {', '.join(missing_required_fields)}")
    
    for field in fields_with_rules:
        validation_columns.append(f"{field}_validation")
    validation_columns.append("is_valid_row")
    
    # Create new headers with validation columns
    new_headers = headers + validation_columns
    
    # Create a StringIO object to write CSV data
    output = StringIO()
    csv_writer = csv.writer(output)
    
    # Write headers
    csv_writer.writerow(new_headers)
    
    # Validate each row
    for row in data_rows:
        # Initialize validation results only for fields with rules
        validation_results = {f"{field}_validation": "PASS" for field in fields_with_rules}
        validation_results["is_valid_row"] = "PASS"
        
        # Create a dictionary of field values from the row
        field_values = dict(zip(headers, row))
        
        # Validate each field according to rules
        for field in fields_with_rules:
            # Skip validation if field is not in headers
            if field not in headers:
                continue
                
            rules = validation_rules[field]
            field_value = field_values.get(field, "").strip()
            
            # Required field validation
            if rules.get("is_required", False) and not field_value:
                validation_results[f"{field}_validation"] = "FAIL"
                validation_results["is_valid_row"] = "FAIL"
                continue
            
            # Skip further validation if field is empty and not required
            if not field_value and not rules.get("is_required", False):
                continue
            
            # Allowed values validation
            if "allowed_values" in rules and field_value:
                # Convert to number if the allowed values are numbers
                if all(isinstance(x, (int, float)) for x in rules["allowed_values"]):
                    try:
                        field_value = float(field_value)
                    except ValueError:
                        validation_results[f"{field}_validation"] = "FAIL"
                        validation_results["is_valid_row"] = "FAIL"
                        continue
                
                if field_value not in rules["allowed_values"]:
                    validation_results[f"{field}_validation"] = "FAIL"
                    validation_results["is_valid_row"] = "FAIL"
        
        # Prepare row with validation results
        validated_row = row + [validation_results[col] for col in validation_columns]
        csv_writer.writerow(validated_row)
    
    # Get the CSV string
    csv_content = output.getvalue()
    output.close()
    
    return csv_content

@csrf_exempt
@require_http_methods(["POST"])
def validate_uploaded_epic_file(request):
    try:
        # Parse request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON payload'
            }, status=400)

        # Validate file_id presence
        file_id = data.get('file_id')
        if not file_id:
            return JsonResponse({
                'error': 'file_id is required'
            }, status=400)

        # Validate file_id format
        try:
            file_id_obj = ObjectId(file_id)
        except:
            return JsonResponse({
                'error': 'Invalid file_id format'
            }, status=400)

        # Fetch file from database
        try:
            file = fetch_file_from_db(file_id)
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=404)

        # Read file content
        try:
            content = read_file_content(file)
        except ValueError as e:
            return JsonResponse({
                'error': f'Error reading file: {str(e)}'
            }, status=400)

        # Update file status to validated since we're going to validate it
        mongo_db.fs.files.update_one(
            {"_id": file_id_obj},
            {"$set": {"status": "validated"}}
        )

        try:
            # Validate and transform content to CSV using epic rules
            csv_content = validate_file_content(content, EPIC_VALIDATION_RULES)
            # Return just the CSV content directly
            return HttpResponse(csv_content, content_type='text/csv')
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def validate_uploaded_story_file(request):
    try:
        # Parse request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON payload'
            }, status=400)

        # Validate file_id presence
        file_id = data.get('file_id')
        if not file_id:
            return JsonResponse({
                'error': 'file_id is required'
            }, status=400)

        # Validate file_id format
        try:
            file_id_obj = ObjectId(file_id)
        except:
            return JsonResponse({
                'error': 'Invalid file_id format'
            }, status=400)

        # Fetch file from database
        try:
            file = fetch_file_from_db(file_id)
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=404)

        # Read file content
        try:
            content = read_file_content(file)
        except ValueError as e:
            return JsonResponse({
                'error': f'Error reading file: {str(e)}'
            }, status=400)

        # Update file status to validated since we're going to validate it
        mongo_db.fs.files.update_one(
            {"_id": file_id_obj},
            {"$set": {"status": "validated"}}
        )

        try:
            # Validate and transform content to CSV using story rules
            csv_content = validate_file_content(content, STORY_VALIDATION_RULES)
            # Return just the CSV content directly
            return HttpResponse(csv_content, content_type='text/csv')
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_feature_files(request):
    handle = request.GET.get('handle')
    if not handle:
        return JsonResponse({"error": "Feature handle is required"}, status=400)

    # Find the feature
    feature = mongo_db.feature_details.find_one({"handle": handle})
    if not feature:
        return JsonResponse({"error": "Feature not found"}, status=404)

    files_info = []

    # Process story sheets
    for sheet in feature.get('story_sheets', []):
        file_id = sheet.get('file_id')
        if file_id:
            # Get file status from fs.files
            file_info = mongo_db.fs.files.find_one({"_id": ObjectId(file_id)})
            if file_info:
                files_info.append({
                    "file_id": file_id,
                    "filename": sheet.get('filename'),
                    "type": "story",
                    "status": file_info.get('status', 'unknown')
                })

    # Process epic sheets
    for sheet in feature.get('epic_sheets', []):
        file_id = sheet.get('file_id')
        if file_id:
            # Get file status from fs.files
            file_info = mongo_db.fs.files.find_one({"_id": ObjectId(file_id)})
            if file_info:
                files_info.append({
                    "file_id": file_id,
                    "filename": sheet.get('filename'),
                    "type": "epic",
                    "status": file_info.get('status', 'unknown')
                })

    return JsonResponse({
        "handle": handle,
        "files": files_info
    })





