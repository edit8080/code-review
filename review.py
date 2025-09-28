import os
import json
import re
import sys
import google.generativeai as genai

def parse_gemini_response(response_text: str) -> dict:
    match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
    if match:
        json_str = match.group(1)
    else:
        json_str = response_text

    try:
        data = json.loads(json_str)

        return {
            "general_review": data.get("general_review", ""),
            "line_comments": data.get("line_comments", [])
        }
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from Gemini response. Error: {e}", file=sys.stderr)
        print(f"Raw response was: {response_text}", file=sys.stderr)
        return {"general_review": "Failed to parse AI response.", "line_comments": []}

def set_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        delimiter = f"EOF_{name.upper()}"
        print(f"{name}<<{delimiter}", file=f)
        print(value, file=f)
        print(delimiter, file=f)

def main():
    # 1. 환경 변수 읽기
    api_key = os.environ.get("GEMINI_API_KEY")
    diff_text = os.environ.get("PR_DIFF")
    prompt_path = os.environ.get("PROMPT_PATH")

    if not api_key:
        print("GEMINI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    if not diff_text or diff_text.strip() == "":
        set_output("line_comments", "[]")
        set_output("general_review", "No changes detected.")
        return

    # 2. 프롬프트 파일 읽기
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"Prompt file not found at {prompt_path}", file=sys.stderr)
        sys.exit(1)
    
    prompt = prompt_template.format(diff_text=diff_text)

    # 3. Gemini API 호출
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        parsed_data = parse_gemini_response(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. GitHub API 형식으로 line_comments 변환
    github_review_comments = []
    line_comments_data = parsed_data.get("line_comments", [])

    if isinstance(line_comments_data, list):
        for item in line_comments_data:
            if all(key in item for key in ["file_path", "line_number", "comment", "priority"]):
                github_review_comments.append({
                    "path": item["file_path"],
                    "line": int(item["line_number"]),
                    "body": f"**[${item['priority']}]**\n\n{item['comment']}"
                })

    # 5. 최종 결과물을 두 개의 출력 변수로 설정
    set_output("general_review", parsed_data.get("general_review", "No general review provided."))
    set_output("line_comments", json.dumps(github_review_comments))

if __name__ == "__main__":
    main()
