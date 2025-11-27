import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os
import requests
from FinMind.data import DataLoader

# --- 0. 設定與金鑰 ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS 樣式 (核心修復：橫向捲動 + 白底黑字) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_png_as_page_bg(png_file):
    if not os.path.exists(png_file): return
    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str: return
    
    # 使用 format 注入背景圖
    page_bg_img = """
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{0}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* 加上一層半透明遮罩，避免背景太花干擾 */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.3);
        pointer-events: none;
        z-index: 0;
    }}
    </style>
    """.format(bin_str)
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局字體：強制黑色 */
    .stApp { color: #000000; font-family: "Microsoft JhengHei", sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 核心容器：純白不透明卡片 --- */
    div.element-container, div.stMarkdown, div[data-testid="stVerticalBlock"] > div {
        /* 這裡不強制設定所有容器，避免破壞佈局，改為針對特定 class 設定 */
    }

    /* 我們自定義的卡片類別 */
    .white-card {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        border: 1px solid #ccc;
        position: relative;
        z-index: 1;
        opacity: 1 !important; /* 絕對不透明 */
    }
    
    /* 強制卡片內所有文字為黑色 */
    .white-card *, .white-card p, .white-card span, .white-card div, .white-card h2, .white-card h3 {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* --- 1. 搜尋框優化 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important; /* 金色邊框 */
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .stTextInput label {
        color: #ffffff !important; /* 標籤維持白色，因為在背景上 */
        text-shadow: 2px 2px 4px #000;
        font-weight: bold;
        font-size: 1.1rem;
    }

    /* --- 2. 報價卡片排版 --- */
    .stock-header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 10px; }
    .stock-title { font-size: 1.6rem !important; font-weight: 900 !important; margin: 0; }
    .stock-id { font-size: 1.1rem !important; color: #666 !important; font-weight: normal; }
    
    .price-big { font-size: 3.5rem !important; font-weight: 800 !important; line-height: 1; letter-spacing: -1px; margin: 10px 0;}
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr); /* 強制兩欄 */
        gap: 8px 20px;
        border-top: 1px solid #eee;
        padding-top: 10px;
        margin-top: 10px;
    }
    .stat-row { display: flex; justify-content: space-between; align-items: center; }
    .stat-lbl { color: #666 !important; font-size: 0.9rem !important; }
    .stat-val { color: #000 !important; font-weight: bold !important; font-size: 1.05rem !important; }

    /* --- 3. 橫向滑動按鈕列 (重點修正) --- */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* 禁止換行 */
        overflow-x: auto !important;  /* 允許左右滑動 */
        gap: 8px !important;
        background-color: #ffffff !important;
        padding: 10px 5px !important;
        border-radius: 10px !important;
        white-space: nowrap !important; /* 內容不換行 */
        -webkit-overflow-scrolling: touch; /* 手機滑動順暢 */
    }
    /* 隱藏捲軸但保留功能 */
    div[role="radiogroup"]::-webkit-scrollbar { display: none; }
    
    div[role="radiogroup"] label {
        flex: 0 0 auto !important; /* 固定寬度，不壓縮 */
        min-width: 50px !important;
        text-align: center !important;
        padding: 6px 12px !important;
        border-radius: 20px !important;
        background-color: #f0f0f0 !important; /* 未選中：淺灰 */
        border: 1px solid #ddd !important;
        margin: 0 !important;
        cursor: pointer;
    }
    
    div[role="radiogroup"] label p {
        color: #333 !important; /* 未選中：深黑字 */
        font-weight: bold !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
    }
    
    /* 選中狀態 (Streamlit 生成的結構比較複雜，這招通常有效) */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #000000 !important; /* 選中：黑底 */
        border-color: #000000 !important;
    }
    div[role="radiogroup"] label[data-checked="true"] p {
        color: #ffffff !important; /* 選中：白字 */
    }

    /* --- 4. 圖表容器 --- */
    .chart-box {
        background-color: #fff !important;
        border-radius: 12px;
        padding: 5px;
        border: 1px solid #ccc;
    }
    /* Plotly 背景強制白 */
    .js-plotly-plot .plotly .main-svg { background: white !important; }

    /* 標題 */
    h1 { text-shadow: 3px 3px 8px #000; color: white !important; margin-bottom: 15px; text-align: center; font-weight: 900; }
    
    /* 隱藏預設元素 */
    [data-testid="stMetric"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明",
    "3231.TW": "緯創", "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微"
}

@st.cache_data(ttl=3600)
def resolve_ticker(user_input):
    user_input = user_input.strip().upper()
    if user_input.isdigit():
        # 優先嘗試上市
        ticker_tw = f"{user_input}.TW"
        try:
            s = yf.Ticker(ticker_tw)
            if not s.history(period="1d").empty: return ticker_tw, s.info.get('longName', ticker_tw)
        except: pass
        # 再嘗試上櫃
        ticker_two = f"{user_input}.TWO"
        try:
            s = yf.Ticker(ticker_two)
            if not s.history(period="1d").empty: return ticker_two, s.info.get('longName', ticker_two)
        except: pass
        return None, None
    else:
        try:
            s = yf.Ticker(user_input)
            if not s.history(period="1d").empty: return user_input, s.info.get('longName', user_input)
        except: pass
        return None, None

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def generate_report_html(name, ticker, latest, df):
    price = latest['Close']
    ma20 = latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭" if price > ma20 else "空頭"
    kd_stat = "黃金交叉" if k > d else "死亡交叉"
    
    return f"""
    <div class="white-card">
        <h3 style="border-bottom:2px solid #FFD700; padding-bottom:5px; margin-bottom:10px; font-size:1.3rem; font-weight:bold;">📊 分析報告</h3>
        <p><b>趨勢：</b>{trend}格局 (股價 vs 月線)。</p>
        <p><b>指標：</b>KD ({k:.1f}/{d:.1f}) 呈現 <b>{kd_stat}</b>。</p>
        <p><b>建議：</b>{'偏多操作' if price > ma20 and k > d else '保守觀望'}</p>
    </div>
    """

# --- 4. UI 介面 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 卡片 A：搜尋
target_input = st.text_input("🔍 搜尋代號 (如: 2330, 4903)", value="2330")

if target_input:
    with st.spinner("搜尋中..."):
        target, name = resolve_ticker(target_input)
        if not target:
            st.error("❌ 找不到代號，請確認輸入是否正確。")
            st.stop()
else:
    target, name = "2330.TW", "台積電"

try:
    stock = yf.Ticker(target)
    info = stock.info
    if 'name' not in locals(): name = STOCK_NAMES.get(target, info.get('longName', target))
    
    # 卡片 B：報價
    df_fast = stock.history(period="5d")
    if not df_fast.empty:
        latest_fast = df_fast.iloc[-1]
        prev = df_fast['Close'].iloc[-2]
        price = latest_fast['Close']
        chg = price - prev
        pct = (chg / prev) * 100
        # 紅漲綠跌
        c_txt = "#e53935" if chg >= 0 else "#43a047"
        arrow = "▲" if chg >= 0 else "▼"
        
        st.markdown(f"""
        <div class="white-card">
            <div class="stock-header">
                <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
            </div>
            <div style="display:flex; align-items:baseline; gap:10px; margin-bottom:15px;">
                <div class="price-big" style="color:{c_txt}">{price:.2f}</div>
                <div style="color:{c_txt}; font-weight:bold; font-size:1.2rem;">{arrow} {abs(chg):.2f} ({abs(pct):.2f}%)</div>
            </div>
            <div class="stats-grid">
                <div class="stat-row"><span class="stat-lbl">最高</span><span class="stat-val" style="color:#e53935">{latest_fast['High']:.2f}</span></div>
                <div class="stat-row"><span class="stat-lbl">最低</span><span class="stat-val" style="color:#43a047">{latest_fast['Low']:.2f}</span></div>
                <div class="stat-row"><span class="stat-lbl">昨收</span><span class="stat-val">{prev:.2f}</span></div>
                <div class="stat-row"><span class="stat-lbl">開盤</span><span class="stat-val">{latest_fast['Open']:.2f}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 卡片 C：週期選單 (橫向滑動)
    # 使用 HTML 結構讓它包在 white-card 裡面，但 Streamlit 的 radio 比較難包，所以我們用 CSS 讓它看起來像一組
    st.markdown('<div class="white-card" style="padding:10px;">', unsafe_allow_html=True)
    p_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
    p_label = st.radio("週期", list(p_map.keys()), horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 卡片 D：K 線圖
    interval = p_map[p_label]
    d_period = "2y"
    if interval in ["1m", "5m", "30m", "60m"]: d_period = "5d"
    
    df = stock.history(period=d_period, interval=interval)
    if p_label == "10分": df = df.resample('10min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
    
    if not df.empty:
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        st.markdown('<div class="white-card chart-box" style="padding:0;">', unsafe_allow_html=True)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
        
        # K線 & MA
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K", increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
        for ma, c in [('MA5','#2962ff'), ('MA10','#aa00ff'), ('MA20','#ff6d00')]:
            if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
        
        # Volume
        colors = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Vol'), row=2, col=1)
        
        # KD
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#2962ff', width=1), name='K'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff6d00', width=1), name='D'), row=3, col=1)
        
        # 設定顯示範圍 (最近 45 根)
        if len(df) > 45:
            fig.update_xaxes(range=[df.index[-45], df.index[-1]], row=1, col=1)
        
        # 樣式調整 (移除滑桿，啟用拖曳)
        fig.update_layout(
            height=600, margin=dict(l=10,r=10,t=10,b=10), 
            paper_bgcolor='white', plot_bgcolor='white',
            showlegend=False, hovermode='x unified',
            dragmode='pan', 
            xaxis=dict(rangeslider_visible=False), 
            yaxis=dict(fixedrange=True) # Y軸鎖定，只能左右拖
        )
        # 十字線
        for r in [1,2,3]:
            fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)
            fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)

        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # 卡片 E：分析報告
        # 這裡先只抓 Yahoo 的法人模擬 (因為 FinMind 容易卡住，先求穩)
        st.markdown(generate_report_html(name, target, latest, None), unsafe_allow_html=True)

    else:
        st.warning("此週期無數據。")

except Exception as e:
    st.error(f"讀取錯誤 ({e})")


