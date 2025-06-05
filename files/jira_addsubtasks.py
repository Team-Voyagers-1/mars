import requests
import json

# ---------- Configuration ----------
JIRA_BASE_URL = "https://team-jira-voyagers.atlassian.net/"  # <-- Replace with your domain
EMAIL = "6yq6kv526n@privaterelay.appleid.com"                     # <-- Replace with your email
PROJECT_KEY = "SCRUM" # Your Jira project key

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
AUTH = (EMAIL, API_TOKEN)


# ---------- Helper to get accountId from email ----------
def get_account_id_by_email(email):
    response = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/user/search?query={email}",
        headers=HEADERS,
        auth=AUTH
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


# ---------- Create Sub-task ----------
def create_sub_task(parent_key, summary, description, assignee_email):
    account_id = get_account_id_by_email(assignee_email)
    if not account_id:
        print("❌ Could not resolve assignee accountId. Aborting sub-task creation.")
        return

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
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
        f"{JIRA_BASE_URL}/rest/api/3/issue",
        headers=HEADERS,
        auth=AUTH,
        data=json.dumps(payload)
    )

    if response.status_code == 201:
        subtask_key = response.json()["key"]
        print(f"✅ Sub-task created: {subtask_key}")
    else:
        print(f"❌ Failed to create sub-task: {response.status_code} - {response.text}")


# ---------- Example Usage ----------
if __name__ == "__main__":
    create_sub_task(
        parent_key="SCRUM-59", # Replace with your Story key
        summary="Review",
        description="Ensure team has everything to complete the tasks.",
        assignee_email="jmalani54@gmail.com" # Replace with real user's email in Jira
    )