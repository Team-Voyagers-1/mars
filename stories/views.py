from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.file_reader import extract_text_from_file, parse_csv_records
from utils.openai_client import generate_story_details, generate_epic_details
from utils.jira_connector import create_jira_issue,generate_jql,get_jql_result,update_story_response
from users.mongo import mongo_db
from bson import ObjectId

class GenerateStoriesView(APIView):
    def post(self, request):
        try:
            # GET FEATURE FROM HANDLE
            # GET FILES FROM FEATURE
            # EXTRACT CONTENT AND RECORDS FROM FILES
            context = extract_text_from_file("files/context.txt")
            records = parse_csv_records("files/StorySheetTemplate.csv")

            stories = []
            for row in records:
                row["labels"] = 'feature_handle, ' + row['labels']
                story = generate_story_details(context, row)
                result = create_jira_issue(story)
                stories.append(result)

            return Response({"stories": stories}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateEpicsView(APIView):
    def post(self, request):
        try:
            context = extract_text_from_file("files/context.txt")
            records = parse_csv_records("files/EpicSheetTemplate.csv")

            epics = []
            for row in records:
                epic = generate_epic_details(context, row)
                print(epic)
                # epic.summary, result.key - is unique for each epic
                # result = create_jira_issue(epic)
                # epics.append(result)

            return Response({"epics": epics}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetStoriesView(APIView):
    def get(self, request):
        try:
            user_id = request.headers['User']; 
            users = mongo_db.users
            user = users.find_one({"_id": ObjectId(user_id)})
            jql = generate_jql(user['role'], request.GET.get('feature_handle'))
            stories = get_jql_result(jql)
            stories = update_story_response(stories)
            print(stories)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
