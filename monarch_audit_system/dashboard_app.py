"""
dashboard_app.py
================
Monarch Analytics — Interactive Plotly Dash Dashboard

Run with: python dashboard_app.py
Then open: http://localhost:8050
"""

import os
import json
import pandas as pd
import numpy as np

try:
    import dash
    from dash import dcc, html, Input, Output
    import plotly.graph_objects as go
    import plotly.express as px
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

CLEAN_DIR = "audit_workspace/cleaned_data"
ANALYSIS_DIR = "audit_workspace/analysis"

# ── Brand Theme ───────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#0D1B2A", "card": "#1B4F72", "border": "#2E86AB",
    "text": "#FFFFFF", "accent": "#F4A261", "green": "#2ECC71",
    "red": "#E63946", "light": "#A8DADC"
}

LAYOUT = dict(
    paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["bg"],
    font=dict(color=COLORS["text"], family="Calibri"),
    margin=dict(l=40, r=40, t=50, b=40),
)


def load_data():
    """Load all cleaned datasets and KPI results."""
    data = {}
    files = {
        "sales": "sales_clean.csv", "marketing": "marketing_clean.csv",
        "customers": "customers_clean.csv", "products": "products_clean.csv",
    }
    for key, fname in files.items():
        path = os.path.join(CLEAN_DIR, fname)
        if os.path.isfile(path):
            data[key] = pd.read_csv(path)

    kpi_path = os.path.join(ANALYSIS_DIR, "kpi_results.json")
    data["kpis"] = json.load(open(kpi_path)) if os.path.isfile(kpi_path) else {}

    leak_path = os.path.join(ANALYSIS_DIR, "revenue_leak_report.json")
    data["leaks"] = json.load(open(leak_path)) if os.path.isfile(leak_path) else {}

    return data


def make_revenue_trend(sales):
    """Monthly revenue trend line chart."""
    won = sales[sales["deal_stage"] == "closed_won"].copy()
    monthly = won.groupby("month")["revenue"].sum().reset_index().sort_values("month")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue"],
        mode="lines+markers", line=dict(color=COLORS["accent"], width=3),
        marker=dict(size=8, color=COLORS["red"]),
        fill="tozeroy", fillcolor="rgba(244,162,97,0.15)", name="Revenue"
    ))
    fig.update_layout(title="Monthly Revenue Trend", **LAYOUT,
                      yaxis=dict(tickprefix="₹", gridcolor="#1B4F72"),
                      xaxis=dict(gridcolor="#1B4F72"))
    return fig


def make_channel_roas(marketing):
    """ROAS by channel bar chart."""
    by_ch = marketing.groupby("channel").agg(
        spend=("spend", "sum"), revenue=("revenue_generated", "sum")
    ).reset_index()
    by_ch["roas"] = (by_ch["revenue"] / by_ch["spend"]).round(2)
    fig = go.Figure(go.Bar(
        x=by_ch["channel"], y=by_ch["roas"],
        marker_color=COLORS["border"], text=by_ch["roas"].apply(lambda x: f"{x:.1f}x"),
        textposition="outside", textfont=dict(color="white")
    ))
    fig.add_hline(y=2, line_dash="dash", line_color=COLORS["red"],
                  annotation_text="2x Target", annotation_font_color=COLORS["red"])
    fig.update_layout(title="ROAS by Channel", **LAYOUT,
                      yaxis=dict(gridcolor="#1B4F72"), xaxis=dict(gridcolor="#1B4F72"))
    return fig


def make_ltv_distribution(customers):
    """Customer LTV distribution histogram."""
    fig = go.Figure(go.Histogram(
        x=customers["total_revenue"], nbinsx=12,
        marker_color=COLORS["border"], marker_line_color="white", marker_line_width=0.5
    ))
    fig.add_vline(x=customers["total_revenue"].mean(), line_dash="dash",
                  line_color=COLORS["accent"],
                  annotation_text=f"Mean ₹{customers['total_revenue'].mean():,.0f}",
                  annotation_font_color=COLORS["accent"])
    fig.update_layout(title="Customer LTV Distribution", **LAYOUT,
                      xaxis=dict(tickprefix="₹", gridcolor="#1B4F72"),
                      yaxis=dict(gridcolor="#1B4F72"))
    return fig


