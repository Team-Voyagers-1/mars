from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.file_reader import extract_text_from_file, parse_csv_records
from utils.openai_client import generate_story_details

class GenerateStoriesView(APIView):
    def post(self, request):
        try:
            # GET FEATURE FROM HANDLE
            # GET FILES FROM FEATURE
            # EXTRACT CONTENT AND RECORDS FROM FILES
            context = extract_text_from_file("files/context.txt")
            records = parse_csv_records("files/stories.csv")

            stories = []
            for row in records:
                story = generate_story_details(context, row)
                stories.append(story)

            return Response({"stories": stories}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
