import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os
import time
import requests

# --- 0. 設定與金鑰 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# --- 1. Session State (自選股與錯誤處理) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["2330.TW", "NVDA"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "2330.TW"

def add_to_watchlist():
    ticker = st.session_state.current_ticker
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
        st.toast(f"✅ 已加入 {ticker}")

def remove_from_watchlist(t):
    if t in st.session_state.watchlist:
        st.session_state.watchlist.remove(t)
        st.toast(f"🗑️ 已移除 {t}")
        # 如果移除的是當前顯示的，切換回預設
        if t == st.session_state.current_ticker:
            st.session_state.current_ticker = "2330.TW" if "2330.TW" in st.session_state.watchlist else st.session_state.watchlist[0] if st.session_state.watchlist else "2330.TW"

# --- 2. 視覺樣式 (深色毛玻璃風格) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_bg_hack(png_file):
    # 預設深色底，防止圖片載入失敗刺眼
    st.markdown('<style>.stApp {background-color: #121212;}</style>', unsafe_allow_html=True)
    
    bin_str = get_base64_of_bin_file(png_file)
    if bin_str:
        st.markdown(f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* 遮罩層，讓背景暗一點，字才看得清楚 */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.4); 
            pointer-events: none;
            z-index: 0;
        }}
        </style>
        ''', unsafe_allow_html=True)

set_bg_hack('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局文字設定 - 預設白色，易讀 */
    .stApp, p, h1, h2, h3, h4, h5, h6, span, li, div, label {
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    
    /* 隱藏預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- 核心：毛玻璃卡片 (Glassmorphism) --- */
    .glass-card {
        background: rgba(30, 30, 30, 0.85); /* 深色半透明 */
        backdrop-filter: blur(12px);         /* 背後模糊 */
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.15); /* 淡淡的白邊 */
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* 輸入框美化 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.7) !important;
        color: #fff !important;
        border: 1px solid #FFD700 !important; /* 金邊 */
        border-radius: 12px;
    }
    
    /* 橫向滑動選單 (手機優化) */
    .scroll-wrapper {
        display: flex;
        overflow-x: auto;
        gap: 8px;
        padding-bottom: 5px;
        margin-bottom: 10px;
        -webkit-overflow-scrolling: touch;
    }
    .scroll-wrapper::-webkit-scrollbar { height: 0px; } /* 隱藏捲軸 */
    
    /* 自訂 Radio 按鈕樣式 (取代 Streamlit 原生) */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2);
        color: #fff !important;
        border-radius: 20px;
        padding: 5px 15px !important;
        margin-right: 5px;
        min-width: 60px;
        text-align: center;
        transition: 0.3s;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important; /* 選中變金色 */
        border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p {
        color: #000 !important; /* 選中字變黑 */
        text-shadow: none !important;
        font-weight: bold;
    }

    /* 報價大數字 */
    .price-big { font-size: 2.8rem; font-weight: 800; margin: 5px 0; line-height: 1.1; }
    .price-up { color: #ff5252 !important; text-shadow: 0 0 10px rgba(255, 82, 82, 0.4); }
    .price-down { color: #69f0ae !important; text-shadow: 0 0 10px rgba(105, 240, 174, 0.4); }
    
    /* 按鈕 */
    .stButton button {
        background: rgba(255,255,255,0.1);
        color: white;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Plotly 圖表容器 (修正空白問題) */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important; /* 透明背景 */
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 資料處理 (增加 Retry 機制) ---

@st.cache_data(ttl=600)
def search_stock(query):
    """
    強化的搜尋邏輯：
    1. 嘗試直接代號 (如 2330.TW)
    2. 數字 -> 嘗試上市 (.TW) -> 失敗嘗試上櫃 (.TWO) -> 失敗當美股
    """
    query = query.strip().upper()
    
    # 定義重試函式
    def try_fetch(ticker):
        try:
            # 加入 headers 模擬瀏覽器，減少被擋機率
            stock = yf.Ticker(ticker)
            # 必須真的抓到歷史資料才算存在
            hist = stock.history(period="5d")
            if not hist.empty:
                return ticker, stock.info
        except Exception:
            return None, None
        return None, None

    # 情境 A: 使用者已經輸入完整代號 (有小數點)
    if "." in query:
        return try_fetch(query)

    # 情境 B: 純數字 (優先查台股)
    if query.isdigit():
        # 1. 優先試上市
        res = try_fetch(f"{query}.TW")
        if res[0]: return res
        
        # 2. 其次試上櫃 (這是您遇到 4903 的問題點)
        res = try_fetch(f"{query}.TWO")
        if res[0]: return res

    # 情境 C: 英文或混雜 (當美股查)
    return try_fetch(query)

@st.cache_data(ttl=60)
def get_stock_data(ticker, period, interval):
    """
    取得股價並快取，防止重複請求導致 Rate Limit
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty: return None
        return df
    except:
        return None

def calculate_indicators(df):
    if df is None or len(df) < 5: return df
    
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    # KD
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# --- 4. UI 主程式 ---

st.markdown("<h1 style='text-align:center;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 控制區 (搜尋 + 自選)
with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input("🔍 搜尋 (輸入 4903, 2330, NVDA...)", placeholder="股票代號")
        if query:
            with st.spinner("搜尋中..."):
                ticker, info = search_stock(query)
                if ticker:
                    st.session_state.current_ticker = ticker
                    # 清空輸入框的小技巧 (非必要，但體驗較好)
                else:
                    st.error(f"❌ 找不到 '{query}'，請確認代號是否正確。")

    with c2:
        # 自選股選單
        select = st.selectbox("⭐ 自選股", ["(選擇股票)"] + st.session_state.watchlist)
        if select != "(選擇股票)":
            st.session_state.current_ticker = select

# 主內容區
target = st.session_state.current_ticker

if target:
    # 取得資料 (日線預設，用來顯示報價)
    df_daily = get_stock_data(target, "1y", "1d")
    
    if df_daily is None:
        st.warning(f"⚠️ 無法載入 {target} 的數據，可能是連線問題或 API 限制，請稍後再試。")
    else:
        # 計算指標
        df_daily = calculate_indicators(df_daily)
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        
        # 決定顏色 (台股紅漲綠跌)
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        # 取得名稱 (盡量處理)
        try:
            stock_obj = yf.Ticker(target)
            # 使用 fast_info 比較不耗資源
            # 或是從 search_stock 緩存中拿
            stock_name = target
            if 'longName' in stock_obj.info:
                stock_name = stock_obj.info['longName']
        except: stock_name = target

        # --- A. 報價卡片 (Glass Card) ---
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:1.2rem; opacity:0.8;">{stock_name}</div>
                    <div style="font-size:0.9rem; opacity:0.6;">{target}</div>
                </div>
                <div style="text-align:right;">
                    <div class="{color_cls}" style="font-size:1.5rem; font-weight:bold;">
                        {arrow} {abs(change):.2f} ({abs(pct):.2f}%)
                    </div>
                </div>
            </div>
            <div class="{color_cls} price-big">{latest['Close']:.2f}</div>
            <div style="display:flex; gap:15px; font-size:0.9rem; opacity:0.8; margin-top:5px;">
                <span>量: {int(latest['Volume']/1000):,} K</span>
                <span>高: {latest['High']:.2f}</span>
                <span>低: {latest['Low']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 自選股操作按鈕
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("❤️ 加入自選"): add_to_watchlist()
        with c_btn2:
            if st.button("🗑️ 移除自選"): remove_from_watchlist(target)

        # --- B. 圖表與分析 ---
        tabs = st.tabs(["📈 K線圖", "📝 戰情分析", "🏛️ 籌碼"])

        with tabs[0]:
            # 週期按鈕
            t_map = {"1分": "1m", "5分": "5m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
            selected_period = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            
            interval = t_map[selected_period]
            period_len = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
            
            with st.spinner("載入圖表..."):
                # 使用 unique key 強制重繪
                chart_key = f"chart_{target}_{interval}"
                df_chart = get_stock_data(target, period_len, interval)
                
                if df_chart is not None:
                    df_chart = calculate_indicators(df_chart)
                    
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                    
                    # K線
                    fig.add_trace(go.Candlestick(
                        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
                        name="K線", increasing_line_color='#ff5252', decreasing_line_color='#69f0ae'
                    ), row=1, col=1)
                    
                    # 均線
                    if 'MA5' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='cyan', width=1), name='MA5'), row=1, col=1)
                    if 'MA20' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='yellow', width=1), name='MA20'), row=1, col=1)

                    # KD
                    if 'K' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['K'], line=dict(color='#ff5252', width=1), name='K'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['D'], line=dict(color='#69f0ae', width=1), name='D'), row=2, col=1)

                    # 佈局 (深色主題)
                    fig.update_layout(
                        height=450,
                        margin=dict(l=10, r=40, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', # 透明
                        plot_bgcolor='rgba(0,0,0,0)',  # 透明
                        font=dict(color='white'),
                        xaxis_rangeslider_visible=False,
                        dragmode='pan',
                        showlegend=False
                    )
                    # 網格淡化
                    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', row=1, col=1)
                    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', row=1, col=1)
                    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', row=2, col=1)

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True}, key=chart_key)
                else:
                    st.error("暫無此週期數據")

        with tabs[1]:
            # 分析報告
            ma5 = latest.get('MA5', 0)
            ma20 = latest.get('MA20', 0)
            k = latest.get('K', 50)
            d = latest.get('D', 50)
            
            trend = "多頭排列" if latest['Close'] > ma20 else "空方控盤"
            kd_msg = "黃金交叉 (↑)" if k > d else "死亡交叉 (↓)"
            
            # 策略建議
            if latest['Close'] > ma20 and k > d:
                advice = "✅ 偏多操作：股價站上月線且指標翻多，可沿 5 日線佈局。"
            elif latest['Close'] < ma20 and k < d:
                advice = "⚠️ 保守觀望：股價位於月線下且指標偏弱，建議等待止跌。"
            else:
                advice = "⚖️ 區間震盪：多空拉鋸中，建議低買高賣操作。"

            st.markdown(f"""
            <div class="glass-card">
                <h3>📊 戰情分析</h3>
                <p><b>技術趨勢：</b>{trend}</p>
                <p><b>KD 指標：</b>K({k:.1f}) / D({d:.1f}) - <span style="color:#FFD700">{kd_msg}</span></p>
                <hr style="border-color:rgba(255,255,255,0.2);">
                <h4>💡 策略建議</h4>
                <p>{advice}</p>
                <p style="font-size:0.8rem; opacity:0.6;">(支撐參考: {ma20:.2f} | 壓力參考: {ma5*1.05:.2f})</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 公司簡介 (如果有)
            if 'longBusinessSummary' in stock_obj.info:
                summary = stock_obj.info['longBusinessSummary'][:150] + "..."
                st.markdown(f"<div class='glass-card' style='font-size:0.9rem; opacity:0.8'>{summary}</div>", unsafe_allow_html=True)

        with tabs[2]:
             st.markdown("<div class='glass-card'>籌碼資料暫時維護中，請參考技術面。</div>", unsafe_allow_html=True)

# 底部市場概況
st.markdown("---")
c_tw, c_us = st.columns(2)
with c_tw:
    tw_idx = get_stock_data("^TWII", "5d", "1d")
    if tw_idx is not None:
        last = tw_idx.iloc[-1]['Close']
        chg = last - tw_idx.iloc[-2]['Close']
        color = "#ff5252" if chg > 0 else "#69f0ae"
        st.markdown(f"<div style='text-align:center'>🇹🇼 加權<br><span style='color:{color};font-weight:bold;font-size:1.2rem'>{last:.0f} ({chg:+.0f})</span></div>", unsafe_allow_html=True)
with c_us:
    us_idx = get_stock_data("^IXIC", "5d", "1d")
    if us_idx is not None:
        last = us_idx.iloc[-1]['Close']
        chg = last - us_idx.iloc[-2]['Close']
        color = "#ff5252" if chg > 0 else "#69f0ae"
        st.markdown(f"<div style='text-align:center'>🇺🇸 那指<br><span style='color:{color};font-weight:bold;font-size:1.2rem'>{last:.0f} ({chg:+.0f})</span></div>", unsafe_allow_html=True)

