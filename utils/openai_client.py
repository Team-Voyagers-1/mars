import openai
from utils.jira_connector import get_account_id, format_description,get_epic_key


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
    # openai.api_key = "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"
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": "You are a product owner assistant."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     temperature=0.7
    # )

    # ai_output = response['choices'][0]['message']['content']
    # Construct final JIRA issue payload
    issue_payload = {
        "fields": {
            "summary": record["summary"],
            "project": {"key": record["project"]},
            "description": format_description(record["description"]),
            "issuetype": {"name": record["issuetype"]},
            # "customfield_10020": record["sprint"],  # Replace with actual custom field ID
            # "customfield_10016": record["story_points"],  # Story points
            "assignee": {"accountId": get_account_id(record["assignee"])},
            "labels": record["labels"],
            "parent": {"key": get_epic_key(record["parent"], record["project"])}
        }
    }


    # Remove parent key if not present
    # if not record["parent"]:
    #     issue_payload["fields"].pop("parent")

    return issue_payload



def generate_epic_details(context_text: str, record: dict):
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
