import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import random
import asyncio
from typing import List, Dict
from quest import make_questions
from .survey import get_survey_data, get_user_profile, KO_EN_MAPPING # 이미 수정됨urvey import get_survey_data, get_user_profile, KO_EN_MAPPING


# ========================
# Helper Functions
# ========================
def get_survey_topics_from_data() -> Dict[str, List[str]]:
    """
    Extracts all possible survey topics from the opic_data to be used for the exam.
    """
    # Assuming the opic_data dictionary from quest.py is accessible here
    # or that a similar function exists to retrieve it.
    # For this example, we'll use a placeholder structure based on the provided JSON.
    topic_structure = {
        "survey": [
            "have work experience", "living alone in a house/apartment", "living with friends in a house/apartment",
            "living with family in a house/apartment", "dormitory", "military barracks", "student",
            "museum", "watching sports", "TV", "watching cooking programs", "driving", "club", "park",
            "Improving living space", "texting friends", "watching reality shows", "spa/massage shop",
            "camping", "performance", "bar/pub", "billiard", "test preparation", "news", "shopping",
            "beach", "volunteering", "chess", "cafe", "SNS", "movies", "game", "concert", "health",
            "searching job", "reading books to children", "music", "musical instruments", "dancing",
            "writing", "drawing", "cooking", "pets", "reading", "investing", "travel magazine", "singing",
            "basketball", "baseball/softball", "soccer", "american football", "hockey", "cricket",
            "golf", "volleyball", "tennis", "badminton", "table tennis", "swimming", "bicycling",
            "skiing/snowboarding", "ice skating", "jogging", "walking", "yoga", "hiking/trekking",
            "fishing", "taekwondo", "taking fitness classes", "do not exercise",
            "domestic business trip", "overseas business trip", "staycation", "domestic travel",
            "international travel", "newspaper", "taking photos"
        ],
        "role_play": [
            "Getting Ready for Traveling", "Cancelling Appointment", "Item Purchase"
        ],
        "random_question": [
            "technology", "industry", "recycling", "weather"
        ]
    }
    return topic_structure


def get_mapped_survey_topics() -> List[str]:
    """
    Gets the user's selected survey topics from survey.py's session state
    and maps them to their English equivalents.
    """
    survey_data = get_survey_data()
    selected_topics = []

    # Get topics from work, living, and education
    if "work" in survey_data and survey_data["work"].get("field"):
        selected_topics.append(survey_data["work"]["field"])
    if "living" in survey_data:
        selected_topics.append(survey_data["living"])
    if "education" in survey_data and survey_data["education"].get("is_student"):
        selected_topics.append(survey_data["education"]["is_student"])

    # Get topics from multiple-choice activities
    activities = survey_data.get("activities", {})
    for category in ["leisure", "hobbies", "sports", "travel"]:
        selected_topics.extend(activities.get(category, []))

    return [topic for topic in selected_topics if topic]


# ========================
# Main Exam Generation Logic
# ========================
async def create_opic_exam() -> List[str]:
    """
    Generates a full 15-question OPIc-style exam based on the survey results.
    The structure is:
    1.  Self-introduction (1 question)
    2-10. Three sets of 3 questions each from the user's selected survey topics.
    11-13. One set of 3 questions from the 'role-play' category.
    14-15. Two questions from the 'random_question' category.

    Returns:
        A list of 15 questions for the exam.
    """
    exam_questions = []

    # Get user's level from survey data
    survey_data = get_survey_data()
    user_level = survey_data.get("self_assessment", "level_5")

    # 1. Self-introduction (1 question)
    exam_questions.append("Tell me about yourself.")

    # 2-10. Survey questions (3 sets of 3 questions)
    user_survey_topics = get_mapped_survey_topics()

    # Filter out empty or duplicate topics
    unique_topics = list(set(user_survey_topics))

    # Ensure we have at least 3 unique topics to pull from
    if len(unique_topics) >= 3:
        topics_for_exam = random.sample(unique_topics, 3)
    else:
        # If not enough survey topics were selected, fall back to a default set
        all_survey_topics = get_survey_topics_from_data()["survey"]
        topics_for_exam = random.sample(all_survey_topics, 3)

    for topic in topics_for_exam:
        questions = await make_questions(topic, 'survey', user_level, 3)
        exam_questions.extend(questions)

    # 11-13. Role-play questions (3 questions)
    role_play_topics = get_survey_topics_from_data()["role_play"]
    role_play_topic = random.choice(role_play_topics)
    role_play_questions = await make_questions(role_play_topic, 'role_play', user_level, 3)
    exam_questions.extend(role_play_questions)

    # 14-15. Random questions (2 questions)
    random_question_topics = get_survey_topics_from_data()["random_question"]
    random_topic = random.choice(random_question_topics)
    random_questions = await make_questions(random_topic, 'random_question', user_level, 2)
    exam_questions.extend(random_questions)

    return exam_questions


# This part would be used to run the generation logic
# and is where the streamlit app would get the questions.
async def get_final_questions_for_streamlit():
    """
    An entry point for the Streamlit app to get the final exam questions.
    """
    final_questions = await create_opic_exam()
    return final_questions

# main에 넘길거
import streamlit as st
from app.utils.voice_utils import VoiceManager, unified_answer_input

def show_exam():
    questions = st.session_state.get("exam_questions", [])
    exam_idx = st.session_state.get("exam_idx", 0)

    if exam_idx >= len(questions):
        st.success("✅ You've completed the mock exam!")
        if st.button("🔍 Get Feedback"):
            st.session_state.stage = "feedback"
            st.rerun()
        return

    # 현재 질문
    current_question = questions[exam_idx]

    st.title(f"🗣️ Question {exam_idx + 1} of {len(questions)}")

    # 질문 표시 + TTS 재생 버튼
    st.markdown(f"**{current_question}**")
    voice_manager = VoiceManager()

    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("🔊 문제 들려줘", key=f"tts_q_{exam_idx}"):
            voice_manager.play_question_audio(current_question)

    # 답변 입력 (음성 + 텍스트 통합)
    answer = unified_answer_input(exam_idx, current_question)

    # 버튼
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➡️ Next", key=f"next_btn_{exam_idx}"):
            if answer.strip():
                st.session_state.exam_answers.append(answer.strip())
                st.session_state.user_input = ""
                st.session_state.exam_idx += 1
                st.rerun()
            else:
                st.warning("⚠️ 답변을 입력하거나 녹음해 주세요.")

    with col2:
        if st.button("🧹 Clear Answer", key=f"clear_btn_{exam_idx}"):
            st.session_state[f"ans_{exam_idx}"] = ""
            st.session_state[f"text_input_{exam_idx}"] = ""
            st.session_state[f"audio_data_{exam_idx}"] = None
            st.session_state.user_input = ""
            st.rerun()
