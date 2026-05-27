import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="ChatPDF", page_icon="📄")
st.title("📄 ChatPDF - 문서 기반 대화")

# 1. API 키 확인 (메인 페이지에서 입력한 키를 가져옴)
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("👈 왼쪽 사이드바에서 메인 페이지로 이동하여 API Key를 먼저 입력해주세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# 2. 세션 상태 초기화 (자원 관리용)
if "pdf_assistant" not in st.session_state:
    st.session_state.pdf_assistant = None
if "pdf_thread" not in st.session_state:
    st.session_state.pdf_thread = None
if "pdf_vector_store" not in st.session_state:
    st.session_state.pdf_vector_store = None
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

# 3. Vector Store 및 관련 리소스 삭제 함수 (Clear 버튼 기능)
def clear_pdf_resources():
    try:
        # OpenAI 서버에서 Assistant와 Vector Store 삭제
        if st.session_state.pdf_assistant:
            client.beta.assistants.delete(st.session_state.pdf_assistant.id)
        if st.session_state.pdf_vector_store:
            client.beta.vector_stores.delete(st.session_state.pdf_vector_store.id)
    except Exception as e:
        pass # 이미 삭제되었거나 오류 발생 시 무시
    
    # 세션 변수 초기화
    st.session_state.pdf_assistant = None
    st.session_state.pdf_thread = None
    st.session_state.pdf_vector_store = None
    st.session_state.pdf_messages = []
    st.rerun()

# 사이드바 설정 (Clear 버튼 배치)
with st.sidebar:
    st.header("설정")
    if st.button("데이터 초기화 (Clear)"):
        with st.spinner("서버 데이터를 삭제 중입니다..."):
            clear_pdf_resources()
    
    st.divider()
    st.write("실습 예제 PDF: [Attention Is All You Need](https://arxiv.org/pdf/1706.03762)")

# 4. 파일 업로드 (하나의 파일만 입력받도록 설정)
uploaded_file = st.file_uploader("분석할 PDF 파일을 업로드하세요", type=["pdf"])

# 파일이 업로드되었고, 아직 분석(Assistant 생성)을 안 했을 때 실행
if uploaded_file and st.session_state.pdf_assistant is None:
    with st.spinner("AI가 문서를 분석 중입니다. 잠시만 기다려주세요..."):
        # (1) 파일을 OpenAI에 업로드
        file_obj = client.files.create(file=uploaded_file, purpose="assistants")
        
        # (2) Vector Store 생성 및 파일 추가
        vector_store = client.beta.vector_stores.create(name=f"VS_{uploaded_file.name}")
        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            file_ids=[file_obj.id]
        )
        st.session_state.pdf_vector_store = vector_store
        
        # (3) File Search 도구가 활성화된 Assistant 생성
        assistant = client.beta.assistants.create(
            name="PDF Analyzer",
            instructions="너는 제공된 PDF 파일 내용을 바탕으로 사용자의 질문에 답변하는 전문가야.",
            model="gpt-3.5-turbo", # 필요시 gpt-4o 등으로 변경 가능
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )
        st.session_state.pdf_assistant = assistant
        
        # (4) Thread 생성
        st.session_state.pdf_thread = client.beta.threads.create()
        st.success("✅ 문서 분석 완료! 이제 질문해주세요.")

# 5. 채팅 인터페이스
if st.session_state.pdf_assistant:
    # 이전 메시지 출력
    for msg in st.session_state.pdf_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자 질문 입력
    if prompt := st.chat_input("문서 내용에 대해 질문하세요..."):
        # 화면에 질문 출력 및 저장
        st.session_state.pdf_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Thread에 메시지 추가
        client.beta.threads.messages.create(
            thread_id=st.session_state.pdf_thread.id,
            role="user",
            content=prompt
        )

        # AI 실행(Run) 및 결과 대기
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성 중입니다..."):
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=st.session_state.pdf_thread.id,
                    assistant_id=st.session_state.pdf_assistant.id
                )
                
                # 실행이 완료되면 답변 가져오기
                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=st.session_state.pdf_thread.id)
                    ans = messages.data[0].content[0].text.value
                    st.write(ans)
                    st.session_state.pdf_messages.append({"role": "assistant", "content": ans})
                else:
                    st.error(f"오류가 발생했습니다: {run.status}")
else:
    if not uploaded_file:
        st.info("👆 분석할 PDF 파일을 업로드하면 챗봇이 활성화됩니다.")
