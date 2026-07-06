"""
SIEMGuard — AI Security Event Analyzer
A Streamlit chatbot powered by Groq API for SOC/SIEM event analysis.
"""

import streamlit as st
import json
import os
from datetime import datetime

from utils.groq_client import GroqClient
from utils.prompts import get_system_prompt, get_welcome_message
from utils.chat_manager import ChatManager, parse_event_json, get_event_summary

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="SIEMGuard - AI Security Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    /* Main background & text */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: #1A1D27;
        border: 1px solid #2A2D3A;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* User message */
    .stChatMessage[data-testid="user-message"] {
        background-color: #1E2A3A;
        border-color: #00FFAA33;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #1A1D27;
        border-color: #FF6B6B33;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0A0D14;
        border-right: 1px solid #1E2A3A;
    }
    
    /* Sidebar header */
    section[data-testid="stSidebar"] h2 {
        color: #00FFAA;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 255, 170, 0.2);
    }
    
    /* Select boxes & sliders */
    .stSlider label, .stSelectbox label {
        color: #A0A0B0 !important;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #1A2A1A;
        border-color: #00FFAA44;
        color: #C0C0C0;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: #2A1A1A;
        border-color: #FF6B6B44;
    }
    
    /* Success boxes */
    .stSuccess {
        background-color: #1A2A1A;
        border-color: #00FFAA44;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1A1D27;
        color: #00FFAA;
    }
    
    /* Code blocks */
    code {
        background-color: #0D1117 !important;
        border: 1px solid #2A2D3A;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #E0E0E0;
    }
    
    /* Links */
    a {
        color: #00FFAA;
    }
    
    /* Divider */
    hr {
        border-color: #2A2D3A;
    }
    
    /* Status indicator */
    .status-ok {
        color: #00FFAA;
        font-weight: 600;
    }
    .status-warn {
        color: #FFAA00;
        font-weight: 600;
    }
    .status-critical {
        color: #FF6B6B;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ===================== SESSION STATE INIT =====================
if "groq_client" not in st.session_state:
    try:
        st.session_state.groq_client = GroqClient()
    except ValueError as e:
        st.session_state.groq_client = None
        st.session_state.groq_error = str(e)

if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if "language" not in st.session_state:
    st.session_state.language = "en"

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.3

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 2048

if "sample_events" not in st.session_state:
    st.session_state.sample_events = []
    # Try to load sample events from data file
    sample_file = "data/apex_alert_202607060956.json"
    if os.path.exists(sample_file):
        try:
            with open(sample_file, "r") as f:
                data = json.load(f)
            events = data.get("apex_alert", data if isinstance(data, list) else [])
            st.session_state.sample_events = events[:20]  # Max 20 events
        except:
            pass

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #00FFAA; font-size: 28px; margin: 0;">🛡️ SIEMGuard</h1>
        <p style="color: #606080; font-size: 12px; margin: 0;">AI Security Event Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Language Selection
    lang_label = "🌐 Language" if st.session_state.language == "en" else "🌐 Bahasa"
    st.markdown(f"**{lang_label}**")
    lang_options = ["English", "Indonesia"]
    lang_index = 0 if st.session_state.language == "en" else 1
    selected_lang = st.radio(
        label=lang_label,
        options=lang_options,
        index=lang_index,
        label_visibility="collapsed",
        key="lang_radio"
    )
    
    new_lang = "en" if selected_lang == "English" else "id"
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()
    
    st.divider()
    
    # Model Parameters
    if st.session_state.language == "en":
        st.markdown("**⚙️ Model Parameters**")
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Lower = more precise, Higher = more creative"
        )
        st.session_state.max_tokens = st.slider(
            "Max Tokens",
            min_value=256,
            max_value=4096,
            value=st.session_state.max_tokens,
            step=256,
            help="Maximum length of response"
        )
    else:
        st.markdown("**⚙️ Parameter Model**")
        st.session_state.temperature = st.slider(
            "Temperatur",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Lebih rendah = lebih presisi, Lebih tinggi = lebih kreatif"
        )
        st.session_state.max_tokens = st.slider(
            "Token Maksimal",
            min_value=256,
            max_value=4096,
            value=st.session_state.max_tokens,
            step=256,
            help="Panjang maksimal respons"
        )
    
    st.divider()
    
    # Sample Events Loader
    if st.session_state.language == "en":
        st.markdown("**📋 Sample Events**")
        st.caption("Load a sample security event to analyze")
    else:
        st.markdown("**📋 Contoh Event**")
        st.caption("Muat contoh event keamanan untuk dianalisis")
    
    if st.session_state.sample_events:
        event_options = []
        for i, event in enumerate(st.session_state.sample_events[:20]):
            sig = event.get("alert_signature", f"Event #{i+1}")[:60]
            sev = event.get("alert_severity", "?")
            event_options.append(f"[S{sev}] {sig}")
        
        selected_event_idx = st.selectbox(
            label="Select event" if st.session_state.language == "en" else "Pilih event",
            options=range(len(event_options)),
            format_func=lambda x: event_options[x],
            label_visibility="collapsed",
            key="event_selector"
        )
        
        if st.button(
            "📤 Load to Chat" if st.session_state.language == "en" else "📤 Muat ke Chat",
            use_container_width=True,
            type="primary"
        ):
            event = st.session_state.sample_events[selected_event_idx]
            event_json = json.dumps(event, indent=2)
            
            # Add event as user message
            lang = st.session_state.language
            if lang == "en":
                msg = f"Please analyze this security event:\n```json\n{event_json}\n```"
            else:
                msg = f"Tolong analisis event keamanan ini:\n```json\n{event_json}\n```"
            
            st.session_state.chat_manager.add_message("user", msg)
            st.rerun()
    else:
        st.info(
            "No sample events loaded. Add a JSON file to `data/` folder."
            if st.session_state.language == "en"
            else "Tidak ada contoh event. Tambahkan file JSON ke folder `data/`."
        )
    
    st.divider()
    
    # Export & Clear buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "💾 Export" if st.session_state.language == "en" else "💾 Ekspor",
            use_container_width=True
        ):
            chat_text = st.session_state.chat_manager.export_chat("txt")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Download" if st.session_state.language == "en" else "📥 Unduh",
                data=chat_text,
                file_name=f"siemguard_chat_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col2:
        if st.button(
            "🗑️ Clear" if st.session_state.language == "en" else "🗑️ Hapus",
            use_container_width=True,
            type="secondary"
        ):
            st.session_state.chat_manager.clear_history()
            st.rerun()
    
    st.divider()
    
    # API Status
    if st.session_state.language == "en":
        st.markdown("**🔌 API Status**")
    else:
        st.markdown("**🔌 Status API**")
    
    if st.session_state.groq_client:
        st.markdown(
            '<p class="status-ok">✅ Groq API Connected</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="status-critical">❌ {st.session_state.groq_error}</p>',
            unsafe_allow_html=True
        )

