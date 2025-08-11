"""
OPIc 9단계 레벨 시스템 기반 종합 피드백 튜터
- 총점수와 정확한 OPIc 레벨 제공
- 각 답변별 개선된 모범답안 제시 (영어만 보장)
- 통합된 하나의 피드백 시스템
"""
import os
import json
import re
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HANGUL_RE = re.compile(r"[ㄱ-ㅎ가-힣]")

class ComprehensiveOPIcTutor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ---------- 레벨 매핑(9단계) ----------
    def _score_to_level(self, score: int) -> str:
        """점수 기반 OPIc 9레벨 변환"""
        if score >= 93:
            return "AL (Advanced Low)"
        elif score >= 88:
            return "IH (Intermediate High)"
        elif score >= 83:
            return "IM3 (Intermediate Mid 3)"
        elif score >= 78:
            return "IM2 (Intermediate Mid 2)"
        elif score >= 73:
            return "IM1 (Intermediate Mid 1)"
        elif score >= 61:
            return "IL (Intermediate Low)"
        elif score >= 46:
            return "NH (Novice High)"
        elif score >= 31:
            return "NM (Novice Mid)"
        else:
            return "NL (Novice Low)"

    # ---------- 유틸: 한글 포함 여부 / 단어수 ----------
    def _contains_hangul(self, text: str) -> bool:
        """한글 포함 여부 확인"""
        return bool(HANGUL_RE.search(text or ""))

    def _word_count(self, text: str) -> int:
        """단어 개수 계산"""
        return len((text or "").strip().split())

    # ---------- 샘플 답변 영문화/길이 보정 ----------
    def _fix_sample_answer(self, question: str, user_answer: str, sample_answer: str) -> str:
        """
        sample_answer가 한글을 포함하거나 60~80 단어 범위를 벗어나면
        영어 3~4문장, 60~80단어로 자연스럽게 재작성
        """
        needs_english = self._contains_hangul(sample_answer)
        wc = self._word_count(sample_answer)
        needs_length = wc < 60 or wc > 80

        if not needs_english and not needs_length:
            return sample_answer

        # 재작성 프롬프트
        system = (
            "You are an expert OPIc speaking coach. "
            "Rewrite the user's sample answer IN ENGLISH ONLY. "
            "Keep the user's main ideas but improve grammar, vocabulary, and flow. "
            "Return ONLY the final paragraph (no quotes, no extra text)."
        )
        user = f"""
Question: {question}

Original user answer (may be short or imperfect):
{user_answer}

Original sample_answer (to fix):
{sample_answer}

Rewrite requirements:
- English ONLY
- 3–4 sentences, 60–80 words total
- Opening–Body–Conclusion flow
- Include at least two transitions (e.g., However, For example, Additionally, As a result)
- Include at least two concrete details consistent with the topic
- Natural spoken English suitable for the OPIc speaking test
"""
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=220,
                temperature=0.3,
            )
            fixed = resp.choices[0].message.content.strip()
            # 최종 안전장치: 혹시 또 길이 벗어나면 간단 보정(잘라도 3~4문장 유지)
            if self._contains_hangul(fixed):
                fixed = re.sub(HANGUL_RE, "", fixed).strip()
            wc2 = self._word_count(fixed)
            if wc2 > 85:
                # 너무 길면 마지막 문장부터 잘라 단어 수 맞추기
                sentences = re.split(r"(?<=[.!?])\s+", fixed)
                while self._word_count(" ".join(sentences)) > 80 and len(sentences) > 3:
                    sentences.pop()
                fixed = " ".join(sentences)
            elif wc2 < 55:
                # 너무 짧으면 완충 문장 추가 요청(간단 패치)
                fixed += " As a result, it has become a meaningful part of my routine and helps me stay focused."
            return fixed
        except Exception:
            # 문제 발생 시, 원본 반환(최소한 영어만 보장 시도)
            if self._contains_hangul(sample_answer):
                return re.sub(HANGUL_RE, "", sample_answer).strip()
            return sample_answer

    # ---------- 메인 피드백 ----------
    def get_comprehensive_feedback(self, questions: List[str], answers: List[str], user_profile: Dict) -> Dict:
        """전체 시험에 대한 종합 피드백 생성"""
        # 모든 문항(무응답 포함)
        all_qa = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            all_qa.append({
                "question_num": i + 1,
                "question": q,
                "answer": a.strip() if a and a.strip() else "무응답"
            })

        if not all_qa:
            return self._empty_feedback()

        # 시스템 프롬프트: 피드백=한국어 / sample_answer=영어만
        system_prompt = f"""당신은 OPIc 평가 전문가입니다. 각 답변을 신중히 분석하고
피드백과 설명은 **한국어로**, sample_answer는 **영어만**으로 작성하세요.

반드시 지킬 것:
- 모든 sample_answer는 ENGLISH ONLY, 3–4문장, 60–80단어
- Opening–Body–Conclusion
- 최소 2개 연결어(However, For example, Additionally, As a result 등)
- 최소 2개 구체 디테일
- 사용자의 원래 아이디어 유지 + 문법/어휘/흐름 개선
- **무응답 질문에 대해서는 질문 내용에 맞는 완전한 영어 모범답안 작성**
- 무응답인 경우에도 해당 질문에 대한 자연스럽고 구체적인 영어 답변 예시 제공

**중요: 무응답("무응답") 처리 규칙**
- 답변이 "무응답"인 경우 점수는 반드시 0점으로 설정
- strengths는 빈 배열 []로 설정
- improvements에는 구체적인 답변 방법 가이드 제공
- sample_answer는 해당 질문에 완벽한 영어 모범답안 작성

무응답 질문 처리 방법:
- 질문의 핵심을 파악하고 일반적이고 자연스러운 답변 작성
- 개인 경험이나 의견을 포함한 현실적인 영어 답변
- 3-4문장, 60-80단어로 완성된 답변 제공

OPIc 9단계 레벨(점수→레벨)은 다음 기준을 사용:
AL 93~100 / IH 88~92 / IM3 83~87 / IM2 78~82 / IM1 73~77 / IL 61~72 / NH 46~60 / NM 31~45 / NL 0~30

사용자 프로필: {user_profile}

JSON으로만 응답하세요. 다음 형식을 따르세요:
{{
    "overall_score": 76,
    "opic_level": "IM1 (Intermediate Mid 1)",
    "level_description": "제한된 유창함이지만 기본적인 의사소통 가능, 문법 오류 자주 발생",
    "individual_feedback": [
        {{
            "question_num": 1,
            "score": 75,
            "strengths": ["질문에 답하려고 시도함", "관련 어휘 사용"],
            "improvements": ["관사 사용법 개선", "구체적인 예시 추가"],
            "sample_answer": "My hometown is a beautiful coastal city in Korea called Busan, which is famous for its stunning beaches and delicious seafood restaurants. For example, I love going to Haeundae Beach with my family during summer vacations, where we enjoy swimming and eating fresh grilled fish. Additionally, the city has a vibrant nightlife and many cultural festivals throughout the year. As a result, I feel very proud to be from Busan and always recommend it to tourists."
        }}
    ],
    "overall_strengths": ["의사소통 의지 보임"],
    "priority_improvements": ["문법 정확성", "구체적인 세부사항 추가"],
    "study_recommendations": "관사 사용법과 연결어 사용 연습을 하세요."
}}
"""

        qa_text = "\n\n".join(
            f"Q{item['question_num']}: {item['question']}\nA{item['question_num']}: {item['answer']}"
            for item in all_qa
        )

        # 모델 호출
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": qa_text}
                ],
                max_tokens=2200,
                temperature=0.3,
                seed=7  # 재현성 약간 확보
            )
            feedback = json.loads(resp.choices[0].message.content)

            # 총점→레벨 보정
            feedback["opic_level"] = self._score_to_level(int(feedback.get("overall_score", 0)))

            # 모든 sample_answer 영문화/길이 보정(사후 검증)
            for item in feedback.get("individual_feedback", []):
                sa = item.get("sample_answer", "")
                qn = item.get("question_num")
                q = next((x["question"] for x in all_qa if x["question_num"] == qn), "")
                ua = next((x["answer"] for x in all_qa if x["question_num"] == qn), "")
                
                # 무응답 처리: 강제로 0점, 빈 strengths 설정
                if ua == "무응답":
                    item["score"] = 0
                    item["strengths"] = []
                    if not item.get("improvements"):
                        item["improvements"] = ["질문에 답변하기", "개인 경험 포함하기", "구체적인 세부사항 제공"]
                
                # 영어 모범답안 보정
                fixed = self._fix_sample_answer(q, ua, sa)
                item["sample_answer"] = fixed

            return feedback

        except Exception as e:
            print(f"Error generating feedback: {e}")
            return self._fallback_feedback(all_qa)

    # ---------- 빈 입력 ----------
    def _empty_feedback(self):
        """빈 입력에 대한 기본 피드백"""
        return {
            "overall_score": 0,
            "opic_level": "답변 미제공",
            "level_description": "평가할 응답이 없습니다.",
            "individual_feedback": [],
            "overall_strengths": [],
            "priority_improvements": ["시험을 완료하여 피드백을 받으세요"],
            "study_recommendations": "질문에 답변해 주시면 피드백을 제공해드리겠습니다."
        }

    # ---------- 실패 대비 ----------
    def _fallback_feedback(self, all_qa):
        """API 호출 실패 시 대체 피드백"""
        individual_feedback = []
        total_score = 0

        for item in all_qa:
            if item["answer"] == "무응답":
                sample = (
                    "I'm planning to answer this kind of question by giving a brief opening, a concrete example, "
                    "and a short conclusion. For example, I will mention when it happened and what I did. "
                    "Additionally, I will explain how I felt and what I learned so the story sounds complete."
                )
                individual_feedback.append({
                    "question_num": item["question_num"],
                    "score": 0,
                    "strengths": [],
                    "improvements": ["질문에 답변하기", "개인 경험 포함하기", "구체적인 세부사항 제공"],
                    "sample_answer": self._fix_sample_answer(item["question"], "", sample)
                })
            else:
                sample = (
                    "I'd like to improve this answer by adding specific details and smoother transitions. "
                    "For example, I will include when it happened and a concrete outcome. "
                    "Additionally, I will end with a short reflection to make the answer sound complete and natural."
                )
                individual_feedback.append({
                    "question_num": item["question_num"],
                    "score": 50,
                    "strengths": ["답변 시도함"],
                    "improvements": ["더 자세한 내용 추가", "다양한 어휘 사용"],
                    "sample_answer": self._fix_sample_answer(item["question"], item["answer"], sample)
                })
                total_score += 50

        avg = int(round(total_score / max(1, sum(1 for x in all_qa if x['answer'] != '무응답')))) if total_score else 0

        return {
            "overall_score": avg,
            "opic_level": self._score_to_level(avg),
            "level_description": "기본적인 의사소통 능력이 있으나 개선이 필요합니다.",
            "individual_feedback": individual_feedback,
            "overall_strengths": ["대부분의 질문을 완료함"] if total_score else [],
            "priority_improvements": ["구체적인 예시 추가", "연결어 사용"],
            "study_recommendations": "세부사항을 추가하고 더 자연스러운 연결을 위한 연습을 하세요."
        }
