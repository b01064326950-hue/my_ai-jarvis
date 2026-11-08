import streamlit as st
import ollama
from pypdf import PdfReader
from duckduckgo_search import DDGS
import urllib.parse
import os
import base64

# --- 이미지 파일을 안전하게 읽어오는 함수 ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return None

BANNER_FILE = "dh_logo.jpg"
ICON_FILE = "dh_icon.png"

icon_base64 = get_base64_image(ICON_FILE)

# --- 페이지 설정 (브라우저 탭 아이콘) ---
st.set_page_config(page_title="DH GROUP - 자비스 AI", page_icon=ICON_FILE if os.path.exists(ICON_FILE) else "🤖", layout="wide")

# --- CSS 스타일 적용 (채팅창 아이콘을 dh_icon.png로 강제 고정) ---
if icon_base64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: #0B132B;
            color: #E0FBFC;
        }}
        /* 기본 아바타 숨기기 */
        [data-testid="stChatMessageAvatarUser"] img, 
        [data-testid="stChatMessageAvatarAssistant"] img {{
            display: none !important;
        }}
        /* 사용자 아바타 */
        [data-testid="stChatMessageAvatarUser"] {{
            background-image: url("data:image/png;base64,{icon_base64}") !important;
            background-size: cover !important;
            background-position: center !important;
            border-radius: 50% !important;
        }}
        /* 자비스 아바타 */
        [data-testid="stChatMessageAvatarAssistant"] {{
            background-image: url("data:image/png;base64,{icon_base64}") !important;
            background-size: cover !important;
            background-position: center !important;
            border-radius: 50% !important;
        }}
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #0B132B;
            color: #E0FBFC;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 상단 배너 이미지 출력 (dh_logo.jpg) ---
if os.path.exists(BANNER_FILE):
    st.image(BANNER_FILE, use_column_width=True)
else:
    st.title("🚀 DH GROUP - 최강의 만능 AI 비서 자비스")

# --- 1. 왼쪽 사이드바 메뉴 ---
with st.sidebar:
    st.header("⚙️ DH 자비스 설정")
    
    mode = st.radio(
        "사용할 모드 선택",
        ["💬 일반 대화 & 문서", "🔍 인터넷 실시간 검색", "🌐 다국어 번역기", "🎨 이미지 생성기"]
    )
    
    persona = st.selectbox(
        "AI 성격 모드",
        ["친근한 친구 자비스", "일타 코딩·과학 선생님", "츤데레 까칠한 천재"]
    )
    
    persona_prompts = {
        "친근한 친구 자비스": "너는 DH GROUP의 만능 AI 비서 자비스야. 항상 반말로 친근하게 대답하고, 어려운 개념도 재미있는 비유를 들어 쉽게 설명해 줘.",
        "일타 코딩·과학 선생님": "너는 DH GROUP의 친절하고 명확한 선생님이야. 존댓말을 쓰고, 핵심을 단계별로 정리해서 이해하기 쉽게 가르쳐 줘.",
        "츤데레 까칠한 천재": "너는 말투는 조금 틱틱대고 까칠하지만, 결국 질문에는 아주 정확하고 완벽하게 답해주는 DH GROUP의 천재 조수야. 반말을 써."
    }

    st.divider()

    st.subheader("📄 문서 읽히기")
    uploaded_file = st.file_uploader("PDF 또는 TXT 파일 업로드", type=["pdf", "txt"])
    
    document_text = ""
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                document_text += page.extract_text() or ""
        else:
            document_text = uploaded_file.read().decode("utf-8")
        st.success(f"'{uploaded_file.name}' 읽기 완료!")

    st.divider()

    if st.button("🗑️ 대화 내용 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 대화 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 2. 모드별 기능 처리 ---
if mode == "💬 일반 대화 & 문서":
    if prompt := st.chat_input("자비스에게 무엇이든 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        system_instruction = persona_prompts[persona]
        if document_text:
            system_instruction += f"\n\n[참고할 문서 내용]:\n{document_text[:5000]}\n\n위 문서 내용을 바탕으로 답변해줘."

        messages_for_ai = [{"role": "system", "content": system_instruction}] + st.session_state.messages

        with st.chat_message("assistant"):
            def stream_generator():
                stream = ollama.chat(model="llava", messages=messages_for_ai, stream=True)
                for chunk in stream:
                    yield chunk["message"]["content"]
            full_answer = st.write_stream(stream_generator())
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

elif mode == "🔍 인터넷 실시간 검색":
    st.info("💡 최신 뉴스, 날씨, 실시간 정보 등 인터넷에서 검색이 필요한 내용을 입력하세요!")
    if prompt := st.chat_input("검색하고 싶은 내용을 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("🌍 인터넷에서 최신 정보를 검색하는 중..."):
            search_results = ""
            try:
                results = DDGS().text(prompt, max_results=3)
                for r in results:
                    search_results += f"- 제목: {r.get('title')}\n  내용: {r.get('body')}\n  출처링크: {r.get('href')}\n\n"
            except Exception as e:
                search_results = "검색 중 오류가 발생했습니다."

        search_prompt = f"사용자의 질문: {prompt}\n\n[실시간 검색 결과]:\n{search_results}\n\n위 검색 결과를 바탕으로 최신 정보를 반영해 친절하게 답변해줘."
        
        with st.chat_message("assistant"):
            def stream_search():
                stream = ollama.chat(model="llava", messages=[{"role": "user", "content": search_prompt}], stream=True)
                for chunk in stream:
                    yield chunk["message"]["content"]
            full_answer = st.write_stream(stream_search())
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

elif mode == "🌐 다국어 번역기":
    st.info("💡 번역하고 싶은 문장과 원하는 언어(예: 영어로, 일본어로 등)를 함께 적어주세요!")
    if prompt := st.chat_input("예: '오늘 날씨가 참 좋다'를 영어로 번역해줘"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        translate_prompt = f"당신은 전문 번역가입니다. 사용자의 다음 요청에 맞춰 정확하고 자연스럽게 번역 결과를 제공해주세요.\n\n요청: {prompt}"

        with st.chat_message("assistant"):
            def stream_trans():
                stream = ollama.chat(model="llava", messages=[{"role": "user", "content": translate_prompt}], stream=True)
                for chunk in stream:
                    yield chunk["message"]["content"]
            full_answer = st.write_stream(stream_trans())
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

elif mode == "🎨 이미지 생성기":
    st.info("💡 원하시는 이미지를 입력하시면 즉시 생성해 드립니다!")
    if prompt := st.chat_input("생성하고 싶은 이미지를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🎨 이미지를 생성하는 중입니다..."):
                encoded_prompt = urllib.parse.quote(prompt)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                
                st.image(image_url, caption=f"요청: {prompt}", use_column_width=True)
                
                answer_text = f"요청하신 '{prompt}' 이미지를 생성했습니다!"
                st.session_state.messages.append({"role": "assistant", "content": answer_text})