from utils.jira_connector import get_account_id, format_description, get_epic_key
import os 
from openai import AzureOpenAI 

# Azure OpenAI Configuration
endpoint = "https://bh-in-openai-voyagers.openai.azure.com/" 
model_name = "gpt-35-turbo" 
deployment = "gpt-35-turbo" 
subscription_key = "59fe04457dfa4194820ffabc22a6c5bf" 
api_version = "2024-12-01-preview" 

def generate_story_details(context_text: str, record: dict) -> dict:
    """
    Enhances the story record using OpenAI and returns a JIRA-compatible issue payload.
    """
    prompt = f"""
You are a helpful product owner assistant. Based on the following business context and story input, improve the story description and generate a clean JIRA user story format.

Business Context:
{context_text}
-----
Story Input:
Summary: {record['summary']}
Description: {record['description']}

Generate:
- Enhanced Description
- Enhanced Summary
- Acceptance Criteria (as bullet points)
"""
    # Initialize Azure OpenAI client
    client = AzureOpenAI(     
        api_version=api_version,     
        azure_endpoint=endpoint,     
        api_key=subscription_key
    ) 

    # Get completion from Azure OpenAI
    response = client.chat.completions.create(     
        messages=[  
            {"role": "system", "content": "You are a product owner assistant."},
            {"role": "user", "content": prompt}
        ],     
        max_tokens=4096,     
        temperature=1.0,     
        top_p=1.0,     
        model=deployment 
    )

    # Construct final JIRA issue payload
    issue_payload = {
        "fields": {
            "summary": record["summary"],
            "project": {"key": record["project"]},
            "description": format_description(record["description"]),
            "issuetype": {"name": record["issuetype"]},
            "assignee": {"accountId": get_account_id(record["assignee"])},
            "labels": record["labels"],
            "parent": {"key": get_epic_key(record["parent"], record["project"])}
        }
    }

    # Remove parent key if not present
    if not record.get("parent"):
        issue_payload["fields"].pop("parent")

    return issue_payload

def generate_epic_details(context_text: str, record: dict):
    """
    Generates epic details and returns a JIRA-compatible issue payload.
    """
    issue_payload = {
        "fields": {
            "summary": record["summary"],
            "project": {"key": record["project"]},
            "description": format_description(record["description"]),
            "issuetype": {"name": record["issuetype"]},
            "assignee": {"accountId": get_account_id(record["assignee"])},
            "labels": record["labels"]
        }
    }

    return issue_payload
