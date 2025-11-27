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
import re
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

# --- 2. CSS 樣式 (強制修復版) ---
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
    /* 全局設定 */
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

    /* --- 1. 按鈕強制並排修復 (最強硬的 CSS) --- */
    /* 針對放在 columns 裡的按鈕容器 */
    div[data-testid="column"] {
        flex: 1 1 0% !important; 
        min-width: 0 !important;
        width: 50% !important; /* 強制寬度 */
        padding: 0 5px !important;
    }
    
    /* 讓按鈕填滿欄位 */
    .stButton button, .stLinkButton a {
        width: 100% !important;
        height: 48px !important;
        display: flex; justify-content: center; align-items: center;
        border-radius: 12px; font-weight: bold; margin: 0; font-size: 15px;
        white-space: nowrap;
    }
    
    /* --- 2. 週期按鈕修復 --- */
    div[data-testid="stRadio"] > div {
        display: flex; flex-wrap: nowrap !important; overflow-x: auto; gap: 4px; padding-bottom: 2px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2); border-radius: 12px;
        padding: 4px 8px !important; min-width: 40px; text-align: center;
        flex-shrink: 0; margin-right: 0px !important;
    }
    div[data-testid="stRadio"] label p {
        font-size: 13px !important; font-weight: normal !important; margin-bottom: 0px !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p { color: #000 !important; font-weight: bold !important; }

    /* 連結按鈕樣式 */
    .stLinkButton a { background: #6e00ff !important; color: white !important; text-decoration: none; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stButton button { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); color: white; }
    
    /* 報價顏色 */
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; }
    .price-big { font-size: 2.8rem; font-weight: 800; line-height: 1.1; }
    
    /* 圖表透明 */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心：Yahoo 直接驗證 (解決找不到股票) ---

@st.cache_data(ttl=86400)
def check_yahoo_existence(stock_id):
    """
    [核彈級搜股法]
    直接去請求 Yahoo 股市網頁，如果網頁存在，抓取標題 (中文名)。
    這比 yfinance 猜測準確 100 倍。
    """
    # 1. 先把輸入整理乾淨 (去除空格, 轉大寫)
    stock_id = stock_id.strip().upper()
    
    # 2. 如果是台股數字 (如 4903)
    if stock_id.isdigit():
        # 優先嘗試上市 (.TW)
        url_tw = f"https://tw.stock.yahoo.com/quote/{stock_id}.TW"
        try:
            r = requests.get(url_tw, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
            if r.status_code == 200 and "個股走勢" in r.text:
                # 抓取中文名
                match = re.search(r'<title>(.*?)\(', r.text)
                name = match.group(1).strip() if match else stock_id
                return f"{stock_id}.TW", name
        except: pass

        # 再嘗試上櫃 (.TWO)
        url_two = f"https://tw.stock.yahoo.com/quote/{stock_id}.TWO"
        try:
            r = requests.get(url_two, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
            if r.status_code == 200 and "個股走勢" in r.text:
                match = re.search(r'<title>(.*?)\(', r.text)
                name = match.group(1).strip() if match else stock_id
                return f"{stock_id}.TWO", name
        except: pass
    
    # 3. 如果已經帶有後綴 (2330.TW)
    elif ".TW" in stock_id or ".TWO" in stock_id:
        url = f"https://tw.stock.yahoo.com/quote/{stock_id}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
            if r.status_code == 200:
                match = re.search(r'<title>(.*?)\(', r.text)
                name = match.group(1).strip() if match else stock_id
                return stock_id, name
        except: pass
        
    # 4. 美股 (直接回傳，並嘗試用 yfinance 抓簡稱)
    try:
        t = yf.Ticker(stock_id)
        i = t.info
        if 'shortName' in i or 'longName' in i:
            return stock_id, i.get('shortName', i.get('longName', stock_id))
    except: pass

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

c1, c2 = st.columns([2.5, 1.5])
with c1:
    query = st.text_input("搜尋 (4903, 2330, AI...)", placeholder="輸入代號")
    if query:
        with st.spinner(f"正在向 Yahoo 確認 {query}..."):
            # 使用新的 Yahoo 驗證邏輯
            real_ticker, real_name = check_yahoo_existence(query)
            
            if real_ticker:
                st.session_state.current_ticker = real_ticker
                st.session_state.current_name = real_name
                st.rerun()
            else:
                st.error(f"❌ Yahoo 找不到 '{query}'，請確認代號是否正確。")

with c2:
    watch_select = st.selectbox("⭐ 我的自選", ["(切換)"] + st.session_state.watchlist)
    if watch_select != "(切換)":
        st.session_state.current_ticker = watch_select
        # 自選切換時也跑一次名稱確認，確保顯示漂亮中文
        _, real_name = check_yahoo_existence(watch_select)
        st.session_state.current_name = real_name if real_name else watch_select

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
        
        # --- 按鈕並排區 (使用新 CSS 類別) ---
        b1, b2 = st.columns(2) # 這裡會被 CSS 強制修正為並排
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

                    # 設定縮放功能 (Scroll Zoom & Touch Zoom)
                    fig.update_layout(
                        height=500, margin=dict(l=10,r=10,t=10,b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,20,0.7)',
                        font=dict(color='#eee'), showlegend=False,
                        dragmode='pan',  # 設為 pan 模式，這在手機上允許單指拖曳，雙指縮放
                        hovermode='x unified'
                    )
                    # 確保 X 軸可以縮放
                    fig.update_xaxes(fixedrange=False, row=1, col=1)
                    fig.update_xaxes(fixedrange=False, row=2, col=1)
                    
                    # config 設定 scrollZoom 為 True
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                else: st.warning("無資料")

        with tabs[1]:
            # 大數據評分 (FinMind 整合)
            score = 50
            reason = []
            
            # 技術面
            if latest['Close'] > latest['MA20']: score += 15; reason.append("股價站上月線 (+15)")
            else: score -= 10
            
            if latest['MA5'] > latest['MA20']: score += 10; reason.append("短均線多頭排列 (+10)")
            
            if latest['K'] > latest['D']: score += 10; reason.append("KD 黃金交叉 (+10)")
            elif latest['K'] < 20: score += 5; reason.append("KD 超賣區 (+5)")
            
            # 籌碼面 (如果有)
            if chips_df is not None and not chips_df.empty:
                last_chip = chips_df.iloc[0] # 最新一天
                net_buy = last_chip.sum()
                if net_buy > 0: score += 20; reason.append("法人合計買超 (+20)")
                else: score -= 10; reason.append("法人賣超中 (-10)")
            
            # 限制分數範圍
            score = max(0, min(100, score))
            
            c_score = "#ff5252" if score >= 60 else "#00e676" if score <= 40 else "#FFFF00"
            sentiment = "🔥 強力看多" if score >= 75 else "📈 偏多操作" if score >= 60 else "⚖️ 區間震盪" if score >= 40 else "📉 偏空修正"

            st.markdown(f"""
            <div class="glass-card">
                <h3>大數據戰力：<span style="color:{c_score}">{score} 分</span></h3>
                <div style="background:#444; height:10px; border-radius:5px; margin:10px 0;">
                    <div style="background:{c_score}; width:{score}%; height:100%; border-radius:5px;"></div>
                </div>
                <p style="font-weight:bold; font-size:1.2rem;">{sentiment}</p>
                <hr style="border-color:#555">
                <p><b>評分依據：</b></p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in reason])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with tabs[2]:
            if chips_df is not None:
                st.dataframe(chips_df.head(10).style.format("{:.0f}"), use_container_width=True)
            else: st.info("無籌碼資料")

