import os
import json
import re
import sys
import requests
import google.generativeai as genai

# Gemini 응답에서 JSON 객체를 추출
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
        return {"general_review": "Failed to parse AI response.", "line_comments": []}

# PR에 이미 달려있는 봇의 리뷰 코멘트를 모두 가져옴
def get_existing_comments(token: str, owner: str, repo: str, pull_number: int) -> set:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(url)
    response.raise_for_status()
    
    existing_comments = set()
    for comment in response.json():
        # 봇이 작성한 코멘트만 필터링
        if comment.get("user", {}).get("login") == "github-actions[bot]":
            existing_comments.add((comment['path'], comment['line'], comment['body']))
    return existing_comments

# GitHub Action을 위해 출력 변수를 설정
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
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    pull_request_number = os.environ.get("PULL_REQUEST_NUMBER")

    if not all([api_key, github_token, github_repository, pull_request_number]):
        print("Required environment variables are missing.", file=sys.stderr)
        sys.exit(1)
    
    owner, repo = github_repository.split('/')

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

    # PR의 기존 코멘트 가져오기
    try:
        existing_comments = get_existing_comments(github_token, owner, repo, int(pull_request_number))
    except Exception as e:
        print(f"::warning::Could not fetch existing comments: {e}", file=sys.stderr)
        existing_comments = set()

    # 4. 새로운 코멘트 생성 (중복 제외)
    github_review_comments = []
    line_comments_data = parsed_data.get("line_comments", [])
    if isinstance(line_comments_data, list):
        for item in line_comments_data:
            if all(key in item for key in ["file_path", "line_number", "comment", "priority"]):
                path = item["file_path"]
                line = int(item["line_number"])
                body = f"**[{item['priority']}]**\n\n{item['comment']}"
                
                # 이미 존재하는 코멘트가 아니라면 목록에 추가
                if (path, line, body) not in existing_comments:
                    github_review_comments.append({"path": path, "line": line, "body": body})

    # 5. 최종 결과 출력
    set_output("general_review", parsed_data.get("general_review", "No general review provided."))
    set_output("line_comments", json.dumps(github_review_comments))

if __name__ == "__main__":
    main()
