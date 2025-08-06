from pathlib import Path

import streamlit as st #모듈 불러오기
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline #허깅페이스 모델 로깅
import speech_recognition as sr #음성 -> 텍스트(STT) 모듈


# -------------------------
# 페이지 설정 (가장 위)
# -------------------------
st.set_page_config(page_title="🤖 초경량 챗봇", page_icon="🤖") #페이지의 탭 제목, 아이콘 설정

# 스테이지 초기화
if "stage" not in st.session_state:
    st.session_state.stage = "intro"  # intro → survey → chat
# 인트로 화면
# -------------------------
def show_intro():
    # 스타일 정의 (글자 크기 기본, Ava 이미지만 크게)
    st.markdown("""
    <style>
        .block-welcome {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .block-welcome h2.opic-header {
            color: #36f;
            font-size: 2.1rem;
            font-weight: bold;
            white-space: nowrap;
            overflow-wrap: break-word;
            text-align: center;
        }
        .ava-desc {
            text-align: center;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    # 타이틀 + 설명
    st.markdown("""
    <div class="block-welcome" style='text-align: center;'>
        <h2 class="opic-header" style="font-size:2.1rem;">
            🔊 <span style='color:#36f; font-weight:bold;'>Oral Proficiency Interview - computer</span>
            <span style='color: #36f; font-weight:bold;'>(OPIc)</span>
        </h2>
        <p style="font-size:1.25rem; font-weight:bold;">지금부터 <span style='color:#f4621f; font-weight:bold;'>English 말하기 평가</span>를 시작하겠습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # Ava 이미지 + 설명 (이미지만 크게, 가운데 정렬)
    import base64
    ava_path = Path(__file__).parent / "ava.png"
    # Ava 이미지를 가운데 정렬
    if ava_path.exists():
        with open(ava_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <img src="data:image/png;base64,{img_base64}" alt="Ava" style="width: 228px;"/>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div style='font-size: 1.35rem; font-weight: 600; color: #222; text-align: center; margin-top: 18px; margin-bottom: 40px;'>
            본 인터뷰 평가의 진행자는 Ava입니다.
            </div>
            """,
            unsafe_allow_html=True
        )
    # Streamlit 버튼 가운데 정렬
    col1, col2, col3 = st.columns([4, 1.5, 4])
    with col2:
        if st.button("next", key="start_button", help="opic 모의고사 시작", use_container_width=True):
            st.session_state.stage = "survey"
            st.rerun()
# 모델 로드
# -------------------------
@st.cache_resource #캐싱해서 웹 앱이 다시 시작될(새로고침할)때 모델을 다시 로드하지 않도록 함
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
    return pipeline("text2text-generation", model=model, tokenizer=tokenizer)

gen_pipeline = load_model()

# -------------------------
# 상태 초기화
# -------------------------
if "survey_answers" not in st.session_state: #서베이 답변을 저장하는 딕셔너리
    st.session_state.survey_answers = {}
if "chat_history" not in st.session_state: #채팅 기록을 저장하는 리스트(한 세션)
    st.session_state.chat_history = []

# -------------------------
# 서베이 화면 (진행상황 표시 + 단계별 텍스트)
# -------------------------
def show_survey():
    # 단계별 정보
    steps = [
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
        {"label": "Background Survey", "desc": "여가활동 및 취미 조사", "options": [
            # 다중 선택 형식으로 변경됨
        ]}
    ]
    total_steps = len(steps)
    # 현재 단계 추적 (세션 상태)
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0
    step = st.session_state.survey_step

    # 진행 바
    progress_percent = int((step + 1) / total_steps * 100)
    st.markdown("""
    <style>
    .thin-progress-container {
        width: 100%;
        margin-bottom: 28px;
        margin-top: 2px;
    }
    .thin-progress-bar-bg {
        width: 100%;
        height: 7px;
        background: #f3f4f6;
        border-radius: 5px;
        position: relative;
        overflow: hidden;
    }
    .thin-progress-bar-fg {
        height: 100%;
        background: linear-gradient(90deg, #f4621f 60%, #ffb37b 100%);
        border-radius: 5px;
        transition: width 0.4s cubic-bezier(.4,1.3,.6,1);
    }
    .thin-progress-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 7px;
        font-size: 1.07rem;
        font-weight: 600;
        color: #b0b3b8;
        letter-spacing: -0.5px;
    }
    .thin-progress-labels .active {
        color: #f4621f;
        font-weight: 800;
        text-shadow: 0 1px 0 #fff2e6;
    }
    
    /* 라디오 버튼 스타일링 */
    .stRadio > div > div:first-child p {
        font-size: 1.18rem !important;
        font-weight: 600 !important;
        color: rgb(34, 34, 34) !important;
        margin-bottom: 12px !important;
    }
    .stRadio > div > div:nth-child(2) > div > label {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: rgb(51, 51, 51) !important;
        line-height: 1.4 !important;
        padding: 8px 0 !important;
    }
    .stRadio > div > div:nth-child(2) > div > label:hover {
        color: #f4621f !important;
    }
    </style>
    """, unsafe_allow_html=True)
    # 진행 바와 단계 라벨
    st.markdown(
        f"""
        <div class="thin-progress-container">
          <div class="thin-progress-bar-bg">
            <div class="thin-progress-bar-fg" style="width: {progress_percent}%;"></div>
          </div>
          <div class="thin-progress-labels">
            {''.join([
                f'<span class="{ "active" if i==step else "" }">Step {i+1}</span>'
                for i, s in enumerate(steps)
            ])}
          </div>
        </div>
        """, unsafe_allow_html=True
    )

    # 타이틀 + 설명 (왼쪽 정렬)
    st.markdown(
        f"""
        <div style="text-align: left; margin-bottom: 12px;">
            <span style="font-size:2.1rem; font-weight:800; letter-spacing:-1px;">📝 {steps[step]["label"]}</span>
            <div style="font-size:1.13rem; color:#444; margin-top:6px; font-weight:500;">
                질문을 읽고 정확히 답변해 주세요.<br>
                설문에 대한 응답을 기초로 개인별 문항이 출제됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Part 번호를 주황색 배경으로 표시
    st.markdown(
        f"""
        <div style="background:rgba(244, 98, 31, 0.15); border-radius:5px; padding: 8px 12px; margin-bottom: 18px; display: inline-block; border: 1px solid rgba(244, 98, 31, 0.3);">
            <span style="font-size:1.0rem; font-weight:600; color:#f4621f;">Part {step+1} of {total_steps}</span>
        </div>
        """, unsafe_allow_html=True
    )

    # Step 4는 다중 선택, 나머지는 단일 선택
    if step == 3:  # Step 4 (index 3)인 경우
        # 다중 선택 체크박스들
        leisure_activities = [
            "영화보기", "클럽/나이트클럽 가기", "공연보기", "콘서트보기", "박물관가기", 
            "공원가기", "캠핑하기", "해변가기", "스포츠 관람", "주거 개선"
        ]
        hobbies = [
            "아이에게 책 읽어주기", "음악 감상하기", "악기 연주하기", "혼자 노래부르거나 합창하기", 
            "춤추기", "글쓰기(편지, 단문, 시 등)", "그림 그리기", "요리하기", "애완동물 기르기"
        ]
        sports = [
            "농구", "야구/소프트볼", "축구", "미식축구", "하키", "크리켓", "골프", "배구", 
            "테니스", "배드민턴", "탁구", "수영", "자전거", "스키/스노우보드", "아이스 스케이트", 
            "조깅", "걷기", "요가", "하이킹/트레킹", "낚시", "헬스", "운동을 전혀 하지 않음"
        ]
        travel = [
            "국내출장", "해외출장", "집에서 보내는 휴가", "국내 여행", "해외 여행"
        ]
        
        # 선택된 항목들을 저장할 세션 상태 초기화
        if f"leisure_selections_{step}" not in st.session_state:
            st.session_state[f"leisure_selections_{step}"] = []
        if f"hobby_selections_{step}" not in st.session_state:
            st.session_state[f"hobby_selections_{step}"] = []
        if f"sport_selections_{step}" not in st.session_state:
            st.session_state[f"sport_selections_{step}"] = []
        if f"travel_selections_{step}" not in st.session_state:
            st.session_state[f"travel_selections_{step}"] = []
        
        # 전체 선택된 항목 수 계산 (실시간)
        total_selected = (len(st.session_state[f"leisure_selections_{step}"]) + 
                         len(st.session_state[f"hobby_selections_{step}"]) + 
                         len(st.session_state[f"sport_selections_{step}"]) + 
                         len(st.session_state[f"travel_selections_{step}"]))
        
        # 진행상황 표시 (실시간 업데이트)
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
        
        # 1. 여가 활동 질문 (두 개 이상 선택)
        st.markdown("**귀하는 여가 활동으로 주로 무엇을 하십니까? (두 개 이상 선택)**")
        leisure_count = len(st.session_state[f"leisure_selections_{step}"])
        st.markdown(f"<small style='color: #666;'>선택됨: {leisure_count}개 (최소 2개 필요)</small>", unsafe_allow_html=True)
        
        for activity in leisure_activities:
            current_checked = st.checkbox(activity, key=f"leisure_{activity}_{step}", 
                                        value=activity in st.session_state[f"leisure_selections_{step}"])
            
            # 상태 변경 감지 및 업데이트
            if current_checked and activity not in st.session_state[f"leisure_selections_{step}"]:
                st.session_state[f"leisure_selections_{step}"].append(activity)
                st.rerun()
            elif not current_checked and activity in st.session_state[f"leisure_selections_{step}"]:
                st.session_state[f"leisure_selections_{step}"].remove(activity)
                st.rerun()
        
        st.markdown("---")
        
        # 2. 취미/관심사 질문 (한 개 이상 선택)
        st.markdown("**귀하의 취미나 관심사는 무엇입니까? (한 개 이상 선택)**")
        hobby_count = len(st.session_state[f"hobby_selections_{step}"])
        st.markdown(f"<small style='color: #666;'>선택됨: {hobby_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
        
        for hobby in hobbies:
            current_checked = st.checkbox(hobby, key=f"hobby_{hobby}_{step}", 
                                        value=hobby in st.session_state[f"hobby_selections_{step}"])
            
            # 상태 변경 감지 및 업데이트
            if current_checked and hobby not in st.session_state[f"hobby_selections_{step}"]:
                st.session_state[f"hobby_selections_{step}"].append(hobby)
                st.rerun()
            elif not current_checked and hobby in st.session_state[f"hobby_selections_{step}"]:
                st.session_state[f"hobby_selections_{step}"].remove(hobby)
                st.rerun()
        
        st.markdown("---")
        
        # 3. 운동 질문 (한 개 이상 선택)
        st.markdown("**귀하는 주로 어떤 운동을 즐기십니까? (한개 이상 선택)**")
        sport_count = len(st.session_state[f"sport_selections_{step}"])
        st.markdown(f"<small style='color: #666;'>선택됨: {sport_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
        
        for sport in sports:
            current_checked = st.checkbox(sport, key=f"sport_{sport}_{step}", 
                                        value=sport in st.session_state[f"sport_selections_{step}"])
            
            # 상태 변경 감지 및 업데이트
            if current_checked and sport not in st.session_state[f"sport_selections_{step}"]:
                st.session_state[f"sport_selections_{step}"].append(sport)
                st.rerun()
            elif not current_checked and sport in st.session_state[f"sport_selections_{step}"]:
                st.session_state[f"sport_selections_{step}"].remove(sport)
                st.rerun()
        
        st.markdown("---")
        
        # 4. 휴가/출장 질문 (한 개 이상 선택)
        st.markdown("**귀하는 어떤 휴가나 출장을 다녀온 경험이 있습니까? (한개 이상 선택)**")
        travel_count = len(st.session_state[f"travel_selections_{step}"])
        st.markdown(f"<small style='color: #666;'>선택됨: {travel_count}개 (최소 1개 필요)</small>", unsafe_allow_html=True)
        
        for trip in travel:
            current_checked = st.checkbox(trip, key=f"travel_{trip}_{step}", 
                                        value=trip in st.session_state[f"travel_selections_{step}"])
            
            # 상태 변경 감지 및 업데이트
            if current_checked and trip not in st.session_state[f"travel_selections_{step}"]:
                st.session_state[f"travel_selections_{step}"].append(trip)
                st.rerun()
            elif not current_checked and trip in st.session_state[f"travel_selections_{step}"]:
                st.session_state[f"travel_selections_{step}"].remove(trip)
                st.rerun()
        
        answer = "completed" if total_selected >= 12 else None  # 12개 이상 선택해야 완료
        
    else:
        # 기존 단일 선택 방식
        answer = st.radio(steps[step]['desc'], steps[step]["options"], key=f"survey_{step}", index=None)

    # Step 1에서 추가 질문 로직
    sub_answer = None
    sub_sub_answer = None
    sub_sub_sub_answer = None
    sub_sub_sub_sub_answer = None
    if step == 0:  # Step 1인 경우
        if answer in ["사업/회사", "재택근무/재택사업"]:
            sub_answer = st.radio("현재 귀하는 직업이 있으십니까?", ["예", "아니요"], key=f"survey_{step}_sub", index=None)
            if sub_answer == "예":
                sub_sub_answer = st.radio("귀하의 근무 기간은 얼마나 되십니까?", 
                                        ["첫직장- 2개월 미만", "첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"], 
                                        key=f"survey_{step}_sub_sub", index=None)
                if sub_sub_answer in ["첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"]:
                    sub_sub_sub_answer = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?", 
                                                ["예", "아니요"], key=f"survey_{step}_sub_sub_sub", index=None)
        elif answer == "교사/교육자":
            sub_answer = st.radio("현재 귀하는 어디에서 학생을 가르치십니까?", 
                                ["대학 이상", "초등/중/고등학교", "평생교육"], key=f"survey_{step}_sub", index=None)
            if sub_answer is not None:
                sub_sub_answer = st.radio("현재 귀하는 직업이 있으십니까?", ["예", "아니요"], key=f"survey_{step}_sub_sub", index=None)
                if sub_sub_answer == "예":
                    sub_sub_sub_answer = st.radio("귀하의 근무 기간은 얼마나 되십니까?", 
                                                ["2개월 미만 - 첫직장", "2개월 미만 - 교직은 처음이지만 이전에 다른 직업을 가진 적이 있음", "2개월 이상"], 
                                                key=f"survey_{step}_sub_sub_sub", index=None)
                    if sub_sub_sub_answer == "2개월 이상":
                        sub_sub_sub_sub_answer = st.radio("귀하는 부하직원을 관리하는 관리직을 맡고 있습니까?", 
                                                        ["예", "아니요"], key=f"survey_{step}_sub_sub_sub_sub", index=None)
        # "일 경험 없음"을 선택한 경우 추가 질문 없음

    elif step == 1:  # Step 2인 경우
        if answer == "예":
            sub_answer = st.radio("현재 어떤 강의를 듣고 있습니까?", 
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업"], 
                                key=f"survey_{step}_sub", index=None)
        elif answer == "아니요":
            sub_answer = st.radio("최근 어떤 강의를 수강했습니까?", 
                                ["학위 과정 수업", "전문 기술 향상을 위한 평생 학습", "어학수업", "수강 후 5년 이상 지남"], 
                                key=f"survey_{step}_sub", index=None)

    # Next 버튼 활성화 조건
    can_proceed = answer is not None  # 기본: 답변이 선택되었는지 확인
    
    if step == 3:  # Step 4인 경우 (다중 선택)
        # 각 카테고리별 최소 선택 개수 확인
        leisure_ok = len(st.session_state[f"leisure_selections_{step}"]) >= 2  # 여가활동 2개 이상
        hobby_ok = len(st.session_state[f"hobby_selections_{step}"]) >= 1     # 취미 1개 이상
        sport_ok = len(st.session_state[f"sport_selections_{step}"]) >= 1     # 운동 1개 이상
        travel_ok = len(st.session_state[f"travel_selections_{step}"]) >= 1   # 휴가/출장 1개 이상
        total_ok = total_selected >= 12  # 전체 12개 이상
        
        can_proceed = leisure_ok and hobby_ok and sport_ok and travel_ok and total_ok
        
    elif step == 0 and answer is not None:  # Step 1인 경우
        if answer in ["사업/회사", "재택근무/재택사업"]:
            if sub_answer is None:
                can_proceed = False
            elif sub_answer == "예":
                if sub_sub_answer is None:
                    can_proceed = False
                elif sub_sub_answer in ["첫직장- 2개월 이상", "첫직장 아님 - 경험 많음"]:
                    can_proceed = sub_sub_sub_answer is not None  # 4번째 질문도 답변되어야 함
                # 다른 경우는 sub_sub_answer만 있으면 진행 가능
            # sub_answer가 "아니요"인 경우는 그대로 진행 가능
        elif answer in ["교사/교육자"]:
            if sub_answer is None:  # "어디에서 학생을 가르치십니까?" 답변 필요
                can_proceed = False
            elif sub_sub_answer is None:  # "직업이 있으십니까?" 답변 필요
                can_proceed = False
            elif sub_sub_answer == "예":
                if sub_sub_sub_answer is None:  # "근무 기간" 답변 필요
                    can_proceed = False
                elif sub_sub_sub_answer == "2개월 이상":
                    can_proceed = sub_sub_sub_sub_answer is not None  # "관리직" 질문도 답변되어야 함
                # 다른 경우는 sub_sub_sub_answer만 있으면 진행 가능
            # sub_sub_answer가 "아니요"인 경우는 그대로 진행 가능
        # "일 경험 없음"은 메인 답변만 있으면 됨
    elif step == 1 and answer is not None:  # Step 2인 경우
        can_proceed = sub_answer is not None  # 강의 관련 답변만 필요

    # 버튼 영역 (Back은 왼쪽, Next는 오른쪽)
    st.markdown(
        """
        <style>
        .stButton>button {
            background: #f4621f;
            color: #fff;
            font-weight: 700;
            font-size: 1.13rem;
            border-radius: 6px;
            border: none;
            padding: 0.6em 0;
            box-shadow: 0 1px 4px 0 rgba(244,98,31,0.08);
            transition: background 0.18s;
        }
        .stButton>button:hover {
            background: #d94e0b;
            color: #fff;
        }
        .stButton>button:disabled {
            background: #cccccc;
            color: #666666;
        }
        .stButton>button:disabled:hover {
            background: #cccccc;
            color: #666666;
        }
        </style>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([2, 6, 2])
    with col1:
        if st.button("← Back", key=f"survey_back_{step}", use_container_width=True, disabled=(step == 0)):
            if step > 0:
                st.session_state.survey_step -= 1
                st.rerun()
    with col3:
        # 마지막 단계인지에 따라 버튼 텍스트 변경
        button_text = "시작하기 →" if step == total_steps - 1 else "Next →"
        if st.button(button_text, key=f"survey_next_{step}", use_container_width=True, disabled=not can_proceed):
            # 답변 저장
            if "survey_answers" not in st.session_state:
                st.session_state.survey_answers = {}
            
            # Step별 답변 저장
            if step == 0:  # Step 1
                if answer in ["사업/회사", "재택근무/재택사업"] and sub_answer:
                    st.session_state.survey_answers["직업분야"] = answer
                    st.session_state.survey_answers["직업유무"] = sub_answer
                    if sub_sub_answer:
                        st.session_state.survey_answers["근무기간"] = sub_sub_answer
                        if sub_sub_sub_answer:
                            st.session_state.survey_answers["관리직여부"] = sub_sub_sub_answer
                elif answer == "교사/교육자" and sub_answer:
                    st.session_state.survey_answers["직업분야"] = answer
                    st.session_state.survey_answers["교육기관"] = sub_answer
                    if sub_sub_answer:
                        st.session_state.survey_answers["직업유무"] = sub_sub_answer
                        if sub_sub_sub_answer:
                            st.session_state.survey_answers["근무기간"] = sub_sub_answer
                            if sub_sub_sub_sub_answer:
                                st.session_state.survey_answers["교육관리직여부"] = sub_sub_sub_sub_answer
                elif answer == "일 경험 없음":
                    st.session_state.survey_answers["직업분야"] = "무직"
                else:
                    st.session_state.survey_answers["직업분야"] = answer
            elif step == 1:  # Step 2
                if answer == "예" and sub_answer:
                    st.session_state.survey_answers["학생여부"] = answer
                    st.session_state.survey_answers["현재수강강의"] = sub_answer
                elif answer == "아니요" and sub_answer:
                    st.session_state.survey_answers["학생여부"] = answer
                    st.session_state.survey_answers["최근강의수강"] = sub_answer
                else:
                    st.session_state.survey_answers["학생여부"] = answer
            elif step == 2:  # Step 3 (거주형태)
                st.session_state.survey_answers["거주형태"] = answer
            elif step == 3:  # Step 4 (다중 선택)
                st.session_state.survey_answers["여가활동"] = st.session_state[f"leisure_selections_{step}"]
                st.session_state.survey_answers["취미관심사"] = st.session_state[f"hobby_selections_{step}"]
                st.session_state.survey_answers["운동종류"] = st.session_state[f"sport_selections_{step}"]
                st.session_state.survey_answers["휴가출장경험"] = st.session_state[f"travel_selections_{step}"]
            
            # 다음 단계로
            if step < total_steps - 1:
                st.session_state.survey_step += 1
                st.rerun()
            else:
                # 모든 서베이 완료 후 챗봇으로 이동
                st.session_state.stage = "chat"
                st.session_state.survey_step = 0
                st.rerun()

# -------------------------
# 챗봇 화면
# -------------------------
def show_chat(): #실제 챗봇 UI를 띄우고, 사용자의 입력(텍스트 or 음성)을 받음
    st.title("🤖 초경량 챗봇 (FLAN-T5)")
    st.caption("텍스트 입력 또는 음성 입력을 통해 대화하세요!")

    # 저장된 설문 답변 표시 (디버깅용)
    with st.expander("📋 설문 답변 확인하기"):
        if st.session_state.survey_answers:
            st.write("**저장된 설문 답변들:**")
            for key, value in st.session_state.survey_answers.items():
                st.write(f"- **{key}**: {value}")
        else:
            st.write("아직 저장된 설문 답변이 없습니다.")

    # 사이드바 - 음성 입력
    with st.sidebar:
        st.header("🎤 음성 입력")
        if st.button("🎙️ 마이크로 답변하기"):
            recognizer = sr.Recognizer() #speech_recognition 라이브러리로 마이크에서 음성을 녹음함.
            with sr.Microphone() as source:
                st.info("🎧 말해주세요 (최대 60초)...")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=60)
                st.info("🧠 음성 인식 중...")

            try:
                question = recognizer.recognize_google(audio, language="en-US") #구글 STT를 사용해 음성을 텍스트로 변환하고 handle_question()으로 넘김.
                st.success(f"🗣️ 인식된 질문: {question}") 
                handle_question(question)
            except sr.UnknownValueError:
                st.error("😵 음성을 인식하지 못했습니다.")
            except sr.RequestError as e:
                st.error(f"🔌 Google STT 요청 실패: {e}")

    # 텍스트 입력창
    user_input = st.chat_input("💬 메시지를 입력하세요")
    if user_input:
        handle_question(user_input)

    # 대화 렌더링
    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

# -------------------------
# 질문 처리 함수 (텍스트/음성 공통)
# -------------------------
def handle_question(question):
    st.session_state.chat_history.append({"role": "user", "content": question}) #사용자가 입력한 질문을 세션 상태에 저장
    # 프롬프트 생성
    prompt = f"Q: {question}\nA:"
    st.write(f"📨 **프롬프트:** `{prompt}`")

    try:
        response = gen_pipeline(prompt, max_new_tokens=100, do_sample=False)
        st.write(f"🧠 **모델 응답 원본:** {response}")
        answer = response[0]["generated_text"].replace(prompt, "").strip()

        if not answer:
            answer = "🤖 죄송해요, 답변을 생성하지 못했어요. 질문을 더 구체적으로 해주세요!"

        st.session_state.chat_history.append({"role": "bot", "content": answer})
    except Exception as e:
        st.session_state.chat_history.append({"role": "bot", "content": f"❌ 오류 발생: {e}"})


# -------------------------
# 앱 실행
# -------------------------
if st.session_state.stage == "intro":
    show_intro()
elif st.session_state.stage == "survey":
    show_survey()
else:
    show_chat()