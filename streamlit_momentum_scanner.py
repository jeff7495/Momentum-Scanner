
import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

# === CONFIG ===
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
RVOL_LOOKBACK = 20
PRICE_MIN = 1
PRICE_MAX = 20
PERCENT_CHANGE_MIN = 10
REL_VOL_MIN = 5
FLOAT_MAX = 10  # in millions

# Placeholder float values (can be replaced with real API or scraper)
float_data = {'XYZ': 8.2, 'ABC': 7.9, 'TSLA': 800, 'NVDA': 2000}

# === Streamlit UI ===
st.title("Ross Cameron-Style Momentum Scanner")
tickers_input = st.text_input("Enter tickers (comma-separated)", "XYZ,ABC,TSLA,NVDA")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

@st.cache_data
def get_relative_volume(ticker, lookback):
    data = yf.download(ticker, period="30d", interval="1d")
    if data.empty or 'Volume' not in data.columns:
        return 0
    vol_series = data['Volume']
    if len(vol_series) < lookback or vol_series.isnull().all():
        return 0
    avg_vol = vol_series[-lookback:].mean()
    latest_vol = vol_series.iloc[-1]
    return latest_vol / avg_vol if avg_vol else 0

@st.cache_data
def get_news(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}"
    r = requests.get(url)
    articles = r.json().get('articles', [])
    if articles:
        return articles[0]['title']
    return None

@st.cache_data
def scan_tickers(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', 0)
            if price == 0 or prev_close == 0:
                continue
            pct_change = ((price - prev_close) / prev_close) * 100
            rel_vol = get_relative_volume(ticker, RVOL_LOOKBACK)
            float_est = float_data.get(ticker, 999)
            news_headline = get_news(ticker)

            if (
                PRICE_MIN <= price <= PRICE_MAX and
                pct_change >= PERCENT_CHANGE_MIN and
                rel_vol >= REL_VOL_MIN and
                float_est <= FLOAT_MAX and
                news_headline
            ):
                results.append({
                    "Ticker": ticker,
                    "Price": price,
                    "% Change": round(pct_change, 2),
                    "Relative Volume": round(rel_vol, 2),
                    "Float (M)": float_est,
                    "News Headline": news_headline,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            st.warning(f"Error with {ticker}: {e}")
    return pd.DataFrame(results)

if st.button("Run Scanner"):
    df = scan_tickers(tickers)
    if not df.empty:
        st.success("Momentum stocks found!")
        st.dataframe(df)
    else:
        st.info("No qualifying stocks found.")

