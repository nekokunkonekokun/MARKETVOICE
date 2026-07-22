import requests
import streamlit as st
import yfinance as yf
from gtts import gTTS

st.title("日経平均先物 ＆ さいたま市お天気 実況アプリ 🎙️")


# 気象庁APIからさいたま市（埼玉県: 110000）のデータを取得
@st.cache_data(ttl=600)
def fetch_jma_weather():
    jma_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/110000.json"
    res = requests.get(jma_url)
    if res.status_code == 200:
        return res.json()
    return None


if st.button("最新の相場とさいたまの天気をチェックして読み上げる"):
    with st.spinner("株価とさいたまの気象データを取得中..."):

        # ----------------------------------------------------
        # 1. 株価データの取得（日経平均先物）
        # ----------------------------------------------------
        market_text = "日経平均先物のデータを取得できませんでした。"
        try:
            ticker_symbol = "NIY=F"
            stock = yf.Ticker(ticker_symbol)
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
        except Exception as e:
            st.error(f"株価取得時にエラーが発生しました: {e}")

        # ----------------------------------------------------
        # 2. 気象庁APIからさいたま市の天気情報を取得
        # ----------------------------------------------------
        weather_text = "さいたま市の天気情報を取得できませんでした。"

        try:
            jma_data = fetch_jma_weather()

            if jma_data:
                # 天気テキスト（例: "晴れ 夕方から くもり..."）
                area_forecast = jma_data[0]["timeSeries"][0]["areas"][0]
                condition = area_forecast["weathers"][0].replace("　", " ")

                # 気温データの正確な取得ロジック
                # 週間予報データ（jma_data[1]）から今日の「さいたま」の最高・最低気温を取得
                max_temp, min_temp = None, None
                try:
                    weekly_temps = jma_data[1]["timeSeries"][1]["areas"][0]
                    # さいたま地点の気温配列 (min, maxのペア)
                    min_temp = weekly_temps["tempsMin"][0]
                    max_temp = weekly_temps["tempsMax"][0]
                except (IndexError, KeyError):
                    # 万が一週間予報側から取れなかった場合のフォールバック（短期予報データから抽出）
                    temp_series = jma_data[0]["timeSeries"][2]["areas"][0][
                        "temps"
                    ]
                    if len(temp_series) >= 2:
                        # 配列内の数値を比較して小さい方を最低、大きい方を最高とする
                        valid_temps = [
                            int(t) for t in temp_series if t.replace("-", "").isdigit()
                        ]
                        if valid_temps:
                            min_temp = min(valid_temps)
                            max_temp = max(valid_temps)

                # メッセージ組み立て
                if max_temp and min_temp and max_temp != min_temp:
                    temp_info = (
                        f"最高気温は{max_temp}度、最低気温は{min_temp}度です。"
                    )
                elif max_temp:
                    temp_info = f"最高気温は{max_temp}度です。"
                else:
                    temp_info = ""

                weather_text = (
                    f"本日のさいたま市周辺の天気は「{condition}」です。 "
                    f"{temp_info} 今日も一日がんばりましょう！"
                )
            else:
                st.error("気象庁からのデータ取得に失敗しました。")

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
