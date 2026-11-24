"""Visual style: a dark, glassy interface with a soft blue glow.

All the CSS lives here so app.py stays about logic.
"""
import html

import streamlit as st

ACCENT = "#5B8CFF"

STATUS = {
    # status: (color, label)
    "ok": ("#34D399", "Done"),
    "approved": ("#34D399", "Approved by human"),
    "awaiting approval": ("#FBBF24", "Waiting for approval"),
    "denied": ("#F87171", "Denied by human"),
    "blocked": ("#F87171", "Blocked by guardrail"),
    "error": ("#F87171", "Error"),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Instrument+Serif:ital@1&display=swap');

:root {
  --bg: #02050C;
  --panel: rgba(255, 255, 255, 0.035);
  --panel-strong: rgba(255, 255, 255, 0.06);
  --line: rgba(148, 163, 200, 0.16);
  --text: #F3F6FC;
  --muted: rgba(226, 232, 245, 0.62);
  --accent: #5B8CFF;
  --accent-deep: #3D5BF0;
}

html, body, .stApp, [class*="st-"], button, input, textarea, select {
  font-family: 'Geist', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
/* keep Streamlit's icon font for arrows and chevrons */
[data-testid="stIconMaterial"], .material-symbols-rounded {
  font-family: 'Material Symbols Rounded' !important;
}

/* Background: deep navy, a blue glow at the top, and a faint grid */
.stApp {
  background:
    radial-gradient(ellipse 80% 45% at 50% -5%, rgba(61, 91, 240, 0.35), transparent 70%),
    linear-gradient(rgba(148, 163, 200, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 200, 0.045) 1px, transparent 1px),
    var(--bg);
  background-size: 100% 100%, 56px 56px, 56px 56px, 100% 100%;
  color: var(--text);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { opacity: 0.5; }
.block-container { padding-top: 3.5rem; max-width: 1200px; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: rgba(6, 10, 22, 0.92);
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] li { color: var(--muted); margin-bottom: 0.35rem; }

/* Headings and text */
h1, h2, h3 { color: var(--text) !important; letter-spacing: -0.03em; font-weight: 500 !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: var(--muted); }
[data-testid="stWidgetLabel"] p { color: rgba(226, 232, 245, 0.78) !important; }
button p { color: inherit !important; }
.eyebrow {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-style: italic; color: #9DB5FF; font-size: 1.15rem; margin-bottom: 0.5rem;
}

/* Hero */
.hero { text-align: center; margin: 0 auto 2.75rem; max-width: 820px; }
.hero h1 {
  font-size: clamp(2.6rem, 5.5vw, 4.4rem); line-height: 1.02; font-weight: 500 !important;
  letter-spacing: -0.05em; margin: 0.25rem 0 1rem; padding: 0;
}
.hero .accent {
  background: linear-gradient(180deg, #8FB0FF, #4C74FF);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  border-bottom: 2px solid rgba(91, 140, 255, 0.55);
}
.hero p { font-size: 1.15rem; color: var(--muted); max-width: 620px; margin: 0 auto; line-height: 1.55; }

/* Feature cards under the hero */
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 2.5rem; }
.feature {
  background: linear-gradient(180deg, var(--panel-strong), var(--panel));
  border: 1px solid var(--line); border-radius: 16px; padding: 1.1rem 1.2rem;
}
.feature .num {
  width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
  background: rgba(91, 140, 255, 0.14); border: 1px solid rgba(91, 140, 255, 0.4);
  color: #B9CCFF; font-weight: 600; font-size: 0.85rem; margin-bottom: 0.7rem;
}
.feature b { color: var(--text); font-weight: 600; display: block; margin-bottom: 0.2rem; }
.feature span { color: var(--muted); font-size: 0.92rem; line-height: 1.45; }

/* Bordered containers become glass cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(180deg, var(--panel-strong), var(--panel));
  border: 1px solid var(--line) !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 20px 40px -24px rgba(0, 0, 0, 0.8);
}

/* Inputs */
[data-testid="stTextAreaRootElement"], [data-testid="stTextInputRootElement"],
[data-testid="stSelectbox"] [class*="ComboBox"] > div, textarea, input {
  background: rgba(8, 13, 28, 0.85) !important;
  border-color: var(--line) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}

/* Buttons */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 12px; font-weight: 600; letter-spacing: -0.01em;
  border: 1px solid var(--line); background: rgba(255, 255, 255, 0.04); color: var(--text);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover { border-color: rgba(91, 140, 255, 0.6); color: white; }
.stButton > button[kind="primary"] {
  background: linear-gradient(180deg, #6A97FF, var(--accent-deep));
  border: 1px solid rgba(150, 180, 255, 0.55);
  box-shadow: 0 0 0 1px rgba(91, 140, 255, 0.25), 0 8px 28px -6px rgba(76, 116, 255, 0.75);
  color: white;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-1px); }

/* Tabs as pills */
[data-testid="stTabs"] [role="tablist"] { gap: 8px; border-bottom: none !important; box-shadow: none !important; }
[data-testid="stTab"], [data-testid="stTabs"] [role="tab"] {
  background: rgba(255, 255, 255, 0.03) !important; border: 1px solid var(--line) !important;
  border-radius: 999px !important; padding: 6px 18px !important; color: var(--muted) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: rgba(91, 140, 255, 0.16) !important; border-color: rgba(91, 140, 255, 0.6) !important;
  color: white !important;
}
[data-testid="stTabs"] [role="tab"] p { color: inherit !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"], [data-testid="stTabs"] [role="tablist"] > div:empty { display: none !important; }

/* Expanders */
[data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: 12px; background: rgba(0,0,0,0.15); }

/* Agent steps */
.step { display: flex; align-items: center; gap: 12px; }
.step .n {
  min-width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
  background: rgba(91, 140, 255, 0.12); border: 1px solid rgba(91, 140, 255, 0.35);
  color: #B9CCFF; font-weight: 600; font-size: 0.85rem;
}
.step .name { color: var(--text); font-weight: 600; font-family: ui-monospace, 'SF Mono', Menlo, monospace !important; font-size: 0.92rem; }
.badge {
  margin-left: auto; padding: 0.2rem 0.65rem; border-radius: 999px;
  font-size: 0.76rem; font-weight: 600; border: 1px solid;
}

/* Approval card and reply */
.approval-title { font-size: 1.35rem; color: var(--text); font-weight: 500; letter-spacing: -0.02em; }
.amount { color: #FDE68A; font-weight: 600; }
.reply {
  background: linear-gradient(180deg, rgba(91, 140, 255, 0.12), rgba(91, 140, 255, 0.04));
  border: 1px solid rgba(91, 140, 255, 0.35); border-radius: 16px;
  padding: 1.1rem 1.3rem; white-space: pre-wrap; color: var(--text); line-height: 1.6;
}
.empty {
  border: 1px dashed var(--line); border-radius: 16px; padding: 2.2rem 1.5rem;
  text-align: center; color: var(--muted);
}

@media (max-width: 800px) { .features { grid-template-columns: 1fr; } }
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">A support agent you can trust</div>
          <h1>Customer support, resolved by <span class="accent">AI</span>.</h1>
          <p>It looks up orders, checks policy and issues refunds on its own, with guardrails
          in code and a human approval step for anything risky.</p>
        </div>
        <div class="features">
          <div class="feature"><div class="num">1</div><b>Takes real actions</b>
            <span>Calls tools to read orders, search policy, refund and escalate.</span></div>
          <div class="feature"><div class="num">2</div><b>Guardrails in code</b>
            <span>Ownership, refund rules and step limits hold even if the model is tricked.</span></div>
          <div class="feature"><div class="num">3</div><b>Human in the loop</b>
            <span>Refunds over $100 wait for you to approve or deny.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def eyebrow(text):
    st.markdown(f"<div class='eyebrow'>{html.escape(text)}</div>", unsafe_allow_html=True)


def step_header(number, tool, status):
    color, label = STATUS.get(status, ("#94A3B8", status))
    st.markdown(
        f"<div class='step'><div class='n'>{number}</div>"
        f"<div class='name'>{html.escape(tool)}</div>"
        f"<span class='badge' style='color:{color};border-color:{color}55;background:{color}1F'>"
        f"{label}</span></div>",
        unsafe_allow_html=True,
    )


def reply(text):
    st.markdown(f"<div class='reply'>{html.escape(text)}</div>", unsafe_allow_html=True)


def empty(text):
    st.markdown(f"<div class='empty'>{text}</div>", unsafe_allow_html=True)
