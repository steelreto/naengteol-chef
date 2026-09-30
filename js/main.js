// =========================================
// 냉털셰프 프론트엔드 동작
// 1) 모바일 메뉴  2) 글자 수 / 조리 시간 선택
// 3) AI 요청(fetch)  4) 결과 / 로딩 / 에러 표시
// =========================================

const MAX_LENGTH = 200;          // 입력 최대 글자 수 (백엔드와 같은 값)
const TIMEOUT_MS = 25000;        // 25초 안에 응답이 없으면 타임아웃 처리

// ----- 화면 요소 가져오기 -----
const menuToggle = document.getElementById("menuToggle");
const nav = document.getElementById("nav");
const form = document.getElementById("recipeForm");
const input = document.getElementById("ingredients");
const charCount = document.getElementById("charCount");
const timeOptions = document.getElementById("timeOptions");
const submitBtn = document.getElementById("submitBtn");
const result = document.getElementById("result");

let selectedTime = "20분";       // 기본 조리 시간

// ----- 1) 모바일 햄버거 메뉴 -----
menuToggle.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", isOpen);
});

// 메뉴 항목을 누르면 메뉴 닫기
nav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    nav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", false);
  });
});

// ----- 2) 글자 수 표시 / 조리 시간 선택 -----
input.addEventListener("input", () => {
  charCount.textContent = `${input.value.length} / ${MAX_LENGTH}`;
});

timeOptions.addEventListener("click", (e) => {
  const btn = e.target.closest(".time-btn");
  if (!btn) return;
  timeOptions.querySelectorAll(".time-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  selectedTime = btn.dataset.time;
});

// ----- 3) 폼 제출 → AI 요청 -----
form.addEventListener("submit", async (e) => {
  e.preventDefault();                       // 페이지 새로고침 막기

  const ingredients = input.value.trim();

  // 프론트에서 1차 검사 (서버에 불필요한 요청을 보내지 않기 위해)
  if (!ingredients) {
    return showError("재료를 하나 이상 입력해 주세요.");
  }
  if (ingredients.length > MAX_LENGTH) {
    return showError(`재료는 ${MAX_LENGTH}자 이내로 입력해 주세요.`);
  }

  // 타임아웃용 컨트롤러: 시간이 지나면 요청을 취소
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  setLoading(true);

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredients, time: selectedTime }),
      signal: controller.signal,
    });

    // 서버가 JSON이 아닌 응답을 줄 수도 있으니 안전하게 파싱
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      // 4xx / 5xx: 서버가 보낸 안내 문구를 그대로 표시
      return showError(data.error || `요청을 처리하지 못했어요. (오류 코드 ${res.status})`);
    }

    showResult(data.reply);
  } catch (err) {
    if (err.name === "AbortError") {
      showError("응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.");
    } else {
      showError("네트워크 오류가 발생했어요. 인터넷 연결을 확인해 주세요.");
    }
  } finally {
    clearTimeout(timer);
    setLoading(false);
  }
});

// ----- 4) 화면 표시 함수 -----
function setLoading(isLoading) {
  submitBtn.disabled = isLoading;           // 중복 클릭(중복 과금) 방지
  submitBtn.textContent = isLoading ? "레시피 만드는 중..." : "레시피 추천받기";

  if (isLoading) {
    result.hidden = false;
    result.className = "result";
    result.innerHTML = '<div class="loading"><div class="spinner"></div>AI 셰프가 레시피를 고민하고 있어요...</div>';
  }
}

function showResult(text) {
  result.hidden = false;
  result.className = "result";
  result.innerHTML = "";

  const title = document.createElement("h3");
  title.className = "result-title";
  title.textContent = "오늘의 추천 레시피";

  const body = document.createElement("div");
  body.className = "result-text";
  body.textContent = text;                  // textContent: AI 응답을 글자 그대로 표시 (HTML 삽입 방지)

  result.append(title, body);
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showError(message) {
  result.hidden = false;
  result.className = "result is-error";
  result.textContent = "⚠️ " + message;
}
