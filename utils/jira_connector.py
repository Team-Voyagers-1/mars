import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def create_jira_issue(issue_payload: dict) -> dict:
    """
    Sends the issue payload to the JIRA API to create a new issue.
    """
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue"

    response = requests.post(url, json=issue_payload, headers=headers, auth=auth)

    if response.status_code == 201:
        print("✅ Issue created:", response.json()["key"])
        return response.json()
    else:
        print("❌ Failed to create issue:", response.status_code, response.text)
        return {"error": response.text}
  
    
def get_account_id(name_or_email):
    """Looks up Jira accountId based on display name or email."""
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/user/search?query={name_or_email}"
    auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]["accountId"]
        else:
            print(f"⚠️ No Jira user found for: {name_or_email}")
            return None
    else:
        print(f"❌ Failed to search for user {name_or_email}: {response.text}")
        return None


def format_description(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": str(text)}]
        }]
    }


def get_epic_key(summary,project_key):
    jql = f'summary ~ "{summary}" AND issuetype = Epic AND project = {project_key}'
    url = f"{settings.JIRA_BASE_URL}/rest/api/2/search?jql={jql}"

    response = requests.get(
    url,
    headers=headers,
    auth=auth
    )
    data = response.json()
    if data["issues"]:
        epic_key = data["issues"][0]["key"]
        return epic_key
    else:
        return None