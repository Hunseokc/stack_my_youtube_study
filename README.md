# 학습 영상 노트

유튜브 링크와 태그를 넣으면 Gemini가 영상을 분석해서 노션 데이터베이스에 학습 노트를 만들어 줍니다.

```
github.io 폼 ──(GitHub API)──▶ GitHub Actions ──▶ Gemini (영상 분석) ──▶ 노션 페이지 생성
```

노션·Gemini 키는 GitHub Secrets에만 있고, 웹 페이지에는 들어가지 않습니다.

## 처음 설정 (한 번만)

### 1. 노션 Integration
1. https://www.notion.so/profile/integrations 에서 **새 API 통합**을 만들고 Internal Integration Secret(`ntn_...`)을 복사합니다.
2. 노션의 `유튜브 정리` → `학습 영상 노트` 데이터베이스 페이지에서 `···` → **연결** → 방금 만든 통합을 추가합니다.

### 2. Gemini API 키
https://aistudio.google.com/apikey 에서 발급합니다.

### 3. GitHub 저장소
1. 이 폴더를 GitHub 저장소로 올립니다.
2. **Settings → Environments**의 `GEMINI_API_KEY` 환경에 Secrets 세 개를 등록합니다. 워크플로가 이 환경을 지정해서 읽어요. 환경 이름을 바꾸면 [analyze.yml](.github/workflows/analyze.yml)의 `environment:` 값도 같이 바꾸세요.

   | 이름 | 값 |
   |---|---|
   | `GEMINI_API_KEY` | Gemini 키 |
   | `NOTION_TOKEN` | 노션 통합 시크릿 |
   | `NOTION_DATABASE_ID` | `d708a561eb574175a8bb979642b3a76a` |

3. (선택) 같은 환경의 **Variables**에 `GEMINI_MODEL`을 넣으면 모델을 바꿀 수 있습니다. 기본값은 `gemini-flash-latest`이고, 더 꼼꼼한 분석을 원하면 `gemini-pro-latest`를 넣으세요.
4. **Settings → Pages**에서 Source를 `Deploy from a branch`, 브랜치 `main` / `/(root)`로 저장합니다.

### 4. 웹 페이지용 GitHub 토큰
1. https://github.com/settings/personal-access-tokens/new 에서 Fine-grained 토큰을 만듭니다.
2. Repository access는 **이 저장소만** 고르고, Permissions에서 **Actions: Read and write**만 줍니다.
3. `https://<아이디>.github.io/<저장소>/`에 접속해서 설정 창에 토큰을 넣습니다. 토큰은 그 브라우저의 localStorage에만 저장됩니다.

## 사용

링크를 붙여넣고 태그를 고른 뒤 **분석 요청**을 누르면, 보통 1~3분 안에 노션에 페이지가 생깁니다. 아래 **최근 요청** 목록에서 진행 상태를 볼 수 있고, 실패하면 로그 링크가 뜹니다.

| 태그 | 정리되는 내용 |
|---|---|
| 화성 | 진행별 코드표 (코드, 로마숫자, 기능, 보이싱, 뉘앙스, 근거, 시간) |
| 사운드 디자인 | 패치별 단계 (OSC·필터·엔벨로프 설정과 효과) |
| DAW/MIDI | 작업 순서, 단축키, 팁 |
| 리듬 | 16분 그리드 패턴, 그루브 설명 |
| 편곡 | 구간별 악기 구성과 기법 |
| 믹싱 | 트랙별 처리 체인과 설정값 |

모든 노트에는 요약, 키워드(노션 필터용), 난이도, 키·BPM, 주요 구간(클릭하면 그 시간으로 이동), 연습 과제 체크리스트가 들어갑니다.

## 알아둘 점

- **근거 표시**: 각 항목에 `말함`(강사가 설명) / `화면`(영상에 보임) / `추정`(소리로 짐작)이 붙습니다. `추정`은 틀릴 수 있으니 직접 확인하세요.
- 공개 영상과 일부 공개 영상만 분석할 수 있습니다.
- Gemini 무료 등급은 하루에 분석할 수 있는 영상 길이에 제한이 있습니다.
- 개인(private) 저장소의 Actions는 월 2000분까지 무료이고, 한 번 실행에 1~2분 정도 걸립니다.
