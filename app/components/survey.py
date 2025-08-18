# ========================
# Fixed Info Box (진행 바 바로 아래, 카드형 스타일)
# ========================
def render_fixed_info(total_selected: int):
    st.markdown(f"""
<style>
.opic-floating-helper {{
    position: fixed;
    top: 100px;
    right: 40px;
    width: 300px;
    max-width: 32vw;
    background: #fff;
    border: 1px solid rgba(244, 98, 31, 0.22);
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.10);
    padding: 18px 20px 16px 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    transition: box-shadow 0.2s;
}}
.opic-floating-helper .title {{
    font-weight: 800;
    font-size: 1.08rem;
    color: #f4621f;
    margin-bottom: 8px;
}}
.opic-floating-helper .desc {{
    font-size: 0.98rem;
    color: #39424e;
    line-height: 1.5;
}}
.opic-floating-helper .count {{
    margin-top: 12px;
    font-weight: 800;
    color: #2d5a2d;
    font-size: 1.05rem;
}}
@media (max-width: 1200px) {{
    .opic-floating-helper {{ display:none; }}
    .opic-mobile-progress {{
        display: flex;
        position: fixed;
        left: 0; right: 0; bottom: 0;
        z-index: 9999;
        background: #fffbe7;
        border-top: 1.5px solid #f4621f33;
        justify-content: center;
        align-items: center;
        font-size: 1.01rem;
        font-weight: 700;
        color: #f4621f;
        padding: 8px 0 7px 0;
        box-shadow: 0 -2px 12px #0001;
    }}
}}
</style>
<div class="opic-floating-helper">
    <div class="title">선택 진행 상황</div>
    <div class="desc">
        총 <b>12개 이상</b> 선택해야 다음 단계로 이동할 수 있어요.<br>
    </div>
    <div class="count">현재 선택: {total_selected}개</div>
</div>
<div class="opic-mobile-progress">
  선택 {total_selected} / 12개 이상 선택해야 다음 단계로 이동
</div>
""", unsafe_allow_html=True)
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from app.utils.styles import apply_survey_styles, apply_button_styles

# ========================
# 상수 정의
# ========================

# 설문조사 단계별 정보
SURVEY_STEPS = [
    {"label": "Background Survey", "desc": "현재 귀하는 어느 분야에 종사하고 계십니까?", "options": [
        "사업/회사", "재택근무/재택사업", "교사/교육자", "일 경험 없음"
    ]},
    {"label": "Background Survey", "desc": "현재 당신은 학생입니까?", "options": [
        "예", "아니요"
    ]},
    {"label": "Background Survey", "desc": "현재 귀하는 어디에 살고 계십니까?", "options": [
        "개인주택이나 아파트에 홀로 거주", "친구나 룸메이트와 함께 주택이나 아파트에 거주", 
        "가족(배우자/자녀/기타 가족 일원)과 함께 주택이나 아파트에 거주", "학교 기숙사", "군대 막사"
    ]},
    {"label": "Background Survey", "desc": "여가활동 및 취미 조사", "options": []},
    {"label": "Self Assessment", "desc": "본 Self Assessment에 대한 응답을 기초로 개인별 문항이 출제됩니다. 설명을 잘 읽고 본인의 English 말하기 능력과 비슷한 수준을 선택하시기 바랍니다.", "options": []}
]

# 영어 매핑
SURVEY_STEPS_EN = [
    {"label": "Background Survey", "desc": "What field are you currently working in?", "options": [
        "have work experience", "no work experience"
    ]},
    {"label": "Background Survey", "desc": "Are you currently a student?", "options": [
        "student", "not a student"
    ]},
    {"label": "Background Survey", "desc": "Where do you currently live?", "options": [
        "living alone in a house/apartment", "living with friends in a house/apartment", 
        "living with family in a house/apartment", "dormitory", "military barracks"
    ]},
    {"label": "Background Survey", "desc": "Leisure Activities and Hobbies Survey", "options": []},
    {"label": "Self Assessment", "desc": "Based on your responses to this Self Assessment, personalized questions will be generated. Please read the descriptions carefully and select the level that most closely matches your English speaking ability.", "options": []}
]

