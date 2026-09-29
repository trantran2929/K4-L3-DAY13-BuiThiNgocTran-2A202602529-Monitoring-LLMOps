"""Run from the repository root: python -m streamlit run scripts/dashboard.py."""
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config/dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
NUMERIC = ["latency_ms", "ttft_ms", "cost_usd", "tokens_in", "tokens_out", "quality_score"]

st.set_page_config(page_title=CONFIG["title"], layout="wide")
st.markdown("""
<style>
    .stApp {background: #0b1220; color: #e6edf7;}
    .block-container {
        padding: 3.5rem 2.5rem 1.5rem;
        max-width: 1920px;
    }
    [data-testid="stHeadingWithActionElements"] h2 {
        font-size: 1.65rem; padding-top: 0; padding-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    [data-testid="stCaptionContainer"] p {
        color: #a9bad0; font-size: 0.82rem; line-height: 1.55;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #28374e !important;
        border-radius: 14px !important;
    }
    [data-testid="stButton"] button {
        border-radius: 10px; border-color: #365171;
        background: #17283e; color: #e6edf7;
    }
</style>
""", unsafe_allow_html=True)
st.header(CONFIG["title"])
st.caption("Nguồn: data/logs.jsonl · Usage/cost mô phỏng · Quality là heuristic của lab")


def load_logs(path, start, end):
    rows, skipped = [], 0
    if not path.exists():
        return pd.DataFrame(), 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or "ts" not in row or "event" not in row:
                skipped += 1
                continue
            rows.append(row)
        except json.JSONDecodeError:
            skipped += 1
    if not rows:
        return pd.DataFrame(), skipped
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce", format="mixed")
    skipped += int(df["ts"].isna().sum())
    df = df.loc[df["ts"].between(start, end)].copy()
    df["minute"] = df["ts"].dt.floor("min")
    for field in NUMERIC:
        if field not in df:
            df[field] = float("nan")
        df[field] = pd.to_numeric(df[field], errors="coerce")
    for field in ["tool_name", "tool_success", "error_type"]:
        if field not in df:
            df[field] = None
    return df, skipped


