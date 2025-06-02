from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .mongo import mongo_db,fs
from .models import FeatureDetails
from django.utils.text import slugify

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
            "details": [{"file_id": file_id, "filename": file.name}]
        }

        result = mongo_db.feature_details.insert_one(feature)

        return JsonResponse({
            "name": feature["name"],
            "id": str(result.inserted_id),
            "handle": feature["handle"],
            "details": [
                         {
                            "file_id": str(detail["file_id"]),
                            "filename": detail["filename"]
                         }
                         for detail in feature["details"]
            ]
        })

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