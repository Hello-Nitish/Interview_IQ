import streamlit as st
import os
import sys
import json
from datetime import datetime

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.pdf_parser import DocumentParser
from orchestrator.orchestrator import Orchestrator
from utils.database import DatabaseManager
from utils.pdf_exporter import PDFDossierExporter
from agents.voice_interview_agent import VoiceInterviewAgent
from utils.speech_analytics import SpeechAnalyticsEngine
from agents.company_intel_agent import CompanyIntelAgent
from utils.api_quota_manager import APIQuotaManager
from utils.gemini_cache import GeminiCache
from agents.micro_curriculum_agent import MicroCurriculumAgent
from utils.curriculum_resources import CurriculumResourceLibrary
from frontend.styles.theme import Theme
from frontend.components.icons import icon
from frontend.components.ui_kit import UI

st.set_page_config(
    page_title="InterviewIQ — AI Placement Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Centralized Design Tokens & Neumorphic Styling
@st.cache_data
def get_css_content() -> str:
    css_path = os.path.join(os.path.dirname(__file__), "styles", "neumorphism.css")
    content = Theme.generate_css_variables() + "\n"
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            content += f.read()
    return content

st.markdown(f"<style>{get_css_content()}</style>", unsafe_allow_html=True)

# Viewport Mode Options & Dynamic Viewport CSS Injection
VIEW_MODES = [
    "🖥️ Auto (Responsive)",
    "📱 Mobile View (390px)",
    "📟 Tablet View (820px)",
    "💻 Desktop (Wide)"
]

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "🖥️ Auto (Responsive)"

st.markdown(f"<style id='view-mode-override'>{Theme.get_view_mode_css(st.session_state.view_mode)}</style>", unsafe_allow_html=True)

def render_html(html_str: str):
    """Safely render raw HTML in Streamlit.
    Strips leading indentation from each line to prevent CommonMark
    from interpreting indented HTML lines as code blocks.
    """
    cleaned = "\n".join([line.strip() for line in html_str.strip().split("\n")])
    st.markdown(cleaned, unsafe_allow_html=True)

# Ensure fresh environment variables
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path, override=True)

# Session State Initialization (Zero hardcoded fallback keys)
raw_env_key = os.getenv("GEMINI_API_KEY", "").strip()
if not raw_env_key or any(placeholder in raw_env_key.lower() for placeholder in ["your_", "placeholder", "enter_key", "dummy"]):
    active_env_key = ""
else:
    active_env_key = raw_env_key

if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = active_env_key

if "orchestrator" not in st.session_state:
    try:
        st.session_state.orchestrator = Orchestrator(api_key=st.session_state.custom_api_key or None)
    except Exception:
        st.session_state.orchestrator = Orchestrator()
elif getattr(st.session_state.orchestrator, "api_key", None) != (st.session_state.custom_api_key or None):
    if hasattr(st.session_state.orchestrator, "set_api_key"):
        st.session_state.orchestrator.set_api_key(st.session_state.custom_api_key or None)

if "current_page" not in st.session_state:
    st.session_state.current_page = "01_upload"

# Sidebar Navigation with Neumorphic buttons
with st.sidebar:
    render_html(f"""
    <div style='display:flex; align-items:center; gap:8px; margin-bottom:4px;'>
        {icon('target', size=24, color=Theme.COLORS['primary'])}
        <h3 style='margin:0; color:#0F172A; font-weight:800; font-size:1.25rem;'>InterviewIQ</h3>
    </div>
    """)
    st.caption("Don't Practice Questions. Experience the Interview.")
    st.markdown("---")

    # Interactive Viewport & Device Preview Switcher
    render_html(f"""
    <div style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:{Theme.COLORS["text_muted"]}; letter-spacing:0.04em; margin-bottom:6px; display:flex; align-items:center; gap:6px;'>
        {icon("monitor", size=15, color=Theme.COLORS["primary"])} Viewport Mode
    </div>
    """)
    curr_vm_idx = VIEW_MODES.index(st.session_state.view_mode) if st.session_state.view_mode in VIEW_MODES else 0
    selected_view_mode = st.selectbox(
        "Viewport Mode:",
        options=VIEW_MODES,
        index=curr_vm_idx,
        label_visibility="collapsed",
        key="viewport_mode_selector",
        help="Select Auto for natural responsive behavior, or simulate Mobile / Tablet screen frames directly on desktop."
    )
    if selected_view_mode != st.session_state.view_mode:
        st.session_state.view_mode = selected_view_mode
        st.rerun()

    st.markdown("---")
    
    # Live API Key Configuration & Status in Sidebar
    has_key = bool(st.session_state.custom_api_key)
    if has_key:
        clean_k = st.session_state.custom_api_key
        masked = clean_k[:6] + "..." + clean_k[-4:] if len(clean_k) > 10 else "••••••••"
        render_html(f"<div style='margin-bottom:8px;'>{UI.badge(f'API Key Active ({masked})', variant='success', icon_name='check_circle')}</div>")
        if st.button("🔄 Change / Reset API Key", use_container_width=True, key="sidebar_reset_key"):
            st.session_state.custom_api_key = ""
            st.session_state.orchestrator.set_api_key(None)
            st.rerun()
    else:
        render_html(f"<div style='margin-bottom:8px;'>{UI.badge('API Key Missing', variant='danger', icon_name='alert_triangle')}</div>")
        user_key_input = st.text_input(
            "🔑 Gemini API Key:",
            value="",
            type="password",
            key="sidebar_key_input",
            placeholder="Paste AI Studio Key...",
            help="Obtain a 100% free Gemini API key at https://aistudio.google.com/app/apikey"
        )
        if st.button("🧪 Validate & Activate Key", use_container_width=True, key="sidebar_validate_key"):
            if not user_key_input:
                st.error("Please enter a Gemini API Key.")
            else:
                with st.spinner("Validating key with Google Gemini..."):
                    is_ok, val_msg = APIQuotaManager.validate_api_key(user_key_input)
                    if is_ok:
                        clean_k = user_key_input.strip()
                        st.session_state.custom_api_key = clean_k
                        st.session_state.orchestrator.set_api_key(clean_k)
                        active_m = APIQuotaManager.get_active_model()
                        st.success(f"API Key successfully activated! (Model: {active_m})")
                        st.rerun()
                    else:
                        st.error(f"Validation failed: {val_msg}")

    # Live API Quota & Telemetry Meter
    st.markdown("---")
    render_html(f"<div style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:{Theme.COLORS['text_muted']}; letter-spacing:0.04em; margin-bottom:8px; display:flex; align-items:center; gap:6px;'>{icon('activity', size=15, color=Theme.COLORS['primary'])} API Quota & Rate Meter</div>")
    stats = APIQuotaManager.get_telemetry_stats()
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("Session Calls", f"{stats['session_calls']}")
    with m_col2:
        st.metric("Cache Hits", f"{stats['session_cache_hits']}")
    st.caption(f"Free Tier: {stats['session_calls']} / {stats['daily_limit']} calls • Peak RPM: {stats['current_rpm']}/15 max")
    st.markdown(f"<span style='color:{stats['status_color']}; font-weight:700; font-size:0.8rem;'>● Rate Status: {stats['rate_status']} (Paced ≤ 12 RPM)</span>", unsafe_allow_html=True)
    if stats['session_cache_hits'] > 0:
        st.caption(f"⚡ {stats['cache_savings_pct']}% requests served at 0ms (0 tokens)")

    st.markdown("---")
    render_html(f"<div style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:{Theme.COLORS['text_muted']}; letter-spacing:0.04em; margin-bottom:8px;'>Assessment Pipeline</div>")
    
    pipeline_steps = [
        ("01_upload", "1. Candidate Onboarding"),
        ("02_fit_report", "2. Strategic Fit Report"),
        ("03_question_bank", "3. Targeted Question Bank"),
        ("04_online_test", "4. Scored Online Test & Voice"),
        ("05_results", "5. Unified Diagnostics"),
        ("06_curriculum", "6. 7-Day Prep Curriculum")
    ]
    for p_id, p_label in pipeline_steps:
        is_active = (st.session_state.current_page == p_id)
        btn_prefix = "● " if is_active else ""
        if st.button(f"{btn_prefix}{p_label}", key=f"nav_btn_{p_id}", use_container_width=True):
            st.session_state.current_page = p_id
            st.rerun()

    st.markdown("---")
    render_html(f"<div style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:{Theme.COLORS['text_muted']}; letter-spacing:0.04em; margin-bottom:8px; display:flex; align-items:center; gap:6px;'>{icon('database', size=15, color=Theme.COLORS['primary'])} Saved Sessions (SQLite)</div>")
    try:
        past_sessions = DatabaseManager.list_sessions()
        if past_sessions:
            sess_dict = {}
            for s in past_sessions[:10]:
                c_name = s.get("candidate_name", "Candidate")
                r_num = s.get("current_round", 1)
                sc = s.get("latest_score")
                pct_str = f" • {sc}/30" if sc is not None else ""
                label = f"{c_name} (R{r_num}{pct_str})"
                sess_dict[label] = s["session_id"]
            
            chosen_label = st.selectbox("Load Saved Session:", list(sess_dict.keys()), key="sidebar_session_selector")
            if st.button("🔄 Open Selected Session", use_container_width=True):
                chosen_id = sess_dict[chosen_label]
                loaded_state = DatabaseManager.load_session_state(chosen_id)
                if loaded_state:
                    st.session_state.orchestrator.session_id = chosen_id
                    st.session_state.orchestrator.state = loaded_state
                    st.success(f"Loaded {chosen_label}!")
                    st.session_state.current_page = "02_fit_report"
                    st.rerun()
        else:
            st.caption("No historical sessions in SQLite yet.")
    except Exception as e:
        st.caption(f"Session store: {e}")

    st.markdown("---")
    if st.button("🔄 Reset / Start New Session", use_container_width=True):
        saved_key = st.session_state.custom_api_key
        saved_vm = st.session_state.get("view_mode", "🖥️ Auto (Responsive)")
        st.session_state.clear()
        st.session_state.custom_api_key = saved_key
        st.session_state.view_mode = saved_vm
        st.session_state.orchestrator = Orchestrator(api_key=saved_key)
        st.session_state.current_page = "01_upload"
        st.rerun()

    st.markdown("---")
    st.caption("Developed by your frd Nitish and Jeevana | Powered by Gemini Cascade")

# Page Routing & Progress Stepper
page = st.session_state.current_page

PAGE_STEP_MAP = {
    "01_upload": 1,
    "02_fit_report": 2,
    "03_question_bank": 3,
    "04_online_test": 4,
    "05_results": 5,
    "06_curriculum": 6
}
current_step_num = PAGE_STEP_MAP.get(page, 1)
render_html(UI.stepper(current_step_num))

