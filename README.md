# 학습 영상 노트

유튜브 링크와 태그를 넣으면 Gemini가 영상을 분석해서 노션 데이터베이스에 학습 노트를 만들어 줍니다.

```
github.io 폼 ──(GitHub API)──▶ GitHub Actions ──▶ Gemini (영상 분석) ──▶ 노션 페이지 생성
```

노션·Gemini 키는 GitHub Secrets에만 있고, 웹 페이지에는 들어가지 않습니다.

## 직접 써보고 싶다면 (Fork해서 본인 것으로)

이 저장소는 코드만 공개돼 있고, **키와 토큰은 들어 있지 않습니다.** 그래서 이 저장소의 github.io 주소로는 아무도 분석을 돌릴 수 없고(제 저장소에 Actions를 실행할 권한이 없음), 제 Gemini·노션 계정도 쓸 수 없습니다. 쓰려면 아래처럼 본인 계정에 복사해서 본인 키로 설정하세요. 비용·사용량도 전부 본인 계정에서 나갑니다.

1. 우측 상단 **Fork**로 본인 계정에 복사합니다. (공개 저장소 Actions는 무료, 비공개는 월 2000분)
2. Fork한 저장소의 **Actions** 탭에서 *I understand my workflows, go ahead and enable them*을 눌러 워크플로를 켭니다. Fork는 기본이 꺼져 있습니다.
3. 아래 **처음 설정**을 그대로 따라 합니다. 키는 전부 본인 것으로 새로 만듭니다.
4. 노션에 아래 속성을 가진 데이터베이스를 직접 만듭니다. 이름이 다르면 [analyze.py](scripts/analyze.py)의 `create_page`도 맞춰야 합니다.

   | 속성 | 유형 |
   |---|---|
   | 제목 | 제목 |
   | URL | URL |
   | 태그 | 다중 선택 |
   | 채널 | 텍스트 |
   | 요약 | 텍스트 |
   | 키워드 | 다중 선택 |
   | 난이도 | 선택 (입문/중급/고급, 없으면 자동 생성) |
   | 메모 | 텍스트 |

5. 워크플로의 `environment: GEMINI_API_KEY`는 제가 쓰는 환경 이름입니다. 본인 환경 이름으로 바꾸거나, 환경 없이 **Settings → Secrets and variables → Actions**의 Repository secrets에 등록하고 `environment:` 줄을 지워도 됩니다.

> 웹 페이지의 GitHub 토큰은 방문자 본인의 브라우저에만 저장되고, 저장소 주소는 github.io 주소에서 자동으로 채워집니다. 그래서 Fork한 쪽에서 코드를 고칠 필요는 없습니다.

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
   | `NOTION_DATABASE_ID` | 본인 데이터베이스 ID (주소의 `notion.so/` 뒤 32자리) |

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

모든 노트에는 개조식 요약(핵심 한 줄 + 요점), 키워드(노션 필터용), 난이도, 주요 구간(클릭하면 그 시간으로 이동), 연습 과제 체크리스트가 들어갑니다.

## 알아둘 점

- **근거 표시**: 각 항목에 `말함`(강사가 설명) / `화면`(영상에 보임) / `추정`(소리로 짐작)이 붙습니다. `추정`은 틀릴 수 있으니 직접 확인하세요.
- 공개 영상과 일부 공개 영상만 분석할 수 있습니다.
- Gemini 무료 등급은 하루에 분석할 수 있는 영상 길이에 제한이 있습니다.
- 개인(private) 저장소의 Actions는 월 2000분까지 무료이고, 한 번 실행에 1~2분 정도 걸립니다.
