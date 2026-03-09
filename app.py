import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
st.set_page_config(page_title="Instant BI Dashboard", layout="wide")

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
st.title("📊 Conversational BI Dashboard")
st.markdown("Upload a CSV and ask questions like *'Show me total sales by region as a bar chart'*")

if not get_api_key():
    st.warning("API key not found. Add GOOGLE_API_KEY=your_key in .env, then restart Streamlit.")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    schema = get_csv_schema(df)
    
    # Setup In-memory DB
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df.to_sql('data', conn, index=False, if_exists='replace')
    
    query = st.text_input("💬 Ask your data a question:")
    
    if query:
        with st.spinner("Analyzing data..."):
            try:
                # 1. Get SQL and Viz plan from Gemini
                plan = ask_gemini(query, schema)
                
                if not plan:
                    st.error("Failed to get response from Gemini. Please check your API key.")
                    st.stop()
                
                # 2. Execute SQL
                result_df = pd.read_sql_query(plan['sql'], conn)
                
                # 3. Display Results
                st.subheader(f"📈 {query}")
                st.info(f"💡 Insight: {plan['insight']}")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if plan['chart_type'] == 'bar':
                        st.bar_chart(result_df.set_index(plan['x']))
                    elif plan['chart_type'] == 'line':
                        st.line_chart(result_df.set_index(plan['x']))
                    else:
                        st.dataframe(result_df, use_container_width=True)
                
                with col2:
                    st.write("**Generated SQL:**")
                    st.code(plan['sql'], language="sql")
                    
            except Exception as e:
                st.error(f"Could not process query. Error: {e}")