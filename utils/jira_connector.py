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
    response = requests.post(url, headers=headers, auth=auth, json={"fields": issue_payload})

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
    jql = f'summary ~ "{summary}" AND issuetype = Feature AND project = {project_key}'
    issues = get_jql_result(jql)
    epic_key = issues[0]["key"]
    return epic_key
    

def get_jql_result(jql):
    url = f"{settings.JIRA_BASE_URL}/rest/api/2/search?jql={jql}"
    response = requests.get(
    url,
    headers=headers,
    auth=auth
    )
    data = response.json()
    return data['issues']


def generate_jql(user_role: str, feature_handle: str, issue_type: str) -> str:
    status = role_status_map.get(user_role)
    if not status:
        raise ValueError(f"Unsupported role: {user_role}")
    
    return f'Label = {feature_handle} AND status = "{status}" AND issuetype = "{issue_type}"'



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

def update_issue(issue, configs, status, comment):
    users = configs["role_ids"]
    assignee_email = ""
    if (status == "In Review" or status == "Pending Development"):
        assignee_email = get_email("Scrum Master", configs)
        status="IR1"
    if status == "In Refinement":
        assignee_email = get_email("BA Lead", configs)
        status="IR2"
    update_issue_in_jira(issue["issue_key"], status, assignee_email, comment)

        

def get_email(role, configs):
    users = configs["role_ids"]
    for user in users:
        if user['role'] == role:
            return user['email']
    return ""


def get_transition_id(issue_key, target_status):
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        transitions = response.json()["transitions"]
        for t in transitions:
            if t["name"].lower() == target_status.lower():
                return t["id"]
    print(f"⚠️ Transition '{target_status}' not found for {issue_key}")
    return None


def update_issue_in_jira(issue_key, new_status, assignee_email, comment_text):
    print(f"\n🔄 Processing {issue_key}")

    # --- Check if the status is valid ---
    if new_status:
        transition_id = get_transition_id(issue_key, new_status)
        if transition_id is None:
            print(f"❌ Skipping update for {issue_key} as '{new_status}' is not a valid status")
            return  # Exit early if the status is invalid

        # Proceed with the status update if valid
        response = requests.post(
            f"{settings.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
            headers=headers,
            auth=auth,
            data={"transition": {"id": transition_id}}
        )
        if response.status_code == 204:
            print(f"✅ Status updated to '{new_status}'")
        else:
            print(f"❌ Failed to update status: {response.text}")

    # --- Assignee update ---
    if assignee_email:
        account_id = get_account_id(assignee_email)
        if account_id:
            response = requests.put(
                f"{settings.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/assignee",
                headers=headers,
                auth=auth,
                data={"accountId": account_id}
            )
            if response.status_code == 204:
                print(f"✅ Assignee updated to {assignee_email}")
            else:
                print(f"❌ Failed to update assignee: {response.text}")

    # --- Add comment ---
    if comment_text:
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment_text}]
                }]
            }
        }
        response = requests.post(
            f"{settings.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment",
            headers=headers,
            auth=auth,
            data=comment_data
        )
        if response.status_code == 201:
            print("✅ Comment added")
        else:
            print(f"❌ Failed to add comment: {response.text}")



def update_sub_task(issue, configs):
    subtasks = configs["subtask_config"]
    for subtask in subtasks:
        email = get_email(subtask["assignee"], configs)
        create_sub_task(issue["issue_key"], subtask["summary"], subtask["summary"], email)
        

def get_account_id_by_email(email):
    response = requests.get(
        f"{settings.JIRA_BASE_URL}/rest/api/3/user/search?query={email}",
        headers=headers,
        auth=auth
    )
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]['accountId']
        else:
            print(f"⚠️ No user found with email: {email}")
    else:
        print(f"❌ Failed to fetch accountId: {response.text}")
    return None


def create_sub_task(parent_key, summary, description, assignee_email):
    account_id = get_account_id_by_email(assignee_email)
    if not account_id:
        print("❌ Could not resolve assignee accountId. Aborting sub-task creation.")
        return

    payload = {
        "fields": {
            "project": {"key": "SCRUM"},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            },
            "issuetype": {"name": "Subtask"},
            "assignee": {"accountId": account_id}
        }
    }

    response = requests.post(
        f"{settings.JIRA_BASE_URL}/rest/api/3/issue",
        headers=headers,
        auth=auth,
        data=payload
    )

    if response.status_code == 201:
        subtask_key = response.json()["key"]
        print(f"✅ Sub-task created: {subtask_key}")
    else:
        print(f"❌ Failed to create sub-task: {response.status_code} - {response.text}")

