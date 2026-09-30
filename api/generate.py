"""
냉털셰프 백엔드: Vercel Serverless Function (Python)

- 주소: POST /api/generate
- 요청: {"ingredients": "계란, 김치, 밥", "time": "20분"}
- 응답: 성공 {"reply": "..."} / 실패 {"error": "안내 문구"}

AI는 Google Gemini API 무료 등급을 사용한다.
API 키는 코드에 쓰지 않고 환경 변수(GEMINI_API_KEY)에서만 읽는다.
"""

from http.server import BaseHTTPRequestHandler
import json
import os

import requests

# 모델은 환경 변수로 바꿀 수 있게 하고, 없으면 무료 등급의 가벼운 모델을 쓴다
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
MAX_LENGTH = 200                      # 입력 최대 글자 수 (프론트와 같은 값)
TIMEOUT_SEC = 20                      # AI 응답을 기다리는 최대 시간
ALLOWED_TIMES = {"10분 이내", "20분", "30분 이상"}

SYSTEM_PROMPT = """너는 자취생을 위한 요리 도우미다.
사용자가 준 재료를 최대한 활용해 만들 수 있는 메뉴 2개를 추천하라.
소금, 간장, 설탕, 식용유 같은 기본 양념은 있다고 가정한다.
사용자가 고른 조리 시간 안에 만들 수 있는 메뉴만 추천한다.
마크다운 기호(#, *, **)는 쓰지 말고, 반드시 아래 형식으로만 작성한다.

🍳 메뉴 이름
- 사용 재료:
- 있으면 좋은 재료:
- 조리 순서:
  1. ...
  2. ...
  3. ...

입력에 먹을 수 있는 식재료가 하나도 없으면 다른 말 없이 NO_INGREDIENT 라고만 답하라."""


class handler(BaseHTTPRequestHandler):
    # ----- POST 요청 처리 -----
    def do_POST(self):
        # 1) 요청 본문(JSON) 읽기
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "요청 형식이 올바르지 않아요."})

        ingredients = str(body.get("ingredients") or "").strip()
        cook_time = body.get("time") if body.get("time") in ALLOWED_TIMES else "20분"

        # 2) 입력 검증 (프론트를 거치지 않은 요청도 막기 위해 서버에서 한 번 더)
        if not ingredients:
            return self._send(400, {"error": "재료를 하나 이상 입력해 주세요."})
        if len(ingredients) > MAX_LENGTH:
            return self._send(400, {"error": f"재료는 {MAX_LENGTH}자 이내로 입력해 주세요."})

        # 3) 환경 변수에서 API 키 읽기
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return self._send(500, {"error": "서버 설정 오류예요. (API 키 없음)"})

        # 4) Gemini API 호출
        try:
            res = requests.post(
                API_URL,
                headers={
                    "x-goog-api-key": api_key,          # 키는 주소가 아닌 헤더로 전달
                    "Content-Type": "application/json",
                },
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": f"재료: {ingredients}\n조리 시간: {cook_time}"}],
                        }
                    ],
                    "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.8},
                },
                timeout=TIMEOUT_SEC,
            )
        except requests.Timeout:
            return self._send(504, {"error": "응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요."})
        except requests.RequestException:
            return self._send(502, {"error": "AI 서버에 연결하지 못했어요. 잠시 후 다시 시도해 주세요."})

        # 5) Gemini가 오류 코드를 돌려준 경우
        if res.status_code == 429:
            # 무료 등급은 분당/일일 호출 횟수 제한이 있다
            return self._send(429, {"error": "요청이 많아요. 1분 뒤 다시 시도해 주세요."})
        if res.status_code in (400, 401, 403):
            print("Gemini 오류:", res.status_code, res.text[:300])   # Vercel Logs에서 확인용
            return self._send(500, {"error": "서버 설정 오류예요. (API 키 확인 필요)"})
        if res.status_code == 404:
            print("Gemini 오류: 모델을 찾을 수 없음 →", MODEL)
            return self._send(500, {"error": "서버 설정 오류예요. (AI 모델 이름 확인 필요)"})
        if res.status_code >= 400:
            print("Gemini 오류:", res.status_code, res.text[:300])
            return self._send(502, {"error": "레시피를 불러오지 못했어요. 잠시 후 다시 시도해 주세요."})

        # 6) 응답에서 텍스트 꺼내기
        #    구조: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
        try:
            parts = res.json()["candidates"][0]["content"]["parts"]
            reply = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        except (ValueError, KeyError, IndexError, TypeError):
            reply = ""
        if not reply:
            return self._send(502, {"error": "AI 응답을 해석하지 못했어요. 다시 시도해 주세요."})

        if "NO_INGREDIENT" in reply:
            return self._send(422, {"error": "입력하신 내용에서 식재료를 찾지 못했어요. 먹을 수 있는 재료를 입력해 주세요."})

        return self._send(200, {"reply": reply})

    # ----- POST 외의 요청(주소창 접속 등) -----
    def do_GET(self):
        return self._send(405, {"error": "POST 요청만 지원해요."})

    # ----- JSON 응답 보내기 -----
    def _send(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
