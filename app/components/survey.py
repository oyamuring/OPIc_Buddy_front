"""
설문조사 화면 컴포넌트 - 완전 통합 버전
모든 설문 관련 로직이 하나의 파일에 포함됨
"""
import streamlit as st
from utils.styles import apply_survey_styles, apply_button_styles

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
    {"label": "Background Survey", "desc": "여가활동 및 취미 조사", "options": []}
]

# 4단계 다중 선택 옵션들
LEISURE_ACTIVITIES = [
    "영화보기", "클럽/나이트클럽 가기", "공연보기", "콘서트보기", "박물관가기", 
    "공원가기", "캠핑하기", "해변가기", "스포츠 관람", "주거 개선"
]

HOBBIES = [
    "아이에게 책 읽어주기", "음악 감상하기", "악기 연주하기", "혼자 노래부르거나 합창하기", 
    "춤추기", "글쓰기(편지, 단문, 시 등)", "그림 그리기", "요리하기", "애완동물 기르기"
]

SPORTS = [
    "농구", "야구/소프트볼", "축구", "미식축구", "하키", "크리켓", "골프", "배구", 
    "테니스", "배드민턴", "탁구", "수영", "자전거", "스키/스노우보드", "아이스 스케이트", 
    "조깅", "걷기", "요가", "하이킹/트레킹", "낚시", "헬스", "운동을 전혀 하지 않음"
]

TRAVEL = [
    "국내출장", "해외출장", "집에서 보내는 휴가", "국내 여행", "해외 여행"
]

# ========================
# 메인 함수
# ========================

def show_survey():
    """설문조사 화면을 표시합니다."""
    # 스타일 적용
    apply_survey_styles()
    apply_button_styles()
    
    # 현재 단계 추적
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0
    
    step = st.session_state.survey_step
    total_steps = len(SURVEY_STEPS)
    
    # 진행 바 표시
    display_progress_bar(step, total_steps)
    
    # 타이틀과 설명 표시
    display_title_and_description(step)
    
    # Part 번호 표시
    display_part_number(step, total_steps)
    
    # 설문 질문 처리
    if step == 3:  # 4단계 (다중 선택)
        handle_multiple_choice_step(step, total_steps)
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
    answer = st.radio(SURVEY_STEPS[step]['desc'], SURVEY_STEPS[step]["options"], 
                     key=f"survey_{step}", index=None)
    
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
            sub_answers["job"] = st.radio("현재 귀하는 직업이 있으십니까?", ["예", "아니요"], 
                                key=f"survey_{step}_sub", index=None)
            if sub_answers.get("job") == "예":
                sub_answers["period"] = st.radio("귀하의 근무 기간은 얼마나 되십니까?", 
                                        ["첫직장- 2개월 미만", "첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"], 
                                        key=f"survey_{step}_sub_sub", index=None)
                if sub_answers.get("period") in ["첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"]:
                    sub_answers["management"] = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?", 
                                                ["예", "아니요"], key=f"survey_{step}_sub_sub_sub", index=None)
        elif answer == "교사/교육자":
            sub_answers["institution"] = st.radio("현재 귀하는 어디에서 학생을 가르치십니까?", 
                                ["대학 이상", "초등/중/고등학교", "평생교육"], 
                                key=f"survey_{step}_sub", index=None)
            if sub_answers.get("institution") is not None:
                sub_answers["job"] = st.radio("현재 귀하는 직업이 있으십니까?", ["예", "아니요"], 
                                        key=f"survey_{step}_sub_sub", index=None)
                if sub_answers.get("job") == "예":
                    sub_answers["period"] = st.radio("귀하의 근무 기간은 얼마나 되십니까?", 
                                                ["2개월 미만 - 첫직장", 
                                                 "2개월 미만 - 교직은 처음이지만 이전에 다른 직업을 가진 적이 있음", 
                                                 "2개월 이상"], 
                                                key=f"survey_{step}_sub_sub_sub", index=None)
                    if sub_answers.get("period") == "2개월 이상":
                        sub_answers["management"] = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?", 
                                                        ["예", "아니요"], 
                                                        key=f"survey_{step}_sub_sub_sub_sub", index=None)
    
    elif step == 1:  # Step 2
        if answer == "예":
            sub_answers["current_class"] = st.radio("현재 어떤 강의를 듣고 있습니까?", 
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업"], 
                                key=f"survey_{step}_sub", index=None)
        elif answer == "아니요":
            sub_answers["recent_class"] = st.radio("최근 어떤 강의를 수강했습니까?", 
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업", 
                                 "수강 후 5년 이상 지남"], 
                                key=f"survey_{step}_sub", index=None)
    
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
    
    # 진행상황 표시
    display_multi_select_progress(total_selected)
    
    # 각 카테고리별 질문 표시
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
    leisure_count = len(st.session_state[f"leisure_selections_{step}"])
    st.markdown(f"<small style='color: #666;'>선택됨: {leisure_count}개 (최소 2개 필요)</small>", unsafe_allow_html=True)
    
    for activity in LEISURE_ACTIVITIES:
        current_checked = st.checkbox(activity, key=f"leisure_{activity}_{step}", 
                                    value=activity in st.session_state[f"leisure_selections_{step}"])
        
        if current_checked and activity not in st.session_state[f"leisure_selections_{step}"]:
            st.session_state[f"leisure_selections_{step}"].append(activity)
            st.rerun()
        elif not current_checked and activity in st.session_state[f"leisure_selections_{step}"]:
            st.session_state[f"leisure_selections_{step}"].remove(activity)
            st.rerun()
    
    st.markdown("---")