# ===================== MAIN CHAT AREA =====================

# Header
lang = st.session_state.language
if lang == "en":
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="color: #00FFAA; margin: 0;">🛡️ SIEMGuard</h1>
        <p style="color: #808090; margin: 0;">AI-Powered Security Event Analysis & SOC Assistant</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="color: #00FFAA; margin: 0;">🛡️ SIEMGuard</h1>
        <p style="color: #808090; margin: 0;">Analisis Event Keamanan & Asisten SOC Berbasis AI</p>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
chat_history = st.session_state.chat_manager.messages

if not chat_history:
    # Show welcome message
    welcome_msg = get_welcome_message(lang)
    with st.chat_message("assistant"):
        st.markdown(welcome_msg)
else:
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            st.markdown(content)

# ===================== CHAT INPUT =====================
if st.session_state.groq_client:
    # Check if user just selected a sample event (pending message)
    # Get pending message from session state if any
    
    prompt_placeholder = (
        "Paste a security event JSON or ask a question..."
        if lang == "en"
        else "Tempel JSON event keamanan atau ajukan pertanyaan..."
    )
    
    prompt = st.chat_input(prompt_placeholder)
    
    if prompt:
        # Add user message
        st.session_state.chat_manager.add_message("user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if input is a JSON event
        event_json = parse_event_json(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner(
                "🔍 Analyzing event..." if lang == "en" else "🔍 Menganalisis event..."
            ):
                # Get conversation context
                system_prompt = get_system_prompt(lang)
                
                # Add system prompt as first message
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add conversation context (last 6 exchanges)
                context = st.session_state.chat_manager.get_conversation_context(max_messages=10)
                
                # If this is an event analysis, we need to handle it specially
                if event_json:
                    # Use the analyze_event method which has its own system prompt
                    analysis = st.session_state.groq_client.analyze_event(
                        event_json, 
                        language=lang
                    )
                    response = analysis
                else:
                    # Regular conversation
                    all_messages = messages + context
                    response = st.session_state.groq_client.get_response(
                        messages=all_messages,
                        temperature=st.session_state.temperature,
                        max_tokens=st.session_state.max_tokens,
                    )
                
                st.markdown(response)
        
        # Add assistant response to history
        st.session_state.chat_manager.add_message("assistant", response)
else:
    # Show API key configuration instructions
    if lang == "en":
        st.warning("""
        ### ⚠️ Groq API Key Required
        
        To use SIEMGuard, you need to configure your Groq API key:
        
        1. Copy `.env.example` to `.env`
        2. Add your API key: `GROQ_API_KEY=your_key_here`
        3. Get a key at [console.groq.com](https://console.groq.com/keys)
        4. Restart the application
        """)
    else:
        st.warning("""
        ### ⚠️ Diperlukan Kunci API Groq
        
        Untuk menggunakan SIEMGuard, Anda perlu mengatur kunci API Groq:
        
        1. Salin `.env.example` ke `.env`
        2. Tambahkan kunci API: `GROQ_API_KEY=your_key_here`
        3. Dapatkan kunci di [console.groq.com](https://console.groq.com/keys)
        4. Mulai ulang aplikasi
        """)

# Footer
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #505060; font-size: 12px; padding: 10px 0;">
        🛡️ SIEMGuard v1.0 | Powered by Groq API & Streamlit 
        | 🔒 Security Event Analysis Tool
    </div>
    """,
    unsafe_allow_html=True
)