# Self Assessment 레벨 정보
SELF_ASSESSMENT_LEVELS = [
    {
        "level": 1,
        "desc": "나는 10단어 이하의 단어로 말할 수 있습니다."
    },
    {
        "level": 2, 
        "desc": "나는 기본적인 물건, 색깔, 요일, 음식, 의류, 숫자 등을 말할 수 있습니다. 나는 항상 완벽한 문장을 구사하지는 못하고 간단한 질문도 하기 어렵습니다."
    },
    {
        "level": 3,
        "desc": "나는 나 자신, 직장, 친숙한 사람과 장소, 일상에 대한 기본적인 정보를 간단한 문장으로 전달할 수 있습니다. 간단한 질문을 할 수 있습니다."
    },
    {
        "level": 4,
        "desc": "나는 나 자신, 일상, 일/학교, 취미에 대해 간단한 대화를 할 수 있습니다. 나는 이런 친숙한 주제와 일상에 대해 일련의 간단한 문장들을 쉽게 만들어 낼 수 있습니다. 내가 필요한 것을 얻기 위한 질문도 할 수 있습니다."
    },
    {
        "level": 5,
        "desc": "나는 친숙한 주제와 가정, 일/학교, 개인 및 사회적 관심사에 대해 대화할 수 있습니다. 나는 일이나 업무 일이나고 있는 일, 일어난 일에 대해 문장을 연결하여 말할 수 있습니다. 필요한 경우 설명도 할 수 있습니다. 일상 생활에서 예기치 못한 상황이 발생하더라도 대처할 수 있습니다."
    },
    {
        "level": 6,
        "desc": "나는 일/학교, 개인적인 관심사, 시사 문제에 대한 어떤 대화나 토론에도 자신 있게 참여할 수 있습니다. 나는 대부분의 주제에 관해 높은 수준의 정확성과 풍부한 어휘로 상세히 설명할 수 있습니다."
    }
]

# Self Assessment 영어 매핑
SELF_ASSESSMENT_LEVELS_EN = [
    {
        "level": 1,
        "desc": "I can speak using 10 words or less."
    },
    {
        "level": 2,
        "desc": "I can talk about basic objects, colors, days of the week, food, clothing, numbers, etc. I don't always form perfect sentences and have difficulty asking simple questions."
    },
    {
        "level": 3, 
        "desc": "I can communicate basic information about myself, work, familiar people and places, and daily life in simple sentences. I can ask simple questions."
    },
    {
        "level": 4,
        "desc": "I can have simple conversations about myself, daily life, work/school, and hobbies. I can easily create a series of simple sentences about these familiar topics and daily life. I can also ask questions to get what I need."
    },
    {
        "level": 5,
        "desc": "I can converse about familiar topics and home, work/school, and personal and social interests. I can connect sentences to talk about work or what's happening, what happened. I can provide explanations when necessary. I can handle unexpected situations in daily life."
    },
    {
        "level": 6,
        "desc": "I can confidently participate in any conversation or discussion about work/school, personal interests, and current affairs. I can describe most topics in detail with high accuracy and rich vocabulary."
    }
]

# 4단계 다중 선택 옵션들
LEISURE_ACTIVITIES = [
    "영화보기", "클럽/나이트클럽 가기", "공연보기", "콘서트보기", "박물관가기", 
    "공원가기", "캠핑하기", "해변가기", "스포츠 관람", "주거 개선", "술집/바에 가기", "카페/커피전문점 가기",
    "게임하기(비디오, 카드, 보드, 핸드폰 등)", "당구 치기", "체스하기", "SNS에 글 올리기", "친구들과 문자대화하기", "시험 대비 과정 수강하기",
    "TV보기", "리얼리티쇼 시청하기", "뉴스를 보거나 듣기", "요리 관련 프로그램 시청하기", "쇼핑하기", "차로 드라이브하기", "스파/마사지샵 가기", "구직활동하기","자원봉사하기"
] # 총 27개

