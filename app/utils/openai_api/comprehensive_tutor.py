"""
OPIc 9단계 레벨 시스템 기반 종합 피드백 튜터 (안정화 + 동적 길이 버전)
- 전 문항 채점 보장: 배치 처리 + 누락 문항 개별 보정
- JSON 깨짐 자동 복구(safe_json_loads)
- 무응답만 0점(하드가드), 답변이 있으면 길이별 점수 하한 적용
- fallback 점수 분산(전부 50점 문제 해소)
- 모범답안은 '사용자 원문 길이'에 맞춰 동적 생성 (원문>80단어면 절대 축소 금지)
"""
import os
import json
import re
import random
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HANGUL_RE = re.compile(r"[ㄱ-ㅎ가-힣]")

# ---------------------- 유틸 ---------------------- #
def _contains_hangul(text: str) -> bool:
    return bool(HANGUL_RE.search(text or ""))

def _word_count(text: str) -> int:
    return len((text or "").strip().split())


class ComprehensiveOPIcTutor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ---------- 레벨 매핑(9단계) ----------
    def _score_to_level(self, score: int) -> str:
        if score >= 93: return "AL (Advanced Low)"
        if score >= 88: return "IH (Intermediate High)"
        if score >= 83: return "IM3 (Intermediate Mid 3)"
        if score >= 78: return "IM2 (Intermediate Mid 2)"
        if score >= 73: return "IM1 (Intermediate Mid 1)"
        if score >= 61: return "IL (Intermediate Low)"
        if score >= 46: return "NH (Novice High)"
        if score >= 31: return "NM (Novice Mid)"
        return "NL (Novice Low)"

    # ---------- 하한 점수(답변 길이 기반) ----------
    def _min_floor_by_length(self, answer: str) -> int:
        if not answer or answer == "무응답":
            return 0
        wc = _word_count(answer)
        if wc >= 40: return 60
        if wc >= 20: return 50
        if wc >= 5:  return 40
        return 30

    # ---------- JSON 깨짐 복구 로더 ----------
    def _safe_json_loads(self, s: str) -> dict:
        try:
            return json.loads(s)
        except Exception:
            s2 = (s or "").strip()
            s2 = s2.replace("```json", "").replace("```", "").strip()
            # 단순 괄호 복구
            if s2.count("{") > s2.count("}"):
                s2 += "}" * (s2.count("{") - s2.count("}"))
            if s2.count("[") > s2.count("]"):
                s2 += "]" * (s2.count("[") - s2.count("]"))
            return json.loads(s2)

    # ---------- 샘플답안 보정 (동적 길이) ----------
    def _fix_sample_answer(self, question: str, user_answer: str, sample_answer: str) -> str:
        """
        모범답안 길이를 '사용자 원문'에 맞춰 동적으로 조정:
        - 무응답: 60~80 단어
        - 원문 ≤ 80단어: 60~90 단어
        - 81~130단어: [원문, 원문*1.15] (최대 140)
        - 130단어 초과: [원문, 원문*1.10] (최대 180)
        또한 '원문이 80+ 단어면 절대 원문보다 짧지 않게' 재작성.
        """
        def _target_range(user_len: int):
            if user_answer == "무응답":
                return (60, 80)
            if user_len <= 80:
                return (max(60, user_len), 90)
            if user_len <= 130:
                return (user_len, min(int(user_len * 1.15), 140))
            return (user_len, min(int(user_len * 1.10), 180))

        u_wc = _word_count(user_answer or "")
        tmin, tmax = _target_range(u_wc)

        needs_english = _contains_hangul(sample_answer)
        wc = _word_count(sample_answer or "")
        needs_length = wc < tmin or wc > tmax
        needs_rewrite = needs_english or needs_length or not sample_answer

        if not needs_rewrite and not _contains_hangul(user_answer):
            return sample_answer

        system = (
            "You are an expert OPIc speaking coach.\n"
            "Rewrite and EXPAND the model answer IN ENGLISH ONLY.\n"
            "Rules:\n"
            "- Preserve the user's intent and main ideas; refine grammar, vocabulary, and flow.\n"
            "- Clear opening–body–conclusion with at least TWO transitions "
            "(e.g., However, For example, Additionally, As a result).\n"
            "- Add realistic details that fit the user's answer (no contradictions).\n"
            f"- TARGET LENGTH: {tmin}-{tmax} words. If the user's answer is long, DO NOT shorten below the user's length.\n"
            "- Return ONLY the final paragraph (no quotes)."
        )
        user = f"""
Question: {question}

User answer (primary source, {u_wc} words):
{user_answer or "(empty/very short)"}

Original sample_answer (may be empty/short):
{sample_answer or "(empty)"}
"""

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=380,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            fixed = (resp.choices[0].message.content or "").strip()
            if _contains_hangul(fixed):
                fixed = re.sub(HANGUL_RE, "", fixed).strip()

            # 사후 길이 보정: tmin~tmax 범위로 맞춤
            wc2 = _word_count(fixed)
            if wc2 > tmax:
                sentences = re.split(r"(?<=[.!?])\s+", fixed)
                while _word_count(" ".join(sentences)) > tmax and len(sentences) > 3:
                    sentences.pop()
                fixed = " ".join(sentences)
            elif wc2 < tmin:
                fixed += " Additionally, I added a concrete example and a brief takeaway so the story feels complete and consistent with my original answer."
            return fixed
        except Exception:
            # 실패 시: 원문 기반 간단 문단 + 동적 길이 하한 보정
            base = re.sub(HANGUL_RE, "", (user_answer or "")).strip()
            if not base:
                base = "I would present a clear beginning, a specific example, and a short conclusion."
            fallback = (
                f"{base} For example, I explain when it happened and what I did. "
                f"Additionally, I describe what I learned so the story remains detailed and aligned with my original intent."
            )
            return fallback

    # ---------- 공통 시스템 프롬프트(배치 채점) ----------
    def _build_system_prompt(self, n_items: int, question_nums: List[int]) -> str:
        return (
            "너는 OPIc 말하기 시험 전문 채점관이다. 피드백/설명은 한국어, sample_answer는 영어만 작성한다.\n"
            f"- 이번 배치 문항 수: {n_items}, question_num 목록: {question_nums}\n"
            "- individual_feedback 항목 수는 입력 문항 수와 정확히 동일해야 한다(누락·중복 금지).\n\n"
            "출력(JSON only):\n"
            "{\n"
            '  "overall_score": <0~100 int>,\n'
            '  "opic_level": "<AL/IH/IM3/IM2/IM1/IL/NH/NM/NL>",\n'
            '  "level_description": "한국어로, 반드시 opic_level 값과 동일한 등급명을 포함하고, 실제 overall_score와 답변 경향을 반영해 상세하게 작성(예: 강점, 약점, 레벨 근거, 개선 방향 등 포함)",\n'
            '  "individual_feedback": [\n'
            "    {\n"
            '      "question_num": <int>,\n'
            '      "score": <0~100>,\n'
            '      "strengths": ["한국어"],\n'
            '      "improvements": ["한국어"],\n'
            '      "sample_answer": "영어만, 사용자 답변 기반, 2개 이상 전환어, 길이 규칙 준수"\n'
            "    }\n"
            "  ],\n"
            '  "overall_strengths": ["한국어"],\n'
            '  "priority_improvements": ["한국어 2~4개"],\n'
            '  "study_recommendations": "한국어"\n'
            "}\n\n"
            "- 무응답(\"무응답\")만 0점을 부여. 그 외에는 0점 금지.\n"
            "- sample_answer는 반드시 사용자의 답변을 기반으로 개선하되, 허구의 큰 설정 변경은 금지.\n"
            "- 길이 규칙: 사용자의 원문이 80단어를 넘는 경우 sample_answer를 원문보다 짧게 만들지 말고, 유사하거나 약간 더 길게 작성할 것.\n"
            "- level_description에는 반드시 opic_level 값과 동일한 등급명을 포함할 것.\n"
            "- 모든 응답은 반드시 JSON만 출력할 것(JSON only)."
        )

    # ---------- 배치 채점 호출 ----------
    def _grade_batch(self, qa_batch: List[Dict], user_profile: Dict) -> Dict:
        sys = self._build_system_prompt(len(qa_batch), [x["question_num"] for x in qa_batch])
        payload = {"user_profile": user_profile, "qa": qa_batch}
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=1600,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            )
            raw = resp.choices[0].message.content
            return self._safe_json_loads(raw)
        except Exception as e:
            print("[batch error]", e)
            return {"individual_feedback": []}

    # ---------- 단일 문항 채점(보정용) ----------
    def _grade_single(self, item: Dict, user_profile: Dict) -> Dict:
        sys = (
            "너는 OPIc 말하기 시험 전문 채점관이다. 아래 한 문항에 대해 한국어 피드백 + 영어 모범답안을 JSON으로 출력한다.\n"
            "JSON only:\n"
            "{\n"
            '  "question_num": <int>,\n'
            '  "score": <0~100>,\n'
            '  "strengths": ["한국어"],\n'
            '  "improvements": ["한국어"],\n'
            '  "sample_answer": "영어만, 사용자 답변 기반, 2개 이상 전환어, 길이 규칙 준수"\n'
            "}\n"
            "- 무응답(\"무응답\")만 0점. 그 외에는 0점 금지.\n"
            "- 길이 규칙: 사용자의 원문이 80단어 초과라면 sample_answer를 원문보다 짧게 만들지 말 것.\n"
            "- JSON만 출력."
        )
        user = {"user_profile": user_profile, "item": item}
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=520,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
                ],
            )
            return self._safe_json_loads(resp.choices[0].message.content)
        except Exception as e:
            print("[single error]", e)
            return self._fallback_item(item)

    # ---------- 누락 보정 ----------
    def _ensure_full_coverage(self, qa_batch: List[Dict], fb: Dict, user_profile: Dict) -> Dict:
        fb = fb or {}
        fb.setdefault("individual_feedback", [])
        got_by_num = {it.get("question_num"): it for it in fb["individual_feedback"] if isinstance(it, dict)}
        want_nums = [x["question_num"] for x in qa_batch]

        missing = [n for n in want_nums if n not in got_by_num]
        for num in missing:
            item = next(x for x in qa_batch if x["question_num"] == num)
            repaired = self._grade_single(item, user_profile)
            if not isinstance(repaired, dict) or "question_num" not in repaired:
                repaired = self._fallback_item(item)
            got_by_num[num] = repaired

        fb["individual_feedback"] = [got_by_num[n] for n in sorted(got_by_num.keys())]
        return fb

    # ---------- Fallback 개별 문항 ----------
    def _fallback_item(self, item: Dict) -> Dict:
        sample_pool = [
            "I usually structure my answer with a brief opening, a concrete example, and a short conclusion. For example, I explain when it happened and what action I took. Additionally, I describe how I felt and what I learned so the story sounds complete.",
            "I try to be concise but specific; however, I always include at least one detail such as time, place, or result. For example, mentioning a small outcome makes the answer more convincing.",
        ]
        score = 0 if item.get("answer") == "무응답" else max(45, self._min_floor_by_length(item.get("answer", "")))
        return {
            "question_num": item["question_num"],
            "score": score,
            "strengths": [] if score == 0 else ["질문 의도에 맞춰 응답함"],
            "improvements": ["구체적 예시 추가", "전환어 사용", "문장 길이 다양화"],
            "sample_answer": sample_pool[0],
        }

    # ---------- 빈/기본 응답 ----------
    def _empty_feedback(self) -> Dict:
        return {
            "overall_score": 0,
            "opic_level": "답변 미제공",
            "level_description": "평가할 응답이 없습니다.",
            "individual_feedback": [],
            "overall_strengths": [],
            "priority_improvements": ["시험을 완료하여 피드백을 받으세요"],
            "study_recommendations": "각 질문에 40~60초로 응답 작성 후 피드백을 요청하세요.",
            "_debug_used_fallback": True,
        }

    # ---------- 헬퍼 ----------
    def _chunks(self, arr, size):
        for i in range(0, len(arr), size):
            yield arr[i:i+size]

    # ---------- 메인 엔드포인트 ----------
    def get_comprehensive_feedback(self, questions: List[str], answers: List[str], user_profile: Dict) -> Dict:
        # 0) 전체 QA 구성
        all_qa = [{"question_num": i + 1,
                   "question": q,
                   "answer": (a or "").strip() if (a and a.strip()) else "무응답"}
                  for i, (q, a) in enumerate(zip(questions, answers))]

        if not all_qa:
            return self._empty_feedback()

        # 1) 배치로 채점 시도 (4개 단위 추천)
        merged_feedback = {"individual_feedback": []}
        for batch in self._chunks(all_qa, 4):
            fb = self._grade_batch(batch, user_profile)
            fb = self._ensure_full_coverage(batch, fb, user_profile)
            merged_feedback["individual_feedback"].extend(fb["individual_feedback"])

        # 2) 점수 하드가드 + 모범답안 동적 길이 보정
        for item in merged_feedback["individual_feedback"]:
            qn = item.get("question_num")
            orig = next((x for x in all_qa if x["question_num"] == qn), {"question": "", "answer": "무응답"})
            # 무응답만 0점
            if orig["answer"] == "무응답":
                item["score"] = 0
                item["strengths"] = []
                item.setdefault("improvements", ["질문에 답변하기", "개인 경험 포함하기", "구체적인 세부사항 제공"])
            else:
                # 답변이 있는데 0점 또는 하한 미만이면 보정
                try:
                    cur = int(item.get("score", 0))
                except Exception:
                    cur = 0
                floor = self._min_floor_by_length(orig["answer"])
                if cur < floor:
                    item["score"] = floor
            # 모범답안 동적 길이 보정
            item["sample_answer"] = self._fix_sample_answer(orig["question"], orig["answer"], item.get("sample_answer", ""))

        # 3) 전체 점수/레벨 계산
        scores = [int(it.get("score", 0)) for it in merged_feedback["individual_feedback"]]
        overall_score = int(round(sum(scores) / len(scores))) if scores else 0

        # 4) 종합 피드백(상위 레벨)도 OpenAI 응답에서 받아오도록 시도
        # 마지막 배치의 fb에 overall_xxx가 있으면 우선 사용, 없으면 기본값
        last_fb = fb if 'overall_score' in locals() and isinstance(fb, dict) else {}
        level_description = None
        overall_strengths = None
        priority_improvements = None
        study_recommendations = None
        for batch_fb in [fb] if isinstance(fb, dict) else []:
            if batch_fb and isinstance(batch_fb, dict):
                if batch_fb.get('level_description'):
                    level_description = batch_fb['level_description']
                if batch_fb.get('overall_strengths'):
                    overall_strengths = batch_fb['overall_strengths']
                if batch_fb.get('priority_improvements'):
                    priority_improvements = batch_fb['priority_improvements']
                if batch_fb.get('study_recommendations'):
                    study_recommendations = batch_fb['study_recommendations']
        # merged_feedback에 overall_xxx가 있으면 우선 사용
        if 'overall_score' in merged_feedback:
            overall_score = merged_feedback['overall_score']
        if 'opic_level' in merged_feedback:
            opic_level = merged_feedback['opic_level']
        else:
            opic_level = self._score_to_level(overall_score)
        return {
            "overall_score": overall_score,
            "opic_level": opic_level,
            "level_description": level_description or self._score_to_level(overall_score) + " 등급에 해당하는 답변 경향입니다.",
            "individual_feedback": merged_feedback["individual_feedback"],
            "overall_strengths": overall_strengths if overall_strengths is not None else (["대부분의 질문에 응답함"] if scores else []),
            "priority_improvements": priority_improvements if priority_improvements is not None else ["구체적인 예시 추가", "자연스러운 연결어 사용", "문장 구조 다양화"],
            "study_recommendations": study_recommendations if study_recommendations is not None else "각 답변을 45~60초로 정규화하고, Although/Meanwhile/On top of that 등 다양한 연결어를 섞어 연습하세요.",
        }


