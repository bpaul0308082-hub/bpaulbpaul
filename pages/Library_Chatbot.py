import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="부경대 도서관 챗봇", page_icon="🏛️")
st.title("🏛️ 국립부경대학교 도서관 챗봇")
st.info("💡 부경대학교 도서관 규정집을 바탕으로 정확하게 답변해 드립니다.")

# ==========================================
# [요구사항 1] 국립부경대학교 도서관 규정 문자열 저장
# (실제 부경대학교 규정집 내용을 바탕으로 작성됨)
# ==========================================
LIBRARY_RULE = """
[국립부경대학교 도서관 규정]

제20조(휴관일) 도서관 자료실의 휴관일은 다음 각 호와 같다.
1. 일요일 및 법정공휴일
2. 개교기념일
3. 기타 관장이 필요하다고 인정하는 날 
※ 단, 일반열람실의 휴관일은 설날 연휴, 추석 연휴로 한정한다.

제22조(대출책수 및 기간) ① 단행본 대출 책 수 및 기간은 다음 각 호와 같다.
1. 전임교원, 겸임교원, 명예교수, 강사: 50책 이내 90일
2. 직원, 조교, 대학원생: 20책 이내 30일
3. 학부생: 5책 이내 10일
"""

# API 키 확인 (메인 페이지에서 입력한 키 공유)
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("👈 메인 페이지로 이동하여 OpenAI API Key를 먼저 입력해주세요.")
    st.stop()

# 도서관 챗봇 전용 대화 기록 초기화 (일반 챗봇과 대화가 섞이지 않도록 이름 변경)
if "lib_messages" not in st.session_state:
    st.session_state.lib_messages = [{"role": "assistant", "content": "안녕하세요! 국립부경대학교 도서관 챗봇입니다. 도서관 휴관일이나 대출 규정 등에 대해 물어보세요!"}]

# 이전 대화 내용 출력
for message in st.session_state.lib_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ==========================================
# [요구사항 2] 챗봇이 규정집 내용을 바탕으로 대답하게 만들기
# ==========================================
prompt = st.chat_input("질문을 입력하세요 (예: 학부생 책 대여 권수는?)")

if prompt:
    # 사용자 질문 화면 출력 및 세션 저장
    st.session_state.lib_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            client = OpenAI(api_key=st.session_state.api_key)
            
            # [핵심 로직] AI에게 규정집을 먼저 '시스템 프롬프트'로 주입합니다.
            api_messages = [
                {"role": "system", "content": f"너는 국립부경대학교 도서관 안내 챗봇이야. 반드시 다음 제공된 <도서관 규정> 문자열 내용을 바탕으로 친절하게 답변해줘.\n\n<도서관 규정>\n{LIBRARY_RULE}"}
            ]
            
            # 사용자와 나눈 이전 대화 기록 추가
            api_messages.extend([
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.lib_messages
            ])

            # API 호출
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=api_messages
            )
            
            # 답변 출력 및 저장
            assistant_response = response.choices[0].message.content
            st.write(assistant_response)
            st.session_state.lib_messages.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
