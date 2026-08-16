import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib

# ページ基本設定（スマホ表示重視）
st.set_page_config(
    page_title="日経先物 偏差値",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📈 NIY=F 偏差値・トレンド")

# データ取得＆処理（5分間キャッシュ）
@st.cache_data(ttl=300)
def load_data():
    ticker = "NIY=F"
    # 前足・前々足の判定（+2本分）用に少し余裕を持って取得
    df = yf.download(ticker, period="7d", interval="15m", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 日本時間に変換
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Tokyo')
    else:
        df.index = df.index.tz_convert('Asia/Tokyo')

    # トレンド判定ロジック（カット前に計算）
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

    # 最終的に【直近92本】のみを抽出（ここで土日などの空き時間は自然に除去されます）
    df = df.tail(92).copy()

    # 偏差値計算（抽出した92本の中で計算）
    mean_price = df['Close'].mean()
    std_price = df['Close'].std()
    df['Deviation'] = 50 + 10 * (df['Close'] - mean_price) / std_price

    return df

# 更新ボタン
if st.button("🔄 データを最新に更新", use_container_width=True):
    st.cache_data.clear()

with st.spinner("データ取得中..."):
    df = load_data()

# 状態別のマスク再作成（描画用）
cond_up2 = df['Mark'] == '▲▲'
cond_up1 = df['Mark'] == '▲'
cond_down2 = df['Mark'] == '▼▼'
cond_down1 = df['Mark'] == '▼'

latest = df.iloc[-1]
latest_time = df.index[-1].strftime('%m/%d %H:%M')

st.caption(f"最終更新: {latest_time} JST（直近92本表示）")

# --- 1. 最新ステータス表示（スマホ向け2列配置） ---
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

# --- 2. タブ切り替え ---
tab1, tab2 = st.tabs(["📊 偏差値チャート", "📋 直近データ表"])

with tab1:
    fig, ax = plt.subplots(figsize=(10, 5))

    # 土日や空き時間を詰めるため「連番（0〜91）」をX軸として利用
    x_coords = np.arange(len(df))

    # 折れ線（偏差値推移）
    ax.plot(x_coords, df['Deviation'], color='gray', linestyle='-', linewidth=1.2, alpha=0.6)

    # 散布図で色分けマーカーをプロット
    ax.scatter(x_coords[cond_up1], df['Deviation'][cond_up1], color='green', marker='^', s=50, label='1本上(緑)', zorder=4)
    ax.scatter(x_coords[cond_up2], df['Deviation'][cond_up2], color='blue', marker='^', s=80, label='2本連上(青)', zorder=5)
    ax.scatter(x_coords[cond_down1], df['Deviation'][cond_down1], color='orange', marker='v', s=50, label='1本下(橙)', zorder=4)
    ax.scatter(x_coords[cond_down2], df['Deviation'][cond_down2], color='red', marker='v', s=80, label='2本連下(赤)', zorder=5)

    # 平均線 (偏差値50)
    ax.axhline(50, color='black', linestyle='--', alpha=0.5, linewidth=1)

    # X軸の目盛りをすっきり整理（約15本おきに日時を表示）
    step = 15
    tick_indices = list(range(0, len(df), step))
    if (len(df) - 1) not in tick_indices:
        tick_indices.append(len(df) - 1) # 最新足の日時も必ず表示
    
    tick_labels = [df.index[i].strftime('%m/%d %H:%M') for i in tick_indices]
    
    ax.set_xticks(tick_indices)
    ax.set_xticklabels(tick_labels, fontsize=8, rotation=20)

    # グラフ装飾
    ax.set_title("15分足 偏差値トレンド (直近92本)", fontsize=11, fontweight='bold')
    ax.set_ylabel("偏差値", fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # 凡例をシンプルに下部にまとめる
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=4, fontsize=8, frameon=False)

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.write("▼ 直近10本の詳細")
    display_df = df[['Close', 'Deviation', 'Mark', 'Status']].tail(10).copy()
    display_df.columns = ['終値', '偏差値', 'マーク', '状態']
    
    # 日時フォーマットを短く
    display_df.index = display_df.index.strftime('%m/%d %H:%M')
    
    st.dataframe(
        display_df.style.format({'終値': '{:,.1f}', '偏差値': '{:.2f}'}),
        use_container_width=True
    )
