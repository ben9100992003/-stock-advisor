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
from FinMind.data import DataLoader

# --- 0. 設定與金鑰 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. Session State ---
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

# --- 2. CSS 暴力修復 (針對手機排版) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

def set_bg_hack(png_file):
    st.markdown('<style>.stApp {background-color: #121212;}</style>', unsafe_allow_html=True)
    bin_str = get_base64_of_bin_file(png_file)
    if bin_str:
        st.markdown(f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover; background-position: center;
            background-repeat: no-repeat; background-attachment: fixed;
        }}
        .stApp::before {{
            content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6); pointer-events: none; z-index: 0;
        }}
        </style>
        ''', unsafe_allow_html=True)

set_bg_hack('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局文字 */
    .stApp, p, h1, h2, h3, h4, span, div, label, li { color: #ffffff !important; text-shadow: none !important; }
    #MainMenu, footer, header {visibility: hidden;}

    /* 卡片與輸入框 */
    .glass-card {
        background: rgba(25, 25, 25, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border-radius: 16px; padding: 16px; margin-bottom: 15px; border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.8) !important; color: #fff !important;
        border: 1px solid #FFD700 !important; border-radius: 12px;
    }

    /* --- [重點 1] 手機版強制並排 CSS --- */
    /* 這裡使用 Media Query，當螢幕小於 768px (手機/平板) 時生效 */
    @media only screen and (max-width: 768px) {
        /* 強制所有 columns (在同一列的) 寬度為 50%，不准換行 */
        div[data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 50% !important;
        }
    }
    
    /* 按鈕滿版 */
    .stButton button, .stLinkButton a {
        width: 100% !important;
        height: 48px !important;
        display: flex; justify-content: center; align-items: center;
        border-radius: 12px; font-weight: bold; margin: 0;
    }
    
    /* 連結按鈕顏色 */
    .stLinkButton a { background: #6e00ff !important; color: white !important; text-decoration: none; }
    /* 一般按鈕顏色 */
    .stButton button { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); color: white; }
    
    /* --- [重點 2] 週期按鈕修復 --- */
    div[data-testid="stRadio"] > div {
        display: flex; flex-wrap: nowrap !important; overflow-x: auto; gap: 4px; padding-bottom: 2px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2); border-radius: 12px;
        padding: 4px 8px !important; min-width: 35px; text-align: center;
        flex-shrink: 0; margin-right: 0px !important;
    }
    div[data-testid="stRadio"] label p {
        font-size: 12px !important; font-weight: normal !important; margin-bottom: 0px !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p { color: #000 !important; font-weight: bold !important; }

    /* 報價顏色 */
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; }
    .price-big { font-size: 2.8rem; font-weight: 800; line-height: 1.1; }
    
    /* 圖表透明 */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 搜尋邏輯 (地毯式搜索) ---

@st.cache_data(ttl=60)
def brute_force_search(query):
    """
    [地毯式搜股]
    不依賴名稱，直接對 Yahoo 發起測試。
    如果輸入 4903 -> 同時測試 4903.TW 和 4903.TWO
    """
    query = query.strip().upper()
    
    # 定義一個簡單的檢查函數
    def check_ticker(ticker_symbol):
        try:
            t = yf.Ticker(ticker_symbol)
            # 只要有任何一天的歷史資料，就代表存在
            h = t.history(period="1d")
            if not h.empty:
                # 嘗試取得名稱
                name = t.info.get('longName', ticker_symbol)
                # 有時候 yfinance 抓不到中文名，這裡做個簡單對應 (若需要可擴充)
                return ticker_symbol, name
        except: pass
        return None, None

    # 1. 如果輸入純數字 (最常見的情況)
    if query.isdigit():
        # 先試上市 (.TW)
        res_tw = check_ticker(f"{query}.TW")
        if res_tw[0]: return res_tw
        
        # 再試上櫃 (.TWO) -> 這裡就是 4903 找不到的原因，現在一定找得到
        res_two = check_ticker(f"{query}.TWO")
        if res_two[0]: return res_two
        
    # 2. 如果輸入包含 .TW / .TWO
    elif ".TW" in query:
        return check_ticker(query)
        
    # 3. 如果輸入英文 (美股)
    else:
        return check_ticker(query)
    
    return None, None

@st.cache_data(ttl=300)
def get_stock_data_hybrid(ticker, interval, period_days=365):
    is_tw = ".TW" in ticker or ".TWO" in ticker
    is_intraday = interval in ["1m", "5m", "30m", "60m"]
    
    # 台股日線用 FinMind (最準)
    if is_tw and not is_intraday:
        try:
            stock_id = ticker.split('.')[0]
            dl = DataLoader(token=FINMIND_TOKEN)
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            if not df.empty:
                df = df.rename(columns={'date':'Date','open':'Open','max':'High','min':'Low','close':'Close','Trading_Volume':'Volume'})
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                return df
        except: pass
            
    # 其他用 Yahoo
    try:
        yf_period = "1d" if is_intraday else ("1y" if period_days < 500 else "2y")
        stock = yf.Ticker(ticker)
        df = stock.history(period=yf_period, interval=interval)
        if df.empty: return None
        return df
    except: return None

@st.cache_data(ttl=300)
def get_institutional_chips(ticker):
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split('.')[0]
    try:
        dl = DataLoader(token=FINMIND_TOKEN)
        start_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        df['net'] = (df['buy'] - df['sell']) / 1000
        pivot = df.pivot_table(index='date', columns='name', values='net', aggfunc='sum').fillna(0)
        return pivot.sort_index(ascending=False)
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

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Ultimate</h2>", unsafe_allow_html=True)

# 搜尋與自選區 (這裡也強制 50/50 並排)
c1, c2 = st.columns([1, 1])
with c1:
    query = st.text_input("搜尋", placeholder="輸入代號 (4903, 2330)...")
    if query:
        # 使用地毯式搜索
        t, n = brute_force_search(query)
        if t:
            st.session_state.current_ticker = t
            st.session_state.current_name = n
            st.rerun()
        else:
            st.error(f"❌ 查無 {query}")

with c2:
    watch_select = st.selectbox("⭐ 自選", ["(切換)"] + st.session_state.watchlist)
    if watch_select != "(切換)":
        st.session_state.current_ticker = watch_select
        t, n = brute_force_search(watch_select) # 更新名稱
        st.session_state.current_name = n if n else watch_select

target = st.session_state.current_ticker
name = st.session_state.get('current_name', target)

if target:
    df_daily = get_stock_data_hybrid(target, "1d", 365)
    
    if df_daily is not None and not df_daily.empty:
        df_daily = calculate_indicators(df_daily)
        chips_df = get_institutional_chips(target)
        
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        yahoo_url = f"https://tw.stock.yahoo.com/quote/{target}" if ".TW" in target or ".TWO" in target else f"https://finance.yahoo.com/quote/{target}"

        # 報價卡片
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size:1.4rem; font-weight:bold;">{name}</div>
                    <div style="font-size:0.9rem; opacity:0.7;">{target}</div>
                </div>
                <div style="text-align:right;">
                    <div class="{color_cls}" style="font-size:1.2rem; font-weight:bold;">{arrow} {abs(change):.2f} ({abs(pct):.2f}%)</div>
                </div>
            </div>
            <div class="{color_cls} price-big">{latest['Close']:.2f}</div>
            <div style="font-size:0.8rem; opacity:0.8;">量: {int(latest['Volume']/1000):,} K</div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- [重點] 按鈕並排區 ---
        # 由於上面的 CSS 強制設定了 div[data-testid="column"] width: 50%，
        # 這裡只要宣告兩個 columns，它們在手機上就會強制並排。
        b1, b2 = st.columns(2)
        with b1:
            st.link_button("🔗 Yahoo 股市", yahoo_url)
        with b2:
            if target in st.session_state.watchlist:
                if st.button("🗑️ 移除自選"): toggle_watchlist(); st.rerun()
            else:
                if st.button("❤️ 加入自選"): toggle_watchlist(); st.rerun()

        # 分頁
        tabs = st.tabs(["📈 K線圖", "📊 大數據", "🏛️ 籌碼"])
        
        with tabs[0]:
            t_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            sel_p = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = t_map[sel_p]
            p_days = 5 if interval in ["1m", "5m"] else 365
            
            with st.spinner("載入圖表..."):
                df_chart = get_stock_data_hybrid(target, interval, p_days)
                if df_chart is not None:
                    df_chart = calculate_indicators(df_chart)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                    
                    # K線
                    fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="K線", increasing_line_color='#ff5252', decreasing_line_color='#00e676'), row=1, col=1)
                    if 'MA5' in df_chart.columns: fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='cyan', width=1), name='MA5'), row=1, col=1)
                    if 'MA20' in df_chart.columns: fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
                    
                    # KD
                    if 'K' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['K'], line=dict(color='#ff5252', width=1), name='K'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['D'], line=dict(color='#00e676', width=1), name='D'), row=2, col=1)

                    # [重點] 雙手操作設定
                    fig.update_layout(
                        height=500, margin=dict(l=10,r=10,t=10,b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,20,0.7)',
                        font=dict(color='#eee'), showlegend=False,
                        # dragmode='pan': 允許單指拖曳平移
                        # hovermode='x unified': 顯示十字線資訊
                        dragmode='pan', 
                        hovermode='x unified'
                    )
                    # 允許 X 軸縮放 (雙指開合)
                    fig.update_xaxes(fixedrange=False)
                    fig.update_yaxes(fixedrange=False)
                    
                    # scrollZoom=True: 允許滑鼠滾輪或雙指縮放
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                else: st.warning("無資料")

        with tabs[1]:
            # 大數據評分 (FinMind 整合)
            score = 50
            if latest['Close'] > latest['MA20']: score += 20
            if latest['K'] > latest['D']: score += 10
            c_score = "#ff5252" if score >= 60 else "#00e676"
            st.markdown(f"<div class='glass-card'><h3>大數據評分：<span style='color:{c_score}'>{score}</span></h3></div>", unsafe_allow_html=True)
            
        with tabs[2]:
            if chips_df is not None:
                st.dataframe(chips_df.head(10).style.format("{:.0f}"), use_container_width=True)
            else: st.info("無籌碼資料")

