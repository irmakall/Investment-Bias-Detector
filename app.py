"""Investment Bias Detector: decision journal UI (REQ-020, REQ-021).

Run:  streamlit run app.py
Needs GEMINI_API_KEY and GEMINI_MODEL in the environment (same as the eval).
"""

from datetime import date

import streamlit as st

from src.journal import db
from src.journal.display import CHECK_NAMES, LABEL_NAMES, highlight_evidence
from src.llm.gemini import analyze
from src.llm.prompt import prompt_hash

DISCLAIMER = "This analysis looks at your reasoning only. It is not financial advice."

st.set_page_config(page_title="Investment Bias Detector", page_icon="🧭")

# A new connection per script run: Streamlit reruns the script on every click, possibly
# in another thread, and a sqlite3 connection must stay in the thread that opened it.
conn = db.connect(db.DB_PATH)


def run_analysis(note_id: int, text: str) -> None:
    """Call the LLM and store whatever comes back: a result or an error."""
    with st.spinner("Analyzing..."):
        try:
            out = analyze(text)
        except RuntimeError as e:              # missing GEMINI_API_KEY / GEMINI_MODEL
            out = {"error": str(e), "model": ""}
    db.add_analysis(conn, note_id, out, prompt_hash())


def show_analysis(note: dict, where: str) -> None:
    """`where` keeps widget keys unique: the same note can appear in both tabs."""
    a = note["analysis"]
    if a is None:
        st.info("Not analyzed yet.")
    elif a["error"]:
        st.error(f"Analysis failed: {a['error']}")
    else:
        st.markdown(f"**Bias:** {LABEL_NAMES.get(a['label'], a['label'])}")
        st.markdown(highlight_evidence(note["text"], a["evidence"]), unsafe_allow_html=True)
        st.markdown(f"**Why:** {a['rationale']}")
        if a["missing_checks"]:
            st.markdown("**Missing checks:** " + ", ".join(CHECK_NAMES.get(c, c) for c in a["missing_checks"]))
        if a["questions"]:
            st.markdown("**Questions to think about:**")
            for q in a["questions"]:
                st.markdown(f"- {q['text']}")
        st.caption(f"{DISCLAIMER} · model {a['model']} · {a['created_at']}")
        return
    if st.button("Analyze again", key=f"retry-{where}-{note['id']}"):
        run_analysis(note["id"], note["text"])
        st.rerun()


st.title("Investment Bias Detector")
tab_new, tab_journal = st.tabs(["New decision", "Journal"])

with tab_new:
    with st.form("new_note", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ticker = c1.text_input("Ticker", placeholder="NVDA")
        market = c2.radio("Market", ["US", "BIST"], horizontal=True)
        side = c3.radio("Side", ["buy", "sell", "hold"], horizontal=True)
        decision_date = st.date_input("Decision date", value=date.today(), max_value=date.today())
        text = st.text_area("Why are you making this decision?", height=160,
                            help="Write in English. No names, account details or portfolio values: "
                                 "the text is sent to Gemini's free tier.")
        submitted = st.form_submit_button("Save & analyze", type="primary")

    if submitted:
        if not ticker.strip() or not text.strip():
            st.warning("Ticker and note are required.")
        else:
            note_id = db.add_note(conn, decision_date.isoformat(), ticker, market, side, text)
            run_analysis(note_id, text)
            st.session_state["last_note_id"] = note_id

    last_id = st.session_state.get("last_note_id")
    if last_id:
        note = next((n for n in db.list_notes(conn) if n["id"] == last_id), None)
        if note:
            st.divider()
            st.subheader(f"{note['ticker']} · {note['side']} · {note['decision_date']}")
            show_analysis(note, where="new")

with tab_journal:
    notes = db.list_notes(conn)
    if not notes:
        st.info("No notes yet. Write your first one in the New decision tab.")
    for note in notes:
        a = note["analysis"]
        badge = LABEL_NAMES.get(a["label"], "–") if a and a["label"] else ("error" if a else "not analyzed")
        with st.expander(f"{note['decision_date']} · {note['ticker']} · {note['side']} · {badge}"):
            show_analysis(note, where="journal")