HOBBIES = [
    "아이에게 책 읽어주기", "음악 감상하기", "악기 연주하기", "춤추기", "글쓰기(편지, 단문, 시 등)", "그림 그리기", "요리하기", "애완동물 기르기",
    "독서", "주식 투자하기", "신문 읽기", "여행 관련 잡지나 블로그 읽기", "사진 촬영하기", "혼자 노래 부르거나 합창하기"
] # 총 14개

SPORTS = [
    "농구", "야구/소프트볼", "축구", "미식축구", "하키", "크리켓", "골프", "배구", 
    "테니스", "배드민턴", "탁구", "수영", "자전거", "스키/스노우보드", "아이스 스케이트", 
    "조깅", "걷기", "요가", "하이킹/트레킹", "낚시", "헬스", "태권도", "운동 수업 수강하기", "운동을 전혀 하지 않음"
] # 총 24개

TRAVEL = [
    "국내출장", "해외출장", "집에서 보내는 휴가", "국내 여행", "해외 여행"
] # 총 5개

# 영어 매핑
LEISURE_ACTIVITIES_EN = [
    "movies", "club", "performance", "concert", "museum", 
    "park", "camping", "beach", "watching sports", "Improving living space", "bar/pub", "cafe",
    "game", "billiard", "chess", "SNS", "texting friends", "test preparation",
    "TV", "watching reality shows", "news", "watching cooking programs", "shopping", "driving", "spa/massage shop", "searching job", "volunteering"
] # 총 27개

HOBBIES_EN = [
    "reading books to children", "music", "musical instruments", "dancing", "writing", "drawing", "cooking", "pets",
    "reading", "investing", "newspaper", "travel magazines", "taking photos", "singing"
] # 총 14개

SPORTS_EN = [
    "basketball", "baseball/softball", "soccer", "american football", "hockey", "cricket", "golf", "volleyball", 
    "tennis", "badminton", "table tennis", "swimming", "bicycling", "skiing/snowboarding", "ice skating", 
    "jogging", "walking", "yoga", "hiking/trekking", "fishing", "health", "taekwondo", "taking fitness classes", "do not exercise"
] # 총 25개

TRAVEL_EN = [
    "domestic business trip", "overseas business trip", "staycation", "domestic travel", "international travel"
] # 총 5개

# 한국어-영어 매핑 딕셔너리
KO_EN_MAPPING = {
    # Step 1 - 직업
    "사업/회사": "have work experience",
    "재택근무/재택사업": "have work experience", 
    "교사/교육자": "have work experience",
    "일 경험 없음": "no work experience",
    
    # Step 2 - 학생여부
    "예": "student",
    "아니요": "not a student",
    
    # Step 3 - 거주형태
    "개인주택이나 아파트에 홀로 거주": "living alone in a house/apartment",
    "친구나 룸메이트와 함께 주택이나 아파트에 거주": "living with friends in a house/apartment",
    "가족(배우자/자녀/기타 가족 일원)과 함께 주택이나 아파트에 거주": "living with family in a house/apartment",
    "학교 기숙사": "dormitory",
    "군대 막사": "military barracks",
    
    # 서브 질문들 - 직업 관련
    "첫직장- 2개월 미만": "first job - less than 2 months",
    "첫직장- 2개월 이상": "first job - more than 2 months",
    "첫직장 아님 - 경험 많음": "not first job - experienced",
    "2개월 미만 - 첫직장": "less than 2 months - first job",
    "2개월 미만 - 교직은 처음이지만 이전에 다른 직업을 가진 적이 있음": "less than 2 months - first teaching job but had other jobs",
    "2개월 이상": "more than 2 months",
    "대학 이상": "university or higher",
    "초등/중/고등학교": "elementary/middle/high school",
    "평생교육": "lifelong education",
    
    # 서브 질문들 - 교육 관련
    "학위 과정 수업": "degree program courses",
    "전문 기술 향상을 위한 평생 학습": "lifelong learning for professional skills",
    "어학수업": "language courses",
    "수강 후 5년 이상 지남": "more than 5 years since last course",
    
    # Self Assessment 레벨 (레벨 숫자로 저장)
    "레벨 1": "level_1", 
    "레벨 2": "level_2",
    "레벨 3": "level_3", 
    "레벨 4": "level_4",
    "레벨 5": "level_5",
    "레벨 6": "level_6"
}

