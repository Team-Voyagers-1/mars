import requests
import json

# ---------- CONFIGURATION ----------
JIRA_BASE_URL = "https://team-jira-voyagers.atlassian.net/"  # <-- Replace with your domain
EMAIL = "6yq6kv526n@privaterelay.appleid.com"                     # <-- Replace with your email
API_TOKEN = "ATATT3xFfGF0L8V7vCaLR5WktFThYSVWUvwIXuI544j--8XxsDc-EEzNOW1LMsgb9kuGA8MpsuZIB0SXeraHV3aJCQDanSRgfN1SXfdwUJuZoVtD7NarlDHNmcsipG4QKV6AvPC5gSBIggUUbsgPlEOJRvslmjV1FmHpZGTaCStYdGtl80jZg54=9A18D852"                         # <-- Replace with your API token

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
AUTH = (EMAIL, API_TOKEN)


# ---------- User Lookup ----------
def get_account_id(name_or_email):
    url = f"{JIRA_BASE_URL}/rest/api/3/user/search?query={name_or_email}"
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]["accountId"]
    print(f"⚠️ Could not resolve user: {name_or_email}")
    return None


# ---------- Get Transition ID ----------
def get_transition_id(issue_key, target_status):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        transitions = response.json()["transitions"]
        for t in transitions:
            if t["name"].lower() == target_status.lower():
                return t["id"]
    print(f"⚠️ Transition '{target_status}' not found for {issue_key}")
    return None


# ---------- Update Issue ----------
def update_issue(issue_key, new_status, assignee_email, comment_text):
    print(f"\n🔄 Processing {issue_key}")

    # --- Transition (status change) ---
    if new_status:
        transition_id = get_transition_id(issue_key, new_status)
        if transition_id:
            response = requests.post(
                f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
                headers=HEADERS,
                auth=AUTH,
                data=json.dumps({"transition": {"id": transition_id}})
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
                f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/assignee",
                headers=HEADERS,
                auth=AUTH,
                data=json.dumps({"accountId": account_id})
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
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment",
            headers=HEADERS,
            auth=AUTH,
            data=json.dumps(comment_data)
        )
        if response.status_code == 201:
            print("✅ Comment added")
        else:
            print(f"❌ Failed to add comment: {response.text}")


# ---------- Hardcoded Updates ----------
jira_updates = [
    {
        "issue_key": "SCRUM-11",
        "new_status": "In Review",
        "assignee": "jmalani54@gmail.com",
        "comment": "PO Review done. Ready for dev review."
    },
    {
        "issue_key": "SCRUM-12",
        "new_status": "Done",
        "assignee": "jmalani54@gmail.com",
        "comment": "Tested and verified. Closing the story."
    }
]

# ---------- Run Updates ----------
for update in jira_updates:
    update_issue(
        update["issue_key"],
        update.get("new_status"),
        update.get("assignee"),
        update.get("comment")
    )
