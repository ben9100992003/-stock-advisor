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
import xml.etree.ElementTree as ET
from FinMind.data import DataLoader

# --- 0. 設定與金鑰 ---
st.set_page_config(page_title="武吉拉 Wujila Ultimate", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 內建股票大數據 (解決找不到股票的核心) ---
# 這裡內建常見熱門股，確保搜尋絕對命中，不用看 Yahoo 臉色
STATIC_TW_STOCKS = {
    # 熱門上櫃 (容易找不到的)
    "4903": {"name": "聯光通", "suffix": ".TWO"},
    "8069": {"name": "元太", "suffix": ".TWO"},
    "3131": {"name": "弘塑", "suffix": ".TWO"},
    "3293": {"name": "鈊象", "suffix": ".TWO"},
    "6187": {"name": "萬潤", "suffix": ".TWO"},
    "3529": {"name": "力旺", "suffix": ".TWO"},
    "5347": {"name": "世界", "suffix": ".TWO"},
    "5483": {"name": "中美晶", "suffix": ".TWO"},
    # 熱門上市
    "2330": {"name": "台積電", "suffix": ".TW"},
    "2317": {"name": "鴻海", "suffix": ".TW"},
    "2454": {"name": "聯發科", "suffix": ".TW"},
    "2603": {"name": "長榮", "suffix": ".TW"},
    "2609": {"name": "陽明", "suffix": ".TW"},
    "2615": {"name": "萬海", "suffix": ".TW"},
    "3231": {"name": "緯創", "suffix": ".TW"},
    "2382": {"name": "廣達", "suffix": ".TW"},
    "2356": {"name": "英業達", "suffix": ".TW"},
    "3008": {"name": "大立光", "suffix": ".TW"},
    "2303": {"name": "聯電", "suffix": ".TW"},
    "2881": {"name": "富邦金", "suffix": ".TW"},
    "2882": {"name": "國泰金", "suffix": ".TW"},
    "1519": {"name": "華城", "suffix": ".TW"},
    "1513": {"name": "中興電", "suffix": ".TW"},
    "1503": {"name": "士電", "suffix": ".TW"},
    "2376": {"name": "技嘉", "suffix": ".TW"},
    "6669": {"name": "緯穎", "suffix": ".TW"},
    "3035": {"name": "智原", "suffix": ".TW"},
    "3443": {"name": "創意", "suffix": ".TW"},
    "3661": {"name": "世芯-KY", "suffix": ".TW"},
}

# --- 2. Session State ---
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

# --- 3. CSS 樣式 (字體縮小 + 不換行修復) ---
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

    /* --- 關鍵修復：週期按鈕 (字體變小 / 不換行) --- */
    div[data-testid="stRadio"] > div {
        display: flex; flex-wrap: nowrap !important; /* 強制不換行 */
        overflow-x: auto; gap: 4px; padding-bottom: 2px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        padding: 4px 10px !important; /* 縮小內距 */
        min-width: 40px; /* 縮小按鈕 */
        text-align: center;
        flex-shrink: 0; /* 防止被擠壓 */
        margin-right: 0px !important;
    }
    div[data-testid="stRadio"] label p {
        font-size: 12px !important; /* 字體縮小 */
        font-weight: normal !important;
        white-space: nowrap !important; /* 文字不換行 */
        margin-bottom: 0px !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p {
        color: #000 !important; font-weight: bold !important;
    }

    /* --- 關鍵修復：強制按鈕並排 --- */
    div[data-testid="column"] { flex: 1 !important; min-width: 0 !important; }
    
    .stButton button, .stLinkButton a {
        width: 100%; height: 42px; display: flex; justify-content: center; align-items: center;
        border-radius: 10px; font-weight: bold; margin: 0; font-size: 14px;
    }
    .stLinkButton a { background: #6e00ff !important; color: white !important; text-decoration: none; }
    .stButton button { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); color: white; }
    .stButton button:hover { border-color: #FFD700; color: #FFD700; }

    /* 報價顏色 */
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; }
    .price-big { font-size: 2.8rem; font-weight: 800; line-height: 1.1; }

    /* 圖表背景透明 */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 智能搜尋 (優先查內建庫) ---

@st.cache_data(ttl=300)
def smart_search_stock(query):
    query = query.strip().upper()
    
    # 1. 第一關：查內建大數據 (Static DB)
    if query in STATIC_TW_STOCKS:
        data = STATIC_TW_STOCKS[query]
        full_ticker = f"{query}{data['suffix']}"
        return full_ticker, data['name'], {}

    # 2. 第二關：Yahoo 查詢
    def try_fetch(ticker):
        try:
            s = yf.Ticker(ticker)
            # 只要有任何歷史資料就算存在
            if not s.history(period="1d").empty: return ticker, s.info
        except: pass
        return None, None

    # 台股純數字 -> 先猜上市, 再猜上櫃
    if query.isdigit():
        t, i = try_fetch(f"{query}.TW")
        if t: return t, i.get('longName', t), i
        
        t, i = try_fetch(f"{query}.TWO")
        if t: return t, i.get('longName', t), i

    # 已經有後綴
    if ".TW" in query or ".TWO" in query:
        t, i = try_fetch(query)
        if t: return t, i.get('longName', t), i
        
    # 美股/其他
    t, i = try_fetch(query)
    if t: return t, i.get('longName', t), i
    
    return None, None, None

@st.cache_data(ttl=300)
def get_stock_data_hybrid(ticker, interval, period_days=365):
    is_tw = ".TW" in ticker or ".TWO" in ticker
    is_intraday = interval in ["1m", "5m", "30m", "60m"]
    
    # 台股日線用 FinMind
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

@st.cache_data(ttl=300)
def get_news_rss(ticker):
    try:
        q = ticker.replace(".TW", " TW").replace(".TWO", " TWO")
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        resp = requests.get(url, timeout=3)
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall('.//item')[:5]:
            news.append({'title': item.find('title').text, 'link': item.find('link').text, 'date': item.find('pubDate').text[:16]})
        return news
    except: return []

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

def run_backtest(df):
    bt = df.copy()
    bt['Signal'] = 0
    bt.loc[bt['MA5'] > bt['MA20'], 'Signal'] = 1
    bt['Ret'] = bt['Close'].pct_change() * bt['Signal'].shift(1)
    cum = (1 + bt['Ret']).cumprod()
    total = (cum.iloc[-1] - 1) * 100 if not cum.empty else 0
    return total, bt

# --- 5. UI 主程式 ---

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Ultimate</h2>", unsafe_allow_html=True)

c1, c2 = st.columns([2.5, 1.5])
with c1:
    query = st.text_input("搜尋 (如 4903, 2330)", placeholder="輸入代號...")
    if query:
        # 不顯示 loading spinner，讓感覺更快
        t, n, i = smart_search_stock(query)
        if t:
            st.session_state.current_ticker = t
            st.session_state.current_name = n
            st.rerun()
        else:
            st.error(f"❌ 查無此股 ({query})")

with c2:
    watch_select = st.selectbox("⭐ 自選股", ["(切換)"] + st.session_state.watchlist)
    if watch_select != "(切換)":
        st.session_state.current_ticker = watch_select
        t, n, i = smart_search_stock(watch_select)
        st.session_state.current_name = n

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
        
        yahoo_url = f"https://finance.yahoo.com/quote/{target}"
        if ".TW" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TW','')}"
        elif ".TWO" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TWO','')}"

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
        
        # --- 按鈕並排區 ---
        b1, b2 = st.columns([1, 1])
        with b1:
            st.link_button("🔗 Yahoo 股市", yahoo_url)
        with b2:
            if target in st.session_state.watchlist:
                if st.button("🗑️ 移除自選"): toggle_watchlist(); st.rerun()
            else:
                if st.button("❤️ 加入自選"): toggle_watchlist(); st.rerun()

        # 分頁
        tabs = st.tabs(["📈 K線圖", "📊 大數據", "📰 新聞", "🔙 回測", "🏛️ 籌碼"])
        
        with tabs[0]:
            t_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            sel_p = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = t_map[sel_p]
            p_days = 5 if interval in ["1m", "5m", "30m", "60m"] else 365
            
            with st.spinner("載入..."):
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
                        fig.add_hline(y=80, line_dash="dot", line_color="gray", row=2, col=1)
                        fig.add_hline(y=20, line_dash="dot", line_color="gray", row=2, col=1)

                    fig.update_layout(height=450, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,20,0.7)', font=dict(color='#eee'), showlegend=False, dragmode='pan', hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                else: st.warning("無資料")

        with tabs[1]:
            score = 50
            if latest['Close'] > latest['MA20']: score += 20
            if latest['K'] > latest['D']: score += 10
            c_score = "#ff5252" if score >= 60 else "#00e676"
            st.markdown(f"<div class='glass-card'><h3>大數據評分：<span style='color:{c_score}'>{score}</span></h3></div>", unsafe_allow_html=True)
            
        with tabs[2]:
            news = get_news_rss(target)
            for n in news:
                st.markdown(f"<div style='border-bottom:1px solid #333; padding:8px;'><a href='{n['link']}' style='color:#4FC3F7; text-decoration:none;'>{n['title']}</a></div>", unsafe_allow_html=True)
                
        with tabs[3]:
            ret, bt_data = run_backtest(df_daily)
            c = "#ff5252" if ret > 0 else "#00e676"
            st.markdown(f"<div class='glass-card' style='text-align:center'>回測報酬率<br><span style='color:{c}; font-size:1.5rem'>{ret:.1f}%</span></div>", unsafe_allow_html=True)
            
        with tabs[4]:
            if chips_df is not None:
                st.dataframe(chips_df.head(10).style.format("{:.0f}"), use_container_width=True)
            else: st.info("無籌碼資料")

