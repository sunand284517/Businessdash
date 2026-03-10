"""
Streamlit Frontend - Conversational BI Dashboard
Main application entry point
"""
import streamlit as st
import pandas as pd
import sys
import os
import json

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import AnalysisEngine
from visualization.charts import create_chart, get_styling, get_insight_html


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Instant BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Interactive BI Dashboard powered by Gemini AI"}
)

st.markdown(get_styling(), unsafe_allow_html=True)


# --- UTILITY FUNCTIONS ---
@st.cache_data
def load_demo_data():
    """Load demo dataset for quick testing."""
    return pd.DataFrame({
        'Region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West'],
        'Category': ['Electronics', 'Electronics', 'Clothing', 'Clothing', 'Electronics', 'Electronics', 'Clothing', 'Clothing'],
        'Sales': [45000, 32000, 28000, 51000, 39000, 44000, 33000, 47000],
        'Month': ['Jan', 'Jan', 'Jan', 'Jan', 'Feb', 'Feb', 'Feb', 'Feb']
    })


# --- UI HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
        # Hero header with logo
        st.markdown(
                """
                <div class="hero">
                    <div class="logo">BI</div>
                    <div>
                        <h1>📊 Conversational BI Dashboard</h1>
                        <div class="subtitle">Ask natural language questions and get instant AI visualizations</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
        )
with col2:
    st.write("")
    st.write("")
    theme = st.radio("Theme", ["Light", "Dark"], horizontal=True, label_visibility="collapsed")

st.markdown("""
### Ask natural language questions about your data
Upload a CSV and get instant insights with AI-powered visualizations
""")


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Settings")
    chart_height = st.slider("Chart Height", 300, 600, 400)
    show_sql = st.checkbox("Show Generated SQL", value=True)
    show_stats = st.checkbox("Show Data Statistics", value=True)
    st.divider()
    st.markdown("**Sample Queries:**")
    st.caption("💡 Try asking:\n- What are the top categories?\n- Show me sales trends over time\n- Compare performance by region")


# --- FILE UPLOAD SECTION ---
    st.markdown("### 📁 Upload Your Data")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.write("")
    if st.button("📊 Use Demo Data"):
        st.session_state.use_demo = True
        uploaded_file = load_demo_data()

# Check API configuration
if not st.session_state.get('engine'):
    engine = None
else:
    engine = st.session_state.engine

if uploaded_file is not None:
    # Handle both file objects and DataFrames
    if isinstance(uploaded_file, pd.DataFrame):
        df = uploaded_file
    else:
        df = pd.read_csv(uploaded_file)
    
    # Initialize analysis engine
    try:
        engine = AnalysisEngine(df)
        st.session_state.engine = engine
        
        if not engine.is_api_configured():
            st.error("❌ API key not found. Add `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env` file")
            st.stop()
    except Exception as e:
        st.error(f"Failed to initialize engine: {str(e)}")
        st.stop()
    
    # --- DATA OVERVIEW SECTION ---
    # Prepare stats for display (ensure available for all tabs)
    if show_stats:
        stats = engine.get_data_stats()
    else:
        stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include='number').columns),
            'missing_values': int(df.isnull().sum().sum())
        }

    with st.expander("📋 Data Preview & Statistics", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Preview", "Statistics", "Info"])
        
        with tab1:
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Showing first 10 of {len(df)} rows")
        
        with tab2:
            if show_stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{stats['rows']}</div><div class='metric-label'>Total Rows</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{stats['columns']}</div><div class='metric-label'>Columns</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{stats['numeric_columns']}</div><div class='metric-label'>Numeric</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{stats['missing_values']}</div><div class='metric-label'>Missing Values</div></div>", unsafe_allow_html=True)
                
                st.markdown("**Numeric Columns Summary:**")
                st.dataframe(df.describe(), use_container_width=True)
        
        with tab3:
            st.write(f"**Dataset Info:** {stats['rows']} rows × {stats['columns']} columns")
            st.write("**Column Types:**")
            dtype_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null': df.count(),
                'Missing': df.isnull().sum()
            })
            st.dataframe(dtype_info, use_container_width=True)
    
    # --- QUERY SECTION ---
    st.markdown("### 💬 Ask a Question About Your Data")
    
    col1, col2 = st.columns([4, 1])
    # set chart template based on theme
    chart_template = "plotly_white" if theme == "Light" else "plotly_dark"

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
                # Get analysis plan from Gemini
                plan = engine.analyze_query(query)
                
                # Execute the analysis
                result_df = engine.execute_analysis(plan)
                
                # --- DISPLAY RESULTS ---
                st.markdown(f"### 📈 {query}")
                st.markdown(get_insight_html(plan['insight']), unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Visualization:**")
                    
                    try:
                        fig = create_chart(
                            plan['chart_type'],
                            result_df,
                            plan['x'],
                            plan['y'],
                            height=chart_height,
                            template=chart_template
                        )
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.dataframe(result_df, use_container_width=True)
                            
                    except Exception as viz_error:
                        st.warning(f"Could not create visualization: {viz_error}")
                        st.dataframe(result_df, use_container_width=True)
                
                with col2:
                    st.markdown("**Data Summary:**")
                    st.metric("Rows", len(result_df))
                    st.metric("Columns", len(result_df.columns))
                
                # --- ADVANCED OPTIONS ---
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
                        
                        json_str = result_df.to_json(orient='records')
                        json_data = json.dumps(json.loads(json_str), indent=2)
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

else:
    st.info("👈 Upload a CSV file or click 'Use Demo Data' to get started!")
