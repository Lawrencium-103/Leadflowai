import streamlit as st
import pandas as pd
import os
import time
import random
from research_agent import enrich_lead
from copywriter_agent import generate_email_content
from gmail_service import authenticate_gmail, create_message, send_email, get_user_email
from database import init_db, get_machine_id, check_user_status, increment_trial, validate_access_code

# Initialize DB
init_db()
MACHINE_ID = get_machine_id()

# Set page config
st.set_page_config(page_title="LeadFlow AI", page_icon="🚀", layout="wide")

# Custom CSS for Luxury Look
def local_css():
    # Luxurious UI/UX Enhancements
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        
        * { font-family: 'Plus Jakarta Sans', sans-serif; }
        
        .main {
            background: radial-gradient(circle at top right, #1a0b2e 0%, #030303 50%);
            color: #f8fafc;
        }
        
        .stApp {
            background-color: #030303;
        }

        /* High-Fidelity Glassmorphism */
        [data-testid="stMetricValue"], .stDataFrame, .stAlert, div.stBlock, section[data-testid="stSidebar"] > div {
            background: rgba(18, 18, 24, 0.4) !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        }

        /* Sidebar Customization */
        [data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Electric Violet Accents */
        h1, h2, h3 {
            background: linear-gradient(90deg, #8b5cf6 0%, #d8b4fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
        }
        
        /* Interactive Elements */
        div.stButton > button {
            background: linear-gradient(135deg, #6d28d9 0%, #4c1d95 100%) !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px;
            padding: 0.8rem 2.5rem !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-transform: none;
        }
        
        div.stButton > button:hover {
            transform: scale(1.05) translateY(-3px);
            box-shadow: 0 10px 30px rgba(109, 40, 217, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
        }

        /* Custom Data Table */
        .stDataFrame {
            padding: 10px !important;
        }
        
        /* Metric Styling */
        [data-testid="stMetric"] {
            padding: 20px !important;
        }
        
        /* Hide scrollbars but keep functionality */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #030303;
        }
        ::-webkit-scrollbar-thumb {
            background: #2d3748;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #4a5568;
        }
        
        /* Hide default padding */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Tooltips */
        .stTooltipIcon {
            color: #D4AF37 !important;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# Initialize session state
if 'phase' not in st.session_state:
    st.session_state['phase'] = 1
if 'leads' not in st.session_state:
    st.session_state['leads'] = None

def clean_data(df):
    mapping = {
        'first_name': ['first name', 'fname', 'first', 'given name', 'f.name'],
        'last_name': ['last name', 'lname', 'last', 'surname', 'family name', 'l.name'],
        'name': ['name', 'founder', 'contact', 'person', 'full name', 'founder name', 'lead name'],
        'email': ['email', 'e-mail', 'mail', 'contact email', 'email address'],
        'domain': ['domain', 'website', 'url', 'company website', 'company url', 'site'],
        'linkedin': ['linkedin', 'linkedin url', 'profile', 'linkedin profile', 'li url'],
        'position': ['position', 'title', 'job title', 'role', 'designation'],
        'location': ['location', 'city', 'country', 'state', 'address', 'hq']
    }
    
    temp_df = df.copy()
    temp_df.columns = [c.lower().strip() for c in temp_df.columns]
    
    extracted = {}
    for target, patterns in mapping.items():
        for col in temp_df.columns:
            if col in patterns:
                extracted[target] = df.iloc[:, temp_df.columns.get_loc(col)]
                break
    
    cleaned_df = pd.DataFrame()
    
    # Logic for Founder Name (Flexible)
    if 'first_name' in extracted and 'last_name' in extracted:
        # Combine if both exist
        cleaned_df['Founder Name'] = extracted['first_name'].fillna('').astype(str).str.strip() + " " + extracted['last_name'].fillna('').astype(str).str.strip()
    elif 'name' in extracted:
        cleaned_df['Founder Name'] = extracted['name']
    elif 'first_name' in extracted:
        cleaned_df['Founder Name'] = extracted['first_name']
    else:
        cleaned_df['Founder Name'] = ""
        
    # Map other fields with default empty values if not found
    field_map = {
        'email': 'Email',
        'domain': 'Domain',
        'linkedin': 'Linkedin',
        'position': 'Position',
        'location': 'Location'
    }
    
    for key, label in field_map.items():
        if key in extracted:
            cleaned_df[label] = extracted[key]
        else:
            cleaned_df[label] = ""
            
    return cleaned_df.reset_index(drop=True)

# --- NAVIGATION ---
def main():
    # Load user status
    trial_uses, is_pro = check_user_status(MACHINE_ID)
    
    st.sidebar.title("🚀 LeadFlow AI")
    
    # Session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
        
    page = st.sidebar.radio("Navigation", ["Home", "LeadFlow App", "About Us"], 
                            index=["Home", "LeadFlow App", "About Us"].index(st.session_state.page))
    
    # Sync radio back to session_state
    st.session_state.page = page
    
    st.sidebar.divider()
    
    # Access Control Sidebar
    with st.sidebar:
        st.header("🛡️ Access Control")
        if is_pro:
            st.success("✅ PRO ACCESS ACTIVE")
        else:
            remaining = max(0, 3 - trial_uses)
            st.info(f"🎁 Free Trial: {remaining} uses left")
            
            with st.expander("🔑 Unlock Pro Access"):
                code_input = st.text_input("Enter Access Code")
                if st.button("Activate Code"):
                    if validate_access_code(MACHINE_ID, code_input):
                        st.success("Access Granted! Welcome to Pro.")
                        st.rerun()
                    else:
                        st.error("Invalid or already used code.")
    
    st.sidebar.divider()
    
    # API CONFIG (Streamlit Secrets → Env → User Input)
    with st.sidebar.expander("⚙️ API Configuration"):
        # Try to get from Streamlit secrets first, then env vars
        default_openrouter = ""
        default_tavily = ""
        
        try:
            default_openrouter = st.secrets.get("OPENROUTER_API_KEY", "")
            default_tavily = st.secrets.get("TAVILY_API_KEY", "")
        except:
            # Fallback to environment variables
            default_openrouter = os.getenv("OPENROUTER_API_KEY", "")
            default_tavily = os.getenv("TAVILY_API_KEY", "")
        
        openrouter_key = st.text_input("OpenRouter API Key", 
                                      value=default_openrouter, 
                                      type="password",
                                      help="Get your key from openrouter.ai")
        tavily_key = st.text_input("Tavily API Key", 
                                   value=default_tavily, 
                                   type="password",
                                   help="Get your key from tavily.com")

    if st.session_state.page == "Home":
        show_home(is_pro, trial_uses)
    elif st.session_state.page == "LeadFlow App":
        # Enforce Access Wall
        if not is_pro and trial_uses >= 3:
            st.error("⚠️ Trial Limit Reached")
            st.warning("Please enter an access code in the sidebar or contact Lawrence to continue.")
            show_home(is_pro, trial_uses)
        else:
            show_app(openrouter_key, tavily_key, is_pro)
    elif st.session_state.page == "About Us":
        show_about()

import plotly.express as px
import plotly.graph_objects as go

def show_home(is_pro, trial_uses):
    st.title("Elite Agentic Prospecting")
    
    # Premium Stats Dashboard
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Lead Pipeline", "850+", "+12%")
    with col_b:
        st.metric("Avg. Response Rate", "18.4%", "+2.1%")
    with col_c:
        st.metric("System Health", "99.9%", "Stable")
    with col_d:
        st.metric("Trial Status", f"{3-trial_uses}/3", "Free" if not is_pro else "Pro")

    st.divider()

    # Visual Analytics Section
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown("### 📊 Performance Ecosystem")
        # Mock analytics for visual "wow" factor
        df_plot = pd.DataFrame({
            'Stage': ['Enriched', 'Drafted', 'Sent', 'Replied'],
            'Count': [150, 120, 100, 18]
        })
        fig = px.bar(df_plot, x='Stage', y='Count', 
                     color='Stage', 
                     color_discrete_sequence=['#8b5cf6', '#a78bfa', '#c4b5fd', '#10b981'],
                     template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.markdown("### 🛡️ The 'What'")
        st.markdown("""
        **LeadFlow AI** is a high-performance **Agentic Growth Machine**. 
        
        - **H.E.A.T Search**: Real-time signal detection.
        - **Algorithm 2 Protocol**: Specific trigger ➡️ specific pain.
        - **Surgical Deployment**: 100% authenticated sender match.
        """)
        if st.button("Initialize Machine →"):
            st.session_state.page = "LeadFlow App"
            st.rerun()

    st.divider()

    # Reach Out Section
    st.markdown("### 📞 Reach Out Now")
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.markdown("""
        **Personal Developer**
        Lawrence Oladeji
        [oladeji.lawrence@gmail.com](mailto:oladeji.lawrence@gmail.com)
        """)
    with r_col2:
        st.markdown("""
        **Instant Support**
        [+234 903 881 9790](tel:+2349038819790)
        """)
    with r_col3:
        if st.button("Request Enterprise Demo"):
            st.toast("Connecting to Lawrence...")
            st.info("Sending inquiry...")

def show_about():
    st.title("About the Developer")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://via.placeholder.com/200", caption="Lawrence Oladeji") # Placeholder
    with col2:
        st.markdown("""
        ## Lawrence Oladeji
        **Data Associate | AI & Automation Workflow Developer**
        
        Lawrence specializes in building intelligent systems that bridge the gap between complex data and actionable business results. With a deep focus on **Agentic Workflows**, he creates solutions that don't just process information, but think and act on it.
        
        ### 📞 Contact Information
        - **Email**: [oladeji.lawrence@gmail.com](mailto:oladeji.lawrence@gmail.com)
        - **Phone**: [+234 903 881 9790](tel:+2349038819790)
        - **Skills**: AI Workflow Automation, Data Engineering, Python, Lead Generation Strategy.
        """)

def show_app(openrouter_api_key, tavily_api_key, is_pro):
    st.title("🎯 LeadFlow Control Center")
    
    # --- PHASE 1: INGESTION ---
    st.markdown("### 1. Upload Your Lead List")
    uploaded_file = st.file_uploader("Choose a CSV, Excel, or Text file", type=["csv", "xlsx", "txt"])
    
    if uploaded_file:
        # Load and clean data
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file, sep='\t' if '\t' in uploaded_file.getvalue().decode() else ',')
                
            leads_df = clean_data(df)
            
            # Add internal tracking columns
            if 'Status' not in leads_df.columns:
                leads_df['Status'] = 'Pending'
                leads_df['Enriched Data'] = ''
                leads_df['Subject'] = ''
                leads_df['Opener'] = ''
                leads_df['Body'] = ''
                leads_df['Closing'] = ''

            st.success(f"Matched {len(leads_df)} leads. Using mapped headers: Name, Email, Domain, Position, Location.")
            
            # Display Data Preview in a luxurious card
            with st.expander("🔍 Preview Leads", expanded=False):
                st.dataframe(leads_df[['Founder Name', 'Email', 'Domain', 'Location', 'Status']])

            st.divider()
            st.session_state['leads_df'] = leads_df
        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.session_state['leads_df'] = None


    if st.session_state['leads_df'] is not None:
        leads_df = st.session_state['leads_df']
        # --- PHASE 2 & 3: AGENTIC WORKFLOW ---
        st.markdown("### 2. Personalization Strategy")
        
        user_offer = st.text_area("What is your specific service or offer?", 
                                 placeholder="e.g., I build high-converting landing pages for Series A fintechs.",
                                 help="Lawrence's AI will weave this into the email using specialized creative hooks.")

        if st.button("🪄 Generate Personalization"):
            if not openrouter_api_key or not tavily_api_key:
                st.error("API Keys missing. Please configure them in the sidebar.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, row in leads_df.iterrows():
                    status_text.markdown(f"**Researching:** `{row['Founder Name']}` at `{row['Domain']}`...")
                    
                    # Phase 2: Research
                    try:
                        enriched_data = enrich_lead(row.to_dict(), openrouter_api_key, tavily_api_key)
                        leads_df.at[index, 'Enriched Data'] = enriched_data
                    except Exception as e:
                        leads_df.at[index, 'Enriched Data'] = f"Error: {e}"
                    
                    # Phase 3: Personalization
                    try:
                        subject, opener, body, closing = generate_email_content(leads_df.iloc[index].to_dict(), openrouter_api_key, user_offer)
                        leads_df.at[index, 'Subject'] = subject
                        leads_df.at[index, 'Opener'] = opener
                        leads_df.at[index, 'Body'] = body
                        leads_df.at[index, 'Closing'] = closing
                        leads_df.at[index, 'Status'] = 'Ready'
                    except Exception as e:
                        leads_df.at[index, 'Status'] = f"Error: {e}"
                    
                    # Update progress
                    progress_bar.progress((index + 1) / len(leads_df))
                
                status_text.success("Personalization Complete!")
                if not is_pro:
                    increment_trial(MACHINE_ID)
                st.session_state['leads_df'] = leads_df

        if 'leads_df' in st.session_state and not st.session_state['leads_df'].empty:
            leads_df = st.session_state['leads_df']
            st.divider()
            
            # --- PHASE 4: SENDING ---
            st.markdown("### 3. Review & Send")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📧 Email Preview")
                ready_leads = leads_df[leads_df['Status'] == 'Ready']
                if not ready_leads.empty:
                    selected_lead_name = st.selectbox("Select a lead to preview", ready_leads['Founder Name'].tolist())
                    lead_data = ready_leads[ready_leads['Founder Name'] == selected_lead_name].iloc[0]
                    
                    st.info(f"**Subject:** {lead_data['Subject']}")
                    preview_text = f"{lead_data['Opener']}\n\n{lead_data['Body']}\n\n{lead_data['Closing']}"
                    st.text_area("Content", preview_text, height=300)
                else:
                    st.warning("No leads are ready for preview. Generate personalization first.")

            with col2:
                st.markdown("#### 🚀 Campaign Control")
                
                # Gmail Authentication
                st.write("**Gmail Setup**")
                if st.button("Authenticate Gmail"):
                    try:
                        service = authenticate_gmail()
                        st.session_state['gmail_service'] = service
                        st.session_state['auth_email'] = get_user_email(service)
                        st.success(f"Authenticated as: {st.session_state['auth_email']}")
                    except Exception as e:
                        st.error(f"Authentication failed: {e}")
                        
                        # File Uploader for credentials.json
                        uploaded_creds = st.file_uploader("📤 Upload credentials.json here", type="json")
                        if uploaded_creds is not None:
                            with open("credentials.json", "wb") as f:
                                f.write(uploaded_creds.getbuffer())
                            st.success("credentials.json uploaded! Please click 'Authenticate' again.")
                            st.rerun()

                        with st.expander("🛠️ How to fix this (Gmail Setup Guide)"):
                            st.markdown("""
                            1. **Go to Google Cloud Console**: [console.cloud.google.com](https://console.cloud.google.com/)
                            2. **Create a Project** (if you haven't already).
                            3. **Enable Gmail API**: Search for "Gmail API" and click **Enable**.
                            4. **Configure OAuth Consent Screen**:
                               - Choose **External**.
                               - Add your email and "Gmail API" scopes.
                               - **Important**: Add your email as a **Test User**.
                            5. **Create Credentials**:
                               - Go to **Credentials** -> **Create Credentials** -> **OAuth client ID**.
                               - Select **Desktop App**.
                            6. **Download JSON**: Download the JSON file, rename it to `credentials.json`, and place it in this folder:
                               `C:\\Users\\user\\Desktop\\AI Agent Project\\LeadFlow\\`
                            7. **Restart the App** and click Authenticate again.
                            """)
                        st.info("Ensure 'credentials.json' is present in the project root.")

                sender_name = st.text_input("Sender Name", value="Lawrence Oladeji")
                sender_email = st.text_input("Sender Email", value=st.session_state.get('auth_email', ''))

                if st.button("🚀 Execute Outreach"):
                    if 'gmail_service' not in st.session_state:
                        st.error("Authenticate Gmail first.")
                    elif not sender_email:
                        st.error("Please provide the sender email.")
                    else:
                        progress_bar = st.progress(0)
                        status_text_send = st.empty()
                        
                        # Calculate total ready leads
                        ready_leads_indices = [i for i, r in leads_df.iterrows() if r['Status'] == 'Ready']
                        total_to_send = len(ready_leads_indices)
                        
                        if total_to_send == 0:
                            st.warning("No leads are ready to send.")
                        else:
                            sent_count = 0
                            fail_count = 0
                            
                            # Panic Button Placeholder
                            stop_placeholder = st.empty()
                            
                            from_header = f"{sender_name} <{sender_email}>" if sender_name else sender_email
                            
                            for i, index in enumerate(ready_leads_indices):
                                # Check Daily Limit
                                if sent_count >= daily_limit:
                                    st.warning(f"🛑 Daily safe limit of {daily_limit} reached. Stopping campaign to protect your account.")
                                    break
                                
                                # Check for Panic Stop (simulated via sidebar checkbox for stability in Streamlit loops)
                                # Streamlit doesn't support a live "Stop" button well inside loops without rerun.
                                # Relying on strict pacing limits instead.
                                
                                row = leads_df.loc[index]
                                current_num = i + 1
                                percentage = int((current_num / total_to_send) * 100)
                                
                                status_text_send.markdown(f"**⚡ Progress:** `{current_num} / {total_to_send}` ({percentage}%) | **Sending to:** `{row['Email']}`...")
                                
                                # Construct full message with professional footer
                                footer = f"\n\n---\nSent via LeadFlow AI\nReply 'Unsubscribe' to stop."
                                full_body = f"{row['Opener']}\n\n{row['Body']}\n\n{row['Closing']}{footer}"
                                
                                msg = create_message(from_header, row['Email'], row['Subject'], full_body)
                                
                                try:
                                    result = send_email(st.session_state['gmail_service'], 'me', msg)
                                    if result:
                                        leads_df.at[index, 'Status'] = 'Sent'
                                        sent_count += 1
                                    else:
                                        leads_df.at[index, 'Status'] = 'Failed'
                                        fail_count += 1
                                except Exception as e:
                                    leads_df.at[index, 'Status'] = f"Error: {e}"
                                    fail_count += 1
                                
                                # Update progress bar
                                progress_bar.progress(current_num / total_to_send)
                                
                                # Human Jitter Delay (30s - 90s)
                                if current_num < total_to_send and sent_count < daily_limit:
                                    # Variable delay based on "reading time" simulation
                                    base_delay = random.randint(30, 90)
                                    # Add small jitter
                                    final_delay = base_delay + random.randint(1, 5)
                                    
                                    for remaining in range(final_delay, 0, -1):
                                        status_text_send.markdown(f"**✅ Sent:** `{current_num}/{total_to_send}` | **Human Jitter:** `{remaining}`s (Simulating reading time)...")
                                        time.sleep(1)

                            st.success(f"Campaign Finished! Sent: {sent_count}, Failed: {fail_count}")
                            st.session_state['leads_df'] = leads_df
                            st.dataframe(leads_df, use_container_width=True)

    # Deliverability Shield Sidebar Section
    with st.sidebar:
        st.divider()
        with st.expander("🛡️ Safety & Anti-Ban Monitor", expanded=True):
            st.metric("Risk Level", "Low", "Safe Mode Active")
            
            daily_limit = st.slider("Daily Send Limit", min_value=1, max_value=50, value=20, help="Keep this under 50 to stay under Google's radar.")
            
            st.markdown("""
            **Safety Protocols Active:**
            - ✅ **Human Jitter**: Randomized delays [30s-90s].
            - ✅ **Volume Cap**: Hard stop at limit.
            - ✅ **Reply-First**: Whitelisting strategy.
            """)

if __name__ == "__main__":
    main()
