"""
Visualization Module - Creates interactive charts using Plotly
"""
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def create_chart(chart_type, data, x_col, y_col, title="", height=400, template="plotly_white"):
    """
    Create an interactive chart based on type.
    
    Args:
        chart_type: str ('bar', 'line', 'pie', 'table')
        data: pandas DataFrame
        x_col: str, column name for x-axis
        y_col: str, column name for y-axis
        title: str, chart title
        height: int, chart height in pixels
        
    Returns:
        plotly.graph_objects.Figure or None
    """
    try:
        if chart_type == 'bar':
            fig = px.bar(
                data,
                x=x_col,
                y=y_col,
                title=title,
                height=height,
                template=template
            )
            fig.update_traces(marker_color='#667eea')
            
        elif chart_type == 'line':
            fig = px.line(
                data,
                x=x_col,
                y=y_col,
                title=title,
                height=height,
                template=template,
                markers=True
            )
            fig.update_traces(line_color='#667eea')
            
        elif chart_type == 'pie':
            fig = px.pie(
                data,
                names=x_col,
                values=y_col,
                title=title,
                height=height,
                template=template
            )
            
        else:
            # Unsupported chart type
            return None
        
        return fig
        
    except Exception as e:
        raise RuntimeError(f"Error creating {chart_type} chart: {str(e)}")


def get_styling():
    """Get Streamlit CSS styling for the dashboard."""
    return """
        <style>
        :root{
            --accent-1: #667eea;
            --accent-2: #764ba2;
            --muted: #6b7280;
            --card-bg: #ffffff;
        }
        .stApp { background: linear-gradient(180deg, #f7fbff 0%, #ffffff 100%); }
        .block-container { padding: 1.25rem 2rem; }
        header .decoration { display:none; }
        h1 { color: #0f172a; margin-bottom: 0.25rem; }
        h2 { color: #0b4a6f; }
        .hero {
            display:flex; align-items:center; gap:1rem; margin-bottom:1rem;
        }
        .logo {
            width:64px; height:64px; border-radius:12px; background:linear-gradient(135deg,var(--accent-1),var(--accent-2)); display:flex; align-items:center; justify-content:center; color:white; font-weight:700; font-size:22px;
        }
        .subtitle { color: var(--muted); margin-top:0.25rem }
        .metric-card { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 1.25rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 6px 18px rgba(34,41,47,0.08);
        }
        .metric-value { font-size:20px; font-weight:700 }
        .metric-label { font-size:12px; color: rgba(255,255,255,0.85) }
        .insight-box {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 0.85rem 1rem;
                border-radius: 10px;
                margin: 0.75rem 0;
                box-shadow: 0 6px 18px rgba(34,41,47,0.06);
        }
        .upload-box { border: 1px dashed #e6eef8; padding: 1rem; border-radius: 8px; background: #fbfdff }
        </style>
        """


def get_insight_html(insight_text):
    """Generate HTML for insight box."""
    return f"""
    <div class="insight-box">
        <b>💡 Key Insight:</b> {insight_text}
    </div>
    """
