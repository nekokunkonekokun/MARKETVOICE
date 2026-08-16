import japanize_matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ページ設定
st.set_page_config(page_title="15分足 勝敗・損益幅分析", layout="wide")

# ブラウザの自動翻訳による 'removeChild' エラーを防止
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

st.title("🎲 CME日経225先物 15分足ギャンブル分析")
st.caption(
    "直近5本・25本の1本ごとの勝敗数と平均変動幅（勝ち幅・負け幅）を可視化します"
)


# データ取得
@st.cache_data(ttl=300)
def load_data():
  symbol = "NIY=F"
  df = yf.download(symbol, period="60d", interval="15m")

  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

  # 1本ごとの前本比差分
  df["Diff"] = df["Close"].diff()
  df["Win_Val"] = np.where(df["Diff"] > 0, df["Diff"], np.nan)
  df["Loss_Val"] = np.where(df["Diff"] < 0, df["Diff"].abs(), np.nan)

  # ローリング計算
  for w in [5, 25]:
    df[f"Win_{w}"] = (df["Diff"] > 0).rolling(w).sum().fillna(0)
    df[f"Loss_{w}"] = (df["Diff"] < 0).rolling(w).sum().fillna(0)
    # 該当期間に勝ち/負けがない場合は0で埋める
    df[f"AvgWin_{w}"] = (
        df["Win_Val"].rolling(w, min_periods=1).mean().fillna(0)
    )
    df[f"AvgLoss_{w}"] = (
        df["Loss_Val"].rolling(w, min_periods=1).mean().fillna(0)
    )

  # 最初のNaN行を除去
  df = df.dropna(subset=["Close"]).copy()
  return df


with st.spinner("最新データを取得中..."):
  df = load_data()

if df.empty:
  st.error("データの取得に失敗しました。時間をおいて再試行してください。")
  st.stop()

latest = df.iloc[-1]

# メトリクス表示
col1, col2 = st.columns(2)


def fmt_val(val):
  """NaN安全な数値フォーマット関数"""
  return f"{val:.1f}" if pd.notnull(val) else "0.0"


with col1:
  st.subheader("■ 直近5本（75分）")
  st.metric(
      label="勝敗",
      value=f"{int(latest['Win_5'])}勝 {int(latest['Loss_5'])}敗",
  )
  st.write(f"**平均勝ち幅:** `{fmt_val(latest['AvgWin_5'])} 円`")
  st.write(f"**平均負け幅:** `{fmt_val(latest['AvgLoss_5'])} 円`")

with col2:
  st.subheader("■ 直近25本（375分）")
  st.metric(
      label="勝敗",
      value=f"{int(latest['Win_25'])}勝 {int(latest['Loss_25'])}敗",
  )
  st.write(f"**平均勝ち幅:** `{fmt_val(latest['AvgWin_25'])} 円`")
  st.write(f"**平均負け幅:** `{fmt_val(latest['AvgLoss_25'])} 円`")

st.divider()

# ----------------------------------------------------
# グラフ描画
# ----------------------------------------------------
# データが200本未満の場合は存在する全データを使用
num_bars = min(len(df), 200)
plot_df = df.iloc[-num_bars:].copy()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

x = np.arange(len(plot_df))
step = 25
tick_indices = x[::step]
tick_labels = plot_df.index[::step].strftime("%m-%d %H:%M")

# 1. 株価チャート
ax1.plot(x, plot_df["Close"], label="日経先物 (NIY=F)", color="black")
ax1.set_xticks(tick_indices)
ax1.set_xticklabels(tick_labels, rotation=15)
ax1.set_title(f"日経225先物 15分足チャート (直近{num_bars}本)")
ax1.set_ylabel("価格 (円)")
ax1.grid(True)
ax1.legend()

# 2. 25本ローリング推移
ax2.plot(x, plot_df["AvgWin_25"], label="直近25本の平均勝ち幅", color="red")
ax2.plot(x, plot_df["AvgLoss_25"], label="直近25本の平均負け幅", color="blue")
ax2.set_xticks(tick_indices)
ax2.set_xticklabels(tick_labels, rotation=15)
ax2.set_title("直近25本における平均勝ち幅 vs 平均負け幅の推移")
ax2.set_ylabel("変動幅 (円)")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
st.pyplot(fig)
