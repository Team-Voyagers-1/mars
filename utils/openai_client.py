from utils.jira_connector import get_account_id, format_description, get_epic_key
import os 
from openai import AzureOpenAI 

# Azure OpenAI Configuration
endpoint = "https://bh-in-openai-voyagers.openai.azure.com/" 
model_name = "gpt-35-turbo" 
deployment = "gpt-35-turbo" 
subscription_key = "59fe04457dfa4194820ffabc22a6c5bf" 
api_version = "2024-12-01-preview" 

def generate_story_details(context_text: str, record: dict, feature_handle: str) -> dict:
    response = get_ai_response(context_text, record)
    labels = (record["labels"] if record["labels"] is not None else []) + ("," + feature_handle)
    parent_summary = record("Parent", None)  # This is the Feature/Parent column
    parent_key = get_epic_key(parent_summary, record["Project"])  # Get the parent issue key
    # Construct final JIRA issue payload
    issue_payload = {
        "project": {"key": record["Project"] or "SCRUM"},
        "summary": record["Summary"],
        "description": format_description(record["Description"]),
        "issuetype": {"name": "Feature"},
        "customfield_10058": format_description(record["Acceptance Criteria"]),  # Generate by AI
        "customfield_10020": record["Sprint"],
        "customfield_10016": record["Story point estimate"],
        "priority": {"name": record["Priority"]},
        "assignee": {"accountId":  get_account_id(record["Assignee"])},
        "parent": {"key": parent_key}
    }


    # Handling labels (customfield_10065)
    labels = (record["Label"] if record["Label"] is not None else []) + [feature_handle]
    if labels:
        issue_payload["customfield_10065"] = [label.strip() for label in str(labels).split(",") if label.strip()]

    # Handling Components (customfield_10068)
    if record["Components"]:
        issue_payload["customfield_10068"] = [record["Components"].strip()]

    # Handling Fix Versions (customfield_10067)
    if record["Fix Versions"]:
        if isinstance(record["Fix Versions"], str):  # If it's a string, strip it
            issue_payload["customfield_10067"] = [record["Fix Versions"].strip()]
        elif isinstance(record["Fix Versions"], float):  # Handle if it’s a float or NaN
            issue_payload["customfield_10067"] = [str(record["Fix Versions"]).strip()]
        else:
            issue_payload["customfield_10067"] = []  # or skip if empty


    # Remove parent key if not present
    # if not record["parent"]:
    #     issue_payload["fields"].pop("parent")
    return issue_payload



def generate_epic_details(context_text: str, record: dict, feature_handle: str):
    response = get_ai_response(context_text, record)
    issue_payload = {
        "project": {"key": "TEST"},
        "summary": response[0],
        "description": format_description(response[2]),
        "issuetype": {"name": "Feature"},
        "customfield_10058": format_description(response[1]),  
        "customfield_10020": record["Sprint"],
        "customfield_10016": record["Story point estimate"],
        "priority": {"name": record["Priority"]},
        "assignee": {"accountId":  get_account_id(record["Assignee"])}
    }

    # Handling labels (customfield_10065)
    labels = (record["Label"] if record["Label"] is not None else []) + [feature_handle]
    if labels:
        issue_payload["customfield_10065"] = labels

    # Handling Components (customfield_10068)
    if record["Components"]:
        issue_payload["customfield_10068"] = [record["Components"].strip()]

    # Handling Fix Versions (customfield_10067)
    if record["Fix Versions"]:
        if isinstance(record["Fix Versions"], str):  # If it's a string, strip it
            issue_payload["customfield_10067"] = [record["Fix Versions"].strip()]
        elif isinstance(record["Fix Versions"], float):  # Handle if it’s a float or NaN
            issue_payload["customfield_10067"] = [str(record["Fix Versions"]).strip()]
        else:
            issue_payload["customfield_10067"] = []  # or skip if empty
    return issue_payload


def get_ai_response(context_text: str, record: dict):
    """
    Enhances the story record using OpenAI and returns a JIRA-compatible issue payload.
    """
    prompt = f"""
You are a helpful product owner assistant. Based on the following business context and story input, improve the story description, write the Acceptance Criteria and modify Summary and generate a clean csv format.
Please make sure to write lengthy and formal paragraphs. Provide the Acceptance Criteria in Gherkin format.
please use | as separator for columns.

Business Context:
{context_text}
-----
Story Input:
Summary: {record['Summary']}
Description: {record['Description']}

Generate in '|' separated format(Summary,Acceptance Criteria,Description):
- Enhanced Summary
- Acceptance Criteria
- Enhanced Description
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
            {"role": "system", "content": "You are a product owner assistant and formats output in CSV."},
            {"role": "user", "content": prompt}
        ],     
        max_tokens=4096,     
        temperature=0.7,     
        top_p=1.0,     
        model=deployment 
    )
    data = response.choices[0].message.content
    start_index = data.index("Summary")
    rows = data[start_index:].split("\n")
    cols = []
    if len(rows) >= 2:
        cols = rows[1].split("|")
    # print("gptResponse: ",cols)
    return cols
