import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Instant BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Interactive BI Dashboard powered by Gemini AI"}
)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main { padding: 0rem 0rem; }
    .block-container { padding: 1rem 2rem; }
    h1 { color: #1f77b4; margin-bottom: 0.5rem; }
    h2 { color: #2e86de; }
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .insight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

def get_api_key():
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

def get_model_candidates():
    configured_model = os.getenv("GEMINI_MODEL")
    candidates = []
    if configured_model:
        candidates.append(configured_model)

    candidates.extend([
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
    ])

    deduped = []
    for model_name in candidates:
        if model_name and model_name not in deduped:
            deduped.append(model_name)
    return deduped

# Initialize Gemini (will be configured when needed)
def get_gemini_model(model_name):
    api_key = get_api_key()
    if not api_key:
        st.error("Missing API key. Set GOOGLE_API_KEY (preferred) or GEMINI_API_KEY in your .env file.")
        return None

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")
        return None

# --- HELPER FUNCTIONS ---
def get_csv_schema(df):
    schema = "Table Name: 'data'\nColumns:\n"
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().unique()[:3].tolist()
        schema += f"- {col} ({dtype}). Examples: {sample}\n"
    return schema

def ask_gemini(prompt, schema):
    system_prompt = f"""
    You are a SQL and Data Viz expert. Use the schema below to answer the user's question.
    Schema: {schema}
    
    Return ONLY a JSON object with these keys:
    "sql": "The SQL query to run",
    "chart_type": "bar", "line", "pie", or "table",
    "x": "column for x-axis",
    "y": "column for y-axis",
    "insight": "A 1-sentence business takeaway"
    """

    last_error = None
    tried_models = get_model_candidates()

    for model_name in tried_models:
        try:
            model = get_gemini_model(model_name)
            if not model:
                return None

            response = model.generate_content([system_prompt, prompt])
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            last_error = e
            continue

    st.error(f"Gemini model unavailable. Tried: {', '.join(tried_models)}. Last error: {last_error}")
    return None

# --- UI LAYOUT ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Conversational BI Dashboard")
with col2:
    st.write("")
    st.write("")
    theme = st.radio("Theme", ["Light", "Dark"], horizontal=True, label_visibility="collapsed")

st.markdown("""
### Ask natural language questions about your data
Upload a CSV and get instant insights with AI-powered visualizations
""")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings")
    chart_height = st.slider("Chart Height", 300, 600, 400)
    show_sql = st.checkbox("Show Generated SQL", value=True)
    show_stats = st.checkbox("Show Data Statistics", value=True)
    st.divider()
    st.markdown("**Sample Queries:**")
    st.caption("💡 Try asking:\n- What are the top categories?\n- Show me sales trends over time\n- Compare performance by region")

if not get_api_key():
    st.error("❌ API key not found. Add `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env` file")
    st.stop()

# File Upload Section
st.markdown("### 📁 Upload Your Data")
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", label_visibility="collapsed")
with col2:
    st.write("")
    if st.button("📊 Use Demo Data"):
        # Create sample data
        demo_data = pd.DataFrame({
            'Region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West'],
            'Category': ['Electronics', 'Electronics', 'Clothing', 'Clothing', 'Electronics', 'Electronics', 'Clothing', 'Clothing'],
            'Sales': [45000, 32000, 28000, 51000, 39000, 44000, 33000, 47000],
            'Month': ['Jan', 'Jan', 'Jan', 'Jan', 'Feb', 'Feb', 'Feb', 'Feb']
        })
        uploaded_file = demo_data

if uploaded_file is not None:
    # Handle both file objects and DataFrames
    if isinstance(uploaded_file, pd.DataFrame):
        df = uploaded_file
    else:
        df = pd.read_csv(uploaded_file)
    
    schema = get_csv_schema(df)
    
    # Setup In-memory DB
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df.to_sql('data', conn, index=False, if_exists='replace')
    
    # --- Data Overview Section ---
    with st.expander("📋 Data Preview & Statistics", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Preview", "Statistics", "Info"])
        
        with tab1:
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Showing first 10 of {len(df)} rows")
        
        with tab2:
            if show_stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Total Rows", len(df))
                with col2:
                    st.metric("📈 Columns", len(df.columns))
                with col3:
                    numeric_cols = df.select_dtypes(include=['number']).shape[1]
                    st.metric("🔢 Numeric", numeric_cols)
                with col4:
                    missing = df.isnull().sum().sum()
                    st.metric("❓ Missing Values", missing)
                
                st.markdown("**Numeric Columns Summary:**")
                st.dataframe(df.describe(), use_container_width=True)
        
        with tab3:
            st.write(f"**Dataset Info:** {len(df)} rows × {len(df.columns)} columns")
            st.write("**Column Types:**")
            dtype_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null': df.count(),
                'Missing': df.isnull().sum()
            })
            st.dataframe(dtype_info, use_container_width=True)
    
    # --- Query Section ---
    st.markdown("### 💬 Ask a Question About Your Data")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Enter your question:",
            placeholder="e.g., What are the top 5 categories by sales?",
            label_visibility="collapsed"
        )
    with col2:
        st.write("")
        analyze_btn = st.button("🔍 Analyze", use_container_width=True, type="primary")
    
    if analyze_btn and query:
        with st.spinner("🤖 Analyzing with AI..."):
            try:
                # 1. Get SQL and Viz plan from Gemini
                plan = ask_gemini(query, schema)
                
                if not plan:
                    st.error("Failed to get response from Gemini. Please check your API key.")
                    st.stop()
                
                # 2. Execute SQL
                result_df = pd.read_sql_query(plan['sql'], conn)
                
                # 3. Display Results with enhanced styling
                st.markdown(f"### 📈 {query}")
                
                # Insight Box
                st.markdown(f"""
                <div class="insight-box">
                    <b>💡 Key Insight:</b> {plan['insight']}
                </div>
                """, unsafe_allow_html=True)
                
                # Main visualization
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Visualization:**")
                    
                    try:
                        if plan['chart_type'] == 'bar':
                            fig = px.bar(
                                result_df,
                                x=plan['x'],
                                y=plan['y'],
                                title="Bar Chart",
                                height=chart_height,
                                template="plotly_white"
                            )
                            fig.update_traces(marker_color='#667eea')
                        elif plan['chart_type'] == 'line':
                            fig = px.line(
                                result_df,
                                x=plan['x'],
                                y=plan['y'],
                                title="Line Chart",
                                height=chart_height,
                                template="plotly_white",
                                markers=True
                            )
                            fig.update_traces(line_color='#667eea')
                        elif plan['chart_type'] == 'pie':
                            fig = px.pie(
                                result_df,
                                names=plan['x'],
                                values=plan['y'],
                                title="Pie Chart",
                                height=chart_height
                            )
                        else:
                            st.dataframe(result_df, use_container_width=True)
                            fig = None
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as viz_error:
                        st.warning(f"Could not create visualization: {viz_error}")
                        st.dataframe(result_df, use_container_width=True)
                
                with col2:
                    st.markdown("**Data Summary:**")
                    col_a, col_b = st.columns(1)
                    with col_a:
                        st.metric("Rows", len(result_df))
                        st.metric("Columns", len(result_df.columns))
                
                # SQL and Export Section
                with st.expander("🔧 Advanced Options"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if show_sql:
                            st.markdown("**Generated SQL Query:**")
                            st.code(plan['sql'], language="sql")
                    
                    with col2:
                        st.markdown("**Export Results:**")
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name="query_results.csv",
                            mime="text/csv"
                        )
                        
                        # JSON export
                        json_data = result_df.to_json(indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_data,
                            file_name="query_results.json",
                            mime="application/json"
                        )
                    
                    st.markdown("**Full Results Table:**")
                    st.dataframe(result_df, use_container_width=True)
                        
            except Exception as e:
                st.error(f"❌ Could not process query. Error: {str(e)}")
                st.info("Try asking a simpler question or check your data format.")