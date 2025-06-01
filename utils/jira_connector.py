import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
# Role-to-status mapping
role_status_map = {
    "Product Owner": "To Do",
    "Scrum Master": "Approved",
    "Business Analyst": "In Review",
    "Dev Lead": "Pending Development"
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
    issues = get_jql_result(jql)
    epic_key = issues[0]["key"]
    return epic_key
    

def get_jql_result(jql):
    url = f"{settings.JIRA_BASE_URL}/rest/api/2/search?jql={jql}"
    print("jql", jql)
    response = requests.get(
    url,
    headers=headers,
    auth=auth
    )
    data = response.json()
    return data['issues']


def generate_jql(user_role: str, feature_handle: str) -> str:
    status = role_status_map.get(user_role)
    if not status:
        raise ValueError(f"Unsupported role: {user_role}")
    
    return f'labels = {feature_handle} AND status = "{status}"'



def update_story_response(issues):
    results = []
    for issue in issues:
        fields = issue["fields"]
        parent = fields.get("parent", {})

        result = {
            "key": issue["key"],
            "summary": fields.get("summary"),
            "issuetype": fields.get("issuetype", {}).get("name"),
            "parent_key": parent.get("key"),
            "parent_summary": parent.get("fields", {}).get("summary")
        }

        results.append(result)

    return results