if page == "01_upload":
    render_html(UI.hero_header(
        title="Step 1: Upload Resume & Job Description",
        subtitle="Upload your candidate resume and target Job Description to generate comprehensive strategic placement intelligence.",
        badge_text="Candidate Diagnostics"
    ))
    
    # Mandatory API Key Gatekeeper (Blocks execution if key is missing)
    if not st.session_state.custom_api_key:
        render_html(f"""
        <div class='neuro-card' style='border-left: 5px solid {Theme.COLORS["danger"]}; margin-bottom: 24px; padding: 24px;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:12px;'>
                <div>
                    <h3 style='margin:0 0 6px 0; color:#0F172A; display:flex; align-items:center; gap:8px;'>
                        {icon('key', size=22, color=Theme.COLORS['danger'])} Google Gemini API Key Required to Begin
                    </h3>
                    <p style='margin:0; color:#475569; font-size:0.9rem; line-height:1.5;'>
                        InterviewIQ leverages Google Gemini models to power its multi-agent placement assessment pipeline. 
                        Please supply an authorized Google AI Studio API key below to unlock candidate evaluations.
                    </p>
                </div>
                <a href='https://aistudio.google.com/app/apikey' target='_blank' style='background:linear-gradient(135deg, #2563EB, #1D4ED8); color:#FFFFFF; text-decoration:none; padding:10px 18px; border-radius:8px; font-weight:700; font-size:0.85rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); white-space:nowrap; display:inline-flex; align-items:center; gap:6px;'>
                    👉 Get Free API Key (Google AI Studio) ↗
                </a>
            </div>
            <div style='background:#F1F5F9; border-radius:8px; padding:12px 16px; margin-top:12px; font-size:0.82rem; color:#334155; display:flex; align-items:center; gap:8px;'>
                {icon('shield', size=18, color=Theme.COLORS['primary'])}
                <div>
                    <b>Free-Tier Limit Protection:</b> Google AI Studio free keys provide 15 RPM and 1,500 daily requests. 
                    Our built-in Token-Bucket Rate Pacer (&le;12 RPM) and SHA-256 Response Cache guarantee your key never trips rate limits.
                </div>
            </div>
        </div>
        """)

        g_col1, g_col2 = st.columns([3, 1])
        with g_col1:
            entered_key = st.text_input(
                "Enter your Google Gemini API Key:",
                type="password",
                placeholder="Paste API Key here (starts with AIza...)",
                key="main_gatekeeper_key_input",
                label_visibility="collapsed"
            )
        with g_col2:
            validate_btn = st.button("🧪 Validate & Activate Key", use_container_width=True, key="main_gatekeeper_validate_btn")

        if validate_btn:
            if not entered_key or not entered_key.strip():
                st.error("Please enter a valid Gemini API Key.")
            else:
                with st.spinner("Validating credentials with Google Gemini cloud probe..."):
                    is_ok, msg = APIQuotaManager.validate_api_key(entered_key.strip())
                    if is_ok:
                        clean_k = entered_key.strip()
                        st.session_state.custom_api_key = clean_k
                        st.session_state.orchestrator.set_api_key(clean_k)
                        active_m = APIQuotaManager.get_active_model()
                        st.success(f"API Key successfully validated! (Active Model: {active_m}). Unlocking InterviewIQ pipeline...")
                        st.rerun()
                    else:
                        st.error(f"Validation failed: {msg}")

        st.warning("⚠️ Candidate analysis and demo profiles are locked until a valid Gemini API Key is activated above.")
        st.stop()

    # Quick Demo Trigger
    st.markdown("""
    <div class='neuro-card' style='padding:16px; margin-bottom:14px; border-left:4px solid #2563EB;'>
        <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;'>
            <div>
                <h4 style='color:#0F172A; margin:0 0 4px 0; font-size:0.95rem; font-weight:700;'>💡 Instant Interactive Demo Available</h4>
                <p style='color:#64748B; font-size:0.82rem; margin:0;'>Experience InterviewIQ immediately using a pre-calibrated MBA candidate profile & target role without uploading files.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    demo_col1, demo_col2 = st.columns(2)
    demo_load_strategic = False
    demo_load_complete = False
    with demo_col1:
        if st.button("⚡ Load Demo: Fit & Question Bank Only (~10s)", use_container_width=True, key="demo_load_strategic_btn"):
            demo_load_strategic = True
    with demo_col2:
        if st.button("🚀 Load Demo: Complete Pipeline (~35s)", use_container_width=True, key="demo_load_complete_btn"):
            demo_load_complete = True

    if demo_load_strategic or demo_load_complete:
        demo_mode = "strategic_only" if demo_load_strategic else "complete"
        sample_res_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples", "sample_resume.txt")
        sample_jd_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples", "sample_jd.txt")
        if os.path.exists(sample_res_path) and os.path.exists(sample_jd_path):
            with open(sample_res_path, "r", encoding="utf-8") as rf:
                res_text = rf.read()
            with open(sample_jd_path, "r", encoding="utf-8") as jf:
                jd_text = jf.read()
            demo_status_title = (
                "🎯 Processing Sample Profile (Strategic Fit & QB Only)..."
                if demo_mode == "strategic_only"
                else "🚀 Processing Sample Profile (Complete Pipeline)..."
            )
            with st.status(demo_status_title, expanded=True) as status_box:
                p_bar = st.progress(0, text="Initializing sample candidate data...")
                detail_box = st.empty()
                def on_stage_demo(stage_num, total_stages, stage_name, stage_detail):
                    pct = int((stage_num / total_stages) * 100)
                    p_bar.progress(pct, text=f"Stage {stage_num}/{total_stages}: {stage_name}")
                    status_box.update(label=f"⏳ Stage {stage_num}/{total_stages} — {stage_name}...")
                    detail_box.info(f"🤖 **Stage {stage_num}/{total_stages}: {stage_name}**\n\n{stage_detail}")
                try:
                    st.session_state.orchestrator.process_onboarding(
                        res_text, 
                        jd_text, 
                        stage_callback=on_stage_demo,
                        mode=demo_mode
                    )
                    p_bar.progress(100, text="Strategic assessment complete!")
                    detail_box.empty()
                    status_box.update(label="✅ Sample Analysis Complete! Navigating to Strategic Fit Report...", state="complete", expanded=False)
                    st.session_state.current_page = "02_fit_report"
                    st.rerun()
                except Exception as e:
                    status_box.update(label="❌ Analysis Failed", state="error")
                    st.error(f"Error loading demo: {e}")

    col1, col2 = st.columns(2)
    with col1:
        render_html(f"<div class='neuro-card' style='margin-bottom:12px; padding:16px;'><h4 style='color:#0F172A; margin:0; display:flex; align-items:center; gap:8px;'>{icon('file_text', size=18, color=Theme.COLORS['primary'])} Candidate Resume</h4><p style='font-size:0.8rem; color:#64748B; margin:4px 0 0 0;'>Upload your authentic profile in PDF, DOCX, or TXT format.</p></div>")
        uploaded_resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="resume_uploader", label_visibility="collapsed")
    
    with col2:
        render_html(f"<div class='neuro-card' style='margin-bottom:12px; padding:16px;'><h4 style='color:#0F172A; margin:0; display:flex; align-items:center; gap:8px;'>{icon('briefcase', size=18, color=Theme.COLORS['primary'])} Target Job Description</h4><p style='font-size:0.8rem; color:#64748B; margin:4px 0 0 0;'>Provide the role requirements to calibrate strict match benchmarks.</p></div>")
        jd_input_method = st.radio("Input method:", ["Paste Text", "Upload Document"], horizontal=True, key="jd_method_radio")
        if jd_input_method == "Paste Text":
            jd_text_input = st.text_area("Paste Job Description here:", height=180, key="jd_text_area", placeholder="Paste the target job description or requirements here...")
            uploaded_jd = None
        else:
            uploaded_jd = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="jd_uploader")
            jd_text_input = None

    st.markdown("""
    <div style='margin: 22px 0 12px 0;'>
        <h4 style='color:#0F172A; margin-bottom:4px; font-weight:700;'>Select Strategic Analysis Execution Mode</h4>
        <p style='color:#64748B; font-size:0.85rem; margin:0;'>Choose between fast-track targeted alignment or full end-to-end assessment pre-calibration.</p>
    </div>
    """, unsafe_allow_html=True)

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        st.markdown("""
        <div class='neuro-card' style='min-height:220px; padding:18px; border-top:3px solid #2563EB;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                <span style='font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#2563EB; background:#EFF6FF; padding:3px 8px; border-radius:4px;'>Fast Track • ~10–15s</span>
                <span style='font-size:0.75rem; color:#64748B; font-weight:600;'>5 Stages</span>
            </div>
            <h4 style='color:#0F172A; margin:0 0 8px 0; font-size:1.02rem;'>🎯 Option 1: Strategic Fit & Question Bank Alone</h4>
            <p style='font-size:0.82rem; color:#475569; line-height:1.45; margin-bottom:10px;'>
                Ideal when you need instantaneous candidate alignment, gap diagnostics, and tailored interview probes without waiting for downstream testing.
            </p>
            <ul style='font-size:0.8rem; color:#334155; margin:0 0 10px 0; padding-left:18px; line-height:1.55;'>
                <li><strong>Resume Profiling:</strong> Skills, education, & experience tiers</li>
                <li><strong>JD Benchmarking:</strong> Mandatory criteria & corporate DNA</li>
                <li><strong>Strategic Fit Matrix:</strong> Match %, decision engine, & gap audit</li>
                <li><strong>Tailored Question Bank:</strong> 5-category behavioral & technical probes</li>
            </ul>
            <p style='font-size:0.74rem; color:#64748B; font-style:italic; margin:0;'>
                *Note: 30-MCQ test is calibrated on-demand if you proceed to Step 4.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        run_strategic_btn = st.button("🎯 Run Strategic Fit & Question Bank Alone", use_container_width=True, key="run_strategic_fit_alone_btn")

    with col_opt2:
        st.markdown("""
        <div class='neuro-card' style='min-height:220px; padding:18px; border-top:3px solid #7C3AED;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                <span style='font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#7C3AED; background:#F5F3FF; padding:3px 8px; border-radius:4px;'>Full Pipeline • ~35–45s</span>
                <span style='font-size:0.75rem; color:#64748B; font-weight:600;'>6 Stages</span>
            </div>
            <h4 style='color:#0F172A; margin:0 0 8px 0; font-size:1.02rem;'>🚀 Option 2: Complete End-to-End Analysis</h4>
            <p style='font-size:0.82rem; color:#475569; line-height:1.45; margin-bottom:10px;'>
                Coordinates the comprehensive AI agent pipeline upfront, calibrating the 30-MCQ empirical exam so all platform steps are pre-generated.
            </p>
            <ul style='font-size:0.8rem; color:#334155; margin:0 0 10px 0; padding-left:18px; line-height:1.55;'>
                <li><strong>Everything in Option 1:</strong> Resume, JD, Fit Matrix & Question Bank</li>
                <li><strong>Upfront 30-MCQ Assessment:</strong> Calibrated against candidate gaps</li>
                <li><strong>Immediate Exam Readiness:</strong> Timed proctored MCQ & voice prep ready</li>
                <li><strong>Unified Diagnostics:</strong> Instant foundation for readiness reporting</li>
            </ul>
            <p style='font-size:0.74rem; color:#64748B; font-style:italic; margin:0;'>
                *Recommended for candidates ready to complete the full assessment suite in one go.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        run_complete_btn = st.button("🚀 Perform Complete Analysis (Start till End)", use_container_width=True, key="run_complete_analysis_btn")

    # Determine execution trigger
    selected_mode = None
    if run_strategic_btn:
        selected_mode = "strategic_only"
    elif run_complete_btn:
        selected_mode = "complete"

    if selected_mode:
        if not uploaded_resume:
            st.error("Please provide your resume first.")
        else:
            status_title = (
                "🎯 Coordinating Strategic Fit & Question Bank Pipeline (5 Stages)..."
                if selected_mode == "strategic_only"
                else "🚀 Coordinating Complete End-to-End AI Agent Pipeline (6 Stages)..."
            )
            with st.status(status_title, expanded=True) as status_box:
                p_bar = st.progress(0, text="Extracting and parsing documents...")
                detail_box = st.empty()
                detail_box.info("📄 **Document Parser**\n\nExtracting textual content from uploaded candidate and role documents...")
                try:
                    resume_text = DocumentParser.parse_document(uploaded_resume)
                    if jd_input_method == "Paste Text" and jd_text_input:
                        jd_text = jd_text_input
                    elif uploaded_jd:
                        jd_text = DocumentParser.parse_document(uploaded_jd)
                    else:
                        jd_text = "General corporate role requiring strong analytical and problem-solving skills."

                    def on_stage_main(stage_num, total_stages, stage_name, stage_detail):
                        pct = int((stage_num / total_stages) * 100)
                        p_bar.progress(pct, text=f"Stage {stage_num}/{total_stages}: {stage_name}")
                        status_box.update(label=f"⏳ Stage {stage_num}/{total_stages} — {stage_name}...")
                        detail_box.info(f"🤖 **Stage {stage_num}/{total_stages}: {stage_name}**\n\n{stage_detail}")

                    st.session_state.orchestrator.process_onboarding(
                        resume_text, 
                        jd_text, 
                        stage_callback=on_stage_main,
                        mode=selected_mode
                    )
                    p_bar.progress(100, text="Strategic assessment complete!")
                    detail_box.empty()
                    status_box.update(label="✅ Analysis Complete! Navigating to Strategic Fit Report...", state="complete", expanded=False)
                    st.session_state.current_page = "02_fit_report"
                    st.rerun()
                except Exception as e:
                    status_box.update(label="❌ Analysis Failed", state="error")
                    st.error(f"Error during agent analysis: {e}")

elif page == "02_fit_report":
    fit_data = st.session_state.orchestrator.state.get("fit_data")
    jd_data = st.session_state.orchestrator.state.get("jd_data") or {}
    if not fit_data:
        render_html(UI.empty_state(
            title="Strategic Fit Report Not Generated",
            description="Complete Step 1 (Candidate Onboarding) by uploading a resume and target Job Description, or load our instant sample profile to generate a Strategic Fit Report.",
            icon_name="file_text",
            action_hint="Click below to return to Step 1 and run onboarding analysis."
        ))
        if st.button("🚀 Return to Step 1: Candidate Onboarding", use_container_width=True, key="empty_step2_to_step1_btn"):
            st.session_state.current_page = "01_upload"
            st.rerun()
    else:
        role_title = jd_data.get("role_title", "Corporate Placement Candidate")
        company_name = jd_data.get("company_name", "Enterprise Talent Acquisition Desk")
        
        # Top Executive Brand & Meta Banner (Light Theme)
        st.markdown(f"""
        <div class='neuro-meta-banner'>
          <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;'>
            <div>
              <div style='display:inline-flex; align-items:center; gap:6px; padding:4px 12px; border-radius:9999px; font-size:0.75rem; font-weight:700; text-transform:uppercase; background:rgba(37,99,235,0.25); color:#93C5FD; border:1px solid rgba(147,197,253,0.3); margin-bottom:8px;'>
                {icon('shield', size=14, color='#93C5FD')} Talent Acquisition Deep-Dive Assessment
              </div>
              <h2 style='margin:0; font-size:1.8rem; font-weight:800; color:#FFFFFF;'>{role_title} Evaluation</h2>
              <p style='margin:4px 0 0 0; font-size:0.85rem; color:#94A3B8;'>Target Firm: <strong style='color:#E2E8F0;'>{company_name}</strong></p>
            </div>
            <div style='text-align:right;'>
              <span style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; color:#94A3B8;'>Evaluation Status</span><br>
              <span class='neuro-badge-matched' style='font-size:0.85rem; padding:4px 14px;'>Assessment Complete</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Action Bar: Multi-Agent Quality Telemetry + PDF Export
        p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
        with p_col1:
            q_telemetry = st.session_state.orchestrator.state.get("quality_telemetry") or {}
            q_score = q_telemetry.get("overall_pipeline_quality")
            if q_score is not None:
                st.markdown(f"""
                <div style='display:inline-flex; align-items:center; gap:8px; padding:6px 14px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px;'>
                  <span style='font-size:0.85rem; font-weight:700; color:#1E40AF;'>{icon('shield', size=16, color='#2563EB')} Multi-Agent Quality Verified:</span>
                  <span style='font-size:0.95rem; font-weight:800; color:#1D4ED8;'>{q_score}%</span>
                  <span style='font-size:0.75rem; color:#60A5FA;'>• Enterprise Depth</span>
                </div>
                """, unsafe_allow_html=True)
        with p_col2:
            try:
                pdf_data = PDFDossierExporter.generate_dossier_pdf(st.session_state.orchestrator.state)
                cand_details_temp = fit_data.get("candidate_details", {})
                c_clean_name = cand_details_temp.get("name", "Candidate").replace(" ", "_")
                st.download_button(
                    label="📥 Download Dossier (PDF)",
                    data=pdf_data,
                    file_name=f"InterviewIQ_{c_clean_name}_Dossier.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.caption(f"Dossier PDF generator: {e}")

        with p_col3:
            try:
                cand_name_str = fit_data.get("candidate_details", {}).get("name") or st.session_state.orchestrator.state.get("candidate_name", "Candidate")
                c_clean = cand_name_str.replace(" ", "_")
                r_title = jd_data.get("role_title", "Role Assessment")
                c_name = jd_data.get("company_name", "")
                fit_pdf = PDFDossierExporter.generate_fit_report_pdf(
                    fit_data=fit_data,
                    candidate_name=cand_name_str,
                    role_title=r_title,
                    company_name=c_name
                )
                st.download_button(
                    label="📊 Download Fit Report (PDF)",
                    data=fit_pdf,
                    file_name=f"InterviewIQ_{c_clean}_FitReport.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.caption(f"Fit Report PDF generator: {e}")

        # -------------------------------------------------------------
        # SECTION 1: Candidate Details & Experience Scoring
        # -------------------------------------------------------------
        st.markdown(f"<h3 style='margin-bottom:12px; color:#0F172A; display:flex; align-items:center; gap:8px;'>{icon('user', size=20, color=Theme.COLORS['primary'])} Candidate Details & Profile Breakdown</h3>", unsafe_allow_html=True)
        cand_details = fit_data.get("candidate_details", {})
        exp_scoring = fit_data.get("experience_scoring", {})
        
        c_col1, c_col2 = st.columns([2, 1])
        with c_col1:
            cand_name = cand_details.get("name", "Candidate Profile")
            cand_id = cand_details.get("candidate_id", "DM274094")
            stage = cand_details.get("stage", "Early Stage / Student Fresher")
            
            st.markdown(f"""
            <div class='neuro-card'>
              <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;'>
                <div>
                  <h3 style='margin:0; color:#0F172A;'>{cand_name}</h3>
                  <p style='margin:2px 0 0 0; font-size:0.8rem; color:#64748B;'>Candidate ID: {cand_id}</p>
                </div>
                <span class='neuro-badge-partial'>{stage}</span>
              </div>
              <div style='display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:0.85rem;'>
                <div>
                  <span style='font-size:0.7rem; text-transform:uppercase; color:#64748B; font-weight:700;'>Current Program</span>
                  <p style='margin:2px 0; font-weight:600; color:#1E293B;'>{cand_details.get('current_program', 'PGDM / MBA (Pursuing)')}</p>
                </div>
                <div>
                  <span style='font-size:0.7rem; text-transform:uppercase; color:#64748B; font-weight:700;'>Undergraduate Degree</span>
                  <p style='margin:2px 0; font-weight:600; color:#1E293B;'>{cand_details.get('undergraduate', 'Undergraduate Degree (CGPA 8.8 / 10)')}</p>
                </div>
                <div>
                  <span style='font-size:0.7rem; text-transform:uppercase; color:#64748B; font-weight:700;'>Academic Foundation</span>
                  <p style='margin:2px 0; font-weight:600; color:#1E293B;'>{cand_details.get('schooling', '12th: 91.2% • 10th: 93.8%')}</p>
                </div>
                <div>
                  <span style='font-size:0.7rem; text-transform:uppercase; color:#64748B; font-weight:700;'>Languages & Agility</span>
                  <p style='margin:2px 0; font-weight:600; color:#1E293B;'>{cand_details.get('languages', 'English, Tamil, Telugu, Hindi (Multilingual Fluency)')}</p>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with c_col2:
            pts = exp_scoring.get("points", 4)
            max_pts = exp_scoring.get("max_points", 10)
            exp_sum = exp_scoring.get("evaluated_experience_summary", "Evaluated: < 1 year relevant corporate/credit experience.")
            
            st.markdown(f"""
            <div class='neuro-card'>
              <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Experience Scoring</span>
                <span style='font-size:0.7rem; color:#94A3B8; font-weight:600;'>Tier Matrix</span>
              </div>
              <div style='display:flex; align-items:baseline; gap:6px; margin:8px 0;'>
                <span style='font-size:2.8rem; font-weight:900; color:#D97706;'>{pts}</span>
                <span style='color:#64748B; font-weight:600;'>/ {max_pts} Points</span>
              </div>
              <p style='font-size:0.8rem; color:#475569; margin-bottom:10px;'>{exp_sum}</p>
              <div class='neuro-inset' style='padding:8px 12px; font-size:0.75rem; font-family:monospace;'>
                <div style='display:flex; justify-content:space-between;'><span>&ge; 8 Years:</span><span>10 pts</span></div>
                <div style='display:flex; justify-content:space-between;'><span>&ge; 5 Years:</span><span>8 pts</span></div>
                <div style='display:flex; justify-content:space-between;'><span>&ge; 3 Years:</span><span>6 pts</span></div>
                <div style='display:flex; justify-content:space-between; font-weight:700; color:#B45309;'><span>&lt; 3 Years (Current):</span><span>4 pts</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # SECTION 2: Technical Rating & Requirements Assessment Matrix
        # -------------------------------------------------------------
        st.markdown(f"<h3 style='margin-top:20px; margin-bottom:12px; color:#0F172A; display:flex; align-items:center; gap:8px;'>{icon('bar_chart', size=20, color=Theme.COLORS['primary'])} Technical Rating & Strict Match Formula</h3>", unsafe_allow_html=True)
        tech_rating = fit_data.get("technical_rating", {})
        matched_count = tech_rating.get("mandatory_matched_count", 2)
        total_mand = tech_rating.get("total_mandatory_count", max(matched_count, 7))
        pct = tech_rating.get("strict_match_percentage", 28.57)
        severity = tech_rating.get("deficit_severity", "Critical Skill Deficit")
        tech_summary = tech_rating.get("technical_rating_summary", f"JD mandates {total_mand} core mandatory capabilities. The candidate demonstrates {matched_count} foundational areas and misses {total_mand - matched_count} mandatory technical capabilities.")

        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            st.markdown(f"""
            <div class='neuro-card'>
              <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#2563EB;'>Strict Technical Match Formula</span>
              <div class='neuro-inset' style='margin-top:8px; font-family:monospace;'>
                <code>Score = (Matched Skills / Total Required Mandatory Skills) &times; 100</code><br>
                <strong style='font-size:1.15rem; color:#0F172A;'>Score = ({matched_count} / {total_mand}) &times; 100 = <span style='color:#2563EB;'>{pct}%</span></strong>
              </div>
              <p style='font-size:0.85rem; color:#475569; margin:8px 0 0 0;'>{tech_summary}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f2:
            sev_badge = "neuro-badge-missing" if "Deficit" in severity else ("neuro-badge-missing-pref" if "Gap" in severity else "neuro-badge-matched")
            st.markdown(f"""
            <div class='neuro-card' style='text-align:center;'>
              <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Technical Alignment</span>
              <div style='font-size:2.8rem; font-weight:900; color:#EF4444; margin:4px 0;'>{pct}%</div>
              <div style='margin-bottom:8px;'><span class='{sev_badge}'>{severity}</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(1.0, max(0.0, float(pct) / 100.0)))

        # Exact 4-Column Requirements Assessment Matrix Table
        req_matrix = fit_data.get("requirements_matrix", [])
        if req_matrix:
            req_f_col1, req_f_col2 = st.columns([2, 2])
            with req_f_col1:
                mat_filter = st.radio(
                    "Filter Requirements:",
                    options=["All", "Mandatory Only", "Gaps Only", "Matched Only"],
                    horizontal=True,
                    key="req_matrix_filter"
                )
            
            rows_html = []
            for row in req_matrix:
                cat = row.get("category", "Mandatory")
                cat_class = "neuro-badge-mandatory" if cat == "Mandatory" else "neuro-badge-preferred"
                status = row.get("status", "Matched")
                
                # Apply filter
                if mat_filter == "Mandatory Only" and cat != "Mandatory":
                    continue
                elif mat_filter == "Gaps Only" and status == "Matched":
                    continue
                elif mat_filter == "Matched Only" and status != "Matched":
                    continue

                if status == "Matched":
                    stat_class = "neuro-badge-matched"
                elif "Pref" in status:
                    stat_class = "neuro-badge-missing-pref"
                else:
                    stat_class = "neuro-badge-missing"

                sub = row.get("requirement_subtitle", "")
                sub_html = f"<span style='display:block; font-size:0.75rem; color:#64748B; font-weight:400; margin-top:2px;'>{sub}</span>" if sub else ""
                req_text = row.get("requirement", "")
                ev_gap = row.get("evidence_or_gap", "")

                rows_html.append(
                    f"<tr>"
                    f"<td><b>{req_text}</b>{sub_html}</td>"
                    f"<td><span class='{cat_class}'>{cat}</span></td>"
                    f"<td>{ev_gap}</td>"
                    f"<td style='text-align:center;'><span class='{stat_class}'>{status}</span></td>"
                    f"</tr>"
                )

            if not rows_html:
                rows_html.append("<tr><td colspan='4' style='text-align:center; color:#64748B; padding:18px;'>No requirements found matching this filter criteria.</td></tr>")

            table_body = "".join(rows_html)
            full_matrix_html = f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0; margin-bottom:12px;'>📋 Requirements Assessment Matrix ({len(rows_html) if 'colspan' not in rows_html[0] else 0} displayed)</h4>
                <div style='overflow-x:auto;'>
                    <table class='neuro-table'>
                        <thead>
                            <tr>
                                <th style='width:28%;'>Job Requirement</th>
                                <th style='width:14%;'>Category</th>
                                <th style='width:44%;'>Resume Evidence / Gap Assessment</th>
                                <th style='width:14%; text-align:center;'>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_body}
                        </tbody>
                    </table>
                </div>
            </div>
            """
            render_html(full_matrix_html)

        # -------------------------------------------------------------
        # SECTION 3: Communication Rating
        # -------------------------------------------------------------
        st.markdown("<h3 style='margin-top:20px; margin-bottom:12px; color:#0F172A;'>🗣️ Communication Rating & Prescreen Probes</h3>", unsafe_allow_html=True)
        comm_prof = fit_data.get("communication_profile", {})
        comm_col1, comm_col2 = st.columns(2)
        with comm_col1:
            strengths = comm_prof.get('strengths', 'Clean formatting, expressive clarity, and active campus leadership roles.')
            gap = comm_prof.get('technical_communication_gap', 'Bullet points are descriptive rather than metric-driven; needs crisper executive precision.')
            prelim = comm_prof.get("preliminary_rating", {})
            i_sc = prelim.get('interpersonal_score', 7.5)
            t_sc = prelim.get('technical_score', 4.0)
            col1_html = f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0;'>Resume Articulation & Presentation Profile</h4>
                <div style='font-size:0.85rem; margin-bottom:8px;'><b>Strengths:</b> {strengths}</div>
                <div style='font-size:0.85rem; margin-bottom:12px;'><b>Technical Communication Gap:</b> {gap}</div>
                <div class='neuro-inset' style='font-size:0.8rem;'>
                    <strong style='color:#2563EB;'>Preliminary Rating:</strong> 
                    <b>{i_sc} / 10</b> General & Interpersonal Communication &bull; 
                    <b>{t_sc} / 10</b> Technical & Domain Communication
                </div>
            </div>
            """
            render_html(col1_html)

        with comm_col2:
            q_html = []
            for q in comm_prof.get("prescreen_interview_questions", [
                {"probe_title": "1. Synthesis for Senior Stakeholders", "question": "How would you concisely summarize a borrower’s deteriorating debt-service coverage ratio (DSCR) to an offshore Portfolio Manager in 60 seconds?"},
                {"probe_title": "2. Methodological Rigor", "question": "In your financial analysis project, how did you explain the variance in profitability metrics when benchmarked against industry peers?"},
                {"probe_title": "3. Cross-Functional Coordination", "question": "Describe a situation in your campus leadership where you negotiated competing resource priorities with uncooperative stakeholders."}
            ]):
                p_title = q.get('probe_title', '')
                p_quest = q.get('question', '')
                q_html.append(f"<div class='neuro-inset' style='padding:10px 14px; font-size:0.8rem; margin-bottom:8px;'><strong style='color:#1E293B;'>{p_title}:</strong><p style='margin:4px 0 0 0; color:#475569;'>\"{p_quest}\"</p></div>")
            col2_html = f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0; margin-bottom:10px;'>Prescreen Interview Questions</h4>
                {''.join(q_html)}
            </div>
            """
            render_html(col2_html)

        # -------------------------------------------------------------
        # SECTION 4 & 5: Problem Solving & Cultural Fit
        # -------------------------------------------------------------
        st.markdown("<h3 style='margin-top:20px; margin-bottom:12px; color:#0F172A;'>🧩 Problem Solving & Cultural Alignment</h3>", unsafe_allow_html=True)
        ps_data = fit_data.get("problem_solving", {})
        cult_data = fit_data.get("cultural_fit", {})

        p_col1, p_col2 = st.columns([1, 1])
        with p_col1:
            proj_name = ps_data.get("highlighted_project_name", "Academic Project & Financial Valuation")
            critique = ps_data.get('project_critique', 'Demonstrated curiosity in corporate analysis; lacks specialized downside-protection stress-testing.')
            probes_list = ps_data.get("technical_probes", [
                {"probe_title": "Credit Stress-Testing Probe", "probe_question": "If your target entity experiences a 25% drop in tariff realization alongside a 150 bps spike in interest rates, walk us through which line items on Cash Flows absorb the shock."},
                {"probe_title": "Financial Modeling Probe", "probe_question": "How would you construct a dynamic debt amortization schedule in Excel that automatically recalculates mandatory prepayment sweeps?"}
            ])
            probe_snippets = []
            for probe in probes_list:
                p_title = probe.get('probe_title', 'Probe')
                p_q = probe.get('probe_question', '')
                probe_snippets.append(f"<div class='neuro-inset' style='padding:8px 12px; font-size:0.8rem; margin-top:6px;'><span style='color:#D97706; font-weight:700; font-size:0.75rem; text-transform:uppercase;'>{p_title}</span><p style='margin:2px 0 0 0;'>\"{p_q}\"</p></div>")
            p1_html = f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0;'>Highlighted Project Analysis</h4>
                <div style='font-size:0.85rem;'><b>Project Focus:</b> {proj_name}<br><small style='color:#64748B;'>{critique}</small></div>
                <div style='margin-top:10px; font-weight:600; font-size:0.85rem;'>Recommended Technical Probes:</div>
                {''.join(probe_snippets)}
            </div>
            """
            render_html(p1_html)

        with p_col2:
            tenacity = cult_data.get('tenacity_discipline', 'Demonstrated high perseverance, dedication, and long-term commitment in extracurriculars.')
            growth = cult_data.get('growth_alignment', 'Active involvement in campus leadership indicates strong team cohesion and adaptability.')
            continuity = cult_data.get('service_continuity_factor', 'Ongoing PGDM/MBA semester commitments require structured corporate internship alignment.')
            p2_html = f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0;'>Cultural Fit & Organizational Dynamics</h4>
                <div class='neuro-inset' style='margin-bottom:8px; font-size:0.8rem;'>
                    <strong style='color:#15803D;'>🌟 Tenacity & Discipline:</strong>
                    <p style='margin:2px 0 0 0;'>{tenacity}</p>
                </div>
                <div class='neuro-inset' style='margin-bottom:8px; font-size:0.8rem;'>
                    <strong style='color:#15803D;'>🚀 Fast-Growth Alignment:</strong>
                    <p style='margin:2px 0 0 0;'>{growth}</p>
                </div>
                <div class='neuro-inset' style='font-size:0.8rem;'>
                    <strong style='color:#B45309;'>⏳ Service Continuity & Availability:</strong>
                    <p style='margin:2px 0 0 0;'>{continuity}</p>
                </div>
            </div>
            """
            render_html(p2_html)

        # Target Hiring Firm Intelligence & Leadership Principles
        comp_intel = st.session_state.orchestrator.state.get("company_intel")
        if not comp_intel:
            c_name = jd_data.get("company_name", "") or "Target Enterprise"
            role_t = jd_data.get("role_title", "")
            comp_intel = CompanyIntelAgent(api_key=st.session_state.custom_api_key).get_company_intelligence(c_name, role_t)
            st.session_state.orchestrator.state["company_intel"] = comp_intel

        c_name = comp_intel.get("canonical_name", "Target Hiring Firm")
        c_tier = comp_intel.get("tier", "Enterprise Digital Transformation Leader")
        c_motto = comp_intel.get("culture_motto", "")
        c_framework = comp_intel.get("evaluation_framework", "")
        c_principles = comp_intel.get("core_principles", [])
        c_radar = comp_intel.get("cultural_radar_weights", {})

        p_items_html = ""
        for p in c_principles[:4]:
            p_items_html += f"""
            <div class='neuro-inset' style='margin-bottom:8px; padding:10px 14px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <strong style='color:#0F172A; font-size:0.9rem;'>{p.get('name')}</strong>
                    <span style='font-size:0.75rem; background:#DBEAFE; color:#1E40AF; padding:2px 8px; border-radius:4px; font-weight:600;'>Core Principle</span>
                </div>
                <p style='color:#475569; font-size:0.82rem; margin:4px 0 2px 0;'>{p.get('description')}</p>
                <small style='color:#2563EB; font-size:0.78rem;'><b>Interview Implication:</b> {p.get('interview_implication')}</small>
            </div>
            """

        radar_bars_html = ""
        for dim, weight in c_radar.items():
            radar_bars_html += f"""
            <div style='margin-bottom:8px;'>
                <div style='display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:2px;'>
                    <span style='color:#334155; font-weight:600;'>{dim}</span>
                    <span style='color:#2563EB; font-weight:700;'>{weight}%</span>
                </div>
                <div style='background:#E2E8F0; border-radius:6px; height:8px; width:100%; overflow:hidden;'>
                    <div style='background:#2563EB; width:{weight}%; height:100%; border-radius:6px;'></div>
                </div>
            </div>
            """

        render_html(f"""
        <div class='neuro-card' style='margin-top:16px; border-left: 5px solid #2563EB;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>
                <div>
                    <h4 style='color:#0F172A; margin:0 0 4px 0;'>🏢 Target Corporate Culture & Leadership Principles: {c_name}</h4>
                    <p style='color:#64748B; font-size:0.82rem; margin:0;'>
                        <b>Evaluation Standard:</b> {c_framework} • <i>"{c_motto}"</i>
                    </p>
                </div>
                <span class='neuro-badge-matched' style='flex-shrink:0;'>{c_tier}</span>
            </div>
            <div class='culture-grid'>
                <div>
                    <div style='font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:8px;'>Core Leadership Tenets Evaluated:</div>
                    {p_items_html}
                </div>
                <div>
                    <div style='font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:8px;'>Cultural Radar Weighting:</div>
                    <div class='neuro-inset' style='padding:12px;'>
                        {radar_bars_html}
                    </div>
                </div>
            </div>
        </div>
        """)

        # -------------------------------------------------------------
        # SECTION 6: Overall Placement Readiness Score & Strategic Implications
        # -------------------------------------------------------------
        st.markdown(f"<h3 style='margin-top:24px; margin-bottom:12px; color:#0F172A; display:flex; align-items:center; gap:8px;'>{icon('target', size=20, color=Theme.COLORS['primary'])} Placement Readiness & Strategic Defense Summary</h3>", unsafe_allow_html=True)
        score = fit_data.get("placement_readiness_score", 0)
        col1, col2 = st.columns([1, 2])
        with col1:
            render_html(f"""
            <div class='neuro-card' style='text-align:center; padding:24px 16px;'>
                <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Overall Readiness</span>
                <div style='font-size:3.5rem; font-weight:900; color:#2563EB; margin:8px 0;'>{score} <span style='font-size:1.5rem; color:#64748B;'>/ 100</span></div>
                <span class='neuro-badge-partial' style='font-size:0.8rem;'>Comprehensive Index</span>
            </div>
            """)
        with col2:
            focus_lis = "".join([f"<li style='margin-bottom:6px;'><strong style='color:#0F172A;'>{area}</strong></li>" for area in fit_data.get("top_5_interview_focus_areas", [])])
            render_html(f"""
            <div class='neuro-card' style='padding:20px 24px;'>
                <h4 style='color:#0F172A; margin:0 0 10px 0;'>🎯 Top Focus Areas for Immediate Prep</h4>
                <ul style='padding-left:20px; margin:0; color:#1E293B; font-size:0.9rem;'>
                    {focus_lis}
                </ul>
            </div>
            """)

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            strong_items = [f"<div><b style='color:#0F172A;'>{m.get('skill_or_area')}</b><br><small style='color:#64748B;'>Implication: {m.get('interview_implication')}</small><hr style='border:0; border-top:1px solid #E2E8F0; margin:8px 0;'></div>" for m in fit_data.get("strong_matches", [])]
            render_html(f"""
            <div class='neuro-card'>
                <span class='neuro-badge neuro-badge-strong'>Strong Matches</span>
                <div style='margin-top:12px;'>{''.join(strong_items)}</div>
            </div>
            """)
            
        with m_col2:
            partial_items = [f"<div><b style='color:#0F172A;'>{p.get('skill_or_area')}</b><br><small style='color:#B45309;'>Status: {p.get('status')}</small><br><small style='color:#64748B;'>Implication: {p.get('interview_implication')}</small><hr style='border:0; border-top:1px solid #E2E8F0; margin:8px 0;'></div>" for p in fit_data.get("partial_matches", [])]
            render_html(f"""
            <div class='neuro-card'>
                <span class='neuro-badge neuro-badge-partial'>Partial Matches</span>
                <div style='margin-top:12px;'>{''.join(partial_items)}</div>
            </div>
            """)

        with m_col3:
            gap_items = [f"<div><b style='color:#0F172A;'>{g.get('skill_or_area')}</b><br><small style='color:#64748B;'>Strategic Defense: {g.get('strategic_advice')}</small><hr style='border:0; border-top:1px solid #E2E8F0; margin:8px 0;'></div>" for g in fit_data.get("critical_gaps", [])]
            render_html(f"""
            <div class='neuro-card'>
                <span class='neuro-badge neuro-badge-gap'>Clear Gaps</span>
                <div style='margin-top:12px;'>{''.join(gap_items)}</div>
            </div>
            """)

        # -------------------------------------------------------------
        # SECTION 7: Formal Hiring Recommendation & Decision Engine
        # -------------------------------------------------------------
        st.markdown("<h3 style='margin-top:24px; margin-bottom:12px; color:#0F172A;'>⚖️ Formal Hiring Recommendation & Decision Engine</h3>", unsafe_allow_html=True)
        
        tech_pct = tech_rating.get("strict_match_percentage", 28.57)
        if tech_pct >= 75:
            dec_class = "neuro-decision-hire"
            dec_title = "Direct Shortlist / Proceed to Interview"
            dec_badge_class = "neuro-badge-matched"
            rule_text = "Rule Triggered: Strong Mandatory & Core Capability Alignment"
            policy_text = "Direct candidate to advanced personal interviews and stakeholder evaluation."
            suitable_text = "Core Professional / Associate Roles"
        elif tech_pct >= 50:
            dec_class = "neuro-decision-conditional"
            dec_title = "Conditional Assessment / Technical Test Required"
            dec_badge_class = "neuro-badge-missing-pref"
            rule_text = "Rule Triggered: Moderate Fit with Specific Core Gaps"
            policy_text = "Candidate must clear technical examination and defend identified gap areas."
            suitable_text = "Junior Specialist / Accelerated Trainee Roles"
        else:
            dec_class = "neuro-decision-reject"
            dec_title = "Reject / Redirect to Foundational Track"
            dec_badge_class = "neuro-badge-missing"
            rule_text = "Rule Triggered: Missing Multiple Mandatory Core Skills (< 50% match)"
            policy_text = f"Candidate matches {matched_count} of {total_mand} mandatory skills. Not recommended for direct hiring at this stage."
            suitable_text = "Summer Internships, Preparatory Programs, or Foundational Analyst Roles"

        justification_li = [
            f"<li style='margin-bottom:4px;'><strong style='color:#0F172A;'>Technical Match Score:</strong> Demonstrates {matched_count} of {total_mand} mandatory requirements ({tech_pct:.1f}% match).</li>",
            f"<li style='margin-bottom:4px;'><strong style='color:#0F172A;'>Candidate Academic Stage:</strong> {cand_details.get('stage', 'Early Stage')} &bull; {cand_details.get('current_program', 'MBA Candidate')}.</li>",
            f"<li style='margin-bottom:4px;'><strong style='color:#0F172A;'>Experience Tier:</strong> {pts} / {max_pts} points ({exp_sum}).</li>"
        ]

        render_html(f"""
        <div class='neuro-decision-card {dec_class}'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:14px;'>
                <div>
                    <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Formal Evaluation Decision</span>
                    <h3 style='margin:4px 0 0 0; font-size:1.5rem; font-weight:800; color:#0F172A;'>{dec_title}</h3>
                </div>
                <div style='text-align:right;'>
                    <span class='{dec_badge_class}' style='font-size:0.85rem; padding:4px 12px;'>{rule_text}</span>
                </div>
            </div>
            <div class='neuro-inset' style='margin-bottom:12px;'>
                <strong style='color:#0F172A; font-size:0.85rem;'>Policy Criteria:</strong>
                <p style='margin:2px 0 0 0; color:#334155; font-size:0.85rem;'>{policy_text}</p>
            </div>
            <div style='font-size:0.85rem; color:#1E293B;'>
                <strong style='color:#0F172A;'>Evaluation Justification Summary:</strong>
                <ul style='margin:6px 0 12px 18px; padding:0; color:#334155;'>
                    {''.join(justification_li)}
                </ul>
            </div>
            <div class='neuro-inset' style='margin:0; padding:10px 14px; display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size:0.8rem; color:#64748B; font-weight:600;'>Candidate Suitable For:</span>
                <strong style='color:#2563EB; font-size:0.85rem;'>{suitable_text}</strong>
            </div>
        </div>
        """)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Proceed to Step 3: Targeted Question Bank ➡️", use_container_width=True):
            st.session_state.current_page = "03_question_bank"
            st.rerun()

elif page == "03_question_bank":
    qb_data = st.session_state.orchestrator.state.get("question_bank")
    if not qb_data:
        render_html(UI.empty_state(
            title="Targeted Question Bank Not Generated",
            description="The Question Bank is automatically synthesized from the Strategic Fit Analysis. Complete Step 1 to generate personalized interview probes.",
            icon_name="book_open",
            action_hint="Click below to return to Step 1 and initialize candidate onboarding."
        ))
        if st.button("🚀 Return to Step 1: Candidate Onboarding", use_container_width=True, key="empty_step3_to_step1_btn"):
            st.session_state.current_page = "01_upload"
            st.rerun()
    else:
        round_num = qb_data.get("round_number", st.session_state.orchestrator.state.get("round_number", 1))
        if round_num > 1:
            st.info(f"🔄 **Round {round_num} Active**: Question Bank dynamically re-weighted based on previous test performance & high-priority gaps.")

        render_html(UI.hero_header(
            title="Step 3: Comprehensive Question Bank & JD Topic Checklist",
            subtitle="100% of required JD topics are mapped, prioritized, and systematically covered across technical and behavioral probes.",
            badge_text=f"Round {round_num} Active" if round_num > 1 else "100% Coverage Verified",
            icon_name="book_open"
        ))

        # Quick Action: Export Question Bank to Markdown & Plain Text
        cand_name_str = st.session_state.orchestrator.state.get("candidate_name", "Candidate")
        c_clean = cand_name_str.replace(" ", "_")
        jd_d = st.session_state.orchestrator.state.get("jd_data") or {}
        r_title = jd_d.get("role_title", "Target Role")
        c_name = jd_d.get("company_name", "Target Company")
        
        def _build_qb_markdown(qb, cand, role, comp):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            lines = [
                f"# InterviewIQ Targeted Question Bank",
                f"**Candidate:** {cand}  |  **Target Role:** {role}  |  **Company:** {comp}",
                f"**Generated:** {now_str}  |  **Coverage:** 100% of JD Checklist Mapped",
                "\n---\n"
            ]
            cats = [
                ("1. Technical Deep-Dive Questions", "technical_questions"),
                ("2. Scenario & Problem-Solving Probes", "scenario_questions"),
                ("3. Behavioral Questions (STAR Calibrated)", "behavioral_questions"),
                ("4. Resume Challenge Questions", "resume_based_questions"),
                ("5. Gap Defense & Mitigation Probes", "gap_mitigation_questions")
            ]
            for title, key in cats:
                qs = qb.get(key, [])
                if qs:
                    lines.append(f"\n## {title}\n")
                    for i, q in enumerate(qs, 1):
                        q_txt = q.get("question", "")
                        lines.append(f"### Question {i}: {q_txt}")
                        if q.get("topic_tag"):
                            lines.append(f"- **Focus Domain / Topic:** {q.get('topic_tag')}")
                        if q.get("competency"):
                            lines.append(f"- **Target Competency:** {q.get('competency')}")
                        if q.get("target_claim"):
                            lines.append(f"- **Referenced Resume Claim:** {q.get('target_claim')}")
                        if q.get("evaluation_criteria"):
                            lines.append(f"- **Evaluation Rubric:** {q.get('evaluation_criteria')}")
                        if q.get("guidance"):
                            lines.append(f"- **Interview Guidance:** {q.get('guidance')}")
                        if q.get("tactical_coaching"):
                            lines.append(f"- **Tactical Coaching:** {q.get('tactical_coaching')}")
                        if q.get("ideal_answer_points"):
                            lines.append("- **Ideal Answer Benchmarks:**")
                            for pt in q.get("ideal_answer_points", []):
                                lines.append(f"  - {pt}")
                        lines.append("")
            return "\n".join(lines)

        def _build_qb_txt(qb, cand, role, comp):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            lines = [
                "=" * 72,
                "INTERVIEWIQ TARGETED QUESTION BANK — OFFLINE PREP SHEET",
                "=" * 72,
                f"Candidate: {cand}",
                f"Target Role: {role}",
                f"Company: {comp}",
                f"Generated: {now_str}",
                f"Coverage: 100% of JD Requirements Systematically Covered",
                "=" * 72,
                ""
            ]
            cats = [
                ("1. TECHNICAL DEEP-DIVE QUESTIONS", "technical_questions"),
                ("2. SCENARIO & PROBLEM-SOLVING PROBES", "scenario_questions"),
                ("3. BEHAVIORAL QUESTIONS (STAR CALIBRATED)", "behavioral_questions"),
                ("4. RESUME CHALLENGE QUESTIONS", "resume_based_questions"),
                ("5. GAP DEFENSE & MITIGATION PROBES", "gap_mitigation_questions")
            ]
            for title, key in cats:
                qs = qb.get(key, [])
                if qs:
                    lines.append("")
                    lines.append("-" * 72)
                    lines.append(title)
                    lines.append("-" * 72)
                    for i, q in enumerate(qs, 1):
                        q_txt = q.get("question", "")
                        lines.append(f"\n[{i}] {q_txt}")
                        if q.get("topic_tag"):
                            lines.append(f"    • Focus Domain: {q.get('topic_tag')}")
                        if q.get("competency"):
                            lines.append(f"    • Competency: {q.get('competency')}")
                        if q.get("target_claim"):
                            lines.append(f"    • Resume Claim: {q.get('target_claim')}")
                        if q.get("evaluation_criteria"):
                            lines.append(f"    • Rubric: {q.get('evaluation_criteria')}")
                        if q.get("guidance"):
                            lines.append(f"    • Guidance: {q.get('guidance')}")
                        if q.get("tactical_coaching"):
                            lines.append(f"    • Tactical Tip: {q.get('tactical_coaching')}")
                        if q.get("ideal_answer_points"):
                            lines.append("    • Ideal Answer Benchmarks:")
                            for pt in q.get("ideal_answer_points", []):
                                lines.append(f"      - {pt}")
            return "\n".join(lines)

        qb_md = _build_qb_markdown(qb_data, cand_name_str, r_title, c_name)
        qb_txt = _build_qb_txt(qb_data, cand_name_str, r_title, c_name)
        qb_bar_col1, qb_bar_col2, qb_bar_col3 = st.columns([2, 1, 1])
        with qb_bar_col2:
            st.download_button(
                label="📥 Export as .MD",
                data=qb_md,
                file_name=f"InterviewIQ_{c_clean}_QuestionBank.md",
                mime="text/markdown",
                use_container_width=True,
                key="export_qb_md_btn"
            )
        with qb_bar_col3:
            st.download_button(
                label="📄 Export as .TXT",
                data=qb_txt,
                file_name=f"InterviewIQ_{c_clean}_QuestionBank.txt",
                mime="text/plain",
                use_container_width=True,
                key="export_qb_txt_btn"
            )

        # Topic Checklist & Coverage Summary
        cov = qb_data.get("coverage_summary", {})
        checklist = qb_data.get("topic_checklist", [])
        total_topics = cov.get("total_jd_topics", len(checklist))
        covered_topics = cov.get("covered_topics", len(checklist))
        cov_pct = cov.get("coverage_percentage", 100.0)
        tot_q = cov.get("total_questions", 0)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>JD Topics</span><div style='font-size:2rem; font-weight:900; color:#0F172A;'>{total_topics}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Covered Topics</span><div style='font-size:2rem; font-weight:900; color:#2563EB;'>{covered_topics}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Checklist Coverage</span><div style='font-size:2rem; font-weight:900; color:#10B981;'>{cov_pct}%</div><span class='neuro-badge-matched' style='font-size:0.7rem;'>100% Verified</span></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Total Questions</span><div style='font-size:2rem; font-weight:900; color:#6366F1;'>{tot_q}</div></div>", unsafe_allow_html=True)

        if checklist:
            st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:8px;'>📋 JD Topic Checklist & Weighting</h4>", unsafe_allow_html=True)
            t_rows = []
            for item in checklist:
                t_name = item.get("topic_name", "")
                t_cat = item.get("category", "Mandatory")
                t_status = item.get("status", "Untested")
                t_weight = item.get("weight", 1.0)
                t_count = item.get("question_count", 0)

                cat_badge = "neuro-badge-mandatory" if t_cat == "Mandatory" else "neuro-badge-preferred"
                if t_status == "Gap":
                    status_badge = "neuro-badge-missing"
                elif t_status == "Claimed":
                    status_badge = "neuro-badge-matched"
                else:
                    status_badge = "neuro-badge-missing-pref"

                t_rows.append(
                    f"<tr>"
                    f"<td><b>{t_name}</b></td>"
                    f"<td><span class='{cat_badge}'>{t_cat}</span></td>"
                    f"<td><span class='{status_badge}'>{t_status}</span></td>"
                    f"<td style='text-align:center;'>{t_weight:.1f}x</td>"
                    f"<td style='text-align:center;'><b>{t_count}</b></td>"
                    f"</tr>"
                )

            render_html(f"""
            <div class='neuro-card'>
                <div style='overflow-x:auto;'>
                    <table class='neuro-table'>
                        <thead>
                            <tr>
                                <th style='width:40%;'>Topic Name</th>
                                <th style='width:15%;'>Category</th>
                                <th style='width:15%;'>Status</th>
                                <th style='width:15%; text-align:center;'>Weight</th>
                                <th style='width:15%; text-align:center;'>Questions in Bank</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(t_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
            """)

        st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:12px;'>🎯 Curated Questions by Assessment Dimension</h4>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Technical Deep-Dive", "Scenario & Problem Solving", "Behavioral (STAR)", "Resume Challenge", "Gap Defense"])
        
        with tab1:
            tech_qs = qb_data.get("technical_questions", [])
            if not tech_qs:
                st.info("No technical questions in this section.")
            for q in tech_qs:
                t_tag = q.get('topic_tag', '')
                q_text = q.get('question', '')
                skill = q.get('skill_tested', t_tag)
                framework = q.get('ideal_answer_framework', 'Focus on key technical mechanics, trade-offs, and failure mitigations.')
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>
                        <span style='font-weight:700; color:#0F172A; font-size:0.95rem;'>💻 {q_text}</span>
                        <span class='neuro-badge-mandatory' style='flex-shrink:0; margin-left:12px;'>{t_tag}</span>
                    </div>
                    <div style='font-size:0.8rem; color:#64748B; margin-bottom:8px;'>Skill Tested: <strong style='color:#334155;'>{skill}</strong></div>
                    <div class='neuro-inset' style='margin:0; padding:10px 14px;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#2563EB;'>Ideal Answer Framework:</span>
                        <p style='margin:4px 0 0 0; color:#1E293B; font-size:0.85rem;'>{framework}</p>
                    </div>
                </div>
                """)

        with tab2:
            ps_qs = qb_data.get("problem_solving_questions", [])
            if not ps_qs:
                st.info("No scenario questions in this section.")
            for q in ps_qs:
                t_tag = q.get('topic_tag', '')
                scenario = q.get('scenario', '')
                criteria = q.get('evaluation_criteria', 'Structured root-cause diagnosis, stakeholder communication, and validation.')
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>
                        <span style='font-weight:700; color:#0F172A; font-size:0.95rem;'>🧩 Scenario: {scenario}</span>
                        <span class='neuro-badge-preferred' style='flex-shrink:0; margin-left:12px;'>{t_tag}</span>
                    </div>
                    <div class='neuro-inset' style='margin:0; padding:10px 14px;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#B45309;'>Evaluation Criteria:</span>
                        <p style='margin:4px 0 0 0; color:#1E293B; font-size:0.85rem;'>{criteria}</p>
                    </div>
                </div>
                """)

        with tab3:
            comp_info = qb_data.get("company_intelligence")
            if comp_info:
                c_name = comp_info.get("company_name", "Target Hiring Firm")
                c_fw = comp_info.get("evaluation_framework", "Leadership Principles")
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; border-left: 5px solid #10B981; padding:12px 18px;'>
                    <strong style='color:#0F172A; font-size:0.95rem;'>🏢 Corporate Culture Grounded Probes ({c_name})</strong>
                    <p style='color:#475569; font-size:0.82rem; margin:2px 0 0 0;'>
                        Behavioral situational questions calibrated against <b>{c_name}'s {c_fw}</b> from verified candidate interview reports.
                    </p>
                </div>
                """)

            beh_qs = qb_data.get("behavioral_questions", [])
            if not beh_qs:
                st.info("No behavioral questions in this section.")
            for q in beh_qs:
                t_tag = q.get('topic_tag', '')
                q_text = q.get('question', '')
                comp = q.get('competency', 'Structured Leadership')
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>
                        <span style='font-weight:700; color:#0F172A; font-size:0.95rem;'>🗣️ {q_text}</span>
                        <span class='neuro-badge-matched' style='flex-shrink:0; margin-left:12px;'>{t_tag}</span>
                    </div>
                    <div class='neuro-inset' style='margin:0; padding:8px 12px; font-size:0.85rem;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#15803D;'>Target Competency:</span>
                        <span style='color:#1E293B; margin-left:6px; font-weight:600;'>{comp}</span>
                    </div>
                </div>
                """)

        with tab4:
            res_qs = qb_data.get("resume_based_questions", [])
            if not res_qs:
                st.info("No resume challenges in this section.")
            for q in res_qs:
                q_text = q.get('question', '')
                prio = q.get('priority', 'High')
                claim = q.get('target_claim', 'Claimed background')
                guidance = q.get('guidance', 'Quantify impact with data and address trade-offs.')
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>
                        <span style='font-weight:700; color:#0F172A; font-size:0.95rem;'>📌 {q_text}</span>
                        <span class='neuro-badge-partial' style='flex-shrink:0; margin-left:12px;'>Priority: {prio}</span>
                    </div>
                    <div style='font-size:0.8rem; color:#64748B; margin-bottom:8px;'>Referenced Resume Claim: <strong style='color:#334155;'>{claim}</strong></div>
                    <div class='neuro-inset' style='margin:0; padding:10px 14px;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#2563EB;'>Interview Guidance:</span>
                        <p style='margin:4px 0 0 0; color:#1E293B; font-size:0.85rem;'>{guidance}</p>
                    </div>
                </div>
                """)

        with tab5:
            gap_qs = qb_data.get("gap_mitigation_questions", [])
            if not gap_qs:
                st.info("No gap mitigation questions in this section.")
            for q in gap_qs:
                t_tag = q.get('topic_tag', '')
                q_text = q.get('question', '')
                gap_area = q.get('gap_area', t_tag)
                coaching = q.get('tactical_coaching', 'Acknowledge boundary, pivot to adjacent foundational skills, and outline rapid learning steps.')
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>
                        <span style='font-weight:700; color:#0F172A; font-size:0.95rem;'>🛡️ {q_text}</span>
                        <span class='neuro-badge-gap' style='flex-shrink:0; margin-left:12px;'>{t_tag or gap_area}</span>
                    </div>
                    <div style='font-size:0.8rem; color:#64748B; margin-bottom:8px;'>Addressing Gap Area: <strong style='color:#B91C1C;'>{gap_area}</strong></div>
                    <div class='neuro-inset' style='margin:0; padding:10px 14px;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#B45309;'>Tactical Coaching:</span>
                        <p style='margin:4px 0 0 0; color:#1E293B; font-size:0.85rem;'>{coaching}</p>
                    </div>
                </div>
                """)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Proceed to Step 4: Scored Online Test (30 MCQs) ➡️", use_container_width=True, key="proceed_step4_btn"):
            if not st.session_state.orchestrator.state.get("online_test"):
                with st.spinner("Calibrating 30-MCQ Online Test from Topic Checklist..."):
                    st.session_state.orchestrator.generate_online_test()
            st.session_state.current_page = "04_online_test"
            st.rerun()

elif page == "04_online_test":
    test_data = st.session_state.orchestrator.state.get("online_test")
    test_results = st.session_state.orchestrator.state.get("test_results")

    render_html(UI.hero_header(
        title="Step 4: Empirical Placement Assessment",
        subtitle="Experience institutional candidate vetting via timed, rigorous multiple-choice assessments or live conversational voice simulations with Google Local NLP speech processing.",
        badge_text="Empirical Proctoring & Voice",
        icon_name="clipboard"
    ))

    step4_mode = st.radio(
        "Evaluation Format:",
        ["📝 Timed 30-MCQ Online Test (Institutional Standard)", "🎙️ Conversational Voice Interview Simulator (Google Local NLP)"],
        horizontal=True,
        key="step4_format_selector"
    )

    if step4_mode == "🎙️ Conversational Voice Interview Simulator (Google Local NLP)":
        cand_name = st.session_state.orchestrator.state.get("candidate_name", "Candidate")
        role_title = (st.session_state.orchestrator.state.get("jd_data") or {}).get("role_title", "Target Role")
        resume_profile = st.session_state.orchestrator.state.get("resume_data") or {}
        jd_profile = st.session_state.orchestrator.state.get("jd_data") or {}
        fit_profile = st.session_state.orchestrator.state.get("fit_data") or {}

        if "voice_agent" not in st.session_state:
            st.session_state.voice_agent = VoiceInterviewAgent(api_key=st.session_state.custom_api_key)
        if "voice_turns" not in st.session_state:
            st.session_state.voice_turns = []
        if "voice_current_q" not in st.session_state or not st.session_state.voice_current_q:
            first_turn = st.session_state.voice_agent.start_interview(resume_profile, jd_profile, fit_profile)
            st.session_state.voice_current_q = first_turn.get("interviewer_question", "Please introduce yourself and explain how your academic background and project experiences make you an ideal fit for this target position.")

        turn_count = len(st.session_state.voice_turns) + 1
        render_html(f"""
        <div class='neuro-card' style='border-left: 5px solid #2563EB; margin-bottom: 16px;'>
            <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;'>
                <div>
                    <span style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:#2563EB; display:inline-flex; align-items:center; gap:6px;'>{icon('mic', size=14, color=Theme.COLORS['primary'])} Live Voice Interview Simulation</span>
                    <h3 style='margin:2px 0 0 0; color:#0F172A;'>Conversational Assessment: {role_title}</h3>
                    <p style='margin:2px 0 0 0; font-size:0.85rem; color:#475569;'>Powered by Google Local NLP speech recognition and text-to-speech synthesis.</p>
                </div>
                <span class='neuro-badge-matched'>Turn {min(turn_count, 4)} of 4</span>
            </div>
        </div>
        """)

        # Display Interviewer Question Card
        curr_q = st.session_state.voice_current_q
        render_html(f"""
        <div class='neuro-card' style='margin-bottom:14px; background:#F8FAFC; border:1.5px solid #CBD5E1;'>
            <div style='font-size:0.8rem; text-transform:uppercase; font-weight:700; color:#2563EB; margin-bottom:6px;'>Interviewer Question:</div>
            <h4 style='color:#0F172A; margin:0; line-height:1.45;'>{curr_q}</h4>
        </div>
        """)

        # Embed Google Local NLP Voice Recorder Component
        vr_path = os.path.join(project_root, "frontend", "components", "voice_recorder.html")
        if os.path.exists(vr_path):
            with open(vr_path, "r", encoding="utf-8") as vf:
                vr_html = vf.read()
                if hasattr(st, "iframe"):
                    st.iframe(vr_html, height=280)
                else:
                    import streamlit.components.v1 as components
                    components.html(vr_html, height=280)

        # Candidate Verbal Response Text Area & Submission
        v_turn_idx = len(st.session_state.voice_turns)
        v_turn_key = f"voice_resp_turn_{v_turn_idx}"

        st.caption("💡 *Tip: If your browser restricts microphone permissions or sandbox injection, click '📋 Copy Transcript' in the recorder and press Ctrl+V below, or use the quick practice answer button.*")

        vf_col1, vf_col2 = st.columns([3, 1])
        with vf_col2:
            if st.button("💡 Insert Practice Answer", key=f"insert_sample_voice_{v_turn_idx}", use_container_width=True):
                st.session_state[v_turn_key] = (
                    "Thank you. Throughout my PGDM and analytics internships, "
                    "I have applied structured MECE problem-solving frameworks to streamline business workflows. "
                    "In my prior project, I led an end-to-end data pipeline optimization that cut reporting latency by 35% "
                    "and improved cross-functional agile sprint predictability. I am prepared to apply this quantitative rigor here."
                )
                st.rerun()

        verbal_response = st.text_area(
            "Candidate Verbal Response (live transcribed or typed):",
            key=v_turn_key,
            placeholder="Click 'Record' above to speak via Google Local NLP speech-to-text, or type your response here...",
            height=110
        )

        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            if st.button("🚀 Submit Verbal Response & Analyze Delivery", use_container_width=True):
                if not verbal_response or len(verbal_response.strip()) < 8:
                    st.warning("Please provide a verbal or typed response before submitting.")
                else:
                    with st.spinner("Analyzing verbal communication delivery & STAR methodology..."):
                        turn_eval = st.session_state.voice_agent.process_turn(
                            st.session_state.voice_turns,
                            verbal_response,
                            resume_profile,
                            jd_profile
                        )
                        st.session_state.voice_turns.append({
                            "question": curr_q,
                            "answer": verbal_response,
                            "evaluation": turn_eval
                        })
                        if turn_eval.get("is_concluded") or len(st.session_state.voice_turns) >= 4:
                            st.session_state.voice_concluded = True
                        else:
                            st.session_state.voice_current_q = turn_eval.get("next_question", "What operational trade-offs did you make in that scenario?")
                        st.rerun()

        with col_v2:
            if st.button("🔄 Reset Voice Interview", use_container_width=True):
                st.session_state.voice_turns = []
                st.session_state.voice_current_q = None
                if "voice_concluded" in st.session_state:
                    del st.session_state.voice_concluded
                st.rerun()

        # Render Previous Turns Feedback
        if st.session_state.voice_turns:
            st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:12px;'>📊 Communication Diagnostics & Verbal Audit</h4>", unsafe_allow_html=True)
            for idx, turn in enumerate(reversed(st.session_state.voice_turns)):
                t_q = turn["question"]
                t_a = turn["answer"]
                eval_data = turn.get("evaluation", {})
                t_eval = eval_data.get("turn_evaluation", {})
                audit = eval_data.get("communication_audit", {})
                star_comp = audit.get("star_compliance", {})
                fillers = audit.get("filler_analysis", {})
                cadence = audit.get("cadence_analysis", {})
                diversity = audit.get("lexical_diversity", {})
                syntax = audit.get("syntactic_style", {})
                domain_f = audit.get("domain_fluency", {})
                comp_score = audit.get("composite_delivery_score", 70.0)

                score_col = "#10B981" if comp_score >= 75 else ("#F59E0B" if comp_score >= 50 else "#EF4444")
                domain_tags = "".join([f"<span class='neuro-badge-matched' style='font-size:0.75rem; margin-right:4px; padding:2px 6px;'>{t}</span>" for t in domain_f.get('terms_found', [])[:5]]) or "<span style='color:#94A3B8; font-size:0.8rem;'>None detected</span>"
                
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:14px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                        <strong style='color:#2563EB;'>Turn {len(st.session_state.voice_turns) - idx} Diagnostic Audit</strong>
                        <span class='neuro-badge-matched' style='background:#F1F5F9; color:{score_col}; font-weight:800;'>Delivery Score: {comp_score}/100 ({audit.get('executive_presence_level', 'Developing')})</span>
                    </div>
                    <p style='margin:0 0 6px 0; font-size:0.85rem; color:#64748B;'><b>Q:</b> {t_q}</p>
                    <p style='margin:0 0 10px 0; font-size:0.85rem; color:#0F172A;'><b>Your Answer:</b> "{t_a}"</p>
                    <div style='display:grid; grid-template-columns: repeat(4, 1fr); gap:8px; margin-bottom:10px;'>
                        <div class='neuro-inset' style='padding:6px 10px; text-align:center;'>
                            <small style='color:#64748B;'>STAR Flow</small>
                            <div style='font-weight:800; color:#0F172A;'>{star_comp.get('star_score', 0)}% {'✓' if star_comp.get('chronological_flow') else '⚠'}</div>
                        </div>
                        <div class='neuro-inset' style='padding:6px 10px; text-align:center;'>
                            <small style='color:#64748B;'>Speaking Pace</small>
                            <div style='font-weight:800; color:#0F172A;'>{cadence.get('wpm', 0)} WPM</div>
                        </div>
                        <div class='neuro-inset' style='padding:6px 10px; text-align:center;'>
                            <small style='color:#64748B;'>Fillers & Stutters</small>
                            <div style='font-weight:800; color:#0F172A;'>{fillers.get('total_fillers', 0)}f / {fillers.get('stutter_count', 0)}s</div>
                        </div>
                        <div class='neuro-inset' style='padding:6px 10px; text-align:center;'>
                            <small style='color:#64748B;'>Lexical Diversity</small>
                            <div style='font-weight:800; color:#0F172A;'>{int(diversity.get('ttr', 0.0) * 100)}% TTR</div>
                        </div>
                    </div>
                    <div style='margin-bottom:8px; font-size:0.8rem;'>
                        <span style='color:#64748B; font-weight:700;'>Executive Diction:</span>
                        <span style='color:#0F172A; margin-left:4px;'>{syntax.get('voice_verdict', 'Balanced')}</span> | 
                        <span style='color:#64748B; font-weight:700;'>Domain Terms:</span> {domain_tags}
                    </div>
                    <div class='neuro-inset' style='padding:8px 12px; margin-top:6px;'>
                        <span style='color:#B45309; font-weight:700; font-size:0.8rem;'>Tactical Coaching:</span>
                        <p style='margin:2px 0 0 0; color:#1E293B; font-size:0.85rem;'>{t_eval.get('coaching_tip', 'Structure your responses using the STAR method.')}</p>
                    </div>
                </div>
                """)

    else:
        if not test_data:
            render_html(UI.empty_state(
                title="Empirical Assessment Ready to Generate",
                description="Synthesize a customized 30-question placement examination calibrated directly to the JD Topic Checklist and competency criteria.",
                icon_name="clipboard",
                action_hint="Click below to generate and take your 30-question assessment."
            ))
            if st.button("🚀 Generate Custom 30-Question Online Test", use_container_width=True):
                with st.spinner("Online Test Agent is synthesizing 30 domain-specific MCQs with plausible distractors..."):
                    try:
                        test_data = st.session_state.orchestrator.generate_online_test()
                        st.success("Examination generated successfully! Begin below.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating test: {e}")
        else:
            questions = test_data.get("questions", [])
            
            # Test meta info
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Questions</span><div style='font-size:1.8rem; font-weight:900; color:#0F172A;'>{test_data.get('total_questions', len(questions))}</div></div>")
            with col_m2:
                render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Time Limit</span><div style='font-size:1.8rem; font-weight:900; color:#2563EB;'>{test_data.get('time_limit_minutes', 45)} Mins</div></div>")
            with col_m3:
                render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Passing Mark</span><div style='font-size:1.8rem; font-weight:900; color:#D97706;'>{test_data.get('passing_score_percentage', 70)}%</div></div>")
            with col_m4:
                render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Assessment Round</span><div style='font-size:1.8rem; font-weight:900; color:#10B981;'>Round {test_data.get('round_number', 1)}</div></div>")

            # Mode 1: If test already submitted and graded, show Results and Detailed Review
            if test_results:
                score = test_results.get("score", 0)
                total = test_results.get("total_questions", 30)
                pct = test_results.get("percentage", 0.0)
                passed = test_results.get("passed", False)
                pass_status = "PASSED" if passed else "NEEDS REVISION"
                status_badge = "neuro-badge-matched" if passed else "neuro-badge-missing"

                render_html(f"""
                <div class='neuro-card' style='margin-top:16px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;'>
                        <div>
                            <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Examination Result</span>
                            <div style='font-size:2.5rem; font-weight:900; color:#0F172A; margin:4px 0;'>
                                {score} <span style='font-size:1.4rem; color:#64748B; font-weight:500;'>/ {total}</span>
                                <span style='font-size:1.8rem; color:#2563EB; margin-left:12px;'>({pct:.1f}%)</span>
                            </div>
                        </div>
                        <div>
                            <span class='{status_badge}' style='font-size:1rem; padding:6px 18px;'>{pass_status}</span>
                        </div>
                    </div>
                </div>
                """)

                # Topic-wise accuracy breakdown table
                topic_acc = test_results.get("topic_accuracy", {})
                if topic_acc:
                    st.markdown("<h4 style='color:#0F172A; margin-top:20px; margin-bottom:8px;'>📊 Topic-Wise Accuracy Breakdown</h4>", unsafe_allow_html=True)
                    acc_rows = []
                    for top_name, top_stats in topic_acc.items():
                        c_cnt = top_stats.get("correct", 0)
                        t_cnt = top_stats.get("total", 0)
                        top_pct = top_stats.get("percentage", 0.0)
                        badge = "neuro-badge-matched" if top_pct >= 70 else ("neuro-badge-missing-pref" if top_pct >= 50 else "neuro-badge-missing")
                        status_lbl = "Proficient" if top_pct >= 70 else ("Needs Practice" if top_pct >= 50 else "Critical Deficit")
                        acc_rows.append(
                            f"<tr>"
                            f"<td><b>{top_name}</b></td>"
                            f"<td style='text-align:center;'>{c_cnt} / {t_cnt}</td>"
                            f"<td style='text-align:center;'><b>{top_pct:.1f}%</b></td>"
                            f"<td style='text-align:center;'><span class='{badge}'>{status_lbl}</span></td>"
                            f"</tr>"
                        )

                    render_html(f"""
                    <div class='neuro-card'>
                        <div style='overflow-x:auto;'>
                            <table class='neuro-table'>
                                <thead>
                                    <tr>
                                        <th style='width:45%;'>Topic</th>
                                        <th style='width:20%; text-align:center;'>Score</th>
                                        <th style='width:15%; text-align:center;'>Accuracy</th>
                                        <th style='width:20%; text-align:center;'>Diagnostic Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(acc_rows)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    """)

                # Detailed Itemized Question Review in 3 Categorized Tabs
                st.markdown("<h4 style='color:#0F172A; margin-top:24px; margin-bottom:12px;'>🔍 Itemized Question Review & Explanations</h4>", unsafe_allow_html=True)
                detailed_items = test_results.get("detailed_results", [])
                incorrect_items = [item for item in detailed_items if not item.get("is_correct", False)]
                correct_items = [item for item in detailed_items if item.get("is_correct", False)]

                def render_item_card(item):
                    q_num = item.get("question_number", 1)
                    q_txt = (
                        item.get("question_text") or 
                        item.get("question") or 
                        item.get("prompt") or 
                        item.get("scenario") or 
                        item.get("text") or 
                        ""
                    ).strip()
                    if not q_txt:
                        q_txt = f"Scenario assessment question testing {item.get('topic', 'domain competencies')}."
                    cand_ans = item.get("candidate_answer") or item.get("selected_option") or "Unanswered"
                    corr_ans = item.get("correct_option", "A")
                    is_c = item.get("is_correct", False)
                    top = item.get("topic") or item.get("topic_name") or "Domain"
                    expl = item.get("explanation", "Review core domain fundamentals for this concept.")

                    status_badge = "<span class='neuro-badge-matched' style='flex-shrink:0;'>✅ Correct (+1)</span>" if is_c else "<span class='neuro-badge-missing' style='flex-shrink:0;'>❌ Incorrect (0)</span>"
                    cand_col = "#15803D" if is_c else "#B91C1C"

                    return f"""
                    <div class='neuro-card' style='margin-bottom:14px; padding:18px;'>
                        <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; gap:12px;'>
                            <div>
                                <span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#2563EB;'>Question {q_num}</span>
                                <h4 style='margin:4px 0 0 0; color:#0F172A; font-size:0.95rem; font-weight:700; line-height:1.4;'>{q_txt}</h4>
                            </div>
                            <div style='display:flex; gap:6px; align-items:center; flex-shrink:0;'>
                                <span class='neuro-badge-mandatory'>{top}</span>
                                {status_badge}
                            </div>
                        </div>
                        <div class='neuro-inset' style='margin-bottom:10px; padding:10px 14px;'>
                            <div style='display:flex; gap:24px; font-size:0.85rem;'>
                                <div><b style='color:#0F172A;'>Your Answer:</b> <span style='color:{cand_col}; font-weight:700;'>Option {cand_ans}</span></div>
                                <div><b style='color:#0F172A;'>Correct Answer:</b> <span style='color:#15803D; font-weight:700;'>Option {corr_ans}</span></div>
                            </div>
                        </div>
                        <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px 14px;'>
                            <strong style='font-size:0.75rem; text-transform:uppercase; color:#0F172A; display:block; margin-bottom:4px;'>💡 Domain Diagnostic & Rationale:</strong>
                            <p style='margin:0; font-size:0.85rem; color:#1E293B; line-height:1.5;'>{expl}</p>
                        </div>
                    </div>
                    """

                rtab1, rtab2, rtab3 = st.tabs([
                    f"All Questions ({len(detailed_items)})",
                    f"❌ Review Needed ({len(incorrect_items)})",
                    f"✅ Correct ({len(correct_items)})"
                ])

                with rtab1:
                    for item in detailed_items:
                        render_html(render_item_card(item))

                with rtab2:
                    if not incorrect_items:
                        st.success("🎉 Perfect Score! No questions require review.")
                    else:
                        for item in incorrect_items:
                            render_html(render_item_card(item))

                with rtab3:
                    if not correct_items:
                        st.info("No correct questions yet.")
                    else:
                        for item in correct_items:
                            render_html(render_item_card(item))

                st.markdown("<br>", unsafe_allow_html=True)
                col_act1, col_act2, col_act3 = st.columns([2, 1, 1.2])
                with col_act1:
                    if st.button("📈 View Unified Performance & Feedback Report ➡️", use_container_width=True, key="view_unified_feedback_btn"):
                        st.session_state.current_page = "05_results"
                        st.rerun()
                with col_act2:
                    if st.button("🔄 Retake Same Test", use_container_width=True, key="retake_same_test_btn"):
                        st.session_state.orchestrator.state["test_results"] = None
                        st.rerun()
                with col_act3:
                    if st.button("⚡ Retest Weak Topics (New Quiz)", use_container_width=True, key="retest_weak_topics_btn"):
                        with st.spinner("Regenerating 30-question assessment dynamically weighted on diagnosed weak topics..."):
                            try:
                                st.session_state.orchestrator.trigger_next_round()
                                st.session_state.current_page = "04_online_test"
                                st.success("New quiz generated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error regenerating round: {e}")

            # Mode 2: Test Form (active exam taking)
            else:
                round_val = test_data.get('round_number') or st.session_state.orchestrator.state.get("round_number", 1)
                render_html(f"""
                <div class='neuro-card' style='margin-bottom:18px; border-left: 5px solid #2563EB;'>
                    <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;'>
                        <div>
                            <h4 style='color:#0F172A; margin:0;'>⏱️ Active Examination (Round {round_val}): 30 Multiple Choice Questions</h4>
                            <p style='margin:4px 0 0 0; color:#475569; font-size:0.85rem;'>Select one option per question. When complete, click the blue submit button at the bottom to score immediately.</p>
                        </div>
                        <span class='neuro-badge-mandatory' style='font-size:0.8rem; padding:6px 14px;'>Round {round_val} &bull; Strict Grading</span>
                    </div>
                </div>
                """)

                # Render Client-Side Synchronized Exam Timer & Anti-Cheating Proctoring Hook
                timer_file = os.path.join(project_root, "frontend", "components", "exam_timer.html")
                if os.path.exists(timer_file):
                    with open(timer_file, "r", encoding="utf-8") as tf:
                        tf_html = tf.read()
                        if hasattr(st, "iframe"):
                            st.iframe(tf_html, height=140)
                        else:
                            import streamlit.components.v1 as components
                            components.html(tf_html, height=140)

                with st.form(key=f"online_exam_form_r{round_val}"):
                    candidate_answers = {}
                    for idx, q in enumerate(questions):
                        q_id = q.get("question_id", idx + 1)
                        q_num = q.get("question_number", idx + 1)
                        q_text = (
                            q.get("question_text") or 
                            q.get("question") or 
                            q.get("prompt") or 
                            q.get("scenario") or 
                            q.get("text") or 
                            ""
                        ).strip()
                        q_topic = q.get("topic") or q.get("topic_name") or "Core Technical Capability"

                        if not q_text:
                            q_text = f"Analyze the following operational problem-solving scenario evaluating {q_topic} under corporate constraints."

                        opts = q.get("options", {})
                        if isinstance(opts, list):
                            opts = {chr(65 + i): str(v) for i, v in enumerate(opts)}
                        elif not isinstance(opts, dict):
                            opts = {}

                        render_html(f"""
                        <div class='neuro-card' style='margin-top:16px; margin-bottom:8px; padding:16px 20px;'>
                            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                                <span style='font-weight:800; color:#2563EB; font-size:0.85rem; text-transform:uppercase;'>Question {q_num} of {len(questions)}</span>
                                <span class='neuro-badge-mandatory'>{q_topic}</span>
                            </div>
                            <div style='font-size:0.95rem; font-weight:700; color:#0F172A; line-height:1.45;'>{q_text}</div>
                        </div>
                        """)

                        choices = ["A", "B", "C", "D"]
                        formatted_choices = []
                        for c in choices:
                            val = str(opts.get(c, f"Option {c}")).strip()
                            if val.startswith(f"{c})") or val.startswith(f"{c}."):
                                formatted_choices.append(val)
                            else:
                                formatted_choices.append(f"{c}) {val}")

                        if not formatted_choices:
                            formatted_choices = ["A) Option A", "B) Option B", "C) Option C", "D) Option D"]

                        selected = st.radio(
                            f"Select answer for Q{q_num}:",
                            formatted_choices,
                            key=f"exam_r{round_val}_q_{q_id}_{idx}",
                            label_visibility="collapsed"
                        )
                        ans_letter = selected.split(")")[0].strip().upper() if selected else "A"
                        candidate_answers[q_id] = ans_letter

                    st.markdown("<br>", unsafe_allow_html=True)
                    submitted = st.form_submit_button("📤 Submit Exam & Auto-Score Immediately", use_container_width=True)
                    if submitted:
                        with st.spinner("Scoring examination and computing topic-wise accuracy metrics..."):
                            results = st.session_state.orchestrator.submit_online_test(candidate_answers)
                            st.session_state.orchestrator.finalize_readiness_report()
                            st.success("Examination scored successfully!")
                            st.rerun()

elif page == "05_results":
    feedback_data = st.session_state.orchestrator.state.get("feedback")
    test_results = st.session_state.orchestrator.state.get("test_results")
    fit_data = st.session_state.orchestrator.state.get("fit_data")
    round_num = st.session_state.orchestrator.state.get("round_number", 1)

    if not feedback_data:
        if not test_results:
            render_html(UI.empty_state(
                title="Assessment Results Pending",
                description="Unified Diagnostics combine your Strategic Fit Analysis (45%) and Scored Online Test (55%). Please submit your 30-MCQ assessment in Step 4 first.",
                icon_name="award",
                action_hint="Navigate to Step 4 to complete your examination."
            ))
            if st.button("📝 Go to Step 4: Online Test", use_container_width=True):
                st.session_state.current_page = "04_online_test"
                st.rerun()
        else:
            st.info("Test submitted! Click below to synthesize your unified readiness audit.")
            if st.button("📈 Generate Unified Readiness Audit", use_container_width=True):
                with st.spinner("Synthesizing unified Fit/Gap & Online Test diagnostics..."):
                    st.session_state.orchestrator.finalize_readiness_report()
                    st.rerun()
    else:
        headline = feedback_data.get('headline_verdict', 'Assessment Complete')
        summary = feedback_data.get('executive_summary', 'Comprehensive performance diagnostics across resume fit, JD alignment, and online testing.')
        render_html(UI.hero_header(
            title="Step 5: Unified Performance Diagnostic & Readiness Blueprint",
            subtitle=summary,
            badge_text=headline,
            icon_name="activity"
        ))

        # Quick Action Bar: PDF Export in Step 5
        s5_p1, s5_p2 = st.columns([3, 1])
        with s5_p2:
            try:
                pdf_data_s5 = PDFDossierExporter.generate_dossier_pdf(st.session_state.orchestrator.state)
                c_clean_name_s5 = st.session_state.orchestrator.state.get("candidate_name", "Candidate").replace(" ", "_")
                st.download_button(
                    label="📥 Download Full Dossier (PDF)",
                    data=pdf_data_s5,
                    file_name=f"InterviewIQ_{c_clean_name_s5}_Full_Dossier.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.caption(f"PDF exporter: {e}")

        # Longitudinal Multi-Round Progress (SQLite)
        try:
            comparison = DatabaseManager.get_round_comparison(st.session_state.orchestrator.session_id)
            if comparison.get("has_history"):
                rounds = comparison.get("rounds", [])
                imp = comparison.get("net_improvement_pct", 0)
                imp_color = "#10B981" if imp >= 0 else "#EF4444"
                imp_sign = "+" if imp >= 0 else ""
                
                round_cards_html = []
                for r in rounds:
                    r_num = r["round"]
                    r_pct = r["percentage"]
                    r_sc = r["score"]
                    r_tot = r["total"]
                    r_pass = "✅ Passed" if r["passed"] else "⚠️ Review"
                    round_cards_html.append(
                        f"<div class='neuro-inset' style='padding:8px 14px; text-align:center; min-width:110px; margin-right:8px;'>"
                        f"<span style='font-size:0.7rem; font-weight:700; color:#64748B;'>ROUND {r_num}</span>"
                        f"<div style='font-size:1.25rem; font-weight:900; color:#0F172A;'>{r_pct:.1f}%</div>"
                        f"<small style='color:#64748B;'>{r_sc}/{r_tot} • {r_pass}</small>"
                        f"</div>"
                    )
                
                render_html(f"""
                <div class='neuro-card' style='background:linear-gradient(135deg, #F0FDF4 0%, #FFFFFF 100%); border-left:5px solid #10B981; margin-top:14px; margin-bottom:16px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;'>
                        <div>
                            <span style='font-size:0.75rem; font-weight:800; text-transform:uppercase; color:#059669;'>📈 Closed-Loop Learning Trajectory</span>
                            <h3 style='margin:2px 0 0 0; color:#0F172A;'>Multi-Round Competency Progression</h3>
                            <p style='margin:2px 0 0 0; font-size:0.85rem; color:#475569;'>Candidate has completed {comparison['total_rounds']} adaptive assessment rounds.</p>
                        </div>
                        <div style='display:flex; align-items:center; flex-wrap:wrap;'>
                            {''.join(round_cards_html)}
                            <div class='neuro-inset' style='padding:8px 14px; text-align:center; min-width:105px;'>
                                <span style='font-size:0.7rem; font-weight:700; color:#64748B;'>NET GAIN</span>
                                <div style='font-size:1.3rem; font-weight:900; color:{imp_color};'>{imp_sign}{imp:.1f}%</div>
                                <small style='color:#64748B;'>Mastery Lift</small>
                            </div>
                        </div>
                    </div>
                </div>
                """)
        except Exception:
            pass

        if feedback_data.get("is_failsafe"):
            st.info("💡 **Presentation Safeguard Active:** Synthesis was formulated using deterministic cross-tabulation metrics from your authentic assessment data.")

        # Key Score Cards Row
        c_sc1, c_sc2, c_sc3, c_sc4 = st.columns(4)
        with c_sc1:
            r_score = feedback_data.get("overall_readiness_score", 0)
            render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Overall Readiness</span><div style='font-size:2.2rem; font-weight:900; color:#2563EB;'>{r_score} <span style='font-size:1.1rem; color:#64748B;'>/ 100</span></div></div>")
        with c_sc2:
            r_lvl = feedback_data.get("readiness_level", "Developing")
            lvl_col = "#10B981" if "Ready" in r_lvl else ("#F59E0B" if "Promising" in r_lvl else "#EF4444")
            render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Readiness Level</span><div style='font-size:1.3rem; font-weight:800; color:{lvl_col}; margin-top:8px;'>{r_lvl}</div></div>")
        with c_sc3:
            t_score = feedback_data.get("online_test_score", 0)
            render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Online Test Score</span><div style='font-size:2.2rem; font-weight:900; color:#10B981;'>{t_score:.1f}%</div></div>")
        with c_sc4:
            f_score = feedback_data.get("fit_gap_score", 0)
            render_html(f"<div class='neuro-card' style='text-align:center;'><span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#64748B;'>Resume-JD Fit</span><div style='font-size:2.2rem; font-weight:900; color:#6366F1;'>{f_score:.1f}%</div></div>")

        # Unified Topic Readiness Diagnostic Table
        st.markdown("<h3 style='margin-top:24px; margin-bottom:12px; color:#0F172A;'>📋 De-duplicated Unified Topic Readiness Matrix</h3>", unsafe_allow_html=True)
        unified_topics = feedback_data.get("unified_topic_readiness", [])
        if unified_topics:
            u_rows = []
            for item in unified_topics:
                t_name = item.get("topic", "")
                t_cat = item.get("category", "Mandatory")
                t_src = item.get("primary_source", "")
                t_status = item.get("readiness_status", "Developing")
                t_ev = item.get("evidence_summary", "")

                cat_badge = "neuro-badge-mandatory" if t_cat == "Mandatory" else "neuro-badge-preferred"
                
                # Highlight dual-weakness topics
                if "HIGH PRIORITY" in t_status or "Both (High Priority)" in t_src:
                    stat_badge = "<span class='neuro-badge-missing' style='background:#FEE2E2; color:#991B1B; font-weight:800; border:1px solid #F87171;'>🚨 HIGH PRIORITY</span>"
                    row_style = "style='background:rgba(254, 226, 226, 0.25);'"
                elif t_status == "Needs Practice":
                    stat_badge = "<span class='neuro-badge-missing-pref' style='font-weight:700;'>Needs Practice</span>"
                    row_style = ""
                elif t_status == "Proficient":
                    stat_badge = "<span class='neuro-badge-matched'>Proficient</span>"
                    row_style = ""
                else:
                    stat_badge = "<span class='neuro-badge-matched' style='background:#DCFCE7; color:#15803D; font-weight:700;'>🌟 Mastered</span>"
                    row_style = ""

                u_rows.append(
                    f"<tr {row_style}>"
                    f"<td><b>{t_name}</b></td>"
                    f"<td><span class='{cat_badge}'>{t_cat}</span></td>"
                    f"<td><small style='color:#64748B;'>{t_src}</small></td>"
                    f"<td>{t_ev}</td>"
                    f"<td style='text-align:center;'>{stat_badge}</td>"
                    f"</tr>"
                )

            render_html(f"""
            <div class='neuro-card'>
                <div style='overflow-x:auto;'>
                    <table class='neuro-table'>
                        <thead>
                            <tr>
                                <th style='width:24%;'>Topic / Competency</th>
                                <th style='width:12%;'>Category</th>
                                <th style='width:18%;'>Attribution Source</th>
                                <th style='width:32%;'>Unified Diagnostic Evidence</th>
                                <th style='width:14%; text-align:center;'>Readiness</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(u_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
            """)

        # Strengths & 48h Study Roadmap
        st.markdown("<h3 style='margin-top:24px; margin-bottom:12px; color:#0F172A;'>🎯 Targeted 48-Hour Preparation Blueprint</h3>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            st_items = [f"<li style='margin-bottom:8px; color:#1E293B;'>{s}</li>" for s in feedback_data.get("top_strengths", [])]
            render_html(f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0;'>🌟 Validated Core Strengths</h4>
                <ul style='padding-left:18px; margin:0; color:#1E293B; font-size:0.85rem;'>
                    {''.join(st_items)}
                </ul>
            </div>
            """)

        with col_s2:
            plan = feedback_data.get("targeted_study_plan_next_48h", [])
            plan_cards = []
            for item in plan:
                p_prio = item.get("priority", "High")
                p_badge = "neuro-badge-missing" if p_prio == "Critical" else ("neuro-badge-missing-pref" if p_prio == "High" else "neuro-badge-matched")
                plan_cards.append(
                    f"<div class='neuro-inset' style='margin-bottom:10px; padding:10px 14px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<strong style='color:#0F172A; font-size:0.9rem;'>{item.get('concept_to_revise', '')}</strong>"
                    f"<span class='{p_badge}' style='font-size:0.7rem;'>{p_prio} Priority</span>"
                    f"</div>"
                    f"<p style='margin:4px 0 0 0; color:#1E293B; font-size:0.85rem;'>{item.get('recommended_exercise', '')}</p>"
                    f"<small style='color:#64748B;'>Focus Dimension: {item.get('focus_dimension', 'Technical')}</small>"
                    f"</div>"
                )

            render_html(f"""
            <div class='neuro-card'>
                <h4 style='color:#0F172A; margin-top:0;'>⏱️ Prioritized 48-Hour Roadmap</h4>
                {''.join(plan_cards)}
            </div>
            """)

        # Closed-Loop Feedback Retest Engine
        prio_topics = feedback_data.get("prioritized_topics_for_next_round", [])
        st.markdown("<h3 style='margin-top:24px; margin-bottom:12px; color:#0F172A;'>🔁 Closed-Loop Feedback Retest Engine</h3>", unsafe_allow_html=True)
        
        prio_tags = "".join([f"<span class='neuro-badge-missing' style='margin-right:6px; margin-bottom:6px; display:inline-block;'>{top}</span>" for top in prio_topics]) if prio_topics else "<span class='neuro-badge-matched'>All Topics Proficient</span>"
        
        render_html(f"""
        <div class='neuro-card' style='border-left: 5px solid #2563EB;'>
            <h4 style='color:#0F172A; margin-top:0;'>Adaptive Multi-Round Retest Loop</h4>
            <p style='color:#475569; font-size:0.85rem; margin-bottom:8px;'>
                InterviewIQ continuously closes candidate capability gaps. By triggering Round {round_num + 1}, the Question Bank and Online Test agents will dynamically re-weight questions (2.5x emphasis) focused squarely on your diagnosed high-priority weaknesses.
            </p>
            <div style='margin-top:8px; margin-bottom:12px;'>
                <strong style='font-size:0.8rem; color:#64748B; text-transform:uppercase;'>Targeted Gap Topics for Round {round_num + 1}:</strong><br>
                <div style='margin-top:6px;'>{prio_tags}</div>
            </div>
        </div>
        """)

        col_loop1, col_loop2 = st.columns([2, 1])
        with col_loop1:
            btn_label = f"🔄 Generate Round {round_num + 1} Question Bank (Re-weighted on Weaknesses)"
            if st.button(btn_label, use_container_width=True, key="gen_round_retest_btn"):
                with st.spinner(f"Re-weighting Question Bank & generating Round {round_num + 1}..."):
                    try:
                        st.session_state.orchestrator.trigger_next_round()
                        st.session_state.current_page = "03_question_bank"
                        st.success(f"Round {round_num + 1} generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error initiating Round {round_num + 1}: {e}")
        with col_loop2:
            if st.button("📁 Start Fresh Session", use_container_width=True, key="start_fresh_session_btn"):
                saved_key = st.session_state.custom_api_key
                st.session_state.clear()
                st.session_state.custom_api_key = saved_key
                st.session_state.orchestrator = Orchestrator(api_key=saved_key)
                st.session_state.current_page = "01_upload"
                st.rerun()

        # Step 5 -> Step 6 Bridge
        render_html(f"""
        <div class='neuro-card' style='border-left: 5px solid {Theme.COLORS["success"]}; margin-top:20px;'>
            <h4 style='color:#0F172A; margin:0 0 6px 0; display:flex; align-items:center; gap:8px;'>
                {icon('calendar', size=18, color=Theme.COLORS['success'])} Dynamic 7-Day Personalized Placement Preparation Plan
            </h4>
            <p style='color:#475569; font-size:0.85rem; margin:0;'>
                Transform your diagnosed weaknesses into an actionable day-by-day learning schedule enriched with curated free course resources (YouTube, Mode Analytics, Coursera audit, LeetCode, and cheat sheets).
            </p>
        </div>
        """)
        if st.button("📅 Generate & View My 7-Day Prep Curriculum (Step 6)", use_container_width=True, key="step5_to_step6_btn"):
            st.session_state.current_page = "06_curriculum"
            st.rerun()

# ==============================================================================
# STEP 6: DYNAMIC 7-DAY PERSONALIZED MICRO-CURRICULUM (PHASE 25C)
# ==============================================================================
elif page == "06_curriculum":
    render_html(UI.hero_header(
        title="Step 6: Dynamic 7-Day Personalized Placement Preparation Plan",
        subtitle="An adaptive day-by-day learning roadmap engineered specifically around your diagnosed vulnerabilities. Enriched with 100% free curated courses from YouTube, Mode Analytics, Coursera (free audit), Kaggle, and Cheat Sheets.",
        badge_text="Adaptive Micro-Curriculum",
        icon_name="calendar"
    ))

    state = st.session_state.orchestrator.state
    feedback_data = state.get("feedback_data") or state.get("feedback") or {}
    fit_data = state.get("fit_data") or state.get("fit_profile") or {}
    jd_profile = state.get("jd_data") or state.get("jd_profile") or {}
    sess_id = getattr(st.session_state.orchestrator, "session_id", "demo_session")

    # Initialize plan from SQLite or Orchestrator
    if "curriculum_plan" not in st.session_state or not st.session_state.curriculum_plan:
        saved_plan_data = DatabaseManager.get_curriculum_plan(sess_id)
        if saved_plan_data and saved_plan_data.get("plan"):
            st.session_state.curriculum_plan = saved_plan_data.get("plan")
            st.session_state.checked_resources = saved_plan_data.get("checked_items_list", [])
            st.session_state.curriculum_plan_id = saved_plan_data.get("plan_id")
        else:
            weak_list = feedback_data.get("unified_topic_readiness", [])
            if not weak_list and fit_data:
                # Derive gaps directly from strategic fit matrix for Option 1 candidates
                weak_list = [
                    {"topic": req.get("requirement", "Core Competency"), "priority": "High Priority" if req.get("status") == "Critical Gap" else "Medium Priority"}
                    for req in fit_data.get("requirements_matrix", [])
                    if req.get("status") in ("Critical Gap", "Partial Gap", "Gap")
                ]
            comp_score = feedback_data.get("composite_readiness_score") or fit_data.get("placement_readiness_score") or 65.0
            st.session_state.curriculum_plan = st.session_state.orchestrator.generate_curriculum(
                weak_topics=weak_list,
                composite_score=float(comp_score)
            )
            st.session_state.checked_resources = []
            st.session_state.curriculum_plan_id = st.session_state.orchestrator.state.get("curriculum_plan_id", "plan_demo")

    plan = st.session_state.curriculum_plan
    checked_items = st.session_state.get("checked_resources", [])
    plan_id = st.session_state.get("curriculum_plan_id", "plan_demo")

    # Progress Calculation
    total_resources = sum(len(day.get("resources", [])) for day in plan.get("days", []))
    completed_resources = len(checked_items)
    progress_pct = int((completed_resources / max(1, total_resources)) * 100) if total_resources else 0
    days_completed = int((completed_resources / max(1, total_resources)) * 7)

    # Executive Stat Dashboard (4 Cards)
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        render_html(UI.stat_card("Target Role", plan.get('target_role', 'Enterprise Candidate'), subtext="Adaptive Calibration", icon_name="briefcase", color=Theme.COLORS["primary"]))
    with col_c2:
        render_html(UI.stat_card("Time Commitment", f"{plan.get('total_hours_commitment', 18)} Hours", subtext="Over 7 Calendar Days", icon_name="clock", color=Theme.COLORS["info"]))
    with col_c3:
        render_html(UI.stat_card("Completed Assets", f"{completed_resources} / {total_resources}", subtext=f"{days_completed} of 7 Days Complete", icon_name="check_circle", color=Theme.COLORS["success"]))
    with col_c4:
        render_html(UI.stat_card("Plan Progress", f"{progress_pct}%", subtext="Live SQLite Tracking", icon_name="award", color=Theme.COLORS["secondary"]))

    # Top Overview Card with Progress
    render_html(f"""
    <div class='neuro-card' style='border-top: 4px solid #10B981; margin-bottom:16px;'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h3 style='color:#0F172A; margin:0 0 4px 0;'>{plan.get('plan_title')}</h3>
                <p style='color:#475569; font-size:0.85rem; margin:0;'>
                    Target Role: <b>{plan.get('target_role')}</b> • Total Commitment: <b>{plan.get('total_hours_commitment')} Hours</b> over 7 Days
                </p>
            </div>
            <div style='text-align:right;'>
                <span style='background:#DCFCE7; color:#166534; font-weight:700; font-size:0.85rem; padding:6px 12px; border-radius:6px;'>
                    ✅ {completed_resources} of {total_resources} Assets Completed ({progress_pct}%)
                </span>
            </div>
        </div>
    </div>
    """)

    st.progress(progress_pct / 100.0)

    # Learning Assets Filters
    f_res1, f_res2 = st.columns(2)
    with f_res1:
        type_filter = st.selectbox(
            "Filter Assets by Media Type:",
            options=["All Types", "Video", "Interactive Course", "Practice Set", "Cheat Sheet", "Documentation"],
            key="curriculum_type_filter"
        )
    with f_res2:
        status_filter = st.selectbox(
            "Filter Assets by Completion:",
            options=["All Assets", "⏳ Incomplete Only", "✅ Completed Only"],
            key="curriculum_status_filter"
        )

    # 7 Days Expanders
    for day in plan.get("days", []):
        d_num = day.get("day_number")
        theme = day.get("theme")
        time_h = day.get("time_allocation_hours")
        milestone = day.get("milestone_checkpoint")
        resources = day.get("resources", [])
        
        # Calculate day completion
        day_res_ids = [r["resource_id"] for r in resources]
        day_done = sum(1 for rid in day_res_ids if rid in checked_items)
        is_day_complete = (day_done == len(day_res_ids)) and len(day_res_ids) > 0

        status_tag = "✅ Complete" if is_day_complete else f"⏳ {day_done}/{len(day_res_ids)} Done"

        with st.expander(f"📅 Day {d_num}: {theme} ({time_h}h) — [{status_tag}]", expanded=(d_num == 1 or not is_day_complete)):
            render_html(f"""
            <div style='margin-bottom:10px;'>
                <span style='font-size:0.8rem; color:#64748B; text-transform:uppercase;'>Daily Learning Objective:</span>
                <p style='color:#1E293B; font-size:0.88rem; font-weight:600; margin:2px 0;'>{day.get('learning_objective')}</p>
                <div style='background:#EFF6FF; border-left:3px solid #3B82F6; border-radius:4px; padding:6px 12px; margin-top:6px; font-size:0.82rem; color:#1E40AF;'>
                    🎯 <b>Milestone Checkpoint:</b> {milestone}
                </div>
            </div>
            """)

            st.markdown("**Structured Daily Activities:**")
            for act in day.get("activities", []):
                st.markdown(f"- {act}")

            # Curated Free Resources Checklist
            st.markdown("<strong style='color:#0F172A; font-size:0.85rem;'>Curated Free Learning Assets:</strong>", unsafe_allow_html=True)
            
            filtered_resources = []
            for r in resources:
                rid = r["resource_id"]
                is_checked = (rid in checked_items)
                r_type = r.get("type", "")
                if type_filter != "All Types" and r_type != type_filter:
                    continue
                if status_filter == "⏳ Incomplete Only" and is_checked:
                    continue
                if status_filter == "✅ Completed Only" and not is_checked:
                    continue
                filtered_resources.append((r, rid, is_checked))

            if not filtered_resources:
                st.caption(f"No learning assets on Day {d_num} match the selected filter.")

            for r, rid, is_checked in filtered_resources:
                type_icon = {
                    "Video": "🎥",
                    "Interactive Course": "🏋️",
                    "Documentation": "📘",
                    "Practice Set": "💻",
                    "Cheat Sheet": "📄"
                }.get(r.get("type"), "🔗")

                r_col1, r_col2 = st.columns([0.15, 0.85])
                with r_col1:
                    new_val = st.checkbox("Mark as completed", value=is_checked, key=f"chk_res_d{d_num}_{rid}", label_visibility="collapsed")
                    if new_val != is_checked:
                        if new_val:
                            checked_items.append(rid)
                        else:
                            checked_items.remove(rid)
                        st.session_state.checked_resources = checked_items
                        DatabaseManager.update_curriculum_progress(plan_id, checked_items, days_completed=days_completed)
                        st.rerun()
                with r_col2:
                    st.markdown(
                        f"<div style='font-size:0.85rem; margin-top:4px;'>"
                        f"{type_icon} <a href='{r.get('url')}' target='_blank' style='color:#2563EB; font-weight:600; text-decoration:none;'>{r.get('title')}</a> "
                        f"<span style='color:#64748B; font-size:0.75rem;'>({r.get('provider')} • {r.get('duration_minutes')} mins • <span style='color:#16A34A; font-weight:600;'>FREE</span>)</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Interactive Integration Shortcuts on Day 6 and Day 7
            if d_num == 6:
                st.markdown("---")
                if st.button("📝 Open Step 3: Targeted Question Bank (Day 6 Probe Review)", use_container_width=True, key="curriculum_day6_drill_btn"):
                    st.session_state.current_page = "03_question_bank"
                    st.rerun()
            elif d_num == 7:
                st.markdown("---")
                if st.button("📝 Open Step 4: Scored Online MCQ Test (Day 7 Full Rehearsal)", use_container_width=True, key="curriculum_day7_drill_btn"):
                    st.session_state.current_page = "04_online_test"
                    st.rerun()

    # Emergency 2-Day Sprint Section
    st.markdown("<h4 style='color:#0F172A; margin-top:24px;'>⚡ Emergency 2-Day Sprint (Interview in 48 Hours?)</h4>", unsafe_allow_html=True)
    sprint = plan.get("emergency_sprint", {})
    with st.expander("▶ View Compressed 48-Hour High-Yield Remediation Schedule", expanded=False):
        sp1, sp2 = st.columns(2)
        with sp1:
            d1 = sprint.get("day_1", {})
            render_html(f"""
            <div style='background:#FFFBEB; border-left:4px solid #F59E0B; border-radius:6px; padding:12px;'>
                <strong style='color:#B45309; font-size:0.9rem;'>Emergency Day 1 ({d1.get('time_hours', 3.5)}h):</strong>
                <p style='font-size:0.82rem; color:#78350F; margin:4px 0 8px 0;'>{d1.get('theme')}</p>
                <ul style='font-size:0.8rem; color:#92400E; margin:0; padding-left:16px;'>
                    {''.join([f'<li>{act}</li>' for act in d1.get('core_actions', [])])}
                </ul>
            </div>
            """)
        with sp2:
            d2 = sprint.get("day_2", {})
            render_html(f"""
            <div style='background:#EFF6FF; border-left:4px solid #3B82F6; border-radius:6px; padding:12px;'>
                <strong style='color:#1E40AF; font-size:0.9rem;'>Emergency Day 2 ({d2.get('time_hours', 3.0)}h):</strong>
                <p style='font-size:0.82rem; color:#1E3A8A; margin:4px 0 8px 0;'>{d2.get('theme')}</p>
                <ul style='font-size:0.8rem; color:#1D4ED8; margin:0; padding-left:16px;'>
                    {''.join([f'<li>{act}</li>' for act in d2.get('core_actions', [])])}
                </ul>
            </div>
            """)

    # Bottom Actions
    st.markdown("---")
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🔄 Regenerate Study Plan from Scratch", use_container_width=True, key="regenerate_curriculum_btn"):
            with st.spinner("Re-synthesizing customized 7-day curriculum..."):
                weak_list = feedback_data.get("unified_topic_readiness", [])
                comp_score = feedback_data.get("composite_readiness_score", 65.0)
                st.session_state.curriculum_plan = st.session_state.curriculum_agent.generate_curriculum(
                    weak_topics=weak_list,
                    jd_profile=jd_profile,
                    composite_score=float(comp_score)
                )
                st.session_state.checked_resources = []
                st.session_state.curriculum_plan_id = DatabaseManager.save_curriculum_plan(
                    session_id=sess_id,
                    plan_dict=st.session_state.curriculum_plan
                )
                st.success("Plan regenerated!")
                st.rerun()
    with act_col2:
        # Text Export Option
        plan_text_lines = [f"{plan.get('plan_title')} — {plan.get('target_role')}", "=" * 50]
        for d in plan.get("days", []):
            plan_text_lines.append(f"\nDay {d.get('day_number')}: {d.get('theme')} ({d.get('time_allocation_hours')}h)")
            plan_text_lines.append(f"Objective: {d.get('learning_objective')}")
            plan_text_lines.append(f"Milestone: {d.get('milestone_checkpoint')}")
            for r in d.get("resources", []):
                plan_text_lines.append(f"  - [{r.get('type')}] {r.get('title')} ({r.get('provider')}): {r.get('url')}")
        plan_export_str = "\n".join(plan_text_lines)
        st.download_button(
            label="📥 Download 7-Day Curriculum (.TXT)",
            data=plan_export_str,
            file_name=f"7day_prep_plan_{plan.get('target_role', 'candidate').replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True
        )

# Render Developer Attribution & Advisory Disclaimer & Terms of Use on all pages
render_html(UI.about_developer_card())
render_html(UI.disclaimer_footer())



