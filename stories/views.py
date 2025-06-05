from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.file_reader import extract_text_from_file, parse_csv_records
from utils.openai_client import generate_story_details, generate_epic_details
from utils.jira_connector import create_jira_issue,generate_jql,get_jql_result,update_story_response, update_issue, update_sub_task
from mongo.file_utils import fetch_file_by_id
from users.mongo import mongo_db
from bson import ObjectId

class GenerateStoriesView(APIView):
    def post(self, request):
        try:
              handle = request.data.get('handle')
              feature = mongo_db.feature_details.find_one({"handle": handle})

              file_id = feature["details"][0]["file_id"]
              file_info = fetch_file_by_id(ObjectId(file_id))

              story_file_id = request.data.get('file_id')
              story_file_info = fetch_file_by_id(ObjectId(story_file_id))

              context = extract_text_from_file(file_info["data"],file_info["filename"])
              records = parse_csv_records(story_file_info["data"])

              stories = []
              for row in records:
                story = generate_story_details(context, row, handle)
                story = create_jira_issue(story)
                stories.append(story)

              return Response({"stories": stories}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GenerateEpicsView(APIView):
    def post(self, request):
        try:
            handle = request.data.get('handle')
            feature = mongo_db.feature_details.find_one({"handle": handle})
            file_id = feature["details"][0]["file_id"]
            file_info = fetch_file_by_id(ObjectId(file_id))
            epic_file_id = request.data.get('file_id')
            epic_file_info = fetch_file_by_id(ObjectId(epic_file_id))
            context = extract_text_from_file(file_info["data"],file_info["filename"])
            records = parse_csv_records(epic_file_info["data"])


            epics = []
            for row in records:
                epic = generate_epic_details(context, row, handle)
#                 epic.summary, result.key - is unique for each epic
                result = create_jira_issue(epic)
                epics.append(result)

            return Response({"epics": epics}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetStoriesView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            handle = request.data.get('handle')
            issue_type = request.data.get('issue_type')
        
            users = mongo_db.users
            user = users.find_one({"_id": ObjectId(user_id)})
            jql = generate_jql(user['role'], handle, issue_type)
            stories = get_jql_result(jql)
            stories = update_story_response(stories)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateJiraView(APIView):
    def post(self, request):
        try:
            # Extract request parameters
            feature_handle = request.data.get('feature_handle')
            issues = request.data.get('issues', [])
            jira_status = request.data.get('status')
            comment = request.data.get('comment')
            
            if not feature_handle or not issues or not jira_status:
                return Response(
                    {"error": "feature_handle, issues, and status are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch configurations for the feature
            configs = self.fetch_configs(feature_handle)
            if "error" in configs:
                return Response(configs, status=status.HTTP_404_NOT_FOUND)

            updated_issues = []
            for issue in issues:
                update_issue(issue, configs, jira_status, comment)
                if jira_status == "In Review":
                    update_sub_task(issue, configs)
                    # Call Sub-Task


            return Response({
                "updated_issues": issues,
                "message": "Issues updated successfully",
                "applied_status": jira_status,
                "applied_comment": comment
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def fetch_configs(self, feature_handle):
        try:
            # Get feature details
            feature = mongo_db.feature_details.find_one({"handle": feature_handle})
            if not feature:
                return {"error": f"Feature not found with handle: {feature_handle}"}

            # Get config_id from feature_details
            config_id = feature.get("configs")
            if not config_id:
                return {"error": "No configurations found for this feature"}

            # Get feature configs
            feature_config = mongo_db.feature_configs.find_one({"_id": ObjectId(config_id)})
            if not feature_config:
                return {"error": "Feature configuration not found"}

            # Get IDs from feature_config
            role_ids = feature_config.get("roles_config", [])
            subtask_ids = feature_config.get("subtask_config", [])
            field_ids = feature_config.get("field_config", [])

            # Fetch complete role configurations
            roles_config = list(mongo_db.roles_config.find({"_id": {"$in": role_ids}}))
            roles_config = [{**role, "_id": str(role["_id"])} for role in roles_config]

            # Fetch complete subtask configurations
            subtask_config = list(mongo_db.subtask_config.find({"_id": {"$in": subtask_ids}}))
            subtask_config = [{**subtask, "_id": str(subtask["_id"])} for subtask in subtask_config]

            # Return all configurations
            return {
                "roles_config": roles_config,
                "subtask_config": subtask_config,
                "field_config": field_ids  
            }

        except Exception as e:
            return {"error": f"Error fetching configurations: {str(e)}"}