def plot(panel, values, bars=False):
    fig, ax = plt.subplots(figsize=(6, 2.5), facecolor="#111c2e")
    ax.set_facecolor("#111c2e")
    try:
        if bars:
            ax.bar(values.index.astype(str), values.to_numpy(), color="#48c7d6", width=0.55, zorder=3)
        else:
            values.plot(ax=ax, color=["#48c7d6", "#a99cff"] if isinstance(values, pd.DataFrame) else "#48c7d6",
                        linewidth=1.8, zorder=3)
            ax.set_xlabel("Time (UTC)")
        threshold = panel["threshold"]
        symbol = "≤" if threshold["operator"] == "lte" else "≥"
        ax.axhline(threshold["value"], color="#ff9c96", linestyle="--", linewidth=1.3,
                   label=f"{threshold['aggregation']} {symbol} {threshold['value']}")
        ax.set_ylabel(panel["unit"])
        ax.tick_params(axis="both", labelsize=8, colors="#b6c6db", length=0, pad=7)
        ax.tick_params(axis="both", which="minor", labelsize=8, colors="#b6c6db", length=0, pad=7)
        ax.xaxis.label.set_color("#b6c6db")
        ax.yaxis.label.set_color("#b6c6db")
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.grid(axis="y", color="#2a3a50", linewidth=0.6, alpha=0.7, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_ylim(bottom=0)
        ax.legend(loc="best", fontsize=7, facecolor="#17263b",
                  edgecolor="#34465e", labelcolor="#dce6f4", framealpha=0.95)
        fig.tight_layout(pad=1.2)
        st.pyplot(fig)
    finally:
        plt.close(fig)


@st.fragment(run_every=CONFIG["refresh_seconds"])
def dashboard():
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(minutes=CONFIG["time_range_minutes"])
    time_column, refresh_column = st.columns([6, 1])
    time_column.caption(f"{CONFIG['time_range_minutes']} phút gần nhất · "
               f"{start:%H:%M:%S}–{end:%H:%M:%S} UTC · "
               f"Refresh {CONFIG['refresh_seconds']} giây · {end:%Y-%m-%d}")
    refresh_column.button("Làm mới")
    df, skipped = load_logs(ROOT / "data/logs.jsonl", start, end)
    if skipped:
        st.warning(f"Bỏ qua {skipped} dòng thiếu dữ liệu hoặc JSON/timestamp không hợp lệ.")
    if df.empty:
        st.info("Chưa có log trong cửa sổ này. Giữ API chạy và chạy python scripts/load_test.py.")
        return
    minutes = pd.date_range(start.floor("min"), end.floor("min"), freq="min")
    for offset in range(0, len(CONFIG["panels"]), 3):
        if offset:
            st.markdown('<div style="height: 8px"></div>', unsafe_allow_html=True)
        columns = st.columns(3, gap="medium")
        for column, panel in zip(columns, CONFIG["panels"][offset:offset + 3]):
            with column.container(border=True):
                st.markdown(f"**{panel['title']}**")
                data = df.loc[df["event"].isin(panel["events"])]
                kind = panel["id"]
                if data.empty:
                    st.info("Chưa có event phù hợp; chưa thể đánh giá ngưỡng.")
                    continue
                if kind == "latency":
                    values = pd.Series({
                        "P50": data.latency_ms.quantile(.50),
                        "P95": data.latency_ms.quantile(.95),
                        "P99": data.latency_ms.quantile(.99),
                        "TTFT P95": data.ttft_ms.quantile(.95),
                    })
                    plot(panel, values, bars=True)
                    st.caption(" · ".join(f"{k}: {v:.1f} ms" for k, v in values.items()))
                elif kind == "traffic":
                    values = data.groupby("minute").size().reindex(minutes, fill_value=0)
                    plot(panel, values.rename("requests/min"))
                    st.caption(f"Tổng: {len(data)} requests · Hai phút biên có thể chưa đủ 60 giây.")
                elif kind == "errors":
                    received = data.loc[data.event.eq("request_received")]
                    failed = data.loc[data.event.eq("request_failed")]
                    rate = len(failed) / len(received) * 100 if len(received) else float("nan")
                    plot(panel, pd.Series({"Error rate": rate}), bars=True)
                    tools = data.loc[data.tool_name.eq("retrieval") & data.tool_success.notna()]
                    success = tools.tool_success.eq(True).mean() * 100 if len(tools) else float("nan")
                    if failed.empty:
                        breakdown_text = "Không có lỗi"
                    else:
                        breakdown = failed.error_type.fillna("unknown").value_counts()
                        breakdown_text = "Breakdown: " + " · ".join(
                            f"{name}: {count}" for name, count in breakdown.items()
                        )
                    st.caption(f"Error: {rate:.2f}% · Retrieval: {success:.2f}% ({len(tools)} mẫu) · "
                               f"{breakdown_text}")
                elif kind == "cost":
                    values = data.groupby("minute").cost_usd.sum().reindex(minutes, fill_value=0)
                    plot(panel, pd.DataFrame({"USD/min": values, "Cumulative USD": values.cumsum()}))
                    st.caption(f"Tổng 60 phút: ${values.sum():.6f} · Ngưỡng áp dụng cho tổng cửa sổ.")
                elif kind == "tokens":
                    values = data[["tokens_in", "tokens_out"]].sum()
                    plot(panel, values, bars=True)
                    st.caption(f"Input: {values.tokens_in:,.0f} · Output: {values.tokens_out:,.0f} tokens")
                elif kind == "quality":
                    value = data.quality_score.mean()
                    plot(panel, pd.Series({"Mean quality": value}), bars=True)
                    st.caption(f"Mean: {value:.3f} / 1.0 · Không phải đánh giá chất lượng bởi con người.")


dashboard()
