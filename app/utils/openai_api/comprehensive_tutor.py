"""
OPIc 9단계 레벨 시스템 기반 종합 피드백 튜터
- 총점수와 정확한 OPIc 레벨 제공
- 각 답변별 개선된 모범답안 제시
- 통합된 하나의 피드백 시스템
"""
import os
import json
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class ComprehensiveOPIcTutor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    def get_comprehensive_feedback(self, questions: List[str], answers: List[str], user_profile: Dict) -> Dict:
        """전체 시험에 대한 종합 피드백 생성"""

        # 모든 문항 처리 (답변 있는 것과 없는 것 모두)
        all_qa = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            all_qa.append({
                "question_num": i + 1,
                "question": q,
                "answer": a.strip() if a and a.strip() else "무응답"
            })

        if not all_qa:
            return self._empty_feedback()

        system_prompt = f"""당신은 OPIc 평가 전문가입니다. 각 답변을 신중히 분석하고 구체적이고 실용적인 피드백을 한국어로 제공하세요.

사용자 프로필: {user_profile}

### OPIc 9단계 레벨 (엄격하고 현실적으로 평가):
- AL: 93~100 - 원어민 수준 유창함, 정교한 어휘, 복잡한 문법, 오류 없음
- IH: 88~92 - 매우 유창함, 좋은 어휘 범위, 사소한 문법 오류만 있음
- IM3: 83~87 - 대체로 유창함, 약간의 망설임, 가끔 문법 실수
- IM2: 78~82 - 적절한 유창함, 기본 어휘, 눈에 띄는 문법 오류  
- IM1: 73~77 - 제한된 유창함, 단순한 어휘, 빈번한 문법 실수
- IL: 61~72 - 기본적인 의사소통, 매우 단순한 단어, 많은 문법 오류
- NH: 46~60 - 어색한 문장, 최소한의 어휘, 심각한 문법 문제
- NM: 31~45 - 단편적인 대화, 의미 불분명, 심각한 문법 문제
- NL: 0~30 - 효과적인 의사소통 불가능, 이해할 수 없음

### 엄격한 평가 기준:
1. **문법 오류** (실제 실수 개수 세기):
   - 주어-동사 불일치: 각각 -5점
   - 시제 오류: 각각 -5점
   - 관사 오류 (a/an/the): 각각 -3점
   - 전치사 실수: 각각 -3점

2. **어휘 평가**:
   - 기본 단어만 사용 (good, bad, nice): 최대 IM1 레벨
   - 다양하지만 단순함: IM2-IM3 레벨
   - 좋은 범위의 정교한 단어: IH+ 레벨

3. **내용 개발**:
   - 한 문장 답변: 최대 IL 레벨
   - 어느 정도 세부사항이 있는 2-3문장: IM1-IM2
   - 예시와 함께 잘 개발됨: IM3+

4. **유창성 문제**:
   - 부자연스러운 어순: -3점
   - 불완전한 생각: -5점
   - 질문에 대답하지 않음: -10점

### 모범답안 작성 규칙:
- 사용자 답변의 핵심 아이디어와 주제를 유지하되, 문법을 고치고 어휘를 개선
- 2~4문장으로 확장
- 최소 하나의 연결어 사용 (e.g., "However", "For example", "As a result")
- 최소 하나의 구체적인 예시나 세부사항 포함
- OPIc 말하기 시험에 적합한 자연스러운 구어체 영어 사용

모범답안 작성 시:
1. 사용자의 원래 답변을 주의 깊게 읽기
2. 사용자 답변의 모든 관련 정보와 핵심 아이디어 유지
3. 자연스러운 구어체를 유지하면서 문법, 어휘, 흐름 개선
4. 답변을 더 풍부하게 만들기 위해 1-2개의 구체적인 예시나 세부사항 추가
5. 답변이 2-4문장 길이가 되도록 보장
6. 관련 없는 내용 추가 피하기

**무응답 문제 처리**:
- "무응답"인 경우에도 질문에 대한 모범답안과 학습 조언 제공
- 해당 문제 점수는 0점으로 처리하지만 어떻게 답변해야 하는지 가이드 제공

### 평가 예시:

사용자 답변: "I like movie. I watch movie every day."
분석: 관사 누락, 반복적인 어휘, 너무 단순함
발견된 문제: 관사 (a/the) 없음, 주어-동사 오류, 세부사항 부족
점수: 55 (NH 레벨)
개선 버전: "I really like watching movies in my free time. For example, I enjoy action movies because they're exciting and help me relax after studying."

사용자 답변: "My friend is good person. We go shopping sometimes."
분석: 관사 누락, 기본적인 어휘, 적절한 길이
발견된 문제: 관사 "a" 누락, 더 구체적인 세부사항 필요
점수: 68 (IL 레벨)  
개선 버전: "My best friend is a really good person who always supports me. We love going shopping together on weekends, especially at the mall near my house."

사용자 답변: "무응답"
분석: 답변하지 않음
점수: 0 (무응답)
모범 답변: "Hello, my name is Sarah and I'm from Seoul, South Korea. I'm currently studying business at university and I really enjoy meeting new people from different cultures."

### JSON 출력 형식:
{{
    "overall_score": 76,
    "opic_level": "IM1 (Intermediate Mid 1)",
    "level_description": "제한된 유창함이지만 기본적인 의사소통 가능, 문법 오류 자주 발생",
    "individual_feedback": [
        {{
            "question_num": 1,
            "score": 75,
            "strengths": ["질문에 답하려고 시도함", "관련 어휘 사용"],
            "improvements": ["관사 사용법 개선 (명사 앞에 'a' 추가)", "구체적인 예시 추가", "다양한 문장 구조 사용"],
            "sample_answer": "My hometown is a small city in Korea called Busan. It's famous for its beautiful beaches and delicious seafood, which I really enjoy. However, it can get quite crowded during summer vacation."
        }},
        {{
            "question_num": 2,
            "score": 0,
            "strengths": [],
            "improvements": ["질문에 답변하기", "개인 경험 포함하기", "구체적인 세부사항 제공"],
            "sample_answer": "In my free time, I really enjoy reading books and watching movies. For example, I love mystery novels because they keep me engaged, and I also enjoy Korean dramas with my family on weekends."
        }}
    ],
    "overall_strengths": ["의사소통 의지 보임", "질문과 관련된 답변 시도"],
    "priority_improvements": ["문법 정확성 (관사와 주어-동사 일치)", "개인 경험 기반 구체적인 세부사항 추가", "연결어 사용"],
    "study_recommendations": "관사 사용법 (a/an/the)에 집중하고, 구체적인 예시 하나씩 추가하는 연습을 하세요. 'however', 'for example', 'also'와 같은 연결어를 사용해 보세요."
}}

중요: 항상 사용자의 원래 내용을 바탕으로 모범답안을 작성하세요 - 완전히 새로운 시나리오를 만들지 마세요!
기억하세요: 당신의 역할은 사용자의 답변을 개선하는 것이지, 완전히 다른 것으로 대체하는 것이 아닙니다. 그들의 아이디어와 주제를 유지하되, 올바른 문법, 풍부한 어휘, 더 많은 세부사항으로 개선하세요."""

        qa_text = "\n\n".join(
            f"Q{item['question_num']}: {item['question']}\nA{item['question_num']}: {item['answer']}"
            for item in all_qa
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": qa_text}
                ],
                max_tokens=2000,
                temperature=0.3
            )

            feedback_text = response.choices[0].message.content
            feedback = json.loads(feedback_text)
            
            # 점수 기반으로 레벨 재계산
            feedback["opic_level"] = self._score_to_level(feedback["overall_score"])
            return feedback

        except Exception as e:
            print(f"Error generating feedback: {e}")
            return self._fallback_feedback(all_qa)

    def _empty_feedback(self):
        return {
            "overall_score": 0,
            "opic_level": "답변 미제공",
            "level_description": "평가할 응답이 없습니다.",
            "individual_feedback": [],
            "overall_strengths": [],
            "priority_improvements": ["시험을 완료하여 피드백을 받으세요"],
            "study_recommendations": "질문에 답변해 주시면 피드백을 제공해드리겠습니다."
        }

    def _fallback_feedback(self, all_qa):
        individual_feedback = []
        total_score = 0
        answered_count = 0
        
        for item in all_qa:
            if item["answer"] == "무응답":
                individual_feedback.append({
                    "question_num": item["question_num"],
                    "score": 0,
                    "strengths": [],
                    "improvements": ["질문에 답변하기", "개인 경험 포함하기", "구체적인 세부사항 제공"],
                    "sample_answer": f"'{item['question'][:30]}...' 질문에 대한 개인적인 경험과 구체적인 예시를 포함하여 2-3문장으로 답변해보세요."
                })
            else:
                individual_feedback.append({
                    "question_num": item["question_num"],
                    "score": 50,
                    "strengths": ["답변 시도함"],
                    "improvements": ["더 자세한 내용 추가", "다양한 어휘 사용"],
                    "sample_answer": f"'{item['question'][:30]}...'에 대해 개인적인 세부사항과 예시를 포함하여 답변을 확장해보세요."
                })
                total_score += 50
                answered_count += 1
        
        avg_score = total_score // len(all_qa) if all_qa else 0
        
        return {
            "overall_score": int(avg_score),
            "opic_level": self._score_to_level(int(avg_score)),
            "level_description": "기본적인 의사소통 능력이 있으나 개선이 필요합니다.",
            "individual_feedback": individual_feedback,
            "overall_strengths": ["대부분의 질문을 완료함"] if answered_count > 0 else ["시험 참여"],
            "priority_improvements": ["구체적인 예시 추가", "연결어 사용"],
            "study_recommendations": "세부사항을 추가하고 더 자연스러운 연결을 위한 연습을 하세요."
        }