# ---------------- 사용 예시 ----------------
if __name__ == "__main__":
    questions = [
        "Tell me about yourself.",
        "Describe a time you had to solve a problem quickly.",
        "What do you usually do on weekends?",
        "What's the last movie you watched and what did you think of it?",
        "Tell me about your last overseas business trip.",
    ]
    answers = [
        "Hello, my name is Seohyun and I study business administration at CNU in Daejeon. I enjoy movies and casual soccer with friends. Additionally, I love short trips because they help me clear my mind and learn about new places.",
        "I had to fix a team slide deck right before the presentation because some data was missing. I quickly checked our shared folder, added a simple chart, and double-checked the numbers with my classmate. As a result, our talk went smoothly.",
        "I usually meet friends, watch a movie at home, and sometimes go for a jog along the river. However, when it rains, I read business case studies and take notes.",
        "Oppenheimer impressed me with its mix of science and moral conflict. For example, the sound design and long dialogue scenes made me feel the tension. As a result, I kept thinking about the cost of innovation.",
        "I went to Singapore for a marketing workshop and networking sessions with partners. I joined seminars in the daytime and visited local food markets in the evening to understand the culture. As a result, I gained useful insights and contacts.",
    ]
    user_profile = {"name": "Seohyun", "major": "Business & Data", "target_level": "IH"}

    tutor = ComprehensiveOPIcTutor()
    result = tutor.get_comprehensive_feedback(questions, answers, user_profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
