import streamlit as st
from openai import OpenAI
import time

# 페이지 설정
st.set_page_config(page_title="ChatPDF - 문서 분석", page_icon="📄")
st.title("📄 ChatPDF: 문서 기반 대화")

# 1. API 키 확인
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("👈 메인 페이지에서 OpenAI API Key를 먼저 입력해주세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# 2. 세션 상태 초기화 (리소스 관리용)
if "pdf_assistant" not in st.session_state:
    st.session_state.pdf_assistant = None
if "pdf_thread" not in st.session_state:
    st.session_state.pdf_thread = None
if "pdf_vector_store" not in st.session_state:
    st.session_state.pdf_vector_store = None
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

# ==========================================
# [기능] 리소스 삭제 (Clear 버튼용)
# ==========================================
def clear_pdf_resources():
    try:
        # OpenAI 서버에서 리소스 삭제
        if st.session_state.pdf_assistant:
            client.beta.assistants.delete(st.session_state.pdf_assistant.id)
        if st.session_state.pdf_vector_store:
            client.beta.vector_stores.delete(st.session_state.pdf_vector_store.id)
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    # 세션 상태 초기화
    st.session_state.pdf_assistant = None
    st.session_state.pdf_thread = None
    st.session_state.pdf_vector_store = None
    st.session_state.pdf_messages = []
    st.success("데이터가 초기화되었습니다.")
    st.rerun()

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    # [요구사항] Vector Store 삭제 버튼
    if st.button("데이터 초기화 (Clear)"):
        with st.spinner("서버 데이터를 삭제 중입니다..."):
            clear_pdf_resources()
    
    st.divider()
    st.write("실습 예제 PDF: [Attention Is All You Need](https://arxiv.org/pdf/1706.03762)")

# ==========================================
# [요구사항] Streamlit file uploader (하나만 입력)
# ==========================================
uploaded_file = st.file_uploader("분석할 PDF 파일을 업로드하세요", type=["pdf"])

# 파일이 업로드되었고, 아직 어시스턴트가 생성되지 않은 경우
if uploaded_file and st.session_state.pdf_assistant is None:
    with st.spinner("AI가 문서를 분석 중입니다. 잠시만 기다려주세요..."):
        # 1. 파일을 OpenAI에 업로드
        file_obj = client.files.create(file=uploaded_file, purpose="assistants")
        
        # 2. Vector Store 생성 (v2 방식)
        vector_store = client.beta.vector_stores.create(name=f"VS_{uploaded_file.name}")
        
        # 3. 파일 배치를 벡터 저장소에 추가하고 인덱싱 완료까지 대기(poll)
        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            file_ids=[file_obj.id]
        )
        st.session_state.pdf_vector_store = vector_store
        
        # 4. Assistant 생성 (file_search 툴 활성화 및 벡터 저장소 연결)
        assistant = client.beta.assistants.create(
            name="PDF Analyzer",
            instructions="너는 제공된 PDF 파일 내용을 바탕으로 사용자의 질문에 답변하는 전문가야. 문서에 없는 내용은 모른다고 답해줘.",
            model="gpt-4o", # 파일 검색에 최적화된 최신 모델
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )
        st.session_state.pdf_assistant = assistant
        
        # 5. 대화용 Thread 생성
        st.session_state.pdf_thread = client.beta.threads.create()
        st.success("✅ 문서 분석 완료! 이제 대화를 시작하세요.")

# ==========================================
# 채팅 UI 및 대화 처리
# ==========================================
if st.session_state.pdf_assistant:
    # 이전 대화 출력
    for msg in st.session_state.pdf_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 채팅 입력
    if prompt := st.chat_input("문서 내용에 대해 질문하세요"):
        st.session_state.pdf_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 1. 메시지를 스레드에 추가
        client.beta.threads.messages.create(
            thread_id=st.session_state.pdf_thread.id,
            role="user",
            content=prompt
        )

        # 2. AI 실행 및 답변 대기 (Runs)
        with st.chat_message("assistant"):
            with st.spinner("문서에서 답을 찾는 중..."):
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=st.session_state.pdf_thread.id,
                    assistant_id=st.session_state.pdf_assistant.id
                )
                
                if run.status == "completed":
                    # 마지막 메시지(AI 답변) 가져오기
                    messages = client.beta.threads.messages.list(thread_id=st.session_state.pdf_thread.id)
                    ans = messages.data[0].content[0].text.value
                    st.write(ans)
                    st.session_state.pdf_messages.append({"role": "assistant", "content": ans})
                else:
                    st.error(f"오류 발생: {run.status}")
else:
    if not uploaded_file:
        st.info("👆 분석할 PDF 파일을 업로드하면 챗봇이 활성화됩니다.")

### 🚀 다음 단계
1. GitHub 레포지토리의 `pages` 폴더 안에 **`ChatPDF.py`** 파일을 만듭니다.
2. 위 코드를 복사해서 붙여넣고 저장(Commit)합니다.
3. Streamlit Cloud 웹 앱을 새로고침하거나 **Reboot** 합니다.
4. 파일을 업로드하고 분석이 완료되면 질문을 던져보세요!

**주의사항:** Assistants v2의 벡터 저장소는 유지 비용이 발생할 수 있습니다. 실습이 끝나면 반드시 **Clear** 버튼을 눌러 리소스를 삭제해 주세요! 수고하셨습니다.