def display_hobbies(step):
    """취미/관심사 체크박스를 표시합니다."""
    st.markdown("**귀하의 취미나 관심사는 무엇입니까? (한 개 이상 선택)**")
    hobby_count = len(st.session_state[f"hobby_selections_{step}"])
    st.markdown(f"<small style='color: #666;'>선택됨: {hobby_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
    
    for hobby in HOBBIES:
        current_checked = st.checkbox(hobby, key=f"hobby_{hobby}_{step}", 
                                    value=hobby in st.session_state[f"hobby_selections_{step}"])
        
        if current_checked and hobby not in st.session_state[f"hobby_selections_{step}"]:
            st.session_state[f"hobby_selections_{step}"].append(hobby)
            st.rerun()
        elif not current_checked and hobby in st.session_state[f"hobby_selections_{step}"]:
            st.session_state[f"hobby_selections_{step}"].remove(hobby)
            st.rerun()
    
    st.markdown("---")

def display_sports(step):
    """운동 종류 체크박스를 표시합니다."""
    st.markdown("**귀하는 주로 어떤 운동을 즐기십니까? (한개 이상 선택)**")
    sport_count = len(st.session_state[f"sport_selections_{step}"])
    st.markdown(f"<small style='color: #666;'>선택됨: {sport_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
    
    for sport in SPORTS:
        current_checked = st.checkbox(sport, key=f"sport_{sport}_{step}", 
                                    value=sport in st.session_state[f"sport_selections_{step}"])
        
        if current_checked and sport not in st.session_state[f"sport_selections_{step}"]:
            st.session_state[f"sport_selections_{step}"].append(sport)
            st.rerun()
        elif not current_checked and sport in st.session_state[f"sport_selections_{step}"]:
            st.session_state[f"sport_selections_{step}"].remove(sport)
            st.rerun()
    
    st.markdown("---")

def display_travel(step):
    """휴가/출장 체크박스를 표시합니다."""
    st.markdown("**귀하는 어떤 휴가나 출장을 다녀온 경험이 있습니까? (한개 이상 선택)**")
    travel_count = len(st.session_state[f"travel_selections_{step}"])
    st.markdown(f"<small style='color: #666;'>선택됨: {travel_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
    
    for trip in TRAVEL:
        current_checked = st.checkbox(trip, key=f"travel_{trip}_{step}", 
                                    value=trip in st.session_state[f"travel_selections_{step}"])
        
        if current_checked and trip not in st.session_state[f"travel_selections_{step}"]:
            st.session_state[f"travel_selections_{step}"].append(trip)
            st.rerun()
        elif not current_checked and trip in st.session_state[f"travel_selections_{step}"]:
            st.session_state[f"travel_selections_{step}"].remove(trip)
            st.rerun()

def check_multi_select_completion(step, total_selected):
    """다중 선택 완료 여부를 확인합니다."""
    leisure_ok = len(st.session_state[f"leisure_selections_{step}"]) >= 2
    hobby_ok = len(st.session_state[f"hobby_selections_{step}"]) >= 1
    sport_ok = len(st.session_state[f"sport_selections_{step}"]) >= 1
    travel_ok = len(st.session_state[f"travel_selections_{step}"]) >= 1
    total_ok = total_selected >= 12
    
    return leisure_ok and hobby_ok and sport_ok and travel_ok and total_ok

# ========================
# 답변 저장 및 네비게이션
# ========================

def save_survey_answers(step, answer, sub_answers=None):
    """설문 답변을 간단하고 직관적으로 저장합니다."""
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {
            "work": {},           # 직업 관련
            "education": {},      # 교육 관련
            "living": "",         # 거주 형태
            "activities": {}      # 활동/취미 관련
        }
    
    if step == 0:  # 직업 관련
        st.session_state.survey_data["work"]["field"] = answer
        if sub_answers:
            st.session_state.survey_data["work"]["has_job"] = sub_answers.get("job")
            st.session_state.survey_data["work"]["experience"] = sub_answers.get("period")
            st.session_state.survey_data["work"]["is_manager"] = sub_answers.get("management")
            st.session_state.survey_data["work"]["institution"] = sub_answers.get("institution")
    
    elif step == 1:  # 교육 관련
        st.session_state.survey_data["education"]["is_student"] = answer
        if sub_answers:
            st.session_state.survey_data["education"]["current_course"] = sub_answers.get("current_class")
            st.session_state.survey_data["education"]["recent_course"] = sub_answers.get("recent_class")
    
    elif step == 2:  # 거주 형태
        st.session_state.survey_data["living"] = answer
    
    elif step == 3:  # 활동/취미
        st.session_state.survey_data["activities"] = {
            "leisure": st.session_state[f"leisure_selections_{step}"],
            "hobbies": st.session_state[f"hobby_selections_{step}"],
            "sports": st.session_state[f"sport_selections_{step}"],
            "travel": st.session_state[f"travel_selections_{step}"]
        }

def get_user_profile():
    """사용자 프로필을 간단한 문자열로 반환합니다 (AI 모델용)."""
    if "survey_data" not in st.session_state:
        return "설문조사가 완료되지 않았습니다."
    
    data = st.session_state.survey_data
    profile = []
    
    # 직업 정보
    work_info = f"직업: {data['work'].get('field', '미입력')}"
    if data['work'].get('has_job') == "예":
        if data['work'].get('experience'):
            work_info += f", 경력: {data['work'].get('experience')}"
        if data['work'].get('is_manager') == "예":
            work_info += ", 관리직"
    profile.append(work_info)
    
    # 교육 정보
    education_info = f"학생여부: {data['education'].get('is_student', '미입력')}"
    if data['education'].get('current_course'):
        education_info += f", 현재수강: {data['education'].get('current_course')}"
    elif data['education'].get('recent_course'):
        education_info += f", 최근수강: {data['education'].get('recent_course')}"
    profile.append(education_info)
    
    # 거주 정보
    profile.append(f"거주형태: {data.get('living', '미입력')}")
    
    # 활동 정보
    activities = data.get('activities', {})
    if activities:
        activity_summary = []
        if activities.get('leisure'):
            activity_summary.append(f"여가활동: {', '.join(activities['leisure'][:3])}")
        if activities.get('hobbies'):
            activity_summary.append(f"취미: {', '.join(activities['hobbies'][:3])}")
        if activities.get('sports'):
            activity_summary.append(f"운동: {', '.join(activities['sports'][:3])}")
        profile.append(" | ".join(activity_summary))
    
    return " / ".join(profile)

def display_navigation_buttons(step, total_steps, can_proceed, answer, sub_answers=None):
    """네비게이션 버튼을 표시합니다."""
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        if st.button("← Back", key=f"survey_back_{step}", use_container_width=True, disabled=(step == 0)):
            if step > 0:
                st.session_state.survey_step -= 1
                st.rerun()
    
    with col3:
        button_text = "시작하기 →" if step == total_steps - 1 else "Next →"
        if st.button(button_text, key=f"survey_next_{step}", use_container_width=True, disabled=not can_proceed):
            # 답변 저장
            save_survey_answers(step, answer, sub_answers)
            
            # 다음 단계로
            if step < total_steps - 1:
                st.session_state.survey_step += 1
                st.rerun()
            else:
                st.session_state.stage = "chat"
                st.session_state.survey_step = 0
                st.rerun()
