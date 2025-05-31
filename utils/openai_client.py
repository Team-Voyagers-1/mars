import openai
from decouple import config

# openai.api_key = config("OPENAI_API_KEY")

def generate_story_details(context: str, row: dict) -> dict:
    prompt = f"""
Context:
{context}

Story Base:
Summary: {row.get("summary")}
Story Points: {row.get("story_points")}
Epic: {row.get("epic")}

Generate a detailed user story with description, acceptance criteria, tags, and conditions.
Respond in JSON:
{{
  "summary": "...",
  "description": "...",
  "acceptance_criteria": ["...", "..."],
  "tags": ["..."],
  "conditions": ["..."],
  "story_points": ...
}}
"""
    print(prompt)
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.7
    # )

    # # Parse and return JSON string from AI response
    # content = response['choices'][0]['message']['content']
    # return eval(content)  # you can replace with `json.loads()` if response is valid JSON