# 활동별 매핑 (리스트 순서가 같으므로 zip으로 매핑)
LEISURE_MAPPING = dict(zip(LEISURE_ACTIVITIES, LEISURE_ACTIVITIES_EN))
HOBBY_MAPPING = dict(zip(HOBBIES, HOBBIES_EN))
SPORT_MAPPING = dict(zip(SPORTS, SPORTS_EN))
TRAVEL_MAPPING = dict(zip(TRAVEL, TRAVEL_EN))

# ========================
# 메인 함수
# ========================

def show_survey():
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"
    """설문조사 화면을 표시합니다."""
    # 스타일 적용
    apply_survey_styles()
    apply_button_styles()
    
    # 현재 단계 추적 (0부터 시작)
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0
    
    step = st.session_state.survey_step
    total_steps = len(SURVEY_STEPS)
    

    # 진행 바 표시
    display_progress_bar(step, total_steps)

    # step5(진행 바) 바로 아래에 안내 박스만 렌더
    if step == 3:
        # 반드시 세션 상태 초기화 후 진행 (KeyError 방지)
        initialize_multi_select_state(step)
        render_fixed_info(calculate_total_selected(step))

    # 타이틀과 설명 표시
    display_title_and_description(step)

    # Part 번호 표시
    display_part_number(step, total_steps)

    # 설문 질문 처리
    if step == 3:  # 4단계 (다중 선택)
        handle_multiple_choice_step(step, total_steps)
    elif step == 4:  # 5단계 (Self Assessment)
        handle_self_assessment_step(step, total_steps)
    else:  # 1-3단계 (단일 선택)
        handle_single_choice_step(step, total_steps)

# ========================
# UI 표시 함수들
# ========================

def display_progress_bar(step, total_steps):
    """진행 바를 표시합니다."""
    progress_percent = int((step + 1) / total_steps * 100)
    
    st.markdown(
        f"""
        <div class="thin-progress-container">
          <div class="thin-progress-bar-bg">
            <div class="thin-progress-bar-fg" style="width: {progress_percent}%;"></div>
          </div>
          <div class="thin-progress-labels">
            {''.join([
                f'<span class="{ "active" if i==step else "" }">Step {i+1}</span>'
                for i in range(total_steps)
            ])}
          </div>
        </div>
        """, unsafe_allow_html=True
    )

