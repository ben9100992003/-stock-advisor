import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os
import time

# --- 0. 設定與金鑰 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# --- 1. Session State (自選股與狀態) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["2330.TW", "NVDA"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "2330.TW"

def toggle_watchlist():
    t = st.session_state.current_ticker
    if t in st.session_state.watchlist:
        st.session_state.watchlist.remove(t)
        st.toast(f"🗑️ 已移除 {t}")
    else:
        st.session_state.watchlist.append(t)
        st.toast(f"✅ 已加入 {t}")

# --- 2. 視覺樣式 (CSS 優化) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_bg_hack(png_file):
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
        .stApp::before {{
            content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.5); /* 背景壓暗一點 */
            pointer-events: none; z-index: 0;
        }}
        </style>
        ''', unsafe_allow_html=True)

set_bg_hack('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局文字設定 */
    .stApp, p, h1, h2, h3, h4, span, div, label {
        color: #ffffff !important;
        text-shadow: none !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}

    /* 毛玻璃卡片 */
    .glass-card {
        background: rgba(20, 20, 20, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    /* 輸入框優化 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #fff !important;
        border: 1px solid #FFD700 !important;
        border-radius: 12px;
    }
    
    /* --- 週期按鈕優化 (修正字體過大與換行問題) --- */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap; /* 強制不換行 */
        overflow-x: auto;
        gap: 6px;
        padding-bottom: 5px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 4px 12px !important; /* 縮小內距 */
        margin-right: 0px;
        min-width: 45px; /* 縮小按鈕寬度 */
        text-align: center;
        flex-shrink: 0; /* 防止被擠壓 */
    }
    div[data-testid="stRadio"] label p {
        font-size: 13px !important; /* 字體縮小 */
        font-weight: normal !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important;
        border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p {
        color: #000 !important;
        font-weight: bold !important;
    }

    /* 報價文字 */
    .price-big { font-size: 2.5rem; font-weight: 800; margin: 5px 0; line-height: 1.1; }
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; } /* 改更亮的綠色 */
    
    /* 按鈕樣式 (加入/移除自選) */
    .stButton button {
        width: 100%;
        background: rgba(255,255,255,0.1);
        color: white;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 0.5rem;
    }
    .stButton button:hover {
        border-color: #FFD700;
        color: #FFD700;
    }

    /* Plotly 圖表背景優化 */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 搜尋邏輯 (暴力修正版) ---

@st.cache_data(ttl=600)
def search_stock(query):
    query = query.strip().upper()
    
    # 定義檢查函式
    def check_valid(ticker):
        try:
            s = yf.Ticker(ticker)
            # 關鍵：必須要有歷史股價才算存在，不然 yfinance 有時不會噴錯但會給空資料
            h = s.history(period="1d")
            if not h.empty:
                return ticker, s.info
        except: pass
        return None, None

    # 1. 如果有小數點 (e.g. 2330.TW)，直接查
    if "." in query:
        return check_valid(query)

    # 2. 如果是純數字，先查上市 (.TW) 再查上櫃 (.TWO)
    if query.isdigit():
        # 試上市
        res = check_valid(f"{query}.TW")
        if res[0]: return res
        
        # 試上櫃 (解決 4903 找不到的問題)
        res = check_valid(f"{query}.TWO")
        if res[0]: return res

    # 3. 如果都不是，當美股查
    return check_valid(query)

@st.cache_data(ttl=30) # 短快取，即時性高
def get_stock_data(ticker, period, interval):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty: return None
        return df
    except: return None

def calculate_indicators(df):
    if df is None or len(df) < 5: return df
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# --- 4. UI 主程式 ---

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Wujila</h2>", unsafe_allow_html=True)

# 搜尋與自選區
c1, c2 = st.columns([2.5, 1.5])
with c1:
    query = st.text_input("搜尋 (如 4903, 2330, NVDA)", placeholder="輸入代號...")
    if query:
        with st.spinner("🔍 搜尋中..."):
            t, i = search_stock(query)
            if t:
                st.session_state.current_ticker = t
                st.rerun() # 找到後直接重整畫面
            else:
                st.error(f"❌ 找不到 {query}")

with c2:
    # 顯示目前自選股
    watch_select = st.selectbox("⭐ 我的自選", ["(切換股票)"] + st.session_state.watchlist)
    if watch_select != "(切換股票)":
        st.session_state.current_ticker = watch_select

target = st.session_state.current_ticker

if target:
    # 取得最新報價 (日線)
    df_daily = get_stock_data(target, "5d", "1d")
    
    if df_daily is not None:
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        
        # 決定顏色
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        # 名稱
        try:
            info = yf.Ticker(target).info
            name = info.get('longName', target)
        except: name = target

        # --- A. 報價卡片 ---
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size:1.1rem; opacity:0.9; font-weight:bold;">{target}</div>
                    <div style="font-size:0.9rem; opacity:0.7;">{name}</div>
                </div>
                <div style="text-align:right;">
                    <div class="{color_cls}" style="font-size:1.2rem; font-weight:bold;">
                        {arrow} {abs(change):.2f} ({abs(pct):.2f}%)
                    </div>
                </div>
            </div>
            <div class="{color_cls} price-big">{latest['Close']:.2f}</div>
            <div style="font-size:0.8rem; opacity:0.7; display:flex; gap:10px;">
                <span>量: {int(latest['Volume']/1000):,} K</span>
                <span>高: {latest['High']:.2f}</span>
                <span>低: {latest['Low']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- B. 按鈕區 (並排) ---
        b1, b2 = st.columns(2)
        is_in_watch = target in st.session_state.watchlist
        with b1:
            if not is_in_watch:
                if st.button("❤️ 加入自選"): toggle_watchlist()
            else:
                st.markdown(f"<div style='text-align:center; padding:8px; opacity:0.5; border:1px solid #555; border-radius:12px;'>已在自選</div>", unsafe_allow_html=True)
        with b2:
            if is_in_watch:
                if st.button("🗑️ 移除自選"): toggle_watchlist()
            else:
                st.markdown("") # 佔位

        # --- C. 圖表區 ---
        tabs = st.tabs(["📈 K線圖", "📝 分析"])
        
        with tabs[0]:
            # 週期選單
            t_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            sel_p = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = t_map[sel_p]
            
            # --- 關鍵修正：分時走勢只抓當天 ---
            if interval in ["1m", "5m", "30m", "60m"]:
                period = "1d" # 只有一天，圖形才會大
            else:
                period = "1y" # 日線以上抓長一點
            
            with st.spinner("繪製中..."):
                chart_key = f"{target}_{interval}_{time.time()}" # 強制更新
                df_chart = get_stock_data(target, period, interval)
                
                if df_chart is not None:
                    df_chart = calculate_indicators(df_chart)
                    
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                    
                    # K線
                    fig.add_trace(go.Candlestick(
                        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
                        name="K線", increasing_line_color='#ff5252', decreasing_line_color='#00e676'
                    ), row=1, col=1)
                    
                    # 均線
                    if 'MA5' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='cyan', width=1), name='MA5'), row=1, col=1)
                    if 'MA20' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='#FFD700', width=1), name='MA20'), row=1, col=1)

                    # KD
                    if 'K' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['K'], line=dict(color='#ff5252', width=1), name='K'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['D'], line=dict(color='#00e676', width=1), name='D'), row=2, col=1)

                    # 樣式設定 (背景加深，字變亮)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=40, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(20, 20, 20, 0.7)', # 圖表區塊背景加深，增加對比
                        font=dict(color='#eee'),
                        xaxis_rangeslider_visible=False,
                        showlegend=False,
                        dragmode='pan'
                    )
                    # 網格線稍微明顯一點
                    grid_color = 'rgba(255,255,255,0.15)'
                    fig.update_xaxes(showgrid=True, gridcolor=grid_color, row=1, col=1)
                    fig.update_yaxes(showgrid=True, gridcolor=grid_color, row=1, col=1)
                    fig.update_yaxes(showgrid=True, gridcolor=grid_color, row=2, col=1)

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.warning("⚠️ 此週期暫無資料")

        with tabs[1]:
            # 簡易分析 (KD 與均線)
            k = latest.get('K', 50)
            d = latest.get('D', 50)
            ma20 = latest.get('MA20', latest['Close'])
            
            trend_txt = "多頭" if latest['Close'] > ma20 else "空頭"
            kd_txt = "黃金交叉" if k > d else "死亡交叉"
            
            st.markdown(f"""
            <div class="glass-card">
                <p><b>技術面概況：</b></p>
                <ul>
                    <li>趨勢判斷：<span style="color:{'#ff5252' if trend_txt=='多頭' else '#00e676'}">{trend_txt}</span> (股價 vs 月線)</li>
                    <li>KD 指標：K={k:.1f}, D={d:.1f} ({kd_txt})</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# 底部市場
st.markdown("---")
c_tw, c_us = st.columns(2)
with c_tw:
    twi = get_stock_data("^TWII", "2d", "1d")
    if twi is not None:
        v = twi.iloc[-1]['Close']
        d = v - twi.iloc[-2]['Close']
        c = "#ff5252" if d>0 else "#00e676"
        st.markdown(f"<div style='text-align:center; font-size:0.8rem'>🇹🇼 加權<br><span style='color:{c};font-weight:bold;font-size:1rem'>{v:.0f} ({d:+.0f})</span></div>", unsafe_allow_html=True)

with c_us:
    ixi = get_stock_data("^IXIC", "2d", "1d")
    if ixi is not None:
        v = ixi.iloc[-1]['Close']
        d = v - ixi.iloc[-2]['Close']
        c = "#ff5252" if d>0 else "#00e676"
        st.markdown(f"<div style='text-align:center; font-size:0.8rem'>🇺🇸 那指<br><span style='color:{c};font-weight:bold;font-size:1rem'>{v:.0f} ({d:+.0f})</span></div>", unsafe_allow_html=True)
