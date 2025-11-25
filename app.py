import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 設定網頁標題
st.set_page_config(page_title="智富羅盤 - Yahoo版", page_icon="📈", layout="wide")

# 側邊欄輸入
with st.sidebar:
    st.header("🔍 股票搜尋")
    ticker_input = st.text_input("輸入代號 (台股請加 .TW)", value="2330.TW")
    if st.button("查詢"): pass

# 核心功能
def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 抓取足夠計算 MA60 的資料
        df = stock.history(period="6mo") 
        
        if df.empty: return None, None
        
        # 1. 計算均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        
        # 2. 計算 KD (9日)
        df['9_High'] = df['High'].rolling(9).max()
        df['9_Low'] = df['Low'].rolling(9).min()
        df['RSV'] = 100 * (df['Close'] - df['9_Low']) / (df['9_High'] - df['9_Low'])
        df['K'] = df['RSV'].ewm(com=2).mean() # 快速計算近似值
        df['D'] = df['K'].ewm(com=2).mean()
        
        return df.iloc[-1], stock.info
    except:
        return None, None

# 執行分析
latest, info = analyze_stock(ticker_input)

if latest is not None:
    # 顯示標題與價格
    st.title(f"{info.get('longName', ticker_input)}")
    st.metric("收盤價", f"{latest['Close']:.2f}", f"{latest['Close']-latest['Open']:.2f}")

    # 分析邏輯
    score = 0
    reasons = []
    
    # 均線判斷
    if latest['Close'] > latest['MA20']:
        score += 30
        reasons.append("✅ 股價站上月線 (MA20)")
    else:
        reasons.append("⚠️ 股價跌破月線")
        
    # KD 判斷
    if latest['K'] > latest['D']:
        score += 20
        reasons.append("✅ KD 黃金交叉")
    else:
        reasons.append("⚠️ KD 死亡交叉")
        
    # 顯示建議卡片
    bg_color = "rgba(40, 167, 69, 0.1)" if score >= 40 else "rgba(220, 53, 69, 0.1)"
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 10px; background-color: {bg_color}; border-left: 5px solid {'green' if score>=40 else 'red'};">
        <h3>AI 建議：{'偏多操作' if score >= 40 else '保守觀望'}</h3>
        <p>{'、'.join(reasons)}</p>
    </div>
    """, unsafe_allow_html=True)

    # 數據表
    col1, col2, col3 = st.columns(3)
    col1.metric("MA5", f"{latest['MA5']:.2f}")
    col2.metric("MA20", f"{latest['MA20']:.2f}")
    col3.metric("K值/D值", f"{int(latest['K'])} / {int(latest['D'])}")
    
    # Yahoo 連結按鈕
    st.markdown("---")
    st.link_button("🔗 前往 Yahoo 股市看法人籌碼", f"https://tw.stock.yahoo.com/quote/{ticker_input}/institutional-trading")

else:
    st.error("找不到資料，請確認代號 (例如 2330.TW)")