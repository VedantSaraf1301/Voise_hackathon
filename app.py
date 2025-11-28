import streamlit as st
from PIL import Image
import os
import json
import base64
import io
import textwrap
from typing import Optional, Tuple
from dotenv import load_dotenv
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet

# ======================
# CONFIGURATION
# ======================
st.set_page_config(
    page_title="Smart Diet Analyzer",
    page_icon="🎃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Main background and theme */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Main content container */
    .main .block-container {
        padding: 2rem 3rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2d3748;
        font-weight: 700;
    }
    
    /* Upload box styling */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        border: none;
    }
    
    [data-testid="stFileUploader"] label {
        color: white !important;
        font-weight: 600;
    }
    
    /* Text input styling */
    .stTextInput input {
        border-radius: 10px;
        border: 2px solid #667eea;
        padding: 10px;
        background: rgba(255, 255, 255, 0.9);
        color: #1a202c !important;
        font-weight: 500;
    }
    
    .stTextInput input::placeholder {
        color: #94a3b8 !important;
        opacity: 0.8;
    }
    
    .stTextInput input:focus {
        border-color: #764ba2;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        background: white;
    }
    
    .stTextInput label {
        color: #e2e8f0 !important;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(72, 187, 120, 0.6);
    }
    
    /* Info box styling */
    .stAlert {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 5px solid #0284c7;
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Image styling */
    [data-testid="stImage"] {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Sidebar subheader */
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    /* Warning/Alert boxes */
    .warning-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid #f59e0b;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid #10b981;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "history.json"
ALLOWED_FILE_TYPES = ['png', 'jpg', 'jpeg']
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
MODEL_SETTINGS = {
    'temperature': 0.2,
    'max_tokens': 400,
    'top_p': 0.5
}
LOGO_PATH = "src/logo.png"

# ======================
# CACHED RESOURCES
# ======================
@st.cache_data
def get_logo_base64() -> Optional[str]:
    """Load and cache logo as base64 string"""
    try:
        with open(LOGO_PATH, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

@st.cache_resource
def initialize_groq_client() -> Groq:
    """Initialize and cache Groq API client"""
    load_dotenv()
    if api_key := os.getenv("GROQ_API_KEY"):
        return Groq(api_key=api_key)
    st.error("GROQ_API_KEY not found in environment")
    st.stop()

def load_history():
    if not os.path.exists(DB_FILE): 
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []
    
def save_to_history(analysis_text):
    import re
    from datetime import datetime
    
    cal_match = re.search(r"Total Estimated Calories:.*?(\d+)", analysis_text)
    calories = int(cal_match.group(1)) if cal_match else 0
    
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "calories": calories,
        "summary": analysis_text[:100] + "..."
    }
    
    history = load_history()
    history.append(new_entry)
    
    with open(DB_FILE, 'w') as f:
        json.dump(history, f, indent=4)

# ======================
# CORE FUNCTIONALITY
# ======================
def process_image(uploaded_file: io.BytesIO) -> Optional[Tuple[str, str]]:
    """Process uploaded image to base64 string with format detection"""
    try:
        with Image.open(uploaded_file) as img:
            fmt = img.format or 'PNG'
            buffer = io.BytesIO()
            img.save(buffer, format=fmt)
            return base64.b64encode(buffer.getvalue()).decode('utf-8'), fmt
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return None

def generate_pdf_content(report_text: str, logo_b64: Optional[str]) -> io.BytesIO:
    """Generate PDF report with logo and analysis content"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    if logo_b64:
        try:
            logo_data = base64.b64decode(logo_b64)
            with Image.open(io.BytesIO(logo_data)) as logo_img:
                aspect = logo_img.height / logo_img.width
                max_width = 150
                img_width = min(logo_img.width, max_width)
                img_height = img_width * aspect
                
            story.append(
                ReportLabImage(io.BytesIO(logo_data), width=img_width, height=img_height)
            )
            story.append(Spacer(1, 12))
        except Exception as e:
            st.error(f"Logo processing error: {str(e)}")

    story.extend([
        Paragraph("<b>Nutrition Analysis Report</b>", styles['Title']),
        Spacer(1, 12),
        Paragraph(report_text.replace('\n', '<br/>'), styles['BodyText'])
    ])

    try:
        doc.build(story)
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
    
    buffer.seek(0)
    return buffer

def generate_ai_analysis(client: Groq, image_b64: str, img_format: str, allergies: str = "") -> Optional[str]:
    """Generate nutritional analysis using Groq's vision API"""
    
    allergy_section = ""
    if allergies and allergies.strip():
        allergy_section = f"""
    
    ⚠️ ALLERGY GUARD ACTIVE ⚠️
    User has declared allergies to: {allergies}
    
    CRITICAL: Cross-reference ALL identified ingredients against this allergy list.
    If ANY allergen is detected or suspected:
    - Flag it with 🚨 WARNING symbol
    - Clearly state which allergen was found
    - Indicate confidence level of detection
    - Recommend consulting ingredient labels for packaged items
    """
    
    vision_prompt = textwrap.dedent(f"""
    As an expert nutritionist with advanced image analysis capabilities, analyze the provided food image:

    1. Identify all visible food items
    2. Estimate calorie content considering:
       - Portion size
       - Cooking method
       - Food density
    3. Mark estimates as "approximate" when assumptions are needed
    4. Calculate total meal calories
    {allergy_section}

    Output format:
    - Food Item 1: [Name] — Estimated Calories: [value] kcal
    - ...
    - **Total Estimated Calories:** [value] kcal
    {f"- **🚨 ALLERGY WARNINGS:** [List any detected allergens here]" if allergies else ""}

    Include confidence levels for unclear images and specify limitations.
    """)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/{img_format.lower()};base64,{image_b64}"
                    }}
                ]
            }],
            **MODEL_SETTINGS
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# ======================
# UI COMPONENTS
# ======================
def render_main_content(logo_b64: Optional[str]):
    """Main content layout and interactions"""
    
    # Hero Section with Logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_b64:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="data:image/png;base64,{logo_b64}" width="120" style="border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="text-align: center;">
                <h1 style="color: #667eea; font-size: 3rem; margin-bottom: 0;">🍽️ PlateWise</h1>
                <p style="color: #64748b; font-size: 1.2rem; margin-top: 10px;">AI-Powered Food & Nutrition Analysis</p>
                <p style="color: #94a3b8; font-size: 0.95rem;">Analyze your meals instantly with advanced AI vision technology</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    if analysis := st.session_state.get('analysis_result'):
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            pdf_buffer = generate_pdf_content(analysis, logo_b64)
            st.download_button(
                "📄 Download Report",
                data=pdf_buffer,
                file_name="nutrition_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col3:
            if st.button("🗑️ Clear Analysis", use_container_width=True):
                del st.session_state.analysis_result
                st.rerun()
        
        # Analysis Results
        st.markdown("### 🎯 Nutrition Analysis Report")
        
        # Check for allergy warnings
        if "🚨" in analysis or "WARNING" in analysis.upper():
            st.markdown("""
                <div class="warning-box">
                    <h4 style="color: #f59e0b; margin: 0;">⚠️ Allergy Alert Detected</h4>
                    <p style="margin: 5px 0 0 0; color: #92400e;">Please review the warnings below carefully.</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.info(analysis)
        
        # Success message
        st.markdown("""
            <div class="success-box">
                <p style="margin: 0; color: #065f46;">✅ Analysis completed successfully! Review your nutritional breakdown above.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Welcome message when no analysis
        st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 15px; margin: 2rem 0;">
                <h3 style="color: #0369a1;">👋 Welcome to PlateWise!</h3>
                <p style="color: #64748b; max-width: 600px; margin: 1rem auto;">
                    Upload a photo of your meal using the sidebar to get instant nutritional analysis powered by AI. 
                    Our advanced system can identify ingredients, estimate calories, and detect potential allergens.
                </p>
                <div style="margin-top: 2rem;">
                    <span style="display: inline-block; margin: 0.5rem; padding: 0.5rem 1rem; background: white; border-radius: 20px; color: #667eea;">📸 Upload Image</span>
                    <span style="display: inline-block; margin: 0.5rem; padding: 0.5rem 1rem; background: white; border-radius: 20px; color: #667eea;">🤖 AI Analysis</span>
                    <span style="display: inline-block; margin: 0.5rem; padding: 0.5rem 1rem; background: white; border-radius: 20px; color: #667eea;">📊 Get Results</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Features section
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
                    <h4 style="color: #334155; margin: 0.5rem 0;">Smart Detection</h4>
                    <p style="color: #64748b; font-size: 0.9rem;">Identifies food items and ingredients accurately</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
                    <h4 style="color: #334155; margin: 0.5rem 0;">Calorie Tracking</h4>
                    <p style="color: #64748b; font-size: 0.9rem;">Estimates calories based on portion sizes</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛡️</div>
                    <h4 style="color: #334155; margin: 0.5rem 0;">Allergy Guard</h4>
                    <p style="color: #64748b; font-size: 0.9rem;">Flags potential allergens in your meals</p>
                </div>
            """, unsafe_allow_html=True)

def render_sidebar(client: Groq):
    """Sidebar upload and processing functionality"""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
                <h2 style="color: #e2e8f0; margin: 0;">📤 Upload Meal</h2>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a food image", 
            type=ALLOWED_FILE_TYPES,
            help="Upload a clear photo of your meal for analysis"
        )
        
        # Allergy Guard Section
        st.markdown("---")
        st.markdown("""
            <div style="text-align: center; padding: 0.5rem 0;">
                <h3 style="color: #fbbf24; margin: 0;">🛡️ Allergy Guard</h3>
                <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0.5rem 0;">Protect yourself from allergens</p>
            </div>
        """, unsafe_allow_html=True)
        
        allergies_input = st.text_input(
            "List your allergies",
            placeholder="e.g., Peanuts, Gluten, Dairy, Shellfish",
            help="Enter comma-separated allergens. We'll flag them if detected."
        )
        
        if allergies_input:
            allergies_list = [a.strip() for a in allergies_input.split(',')]
            st.markdown(f"""
                <div style="background: rgba(251, 191, 36, 0.1); padding: 0.75rem; border-radius: 8px; margin-top: 0.5rem;">
                    <p style="color: #fbbf24; font-size: 0.85rem; margin: 0;">🔔 Monitoring for:</p>
                    <p style="color: #e2e8f0; font-size: 0.9rem; margin: 0.25rem 0 0 0;">{', '.join(allergies_list)}</p>
                </div>
            """, unsafe_allow_html=True)

        if not uploaded_file:
            st.markdown("---")
            st.markdown("""
                <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 10px; margin-top: 1rem;">
                    <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0; text-align: center;">
                        💡 <b>Tip:</b> Take photos in good lighting for best results
                    </p>
                </div>
            """, unsafe_allow_html=True)
            return

        try:
            st.image(Image.open(uploaded_file), caption="📸 Your Meal", use_container_width=True)
        except Exception as e:
            st.error(f"Invalid image file: {str(e)}")
            return

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Analyze Meal", use_container_width=True):
            with st.spinner("🤖 AI is analyzing your meal..."):
                if img_data := process_image(uploaded_file):
                    analysis = generate_ai_analysis(client, *img_data, allergies_input)
                    if analysis:
                        st.session_state.analysis_result = analysis
                        save_to_history(analysis)
                        st.rerun()

# ======================
# APPLICATION ENTRYPOINT
# ======================
def main():
    """Main application controller"""
    client = initialize_groq_client()
    logo_b64 = get_logo_base64()
    
    render_main_content(logo_b64)
    render_sidebar(client)

if __name__ == "__main__":
    main()
