from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .mongo import mongo_db,fs
from .models import FeatureDetails
from django.utils.text import slugify
import json

@csrf_exempt
def upload_feature_details(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        file = request.FILES.get('file')

        if not name or not file:
            return JsonResponse({'error': 'name and file are required'}, status=400)

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

@csrf_exempt
def get_feature_details_filtered(request):
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
        
        # Format response
        response = {
            "name": updated_feature["name"],
            "id": str(updated_feature["_id"]),
            "handle": updated_feature["handle"],
            "details": [
                {
                    **detail,
                    "file_id": str(detail["file_id"]) if "file_id" in detail else None
                } for detail in updated_feature.get("details", [])
            ],
            "story_sheet": {
                "file_id": str(updated_feature["story_sheet"]["file_id"]),
                "filename": updated_feature["story_sheet"]["filename"]
            } if updated_feature.get("story_sheet") else None,
            "epic_sheet": {
                "file_id": str(updated_feature["epic_sheet"]["file_id"]),
                "filename": updated_feature["epic_sheet"]["filename"]
            } if updated_feature.get("epic_sheet") else None
        }
        
        return JsonResponse(response)
    
    # If GET request, return all features
    features = list(mongo_db.feature_details.find())
    filtered_features = [
        {
            "name": feature.get("name"),
            "id": str(feature.get("_id")),
            "handle": feature.get("handle"),
            "details": [
                {
                    **detail,
                    "file_id": str(detail["file_id"]) if "file_id" in detail else None
                } for detail in feature.get("details", [])
            ],
            "story_sheet": {
                "file_id": str(feature["story_sheet"]["file_id"]),
                "filename": feature["story_sheet"]["filename"]
            } if feature.get("story_sheet") else None,
            "epic_sheet": {
                "file_id": str(feature["epic_sheet"]["file_id"]),
                "filename": feature["epic_sheet"]["filename"]
            } if feature.get("epic_sheet") else None
        }
        for feature in features
        if feature.get("story_sheet") and feature.get("epic_sheet")
    ]
    
    return JsonResponse({"features": filtered_features})

