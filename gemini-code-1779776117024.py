import streamlit as st
from openai import OpenAI

# 웹 페이지 기본 설정
st.set_page_config(page_title="LLM Q&A App", page_icon="💡")

st.title("💡 LLM Q&A 웹 앱")
st.write("질문을 입력하면 AI가 답변해 드립니다.")

# ---------------------------------------------------------
# [요구사항 1] API Key 입력 및 session_state 저장 
# ---------------------------------------------------------
# session_state에 api_key가 없다면 빈 문자열로 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.sidebar.header("설정")
# [요구사항 2] type="password"를 사용하여 마스킹 처리
api_key_input = st.sidebar.text_input(
    "OpenAI API Key를 입력하세요",
    type="password",
    value=st.session_state.api_key
)

# 입력값이 변경되면 페이지를 이동해도 유지되도록 session_state 업데이트
if api_key_input:
    st.session_state.api_key = api_key_input

# ---------------------------------------------------------
# [요구사항 3] @st.cache_data를 이용한 LLM 응답 캐싱
# ---------------------------------------------------------
# 동일한 prompt(질문)와 api_key가 들어오면 재실행하지 않고 캐싱된 결과 반환
@st.cache_data(show_spinner="AI가 답변을 생성 중입니다...")
def get_ai_response(prompt, api_key):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # 필요에 따라 모델명 변경 가능
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ---------------------------------------------------------
# [요구사항 4] 사용자 질문 입력 받아 LLM 응답 출력
# ---------------------------------------------------------
user_question = st.text_input("무엇이든 물어보세요!")

if st.button("답변 받기"):
    # 예외 처리: API 키나 질문이 없는 경우 실행 방지
    if not st.session_state.api_key:
        st.sidebar.error("👈 OpenAI API Key를 먼저 입력해주세요.")
    elif not user_question:
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # 캐시된 함수 호출
            answer = get_ai_response(user_question, st.session_state.api_key)
            st.success("답변 생성 완료!")
            st.info(answer)
        except Exception as e:
            st.error(f"오류가 발생했습니다 (API 키가 유효한지 확인하세요): {e}")