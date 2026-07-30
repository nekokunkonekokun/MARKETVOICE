
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib

st.set_page_config(page_title="15分足 勝敗・損益幅分析", layout="wide")

st.title("🎲 CME日経225先物 15分足ギャンブル分析")
st.caption("直近5本・25本の1本ごとの勝敗数と平均変動幅（勝ち幅・負け幅）を可視化します")

# データ取得
@st.cache_data(ttl=300)  # 5分キャッシュ
def load_data():
    symbol = "NIY=F"
    df = yf.download(symbol, period="60d", interval="15m")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['Diff'] = df['Close'].diff()
    df['Win_Val'] = np.where(df['Diff'] > 0, df['Diff'], np.nan)
    df['Loss_Val'] = np.where(df['Diff'] < 0, df['Diff'].abs(), np.nan)
    
    # ローリング計算
    for w in [5, 25]:
        df[f'Win_{w}'] = (df['Diff'] > 0).rolling(w).sum()
        df[f'Loss_{w}'] = (df['Diff'] < 0).rolling(w).sum()
        df[f'AvgWin_{w}'] = df['Win_Val'].rolling(w, min_periods=1).mean()
        df[f'AvgLoss_{w}'] = df['Loss_Val'].rolling(w, min_periods=1).mean()
        
    return df

with st.spinner("最新データを取得中..."):
    df = load_data()

latest = df.iloc[-1]

# メトリクス表示（2列レイアウト）
col1, col2 = st.columns(2)

with col1:
    st.subheader("■ 直近5本（75分）")
    st.metric(
        label="勝敗", 
        value=f"{int(latest['Win_5'])}勝 {int(latest['Loss_5'])}敗"
    )
    st.write(f"**平均勝ち幅:** `{latest['AvgWin_5']:.1f} 円`")
    st.write(f"**平均負け幅:** `{latest['AvgLoss_5']:.1f} 円`")

with col2:
    st.subheader("■ 直近25本（375分）")
    st.metric(
        label="勝敗", 
        value=f"{int(latest['Win_25'])}勝 {int(latest['Loss_25'])}敗"
    )
    st.write(f"**平均勝ち幅:** `{latest['AvgWin_25']:.1f} 円`")
    st.write(f"**平均負け幅:** `{latest['AvgLoss_25']:.1f} 円`")

st.divider()

# グラフ描画
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# 株価チャート
ax1.plot(df.index[-200:], df['Close'].iloc[-200:], label="日経先物 (NIY=F)", color="black")
ax1.set_title("日経225先物 15分足チャート (直近200本)")
ax1.set_ylabel("価格 (円)")
ax1.grid(True)
ax1.legend()

# 25本ローリング推移
ax2.plot(df.index[-200:], df['AvgWin_25'].iloc[-200:], label="直近25本の平均勝ち幅", color="red")
ax2.plot(df.index[-200:], df['AvgLoss_25'].iloc[-200:], label="直近25本の平均負け幅", color="blue")
ax2.set_title("直近25本における平均勝ち幅 vs 平均負け幅の推移")
ax2.set_ylabel("変動幅 (円)")
ax2.grid(True)
ax2.legend()

plt.tight_layout()

# Streamlitに描画
st.pyplot(fig)
