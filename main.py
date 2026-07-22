import requests
import streamlit as st
import yfinance as yf
from gtts import gTTS

st.title("日経平均先物 ＆ さいたま市お天気 実況アプリ 🎙️")

if st.button("最新の相場とさいたまの天気をチェックして読み上げる"):
    with st.spinner("株価とさいたまの気象データを取得中..."):

        # ----------------------------------------------------
        # 1. 株価データの取得（独立した例外処理）
        # ----------------------------------------------------
        market_text = "日経平均先物のデータを取得できませんでした。"
        try:
            ticker_symbol = "NIY=F"
            stock = yf.Ticker(ticker_symbol)
            # period="5d" に伸ばしてデータ未取得を防ぐ
            hist = stock.history(period="5d", interval="1h")

            if not hist.empty and len(hist) >= 5:
                current_price = round(hist["Close"].iloc[-1])
                p4_ago = round(hist["Close"].iloc[-5])
                diff = current_price - p4_ago

                if abs(diff) <= 100:
                    market_trend = "現在はボックス相場です。"
                elif diff > 100:
                    market_trend = (
                        f"4時間前と比べて、およそ {diff:,} 円上がっているので、上げ相場です！"
                    )
                else:
                    market_trend = (
                        f"4時間前と比べて、およそ {abs(diff):,} 円下がっているので、下げ相場です！"
                    )

                market_text = (
                    f"日経平均先物の現在の価格は、およそ {current_price:,} 円です。 "
                    f"{market_trend}"
                )
            else:
                st.warning("株価データが十分取得できませんでした（histが空または不十分です）。")
        except Exception as e:
            st.error(f"株価取得時にエラーが発生しました: {e}")

        # ----------------------------------------------------
        # 2. お天気データの取得（独立した例外処理）
        # ----------------------------------------------------
        weather_text = "さいたま市の天気情報を取得できませんでした。"
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=35.906&longitude=139.638&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo"

        try:
            res_raw = requests.get(weather_url)
            
            # APIエラーのチェック
            if res_raw.status_code != 200:
                st.error(f"天気APIのリクエスト失敗 (Status: {res_raw.status_code})")
            else:
                res = res_raw.json()

                if "current" in res and "daily" in res:
                    temp = res["current"]["temperature_2m"]
                    w_code = res["current"]["weather_code"]

                    # 天気コードを日本語に変換
                    if w_code == 0:
                        condition = "快晴"
                    elif w_code in [1, 2, 3]:
                        condition = "曇り"
                    elif w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                        condition = "雨"
                    elif w_code >= 71:
                        condition = "雪"
                    else:
                        condition = "変わりやすい天気"

                    max_temp = res["daily"]["temperature_2m_max"][0]
                    min_temp = res["daily"]["temperature_2m_min"][0]

                    weather_text = (
                        f"現在のさいたま市の天気は{condition}、気温は{temp}度です。 "
                        f"最高気温は{max_temp}度で、最低気温は{min_temp}度です。 "
                        f"暑いですが、がんばりましょう！"
                    )
                else:
                    st.warning("天気APIからの応答データに必要なキーが含まれていません。")
                    st.write("取得レスポンス:", res)

        except Exception as e:
            st.error(f"天気取得時にエラーが発生しました: {e}")

        # ----------------------------------------------------
        # 3. テキストの統合と読み上げ
        # ----------------------------------------------------
        text = f"{market_text} そして、{weather_text}"

        st.success("処理完了！")
        st.write(text)

        try:
            audio_file = "saitama_stock_weather.mp3"
            tts = gTTS(text=text, lang="ja")
            tts.save(audio_file)
            st.audio(audio_file, format="audio/mp3", autoplay=True)
        except Exception as e:
            st.error(f"音声生成時にエラーが発生しました: {e}")