def make_segment_pie(customers):
    """Revenue by segment donut chart."""
    seg = customers.groupby("segment")["total_revenue"].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=seg["segment"], values=seg["total_revenue"], hole=0.45,
        marker=dict(colors=[COLORS["green"], COLORS["accent"], COLORS["red"]]),
        textfont=dict(color="white", size=13)
    ))
    fig.update_layout(title="Revenue by Customer Segment",
                      paper_bgcolor=COLORS["bg"], font=dict(color=COLORS["text"]),
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig


def make_funnel_chart(sales):
    """Sales funnel bar chart."""
    total = len(sales)
    proposals = len(sales[sales["deal_stage"].isin(["proposal", "closed_won", "closed_lost"])])
    won = len(sales[sales["deal_stage"] == "closed_won"])

    fig = go.Figure(go.Bar(
        x=["Total Leads", "Proposals", "Won"],
        y=[total, proposals, won],
        marker_color=[COLORS["border"], COLORS["accent"], COLORS["green"]],
        text=[total, proposals, won], textposition="outside",
        textfont=dict(color="white", size=14)
    ))
    fig.update_layout(title="Sales Funnel", **LAYOUT,
                      yaxis=dict(gridcolor="#1B4F72"), xaxis=dict(gridcolor="#1B4F72"))
    return fig


def build_app(data):
    """Build the Dash application layout and callbacks."""
    app = dash.Dash(__name__, title="Monarch Analytics — Audit Dashboard")
    kpis = data.get("kpis", {})
    leaks = data.get("leaks", {})
    s = kpis.get("sales", {})
    m = kpis.get("marketing", {})
    c = kpis.get("customer", {})
    f = kpis.get("financial", {})

    def kpi_card(label, value, color=COLORS["accent"]):
        return html.Div([
            html.Div(value, style={"fontSize": "28px", "fontWeight": "bold", "color": color}),
            html.Div(label, style={"fontSize": "12px", "color": COLORS["light"], "marginTop": "4px"}),
        ], style={
            "background": COLORS["card"], "borderRadius": "10px", "padding": "16px 20px",
            "border": f"1px solid {COLORS['border']}", "textAlign": "center",
            "minWidth": "140px", "flex": "1"
        })

    app.layout = html.Div(style={"background": COLORS["bg"], "minHeight": "100vh",
                                  "fontFamily": "Calibri, sans-serif", "color": COLORS["text"]}, children=[

        # Header
        html.Div([
            html.Div("MONARCH ANALYTICS", style={"color": COLORS["accent"], "fontSize": "13px",
                                                  "fontWeight": "bold", "marginBottom": "4px"}),
            html.H1("Business Performance Audit Dashboard",
                    style={"color": "white", "margin": "0", "fontSize": "28px"}),
            html.P("Interactive KPI dashboard — Real-time business intelligence",
                   style={"color": COLORS["light"], "margin": "4px 0 0"})
        ], style={"background": "#0a1520", "padding": "24px 40px",
                  "borderBottom": f"2px solid {COLORS['border']}"}),

        # KPI Cards Row
        html.Div([
            kpi_card("Total Revenue", f"₹{s.get('total_revenue', 0):,.0f}"),
            kpi_card("Avg Deal Value", f"₹{s.get('average_deal_value', 0):,.0f}"),
            kpi_card("Win Rate", f"{s.get('lead_conversion_rate', 0)*100:.1f}%"),
            kpi_card("ROAS", f"{m.get('return_on_ad_spend', 0):.1f}x"),
            kpi_card("CAC", f"₹{m.get('customer_acquisition_cost', 0):,.0f}"),
            kpi_card("LTV", f"₹{c.get('customer_lifetime_value', 0):,.0f}"),
            kpi_card("Retention", f"{c.get('retention_rate', 0)*100:.1f}%"),
            kpi_card("Gross Margin", f"{f.get('gross_margin', 0)*100:.1f}%",
                     color=COLORS["green"]),
        ], style={"display": "flex", "gap": "12px", "padding": "20px 40px",
                  "flexWrap": "wrap"}),

        # Charts Row 1
        html.Div([
            html.Div(dcc.Graph(
                figure=make_revenue_trend(data["sales"]),
                style={"height": "350px"}
            ), style={"flex": "2", "background": COLORS["card"],
                      "borderRadius": "10px", "border": f"1px solid {COLORS['border']}",
                      "padding": "10px"}),
            html.Div(dcc.Graph(
                figure=make_funnel_chart(data["sales"]),
                style={"height": "350px"}
            ), style={"flex": "1", "background": COLORS["card"],
                      "borderRadius": "10px", "border": f"1px solid {COLORS['border']}",
                      "padding": "10px"}),
        ], style={"display": "flex", "gap": "16px", "padding": "0 40px 20px"}),

        # Charts Row 2
        html.Div([
            html.Div(dcc.Graph(
                figure=make_channel_roas(data["marketing"]),
                style={"height": "320px"}
            ), style={"flex": "1", "background": COLORS["card"],
                      "borderRadius": "10px", "border": f"1px solid {COLORS['border']}",
                      "padding": "10px"}),
            html.Div(dcc.Graph(
                figure=make_ltv_distribution(data["customers"]),
                style={"height": "320px"}
            ), style={"flex": "1", "background": COLORS["card"],
                      "borderRadius": "10px", "border": f"1px solid {COLORS['border']}",
                      "padding": "10px"}),
            html.Div(dcc.Graph(
                figure=make_segment_pie(data["customers"]),
                style={"height": "320px"}
            ), style={"flex": "1", "background": COLORS["card"],
                      "borderRadius": "10px", "border": f"1px solid {COLORS['border']}",
                      "padding": "10px"}),
        ], style={"display": "flex", "gap": "16px", "padding": "0 40px 20px"}),

        # Revenue Leaks Panel
        html.Div([
            html.H3("⚠️  Revenue Leak Alerts",
                    style={"color": COLORS["red"], "margin": "0 0 12px"}),
            html.Div([
                html.Div([
                    html.Span(f"[{l['impact_score']}/10] ", style={"color": COLORS["red"], "fontWeight": "bold"}),
                    html.Span(l.get("flag", ""), style={"color": COLORS["accent"]}),
                    html.Br(),
                    html.Span(l.get("description", ""), style={"color": COLORS["light"], "fontSize": "13px"}),
                ], style={"padding": "10px 14px", "marginBottom": "8px",
                          "background": "#0D1B2A", "borderLeft": f"3px solid {COLORS['red']}",
                          "borderRadius": "4px"})
                for l in leaks.get("leaks", [])
            ]) if leaks.get("leaks") else html.Div("✅ No revenue leaks detected.",
                                                    style={"color": COLORS["green"]}),
        ], style={"margin": "0 40px 30px", "background": COLORS["card"],
                  "borderRadius": "10px", "padding": "20px",
                  "border": f"1px solid {COLORS['border']}"}),

        # Footer
        html.Div("© Monarch Analytics  |  Confidential Audit Dashboard",
                 style={"textAlign": "center", "padding": "16px",
                        "color": COLORS["light"], "fontSize": "12px",
                        "borderTop": f"1px solid {COLORS['border']}"}),
    ])

    return app


def run_dashboard():
    """Launch the dashboard server."""
    if not DASH_AVAILABLE:
        print("   ⚠️  Dash not installed. Run: pip install dash")
        return

    print("\n📊 Starting Dashboard Server...")
    data = load_data()
    app = build_app(data)
    print("   ✅ Dashboard ready at http://localhost:8050")
    app.run(debug=False, host="0.0.0.0", port=8050)


if __name__ == "__main__":
    run_dashboard()
