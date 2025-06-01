import pandas as pd
import requests
import json
import sys
import os

# ---------------- CONFIGURATION ----------------
JIRA_BASE_URL = "https://team-jira-voyagers.atlassian.net/"  # <-- Replace with your domain
EMAIL = "6yq6kv526n@privaterelay.appleid.com"                     # <-- Replace with your email
API_TOKEN = "ATATT3xFfGF0L8V7vCaLR5WktFThYSVWUvwIXuI544j--8XxsDc-EEzNOW1LMsgb9kuGA8MpsuZIB0SXeraHV3aJCQDanSRgfN1SXfdwUJuZoVtD7NarlDHNmcsipG4QKV6AvPC5gSBIggUUbsgPlEOJRvslmjV1FmHpZGTaCStYdGtl80jZg54=9A18D852"                         # <-- Replace with your API token
PROJECT_KEY = "SCRUM"
EPIC_LINK_FIELD = "parent"  # Use "customfield_10014" if Jira Cloud requires Epic Link by custom field

# Custom field IDs (Check in Jira Admin > Custom Fields)
SPRINT_FIELD = "customfield_10020"
STORY_POINTS_FIELD = "customfield_10016"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
AUTH = (EMAIL, API_TOKEN)

# ---------- Helper Functions ----------
def make_adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": str(text)}]
        }]
    }

def get_account_id(name_or_email):
    """Looks up Jira accountId based on display name or email."""
    url = f"{JIRA_BASE_URL}/rest/api/3/user/search?query={name_or_email}"
    response = requests.get(url, headers=HEADERS, auth=AUTH)

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

# ---------- Epic Creation ----------
def create_epics(excel_path):
    df = pd.read_excel(excel_path)
    epic_map = {}

    main_label = str(df.iloc[0]["labels"]).split(",")[0].strip()
    map_file = f"epic_map_{main_label}.json"

    for _, row in df.iterrows():
        summary = row["summary"]
        description = row["description"]
        assignee_input = row["assignee"]
        assignee_id = get_account_id(assignee_input)
        labels = [label.strip() for label in str(row["labels"]).split(",") if label.strip()]
        sprint = row.get("sprint", None)
        story_points = row.get("story_points", None)

        fields = {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": make_adf(description),
            "issuetype": {"name": "Epic"},
            "labels": labels
        }

        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}

        if pd.notna(sprint):
            fields[SPRINT_FIELD] = sprint

        if pd.notna(story_points):
            fields[STORY_POINTS_FIELD] = float(story_points)

        print(f"🟠 Creating Epic: {summary}")
        response = requests.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue",
            headers=HEADERS,
            auth=AUTH,
            data=json.dumps({"fields": fields})
        )

        if response.status_code == 201:
            epic_key = response.json()["key"]
            epic_map[summary] = epic_key
            print(f"✅ Created Epic: {epic_key}")
        else:
            print(f"❌ Failed to create Epic: {summary} - {response.text}")

    with open(map_file, "w") as f:
        json.dump(epic_map, f, indent=4)
    print(f"🗂️ Epic mapping saved to {map_file}")

# ---------- Story Creation ----------
def create_stories(excel_path):
    df = pd.read_excel(excel_path)

    main_label = str(df.iloc[0]["labels"]).split(",")[0].strip()
    map_file = f"epic_map_{main_label}.json"

    if not os.path.exists(map_file):
        print(f"❌ Mapping file '{map_file}' not found. Cannot proceed with story creation.")
        return

    with open(map_file) as f:
        epic_map = json.load(f)

    for _, row in df.iterrows():
        summary = row["summary"]
        description = row["description"]
        assignee_input = row["assignee"]
        assignee_id = get_account_id(assignee_input)
        labels = [label.strip() for label in str(row["labels"]).split(",") if label.strip()]
        parent_summary = row.get("parent", None)
        sprint = row.get("sprint", None)
        story_points = row.get("story_points", None)

        fields = {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": make_adf(description),
            "issuetype": {"name": "Story"},
            "labels": labels
        }

        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}

        if pd.notna(sprint):
            fields[SPRINT_FIELD] = sprint

        if pd.notna(story_points):
            fields[STORY_POINTS_FIELD] = float(story_points)

        if parent_summary and parent_summary in epic_map:
            fields[EPIC_LINK_FIELD] = {"key": epic_map[parent_summary]}
        elif parent_summary:
            print(f"⚠️ Epic not found for: {summary} (parent = {parent_summary})")
            continue

        print(f"🟡 Creating Story: {summary}")
        response = requests.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue",
            headers=HEADERS,
            auth=AUTH,
            data=json.dumps({"fields": fields})
        )

        if response.status_code == 201:
            story_key = response.json()["key"]
            print(f"✅ Created Story: {story_key}")
        else:
            print(f"❌ Failed to create Story: {summary} - {response.text}")

# ---------- Entry Point ----------
if __name__ == "__main__":
    input_type = input("Enter type (Epic/Story): ").strip().lower()
    file_path = input("Enter full path to Excel file: ").strip()

    if not os.path.exists(file_path):
        print("❌ File not found. Please check the path.")
        sys.exit(1)

    if input_type == "epic":
        create_epics(file_path)
    elif input_type == "story":
        create_stories(file_path)
    else:
        print("❌ Invalid input type. Must be 'Epic' or 'Story'.")
