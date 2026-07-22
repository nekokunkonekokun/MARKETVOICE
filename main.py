import streamlit as st
import yfinance as yf
from gtts import gTTS
import requests

st.title("日経平均先物 ＆ お天気 実況アプリ 🎙️")

if st.button("最新の相場と天気をチェックして読み上げる"):
    with st.spinner("株価とさいたまの気象データを取得中..."):
        try:
            # 1. 株価データの取得（日経平均先物）
            ticker_symbol = "NIY=F"
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(period="1d", interval="1h")
            
            market_text = ""
            if not hist.empty and len(hist) >= 5:
                current_price = round(hist['Close'].iloc[-1])
                p4_ago = round(hist['Close'].iloc[-5])
                diff = current_price - p4_ago
                
                if abs(diff) <= 100:
                    market_trend = "現在はボックス相場です。"
                elif diff > 100:
                    market_trend = f"4時間前と比べて、およそ {diff:,} 円上がっているので、上げ相場です！"
                else:
                    market_trend = f"4時間前と比べて、およそ {abs(diff):,} 円下がっているので、下げ相場です！"
                
                market_text = (
                    f"日経平均先物の現在の価格は、およそ {current_price:,} 円です。 "
                    f"{market_trend}"
                )
            else:
                market_text = "日経平均先物のデータを十分に取得できませんでした。"

            # 2. Open-Meteoからさいたま市の天気情報を取得（※ weathercode に修正）
            weather_text = "さいたま市の天気情報を取得できませんでした。"
            weather_url = "https://api.open-meteo.com/v1/forecast?latitude=35.906&longitude=139.638&current=temperature_2m,weathercode&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo"
            
            res = requests.get(weather_url).json()
            
            # デバッグ用にAPIの返り値を確認したい場合は、コメントアウトを外してください
            # st.write("API Response:", res)

            if "current" in res and "daily" in res:
                temp = res["current"]["temperature_2m"]
                w_code = res["current"]["weathercode"]
                
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
                
                # デイリーデータから最高・最低気温を取得
                max_temp = res["daily"]["temperature_2m_max"][0]
                min_temp = res["daily"]["temperature_2m_min"][0]
                
                weather_text = (
                    f"現在のさいたま市の天気は{condition}、気温は{temp}度です。 "
                    f"最高気温は{max_temp}度で、最低気温は{min_temp}度です。 "
                    f"暑いですが、がんばりましょう！"
                )

            # 3. 相場解説と天気予報を合体
            text = f"{market_text} そして、{weather_text}"
            
            st.success("取得完了！")
            st.write(text)
            
            # 4. 音声化して再生
            audio_file = "saitama_stock_weather.mp3"
            tts = gTTS(text=text, lang='ja')
            tts.save(audio_file)
            st.audio(audio_file, format="audio/mp3", autoplay=True)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
