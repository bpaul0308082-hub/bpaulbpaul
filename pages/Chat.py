import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="Chatbot", page_icon="💬")
st.title("💬 OpenAI 챗봇")

# 1. API 키 확인 (메인 페이지에서 입력한 키를 가져옴)
# 키가 없으면 경고 메시지를 띄우고 실행을 멈춤
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("👈 왼쪽 사이드바 위쪽의 메뉴를 눌러 메인 페이지로 이동한 후, OpenAI API Key를 먼저 입력해주세요.")
    st.stop()

# 2. 대화 기록 초기화 함수 (Clear 버튼용)
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}]

# 사이드바에 Clear 버튼 추가
st.sidebar.button('대화 내용 지우기 (Clear)', on_click=clear_chat_history)

# 3. 세션 상태에 메시지 기록이 없으면 초기화 수행
if "messages" not in st.session_state:
    clear_chat_history()

# 4. 이전 대화 내용 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 5. 사용자 입력 창 및 AI 응답 처리
prompt = st.chat_input("메시지를 입력하세요...")

if prompt:
    # 사용자 메시지를 화면에 출력하고 세션에 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # OpenAI API 호출하여 답변 생성
    with st.chat_message("assistant"):
        try:
            client = OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # 또는 gpt-4o 등 사용 가능한 모델
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )
            
            # AI의 답변 추출 및 화면 출력
            assistant_response = response.choices[0].message.content
            st.write(assistant_response)
            
            # AI 응답을 세션에 저장 (다음 대화 문맥 유지를 위해)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            st.error(f"API 호출 중 오류가 발생했습니다. API 키를 확인해주세요.\n\n상세 오류: {e}")
