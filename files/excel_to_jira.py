import pandas as pd
import requests
import json
import sys
import os

# ---------------- CONFIGURATION ----------------
JIRA_BASE_URL = "https://team-jira-voyagers.atlassian.net/"  # <-- Replace with your domain
EMAIL = "6yq6kv526n@privaterelay.appleid.com"                     # <-- Replace with your email
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


def get_issue_key_by_summary(summary):
    """Search for an issue by its summary and return the issue key."""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    jql = f'project="{PROJECT_KEY}" AND summary~"{summary}"'
    params = {
        "jql": jql,
        "fields": "key",
        "maxResults": 1  # Adjust based on your needs
    }

    response = requests.get(url, headers=HEADERS, auth=AUTH, params=params)

    if response.status_code == 200:
        issues = response.json()["issues"]
        if issues:
            return issues[0]["key"]  # Return the issue key of the first matched issue
        else:
            print(f"⚠️ No Epic/Feature found with summary: {summary}")
            return None
    else:
        print(f"❌ Failed to search for issue: {response.text}")
        return None


def make_adf(text):
    """Helper function to convert text to Atlassian Document Format"""
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


def create_issues(excel_path, issue_type):
    df = pd.read_csv(excel_path)  # Read CSV file

    for _, row in df.iterrows():
        summary = row["Summary"]
        priority = row["Priority"]
        component = row["Components"]
        fix_version = row["Fix Versions"]
        labels = row["Label"]
        acceptance_criteria = row["Acceptance Criteria"]
        description = row["Description"]
        assignee_input = row["Assignee"]
        reporter_input = row["Reporter"]
        sprint = row["Sprint"]
        story_points = row["Story point estimate"]

        # Initialize parent_key as None
        parent_key = None

        # Check for Parent field only for Stories
        if issue_type == "Story":
            parent_summary = row.get("Parent", None)  # This is the Feature/Parent column
            if parent_summary:
                parent_key = get_issue_key_by_summary(parent_summary)  # Get the parent issue key

        # Find account IDs (similar to earlier)
        assignee_id = get_account_id(assignee_input)
        reporter_id = get_account_id(reporter_input)

        # Construct fields for issue creation (Feature or Story)
        fields = {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": make_adf(description),
            "issuetype": {"name": issue_type},
            "customfield_10058": make_adf(acceptance_criteria),
            "customfield_10020": sprint,
            "customfield_10016": story_points,
            "priority": {"name": priority},
            "assignee": {"accountId": assignee_id},
            "reporter": {"accountId": reporter_id}
        }

        # If the issue is a Story, link it to its Parent (Epic/Feature) using customfield_10006
        if issue_type == "Story" and parent_key:
            fields["parent"] = {"key": parent_key}  # Use the parent field for Story linking

        # Handling labels (customfield_10065)
        if pd.notna(labels):
            fields["customfield_10065"] = [label.strip() for label in str(labels).split(",") if label.strip()]

        # Handling Components (customfield_10068)
        if pd.notna(component):
            fields["customfield_10068"] = [component.strip()]

        # Handling Fix Versions (customfield_10067)
        if pd.notna(fix_version):
            if isinstance(fix_version, str):  # If it's a string, strip it
                fields["customfield_10067"] = [fix_version.strip()]
            elif isinstance(fix_version, float):  # Handle if it’s a float or NaN
                fields["customfield_10067"] = [str(fix_version).strip()]
            else:
                fields["customfield_10067"] = []  # or skip if empty

        # Create the issue (Story or Feature) in JIRA
        print(f"🟠 Creating {issue_type}: {summary}")
        response = requests.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue",
            headers=HEADERS,
            auth=AUTH,
            data=json.dumps({"fields": fields})
        )

        if response.status_code == 201:
            issue_key = response.json()["key"]
            print(f"✅ Created {issue_type}: {issue_key}")
        else:
            print(f"❌ Failed to create {issue_type}: {summary} - {response.text}")


# ---------- Entry Point ----------
if __name__ == "__main__":
    # Ask for issue type (Feature or Story)
    issue_type = input("Enter issue type (Feature or Story): ").strip().capitalize()

    # Ensure valid issue type input
    if issue_type not in ["Feature", "Story"]:
        print("❌ Invalid issue type. Please enter either 'Feature' or 'Story'.")
        sys.exit(1)

    # Ask for the full path to the CSV file
    file_path = input("Enter full path to CSV file: ").strip()

    if not os.path.exists(file_path):
        print("❌ File not found. Please check the path.")
        sys.exit(1)

    # Create issues based on the input
    create_issues(file_path, issue_type)
