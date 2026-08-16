import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib

# ページ基本設定（スマホ表示を考慮）
st.set_page_config(
    page_title="日経先物 偏差値",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # スマホでサイドバーが画面を塞がないよう自動でたたむ
)

st.title("📈 NIY=F 偏差値・トレンド")

# データ取得＆処理（5分間キャッシュ）
@st.cache_data(ttl=300)
def load_data():
    ticker = "NIY=F"
    df = yf.download(ticker, period="5d", interval="15m", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.tail(92).copy()

    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Tokyo')
    else:
        df.index = df.index.tz_convert('Asia/Tokyo')

    # 偏差値計算
    mean_price = df['Close'].mean()
    std_price = df['Close'].std()
    df['Deviation'] = 50 + 10 * (df['Close'] - mean_price) / std_price

    # トレンド判定ロジック
    close = df['Close']
    close_1 = df['Close'].shift(1)
    close_2 = df['Close'].shift(2)

    cond_up2 = (close > close_1) & (close_1 > close_2)
    cond_up1 = (close > close_1) & ~cond_up2
    cond_down2 = (close < close_1) & (close_1 < close_2)
    cond_down1 = (close < close_1) & ~cond_down2

    df['Mark'] = ''
    df['Status'] = '維持'

    df.loc[cond_up1, ['Mark', 'Status']] = ['▲', '1本上昇 (緑)']
    df.loc[cond_up2, ['Mark', 'Status']] = ['▲▲', '2本連続上昇 (青)']
    df.loc[cond_down1, ['Mark', 'Status']] = ['▼', '1本下落 (橙)']
    df.loc[cond_down2, ['Mark', 'Status']] = ['▼▼', '2本連続下落 (赤)']

    return df, cond_up1, cond_up2, cond_down1, cond_down2

# 更新ボタン（押しやすい位置に配置）
if st.button("🔄 データを最新に更新", use_container_width=True):
    st.cache_data.clear()

with st.spinner("データ取得中..."):
    df, cond_up1, cond_up2, cond_down1, cond_down2 = load_data()

latest = df.iloc[-1]
latest_time = df.index[-1].strftime('%m/%d %H:%M')

st.caption(f"最終更新時間: {latest_time} JST")

# --- 1. 最新ステータス表示（スマホ向け2列×2行レイアウト） ---
col1, col2 = st.columns(2)
with col1:
    st.metric("最新終値", f"{latest['Close']:,.1f}")
with col2:
    st.metric("直近偏差値", f"{latest['Deviation']:.2f}")

col3, col4 = st.columns(2)
with col3:
    st.metric("判定マーク", f"{latest['Mark']}")
with col4:
    st.metric("状態", f"{latest['Status']}")

st.markdown("---")

# --- 2. タブ切り替え（スマホの縦長画面で快適に操作するため） ---
tab1, tab2 = st.tabs(["📊 偏差値チャート", "📋 直近データ表"])

with tab1:
    fig, ax = plt.subplots(figsize=(10, 6))

    # ベースライン
    ax.plot(df.index, df['Deviation'], color='gray', linestyle='-', linewidth=1, alpha=0.5, label='偏差値推移')

    # トレンドプロット
    up1, up2 = df[cond_up1], df[cond_up2]
    down1, down2 = df[cond_down1], df[cond_down2]

    ax.scatter(up1.index, up1['Deviation'], color='green', marker='^', s=80, label='1本上昇 (▲ 緑)', zorder=4)
    ax.scatter(up2.index, up2['Deviation'], color='blue', marker='^', s=120, label='2本連続上昇 (▲▲ 青)', zorder=5)
    ax.scatter(down1.index, down1['Deviation'], color='orange', marker='v', s=80, label='1本下落 (▼ 橙)', zorder=4)
    ax.scatter(down2.index, down2['Deviation'], color='red', marker='v', s=120, label='2本連続下落 (▼▼ 赤)', zorder=5)

    ax.axhline(50, color='black', linestyle='--', alpha=0.6, label='平均 (50)')
    
    # スマホで見やすいフォントサイズ調整
    ax.set_title("15分足 偏差値・トレンドチャート", fontsize=12, fontweight='bold')
    ax.set_xlabel("日時 (JST)", fontsize=9)
    ax.set_ylabel("偏差値", fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 凡例をグラフ下部に配置（スマホでの横幅圧迫を防止）
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.write("▼ 直近10本の詳細")
    display_df = df[['Close', 'Deviation', 'Mark', 'Status']].tail(10).copy()
    display_df.columns = ['終値', '偏差値', 'マーク', '状態']
    
    # 日時フォーマットをスマホ用に短縮表示
    display_df.index = display_df.index.strftime('%m/%d %H:%M')
    
    st.dataframe(
        display_df.style.format({'終値': '{:,.1f}', '偏差値': '{:.2f}'}),
        use_container_width=True
    )

