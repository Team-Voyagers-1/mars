from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.file_reader import extract_text_from_file, parse_csv_records
from utils.openai_client import generate_story_details, generate_epic_details
from utils.jira_connector import create_jira_issue,generate_jql,get_jql_result,update_story_response
from mongo.file_utils import fetch_file_by_id
from users.mongo import mongo_db
from bson import ObjectId

class GenerateStoriesView(APIView):
    def post(self, request):
        try:
              handle = request.data.get('handle')
              feature = mongo_db.feature_details.find_one({"handle": handle})

              file_id = feature["details"][0]["file_id"]
              file_info = fetch_file_by_id(file_id)

              story_file_id = request.data.get('file_id')
              story_file_info = fetch_file_by_id(story_file_id)

              context = extract_text_from_file(file_info["data"],file_info["filename"])
              records = parse_csv_records(story_file_info["data"])

              stories = []
              for row in records:
                         row["labels"] = 'feature_handle, ' + str(row['labels'])
                         story = generate_story_details(context, row, handle)
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
