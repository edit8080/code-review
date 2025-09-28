# Gemini AI Code Review Action 🤖

Google의 Gemini API를 사용하여 Pull Request의 코드 변경 사항을 자동으로 리뷰하는 GitHub Action입니다.

이 액션은 설정된 가이드라인에 따라 코드의 특정 라인에 직접 코멘트를 남기고, 전체적인 리뷰 요약을 제공하여 코드 품질을 향상시키고 개발 프로세스의 효율성을 높이는 데 도움을 줍니다.

## ✨ 주요 기능

- **AI 기반 코드 분석**: Google의 gemini-2.5-flash 모델을 사용하여 코드를 분석합니다.
- **라인별/블록별 코멘트**: PR의 "Files changed" 탭에 있는 특정 코드 라인에 직접 피드백을 제공합니다.
- **우선순위 시스템**: P1(Critical)부터 P5(Minor)까지 피드백의 중요도를 분류하여 중요한 문제에 먼저 집중할 수 있도록 돕습니다.
- **맞춤형 리뷰 기준**: 프로젝트의 기술 스택이나 컨벤션에 맞게 프롬프트 파일을 직접 작성하여 리뷰 기준을 커스터마이징할 수 있습니다.

## 🛠️ 시작하기

### 사전 준비

1.  **Gemini API 키 발급**: [Google AI Studio](https://aistudio.google.com/)에 방문하여 Gemini API 키를 발급받으세요.
2.  **GitHub Secrets 설정**: 리뷰를 받을 저장소의 `Settings` > `Secrets and variables` > `Actions` 메뉴로 이동하여, `GEMINI_API_KEY`라는 이름으로 발급받은 API 키를 등록합니다.

### Action 연동

리뷰를 받고 싶은 저장소의 `.github/workflows/` 폴더에 아래 내용으로 `.yml` 파일을 생성하세요.

```yaml
# .github/workflows/code-review.yml

name: "AI Code Review"

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          # private repo 는 checkout 권한을 위해서 별도 token 설정이 필요합니다.
          # - `Settings` > `Secrets and variables` > `Actions` 메뉴에 PAT 이름으로 추가해주세요.
          #
          # token: ${{ secrets.PAT }}
          fetch-depth: 0

      - name: Run Gemini AI Code Review
        uses: edit8080/code-review@v1.0.0
        with:
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          prompt-type: "kotlin-spring-boot" # 사용할 프롬프트 타입을 지정
```

## 프롬프트 타입 (Prompt Type)

prompt-type 을 통해 리뷰에 사용할 기준 프롬프트를 선택할 수 있습니다. 지원되는 프롬프트는 다음과 같습니다.

|       지원유형       | 설명                                                                                      |
| :------------------: | ----------------------------------------------------------------------------------------- |
|      `default`       | 일반적인 소프트웨어 공학 원칙에 기반한 기본 리뷰를 수행합니다. (기본값)                   |
| `kotlin-spring-boot` | Kotlin 및 Spring Boot 기술 스택의 모범 사례와 관용적인 표현에 집중하여 리뷰를 수행합니다. |

gemini-review-action 저장소의 prompts/ 디렉토리에 새로운 .md 파일을 추가하고, prompt-type으로 해당 파일명을 전달하면 새로운 리뷰 기준으로 사용할 수 있습니다.
