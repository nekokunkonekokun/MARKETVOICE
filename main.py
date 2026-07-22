import streamlit as st
import yfinance as yf
from gtts import gTTS
import os

st.title("日経平均先物 相場実況アプリ 🎙️")
st.write("ボタンを押すと、現在の価格と過去4時間の推移、相場の状態を音声で教えてくれます。")

# 更新ボタン
if st.button("最新の相場をチェックして読み上げる"):
    with st.spinner("株価データを取得して音声を作成中..."):
        try:
            # 1. 銘柄コード（日経平均先物：NIY=F）のデータを取得
            ticker_symbol = "NIY=F"
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(period="1d", interval="1h")
            
            # データが十分に取れた場合（現在、1, 2, 3, 4時間前）
            if not hist.empty and len(hist) >= 5:
                current_price = round(hist['Close'].iloc[-1])
                p1_ago = round(hist['Close'].iloc[-2])
                p2_ago = round(hist['Close'].iloc[-3])
                p3_ago = round(hist['Close'].iloc[-4])
                p4_ago = round(hist['Close'].iloc[-5])
                
                # 4時間前との価格差を計算
                diff = current_price - p4_ago
                
                # 相場判定ロジック
                if abs(diff) <= 100:
                    market_trend = "現在はボックス相場です。"
                elif diff > 100:
                    market_trend = f"4時間前と比べて、およそ {diff:,} 円上がっているので、上げ相場です！"
                else:
                    market_trend = f"4時間前と比べて、およそ {abs(diff):,} 円下がっているので、下げ相場です！"
                
                # 読み上げる文章の組み立て
                text = (
                    f"日経平均先物の現在の価格は、およそ {current_price:,} 円です。 "
                    f"過去4時間の推移は、4時間前が {p4_ago:,} 円、"
                    f"3時間前が {p3_ago:,} 円、"
                    f"2時間前が {p2_ago:,} 円、"
                    f"1時間前が {p1_ago:,} 円となっています。 "
                    f"{market_trend}"
                )
                
                # 画面にテキストを表示
                st.success("取得完了！")
                st.write(text)
                
                # 2. gTTSで音声ファイルを作成
                audio_file = "stock_trend.mp3"
                tts = gTTS(text=text, lang='ja')
                tts.save(audio_file)
                
                # 3. Streamlitの音声プレイヤーで再生（自動再生）
                st.audio(audio_file, format="audio/mp3", autoplay=True)
                
            else:
                st.warning("十分な時間足データを取得できませんでした。市場が閉まっている可能性があります。")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

