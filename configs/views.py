from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from users.mongo import mongo_db

def create_or_update_feature_config(handle):
    feature = mongo_db.feature_details.find_one({"handle": handle})
    if not feature:
        raise Exception("Feature not found with handle: " + handle)

    config_id = feature.get("configs")
    if config_id:
        return ObjectId(config_id)  

    result = mongo_db.feature_configs.insert_one({
        "roles_config": [],
        "subtask_config": [],
        "field_config": []
    })
    config_id = result.inserted_id

    mongo_db.feature_details.update_one(
        {"_id": feature["_id"]},
        {"$set": {"configs": config_id}}
    )

    return config_id

class SaveRoleConfigView(APIView):
    def post(self, request):
        try:
            handle = request.data.get("handle")
            role_config = request.data.get("role_config", [])

            if not handle or not isinstance(role_config, list):
                return Response({"error": "Invalid payload"}, status=400)

            feature = mongo_db.feature_details.find_one({"handle": handle})
            if not feature:
                return Response({"error": "Feature not found"}, status=404)

 
            config_id = feature.get("configs")
            if config_id:
                feature_config = mongo_db.feature_configs.find_one({"_id": ObjectId(config_id)})
            else:
                feature_config = {"roles_config": [], "subtask_config": [], "field_config": []}
                config_id = mongo_db.feature_configs.insert_one(feature_config).inserted_id
                mongo_db.feature_details.update_one(
                    {"_id": feature["_id"]}, {"$set": {"configs": config_id}}
                )

            role_ids = feature_config.get("roles_config", [])

            for role in role_config:
                role_name = role.get("role")
                email = role.get("email_id")

                existing = mongo_db.roles_config.find_one({"role": role_name})
                if existing:
                    
                    mongo_db.roles_config.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"email": email}}
                    )
                    role_id = existing["_id"]
                else:
                
                    role_id = mongo_db.roles_config.insert_one({
                        "role": role_name,
                        "email": email
                    }).inserted_id

               
                if role_id not in role_ids:
                    role_ids.append(role_id)

      
            mongo_db.feature_configs.update_one(
                {"_id": ObjectId(config_id)},
                {"$set": {"roles_config": role_ids}}
            )

            return Response({"message": "Role config saved successfully"}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
       


class SaveSubtaskConfigView(APIView):
    def post(self, request):
        try:
            handle = request.data.get("handle")
            subtasks = request.data.get("subtask_config", [])

            if not handle or not subtasks:
                return Response({"error": "Missing handle or subtask_config"}, status=status.HTTP_400_BAD_REQUEST)

            subtask_ids = []
            for subtask in subtasks:
                result = mongo_db.subtask_config.insert_one({
                    "summary": subtask["summary"],
                    "assignee": subtask["assignee"],
                    "SLA": subtask["sla"]
                })
                subtask_ids.append(result.inserted_id)

            config_id = create_or_update_feature_config(handle)
            mongo_db.feature_configs.update_one(
                {"_id": config_id},
                {"$addToSet": {"subtask_config": {"$each": subtask_ids}}}
            )

            return Response({"message": "Subtasks saved", "subtask_ids": [str(_id) for _id in subtask_ids]}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
