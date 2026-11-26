"""Investment Bias Detector: decision journal UI (REQ-020, REQ-021, REQ-025).

Run:  streamlit run app.py
Needs GEMINI_API_KEY and GEMINI_MODEL in the environment (same as the eval).
"""

import io
from datetime import date

import pandas as pd

import streamlit as st

from src.journal import db
from src.journal.display import CHECK_NAMES, LABEL_NAMES, highlight_evidence, with_n
from src.journal.importer import import_trades_from
from src.journal.metrics import behavior_metrics, realized_sells
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
tab_new, tab_journal, tab_metrics = st.tabs(["New decision", "Journal", "Behavior"])

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

with tab_metrics:
    st.caption("Computed in Python from your trades (Midas-style average cost). The LLM is not involved.")

    with st.expander("Import trades from CSV"):
        st.markdown("Columns: `date, ticker, market, side, quantity, price, currency, fee` "
                    "(fee optional). Importing the same file again adds nothing.")
        upload = st.file_uploader("CSV file", type="csv")
        if upload and st.button("Import", key="import"):
            text = io.TextIOWrapper(upload, encoding="utf-8-sig", newline="")
            report = import_trades_from(conn, text)
            st.success(f"{report['imported']} imported, {report['duplicates']} already there.")
            for line_no, reason in report["rejected"]:
                st.error(f"Line {line_no}: {reason}")

    trades = pd.DataFrame(db.list_trades(conn))
    if trades.empty:
        st.info("No trades yet. Import a CSV above.")
    else:
        m = behavior_metrics(trades)
        for currency, c in m["by_currency"].items():
            st.subheader(currency)
            days = lambda x: None if x is None else f"{x:.1f} days"
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Median hold, winners**  \n{with_n(days(c['median_hold_days_winners']), c['n_winners'])}")
            col2.markdown(f"**Median hold, losers**  \n{with_n(days(c['median_hold_days_losers']), c['n_losers'])}")
            ratio = None if c["disposition_ratio"] is None else f"{c['disposition_ratio']:.2f}"
            col3.markdown(f"**Losers held / winners held**  \n"
                          f"{with_n(ratio, min(c['n_winners'], c['n_losers']))}")
            st.caption("Above 1 means losing positions are held longer than winning ones (disposition effect).")

            per_month = f"{c['mean_trades_per_month']:.2f} on average"
            st.markdown(f"**Trades per month** · {with_n(per_month, len(c['trades_per_month']))}")
            st.bar_chart(pd.Series(c["trades_per_month"], name="trades"))

        if m["unmatched_sells"]:
            st.warning(f"{len(m['unmatched_sells'])} sell(s) have no earlier buy in your data, so they are "
                       "left out: " + ", ".join(f"{u['ticker']} on {u['date']}" for u in m["unmatched_sells"]))

        with st.expander("Closed positions"):
            sells, _ = realized_sells(trades)
            st.dataframe(sells, hide_index=True)
        with st.expander("All trades"):
            st.dataframe(trades.drop(columns=["row_hash"]), hide_index=True)