def display_title_and_description(step):
    """타이틀과 설명을 표시합니다."""
    st.markdown(
        f"""
        <div style="text-align: left; margin-bottom: 12px;">
            <span style="font-size:2.1rem; font-weight:800; letter-spacing:-1px;">📝 {SURVEY_STEPS[step]["label"]}</span>
            <div style="font-size:1.13rem; color:#444; margin-top:6px; font-weight:500;">
                질문을 읽고 정확히 답변해 주세요.<br>
                설문에 대한 응답을 기초로 개인별 문항이 출제됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True
    )

def display_part_number(step, total_steps):
    """Part 번호를 표시합니다."""
    st.markdown(
        f"""
        <div style="background:rgba(244, 98, 31, 0.15); border-radius:5px; padding: 8px 12px; margin-bottom: 18px; display: inline-block; border: 1px solid rgba(244, 98, 31, 0.3);">
            <span style="font-size:1.0rem; font-weight:600; color:#f4621f;">Part {step+1} of {total_steps}</span>
        </div>
        """, unsafe_allow_html=True
    )

# ========================
# 단일 선택 처리
# ========================

def handle_single_choice_step(step, total_steps):
    """단일 선택 단계를 처리합니다."""
    radio_key = f"survey_step_{step}"
    answer = st.radio(SURVEY_STEPS[step]['desc'], SURVEY_STEPS[step]["options"], key=radio_key, index=None)

    # 추가 질문 처리
    sub_answers = handle_sub_questions(step, answer)

    # 진행 가능 여부 확인
    can_proceed = check_can_proceed(step, answer, sub_answers)

    # 네비게이션 버튼
    display_navigation_buttons(step, total_steps, can_proceed, answer, sub_answers)

def handle_sub_questions(step, answer):
    """추가 질문들을 처리합니다."""
    sub_answers = {}
    if step == 0:  # Step 1
        if answer in ["사업/회사", "재택근무/재택사업"]:
            # 상위 답변이 변경될 때만 꼬리질문 선택값 초기화
            prev_key = f"survey_step_{step}_prev_answer"
            prev_val = st.session_state.get(prev_key, None)
            if prev_val != answer:
                for k in [f"survey_step_{step}_sub", f"survey_step_{step}_sub_sub", f"survey_step_{step}_sub_sub_sub"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state[prev_key] = answer
                st.rerun()
            sub_answers["job"] = st.radio(
                "현재 귀하는 직업이 있으십니까?",
                ["예", "아니요"],
                key=f"survey_step_{step}_sub_{answer}",  # answer를 key에 포함
                index=None
            )
            if sub_answers.get("job") == "예":
                sub_answers["period"] = st.radio("귀하의 근무 기간은 얼마나 되십니까?",
                                        ["첫직장- 2개월 미만", "첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"], key=f"survey_step_{step}_sub_sub", index=None)
                if sub_answers.get("period") in ["첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"]:
                    sub_answers["management"] = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?",
                                                ["예", "아니요"], key=f"survey_step_{step}_sub_sub_sub", index=None)
        elif answer == "교사/교육자":
            sub_answers["institution"] = st.radio("현재 귀하는 어디에서 학생을 가르치십니까?",
                                ["대학 이상", "초등/중/고등학교", "평생교육"], key=f"survey_step_{step}_sub", index=None)
            if sub_answers.get("institution") is not None:
                sub_answers["job"] = st.radio("현재 귀하는 직업이 있으십니까?", ["예", "아니요"], key=f"survey_step_{step}_sub_sub", index=None)
                if sub_answers.get("job") == "예":
                    sub_answers["period"] = st.radio("귀하의 근무 기간은 얼마나 되십니까?",
                                                ["2개월 미만 - 첫직장",
                                                 "2개월 미만 - 교직은 처음이지만 이전에 다른 직업을 가진 적이 있음",
                                                 "2개월 이상"], key=f"survey_step_{step}_sub_sub_sub", index=None)
                    if sub_answers.get("period") == "2개월 이상":
                        sub_answers["management"] = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?",
                                                        ["예", "아니요"], key=f"survey_step_{step}_sub_sub_sub_sub", index=None)
    elif step == 1:  # Step 2
        if answer == "예":
            sub_answers["current_class"] = st.radio("현재 어떤 강의를 듣고 있습니까?",
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업"], key=f"survey_step_{step}_sub", index=None)
        elif answer == "아니요":
            sub_answers["recent_class"] = st.radio("최근 어떤 강의를 수강했습니까?",
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업",
                                 "수강 후 5년 이상 지남"], key=f"survey_step_{step}_sub", index=None)
    return sub_answers

def check_can_proceed(step, answer, sub_answers):
    """진행 가능 여부를 확인합니다."""
    if answer is None:
        return False
    
    if step == 0:  # Step 1
        if answer in ["사업/회사", "재택근무/재택사업"]:
            if sub_answers.get("job") is None:
                return False
            elif sub_answers.get("job") == "예":
                if sub_answers.get("period") is None:
                    return False
                elif sub_answers.get("period") in ["첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"]:
                    return sub_answers.get("management") is not None
        elif answer == "교사/교육자":
            if sub_answers.get("institution") is None or sub_answers.get("job") is None:
                return False
            elif sub_answers.get("job") == "예":
                if sub_answers.get("period") is None:
                    return False
                elif sub_answers.get("period") == "2개월 이상":
                    return sub_answers.get("management") is not None
    elif step == 1:  # Step 2
        if answer == "예":
            return sub_answers.get("current_class") is not None
        elif answer == "아니요":
            return sub_answers.get("recent_class") is not None
    
    return True

# ========================
# 다중 선택 처리
# ========================

def handle_multiple_choice_step(step, total_steps):
    """다중 선택 단계를 처리합니다."""
    # 선택된 항목들을 저장할 세션 상태 초기화
    initialize_multi_select_state(step)
    
    # 전체 선택된 항목 수 계산
    total_selected = calculate_total_selected(step)


    # 안내 박스는 show_survey에서만 렌더링

    # 체크박스들 렌더
    display_leisure_activities(step)
    display_hobbies(step)
    display_sports(step)
    display_travel(step)

    # 진행 가능 여부 확인
    can_proceed = check_multi_select_completion(step, total_selected)
    answer = "completed" if can_proceed else None

    # 네비게이션 버튼
    display_navigation_buttons(step, total_steps, can_proceed, answer)

def initialize_multi_select_state(step):
    """다중 선택을 위한 세션 상태를 초기화합니다."""
    categories = ["leisure_selections", "hobby_selections", "sport_selections", "travel_selections"]
    
    for category in categories:
        key = f"{category}_{step}"
        if key not in st.session_state:
            st.session_state[key] = []

def calculate_total_selected(step):
    """선택된 항목의 총 개수를 계산합니다."""
    return (len(st.session_state[f"leisure_selections_{step}"]) + 
            len(st.session_state[f"hobby_selections_{step}"]) + 
            len(st.session_state[f"sport_selections_{step}"]) + 
            len(st.session_state[f"travel_selections_{step}"]))

def display_multi_select_progress(total_selected):
    """다중 선택 진행상황을 표시합니다."""
    st.markdown(f"""
    <div style="background:rgba(244, 98, 31, 0.1); border-radius:8px; padding: 12px; margin-bottom: 20px; border: 1px solid rgba(244, 98, 31, 0.2);">
        <div style="font-size:1.1rem; font-weight:600; color:#f4621f; margin-bottom: 4px;">
            아래의 설문에서 총 12개 이상의 항목을 선택하십시오.
        </div>
        <div style="font-size:1.0rem; font-weight:500; color:#2d5a2d;">
            <span style="font-weight:700; color:#f4621f;">{total_selected} 개</span> 항목을 선택했습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_leisure_activities(step):
    """여가 활동 체크박스를 표시합니다."""
    st.markdown("**귀하는 여가 활동으로 주로 무엇을 하십니까? (두 개 이상 선택)**")
    updated_list = []
    for activity in LEISURE_ACTIVITIES:
        checked = st.checkbox(activity, key=f"leisure_{activity}_{step}",
                              value=activity in st.session_state[f"leisure_selections_{step}"])
        if checked:
            updated_list.append(activity)
    if updated_list != st.session_state[f"leisure_selections_{step}"]:
        st.session_state[f"leisure_selections_{step}"] = updated_list
        st.rerun()
    leisure_count = len(updated_list)
    st.markdown(f"<div style='margin-bottom:8px; color:#666; font-size:0.98rem;'>선택됨: <b>{leisure_count}개</b> (최소 2개 필요)</div>", unsafe_allow_html=True)
    st.markdown("---")

def display_hobbies(step):
    """취미/관심사 체크박스를 표시합니다."""
    st.markdown("**귀하의 취미나 관심사는 무엇입니까? (한 개 이상 선택)**")
    updated_list = []
    for hobby in HOBBIES:
        checked = st.checkbox(hobby, key=f"hobby_{hobby}_{step}",
                              value=hobby in st.session_state[f"hobby_selections_{step}"])
        if checked:
            updated_list.append(hobby)
    if updated_list != st.session_state[f"hobby_selections_{step}"]:
        st.session_state[f"hobby_selections_{step}"] = updated_list
        st.rerun()
    hobby_count = len(updated_list)
    st.markdown(f"<div style='margin-bottom:8px; color:#666; font-size:0.98rem;'>선택됨: <b>{hobby_count}개</b> (최소 1개 필요)</div>", unsafe_allow_html=True)
    st.markdown("---")

def display_sports(step):
    """운동 종류 체크박스를 표시합니다."""
    st.markdown("**귀하는 주로 어떤 운동을 즐기십니까? (한개 이상 선택)**")
    updated_list = []
    for sport in SPORTS:
        checked = st.checkbox(sport, key=f"sport_{sport}_{step}",
                              value=sport in st.session_state[f"sport_selections_{step}"])
        if checked:
            updated_list.append(sport)
    if updated_list != st.session_state[f"sport_selections_{step}"]:
        st.session_state[f"sport_selections_{step}"] = updated_list
        st.rerun()
    sport_count = len(updated_list)
    st.markdown(f"<div style='margin-bottom:8px; color:#666; font-size:0.98rem;'>선택됨: <b>{sport_count}개</b> (최소 1개 필요)</div>", unsafe_allow_html=True)
    st.markdown("---")

def display_travel(step):
    """휴가/출장 체크박스를 표시합니다."""
    st.markdown("**귀하는 어떤 휴가나 출장을 다녀온 경험이 있습니까? (한개 이상 선택)**")
    updated_list = []
    for trip in TRAVEL:
        checked = st.checkbox(trip, key=f"travel_{trip}_{step}",
                              value=trip in st.session_state[f"travel_selections_{step}"])
        if checked:
            updated_list.append(trip)
    if updated_list != st.session_state[f"travel_selections_{step}"]:
        st.session_state[f"travel_selections_{step}"] = updated_list
        st.rerun()
    travel_count = len(updated_list)
    st.markdown(f"<div style='margin-bottom:8px; color:#666; font-size:0.98rem;'>선택됨: <b>{travel_count}개</b> (최소 1개 필요)</div>", unsafe_allow_html=True)

def check_multi_select_completion(step, total_selected):
    """다중 선택 완료 여부를 확인합니다."""
    leisure_ok = len(st.session_state[f"leisure_selections_{step}"]) >= 2
    hobby_ok = len(st.session_state[f"hobby_selections_{step}"]) >= 1
    sport_ok = len(st.session_state[f"sport_selections_{step}"]) >= 1
    travel_ok = len(st.session_state[f"travel_selections_{step}"]) >= 1
    total_ok = total_selected >= 12
    
    return leisure_ok and hobby_ok and sport_ok and travel_ok and total_ok

# ========================
# Self Assessment 처리
# ========================

def handle_self_assessment_step(step, total_steps):
    """Self Assessment 단계를 처리합니다."""
    st.markdown(f"""
    <div style="background:rgba(244, 98, 31, 0.1); border-radius:8px; padding: 16px; margin-bottom: 20px; border: 1px solid rgba(244, 98, 31, 0.2);">
        <div style="font-size:1.1rem; font-weight:600; color:#f4621f; margin-bottom: 8px;">
            🎯 자가 평가를 통한 맞춤형 문제 출제
        </div>
        <div style="font-size:1.0rem; font-weight:500; color:#555; line-height: 1.6;">
            아래 6개 레벨 중에서 본인의 영어 말하기 능력과 가장 비슷한 수준을 선택해주세요.<br>
            선택하신 레벨에 따라 개인화된 OPIc 문제가 출제됩니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    level_options = [f"레벨 {info['level']}" for info in SELF_ASSESSMENT_LEVELS]
    level_labels = [f"레벨 {info['level']}: {info['desc']}" for info in SELF_ASSESSMENT_LEVELS]

    selected_label = st.radio(
        "본인에게 가장 가까운 레벨을 하나 선택하세요.",
        options=level_labels,
        key=f"self_assessment_{step}_radio"
    )

    if selected_label:
        idx = level_labels.index(selected_label)
        selected_level = level_options[idx]
    else:
        selected_level = None

    can_proceed = selected_level is not None
    answer = selected_level if selected_level else None
    display_navigation_buttons(step, total_steps, can_proceed, answer)

# ========================
# 답변 저장 및 네비게이션 (설문조사 저장)
# ========================

def save_survey_answers(step, answer, sub_answers=None):
    """설문 답변을 영어로 저장합니다."""
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {}
    
    # survey_data 자체를 완전히 새로 초기화
    if not st.session_state.survey_data:
        st.session_state.survey_data = {
            "work": {},           
            "education": {},      
            "living": "",         
            "activities": {},
            "self_assessment": ""      
        }
    
    # 각 섹션이 딕셔너리인지 확인하고 초기화
    if "work" not in st.session_state.survey_data or not isinstance(st.session_state.survey_data["work"], dict):
        st.session_state.survey_data["work"] = {}
    if "education" not in st.session_state.survey_data or not isinstance(st.session_state.survey_data["education"], dict):
        st.session_state.survey_data["education"] = {}
    if "activities" not in st.session_state.survey_data or not isinstance(st.session_state.survey_data["activities"], dict):
        st.session_state.survey_data["activities"] = {}
    
    if step == 0:  # 직업 관련 - 간단하게만
        st.session_state.survey_data["work"]["field"] = KO_EN_MAPPING.get(answer, answer)
    
    elif step == 1:  # 교육 관련 - 학생 여부만
        st.session_state.survey_data["education"]["is_student"] = KO_EN_MAPPING.get(answer, answer)
    
    elif step == 2:  # 거주 형태
        st.session_state.survey_data["living"] = KO_EN_MAPPING.get(answer, answer)
    
    elif step == 3:  # 활동/취미
        st.session_state.survey_data["activities"] = {
            "leisure": [LEISURE_MAPPING.get(item, item) for item in st.session_state[f"leisure_selections_{step}"]],
            "hobbies": [HOBBY_MAPPING.get(item, item) for item in st.session_state[f"hobby_selections_{step}"]],
            "sports": [SPORT_MAPPING.get(item, item) for item in st.session_state[f"sport_selections_{step}"]],
            "travel": [TRAVEL_MAPPING.get(item, item) for item in st.session_state[f"travel_selections_{step}"]]
        }
    
    elif step == 4:  # Self Assessment
        st.session_state.survey_data["self_assessment"] = KO_EN_MAPPING.get(answer, answer)
    
    # Survey Value Pool 업데이트
    if hasattr(st.session_state, 'update_survey_value_pool'):
        st.session_state.update_survey_value_pool()

def get_user_profile():
    """사용자 프로필을 영어로 반환합니다 (AI 모델용)."""
    if "survey_data" not in st.session_state:
        return "Survey not completed."
    
    data = st.session_state.survey_data
    profile = []
    
    # 직업 정보 (간단하게)
    work_info = f"Work: {data['work'].get('field', 'not specified')}"
    profile.append(work_info)
    
    # 교육 정보 (학생 여부만)
    education_info = f"Student status: {data['education'].get('is_student', 'not specified')}"
    profile.append(education_info)
    
    # 거주 정보
    profile.append(f"Living: {data.get('living', 'not specified')}")
    
    # 활동 정보
    activities = data.get('activities', {})
    if activities:
        activity_summary = []
        if activities.get('leisure'):
            activity_summary.append(f"Leisure: {', '.join(activities['leisure'][:3])}")
        if activities.get('hobbies'):
            activity_summary.append(f"Hobbies: {', '.join(activities['hobbies'][:3])}")
        if activities.get('sports'):
            activity_summary.append(f"Sports: {', '.join(activities['sports'][:3])}")
        profile.append(" | ".join(activity_summary))
    
    # Self Assessment 정보
    self_assessment = data.get('self_assessment', 'not specified')
    profile.append(f"English Level: {self_assessment}")
    
    return " / ".join(profile)

def get_survey_data():
    """설문조사 데이터 전체를 반환합니다."""
    if "survey_data" not in st.session_state:
        return {}
    
    return st.session_state.survey_data

def display_navigation_buttons(step, total_steps, can_proceed, answer, sub_answers=None):
    """네비게이션 버튼을 표시합니다."""
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        if st.button("← Back", key=f"survey_back_{step}", disabled=(step == 0)):
            if step > 0:
                st.session_state.survey_step -= 1
                st.rerun()
    
    with col3:
        button_text = "시작하기 →" if step == total_steps else "Next →"
        if st.button(button_text, key=f"survey_next_{step}", disabled=not can_proceed):
            # 답변 저장
            save_survey_answers(step, answer, sub_answers)
            
            # 다음 단계로
            if step < total_steps - 1:
                st.session_state.survey_step += 1
                st.rerun()
            else:
                st.session_state.stage = "exam"
                st.session_state.survey_step = 0
                st.rerun()
