# 🧊 냉털셰프

냉장고에 남은 재료만 입력하면 AI가 **지금 바로 만들 수 있는 메뉴 2가지**와 조리 순서를 알려주는 웹 서비스입니다.

- **배포 URL:** https://(배포 후 Vercel 주소 입력).vercel.app
- **타겟:** 자취생, 1인 가구 직장인, 메뉴 고민이 귀찮은 사람

## 주요 기능

| 기능 | 설명 |
|---|---|
| 섹션 이동 | 홈 / 이용 방법 / 레시피 만들기 / FAQ, 상단 고정 메뉴로 이동 |
| 반응형 | 768px 이하에서 햄버거 메뉴, 1열 레이아웃으로 전환 |
| AI 레시피 추천 | 재료 + 조리 시간 입력 → 메뉴 2개, 사용 재료, 조리 순서 출력 |
| 실패 처리 | 빈 입력, 200자 초과, 식재료 아님, API 오류, 타임아웃 안내 |
| 다크 모드 | 기기 설정이 다크 모드면 자동으로 어두운 테마 적용 |

## 기술 스택

- **프론트엔드:** HTML, CSS, JavaScript (프레임워크 없음)
- **백엔드:** Vercel Serverless Functions (Python)
- **AI:** Google Gemini API 무료 등급 (`gemini-3.5-flash-lite`)
- **배포:** GitHub + Vercel

## 폴더 구조

```
naengteol-chef/
├── index.html          # 화면 구조 (4개 섹션)
├── css/style.css       # 디자인, 반응형, 다크 모드
├── js/main.js          # 메뉴 동작, fetch 요청, 결과/에러 표시
├── api/generate.py     # 백엔드: AI API 호출 (POST /api/generate)
├── images/             # 이미지 폴더
├── requirements.txt    # Python 패키지 (requests)
├── vercel.json         # 함수 최대 실행 시간 설정
├── .env.example        # 환경 변수 예시 (실제 키 없음)
└── .gitignore          # .env.local 등 키 파일 업로드 차단
```

## 동작 흐름

```
[사용자 입력] → js/main.js 가 fetch('/api/generate') 로 POST 요청
            → api/generate.py 가 환경 변수의 키로 Gemini API 호출
            → JSON 응답 {"reply": "..."} 또는 {"error": "..."}
            → main.js 가 결과 또는 안내 문구를 화면에 표시
```

## 환경 변수 설정

| 이름 | 설명 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio(aistudio.google.com/apikey)에서 무료로 발급한 API 키 |
| `GEMINI_MODEL` | (선택) 사용할 모델 이름. 없으면 `gemini-3.5-flash-lite` |

> ⚠️ API 키 값은 코드, README, 스크린샷 어디에도 적지 않습니다.

**로컬:** `.env.example`을 복사해 `.env.local`을 만들고 키를 입력합니다. `.env.local`은 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

**배포:** Vercel 프로젝트 → Settings → Environment Variables → `GEMINI_API_KEY` 추가 → Deployments에서 Redeploy (환경 변수는 재배포해야 반영됩니다)

## 실행 방법 (로컬)

`index.html`을 더블클릭해서 열면 `/api` 백엔드가 없어 AI 기능이 동작하지 않습니다. Vercel CLI로 실행합니다.

```bash
npm i -g vercel        # Vercel CLI 설치 (최초 1회)
vercel login           # 로그인
vercel dev             # http://localhost:3000 에서 실행
```

## 배포 방법

1. GitHub에 저장소를 만들고 코드를 push 합니다.
2. [vercel.com](https://vercel.com) → Add New → Project → GitHub 저장소 Import
3. Framework Preset은 **Other**로 두고 Deploy
4. Settings → Environment Variables에 `GEMINI_API_KEY` 등록 후 Redeploy
5. 이후에는 `git push` 할 때마다 자동으로 재배포됩니다.

## 테스트 케이스

| 입력 | 기대 결과 |
|---|---|
| `계란, 김치, 밥, 대파` / 10분 이내 | 추천 메뉴 2개와 조리 순서 표시 |
| (빈 값) | "재료를 하나 이상 입력해 주세요." |
| `노트북, 의자` | "입력하신 내용에서 식재료를 찾지 못했어요." |
| 200자 초과 | 입력칸이 200자에서 막히고, API 직접 호출 시 "200자 이내" 안내 |
| API 키 누락/오류 | "서버 설정 오류예요." |

## 보안 및 비용 관리

- API 키는 서버(Python 함수)의 환경 변수에서만 읽고, 브라우저로 전달하지 않습니다.
- 요청 중에는 버튼을 비활성화해 중복 호출(중복 과금)을 막습니다.
- 입력 200자, 응답 `maxOutputTokens` 2048로 호출당 사용량을 제한합니다.
- 무료 등급은 분당·일일 호출 횟수 제한이 있어, 초과 시(429) "1분 뒤 다시 시도" 안내를 표시합니다.
- 키 유출이 의심되면 Google AI Studio에서 즉시 삭제 후 재발급하고, Vercel 환경 변수를 교체한 뒤 재배포합니다.
