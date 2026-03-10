"""
Streamlit Frontend - Conversational BI Dashboard
Main application entry point
"""
import streamlit as st
import pandas as pd
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

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
    # Allow loading a real CSV for demo via env var SAMPLE_CSV_PATH
    sample_path = os.getenv("SAMPLE_CSV_PATH")
    # Packaged demo CSV inside repo (preferred when present)
    packaged_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'nykaa_marketing.csv')
    if os.path.exists(packaged_path):
        try:
            return pd.read_csv(packaged_path)
        except Exception:
            pass
    if sample_path and os.path.exists(sample_path):
        try:
            return pd.read_csv(sample_path)
        except Exception:
            pass
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

    # --- FILTERS & DEFAULT VISUALIZATIONS ---
    # Parse Date column if present
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        except Exception:
            pass

    st.markdown("### 🔎 Filters & Quick Visualizations")
    with st.container():
        fcol1, fcol2, fcol3 = st.columns([2, 2, 1])

        # Date range filter
        if 'Date' in df.columns and df['Date'].notnull().any():
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
            date_range = fcol1.date_input("Date range", value=(min_date, max_date))
        else:
            date_range = None

        # Campaign Type filter
        if 'Campaign_Type' in df.columns:
            types = sorted(df['Campaign_Type'].dropna().unique().tolist())
            sel_types = fcol2.multiselect("Campaign Type", options=types, default=types)
        else:
            sel_types = None

        # Channel filter (multiselect by detecting substrings)
        if 'Channel_Used' in df.columns:
            all_channels = set()
            for v in df['Channel_Used'].dropna().astype(str):
                for c in [c.strip() for c in v.split(',')]:
                    if c:
                        all_channels.add(c)
            all_channels = sorted(all_channels)
            sel_channels = fcol3.multiselect("Channels", options=all_channels, default=all_channels)
        else:
            sel_channels = None

    # Apply filters
    filtered = df.copy()
    if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered['Date'] >= pd.to_datetime(start)) & (filtered['Date'] <= pd.to_datetime(end))]
    if sel_types is not None:
        filtered = filtered[filtered['Campaign_Type'].isin(sel_types)]
    if sel_channels is not None:
        filtered = filtered[filtered['Channel_Used'].astype(str).apply(lambda s: any(ch in s for ch in sel_channels))]

    # Summary metrics
    col_a, col_b, col_c = st.columns(3)
    total_revenue = int(filtered['Revenue'].sum()) if 'Revenue' in filtered.columns else 0
    total_conversions = int(filtered['Conversions'].sum()) if 'Conversions' in filtered.columns else 0
    total_impressions = int(filtered['Impressions'].sum()) if 'Impressions' in filtered.columns else 0
    conversion_rate = (total_conversions / total_impressions * 100) if total_impressions else 0
    with col_a:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_revenue:,}</div><div class='metric-label'>Total Revenue</div></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_conversions:,}</div><div class='metric-label'>Conversions</div></div>", unsafe_allow_html=True)
    with col_c:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{conversion_rate:.2f}%</div><div class='metric-label'>Conversion Rate</div></div>", unsafe_allow_html=True)

    # Default charts: Top Campaigns by Revenue, Revenue Trend, Channel Breakdown
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        if 'Revenue' in filtered.columns and 'Campaign_ID' in filtered.columns:
            top = filtered.groupby('Campaign_ID', as_index=False)['Revenue'].sum().sort_values('Revenue', ascending=False).head(10)
            fig1 = create_chart('bar', top, 'Campaign_ID', 'Revenue', title='Top 10 Campaigns by Revenue', height=420, template=chart_template)
            st.plotly_chart(fig1, use_container_width=True)
        if 'Date' in filtered.columns and 'Revenue' in filtered.columns:
            trend = filtered.groupby(pd.Grouper(key='Date', freq='M'))['Revenue'].sum().reset_index()
            if not trend.empty:
                fig2 = create_chart('line', trend, 'Date', 'Revenue', title='Monthly Revenue Trend', height=360, template=chart_template)
                st.plotly_chart(fig2, use_container_width=True)

    with chart_col2:
        if 'Channel_Used' in filtered.columns and 'Revenue' in filtered.columns:
            # aggregate revenue by channel (split comma-separated channels)
            rows = []
            for _, r in filtered.iterrows():
                rev = r.get('Revenue', 0)
                for ch in str(r.get('Channel_Used', '')).split(','):
                    ch = ch.strip()
                    if ch:
                        rows.append({'channel': ch, 'revenue': rev})
            if rows:
                chdf = pd.DataFrame(rows).groupby('channel', as_index=False)['revenue'].sum().sort_values('revenue', ascending=False)
                fig3 = create_chart('pie', chdf, 'channel', 'revenue', title='Revenue by Channel', height=600, template=chart_template)
                st.plotly_chart(fig3, use_container_width=True)
