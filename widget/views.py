from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .mongo import mongo_db,fs
from .models import FeatureDetails
from django.utils.text import slugify
import json
import os
from bson import ObjectId
import csv
from io import StringIO
from .validation_epic import (
    FIELD_VALIDATION_RULES,
    get_required_fields,
    get_fields_with_allowed_values
)

@csrf_exempt
def upload_feature_details(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        file = request.FILES.get('file')

        if not name or not file:
            return JsonResponse({'error': 'name and file are required'}, status=400)

        try:
            validate_file(file)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        existing = mongo_db.feature_details.find_one({"name": name})
        if existing:
            return JsonResponse({'error': 'Feature with this name already exists'}, status=409)

        handle = slugify(name)

        file_id = fs.put(file, filename=file.name, content_type=file.content_type)


        feature = {
            "name": name,
            "handle": handle,
            "details": [{
                "file_id": file_id,
                "filename": file.name
            }],
            "story_sheet": None,
            "epic_sheet": None
        }

        result = mongo_db.feature_details.insert_one(feature)

        response = {
            "name": feature["name"],
            "id": str(result.inserted_id),
            "handle": feature["handle"],
            "details": [{
                "file_id": str(detail["file_id"]),
                "filename": detail["filename"],
            } for detail in feature["details"]],
            "story_sheet": None,
            "epic_sheet": None
        }

        return JsonResponse(response)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

def get_feature_details(request):
    handle = request.GET.get('handle')
    if not handle:
        return JsonResponse({"error": "Handle is required"}, status=400)

    feature = mongo_db.feature_details.find_one({"handle": handle})
    if not feature:
         return JsonResponse({"error": "Feature not found"}, status=404)

    details = feature.get("details", [])
    for detail in details:
        if "file_id" in detail:
            detail["file_id"] = str(detail["file_id"])

    return JsonResponse({
            "name": feature.get("name"),
            "id": str(feature.get("_id")),
            "handle": feature.get("handle"),
            "details": details
    })

def get_all_features(request):
    feature_collection = mongo_db['feature_details']
    features = feature_collection.find({}, {'_id': 0, 'name': 1, 'handle': 1})
    feature_list = list(features)
    return JsonResponse(feature_list, safe=False)


@csrf_exempt
def update_feature(request):
    if request.method == 'POST':
        handle = request.POST.get('handle')
        file = request.FILES.get('file')
        story_sheet = request.FILES.get('story_sheet')
        epic_sheet = request.FILES.get('epic_sheet')
        
        if not handle:
            return JsonResponse({"error": "Handle is required"}, status=400)
            
        # Find the feature
        feature = mongo_db.feature_details.find_one({"handle": handle})
        if not feature:
            return JsonResponse({"error": "Feature not found"}, status=404)
        
        # Validate all uploaded files
        try:
            if file:
                validate_file(file)
            if story_sheet:
                validate_file(story_sheet)
            if epic_sheet:
                validate_file(epic_sheet)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        
        if file:
            # Store regular file
            file_id = fs.put(file, filename=file.name)
            new_detail = {
                "file_id": file_id,
                "filename": file.name,
                "type": "context"
            }
            # Append new detail to feature
            mongo_db.feature_details.update_one(
                {"handle": handle},
                {"$push": {"details": new_detail}}
            )
        
        if story_sheet:
            # Store story sheet
            file_id = fs.put(story_sheet, filename=story_sheet.name)
            sheet_detail = {
                "file_id": file_id,
                "filename": story_sheet.name
            }
            mongo_db.feature_details.update_one(
                {"handle": handle},
                {"$set": {"story_sheet": sheet_detail}}
            )
            
        if epic_sheet:
            # Store epic sheet
            file_id = fs.put(epic_sheet, filename=epic_sheet.name)
            sheet_detail = {
                "file_id": file_id,
                "filename": epic_sheet.name
            }
            mongo_db.feature_details.update_one(
                {"handle": handle},
                {"$set": {"epic_sheet": sheet_detail}}
            )
        
        # Get updated feature
        updated_feature = mongo_db.feature_details.find_one({"handle": handle})
        
        # Convert ObjectId to string for JSON serialization
        updated_feature["_id"] = str(updated_feature["_id"])
        for detail in updated_feature.get("details", []):
            if "file_id" in detail:
                detail["file_id"] = str(detail["file_id"])
        if "story_sheet" in updated_feature and updated_feature["story_sheet"]:
            updated_feature["story_sheet"]["file_id"] = str(updated_feature["story_sheet"]["file_id"])
        if "epic_sheet" in updated_feature and updated_feature["epic_sheet"]:
            updated_feature["epic_sheet"]["file_id"] = str(updated_feature["epic_sheet"]["file_id"])
    
        return JsonResponse(updated_feature)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

def validate_file(uploaded_file):

    if not uploaded_file:
        raise ValueError("No file was uploaded.")

    # Allowed file types
    allowed_extensions = ['pdf', 'csv', 'txt', 'docx']
    
    # Get the file extension
    file_name, file_extension = os.path.splitext(uploaded_file.name)
    file_extension = file_extension.lower().strip('.')
    
    # Check file type
    if file_extension not in allowed_extensions:
        raise ValueError(f"Invalid file type. Allowed types are: {', '.join(allowed_extensions)}.")
    
    # Check file size
    if uploaded_file.size < 10:  # Size in bytes
        raise ValueError("File is too small. Minimum size is 10 bytes.")
    

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

def validate_file_content(content):
    if not content or len(content) < 1:
        raise ValueError("File is empty or has no headers")

    # Get headers and data
    headers = content[0]
    data_rows = content[1:] if len(content) > 0 else []
    
    # Validation columns only for fields that have rules
    validation_columns = []
    fields_with_rules = [field for field, rules in FIELD_VALIDATION_RULES.items() 
                        if rules.get("is_required") or rules.get("allowed_values")]
    
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
            rules = FIELD_VALIDATION_RULES[field]
            field_value = field_values.get(field, "").strip()
            
            # Required field validation
            if rules.get("is_required", False) and not field_value:
                validation_results[f"{field}_validation"] = "FAIL: Required field is empty"
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
                        validation_results[f"{field}_validation"] = "FAIL: Invalid number format"
                        validation_results["is_valid_row"] = "FAIL"
                        continue
                
                if field_value not in rules["allowed_values"]:
                    validation_results[f"{field}_validation"] = f"FAIL: Value not in allowed list {rules['allowed_values']}"
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
            ObjectId(file_id)
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

        # Validate and transform content to CSV
        csv_content = validate_file_content(content)
        
        # Return just the CSV content directly
        return HttpResponse(csv_content, content_type='text/csv')

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
            ObjectId(file_id)
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

        # Validate and transform content to CSV
        csv_content = validate_file_content(content)
        
        # Return just the CSV content directly
        return HttpResponse(csv_content, content_type='text/csv')

    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)





