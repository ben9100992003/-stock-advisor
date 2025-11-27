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

# --- 2. 視覺樣式 (Glassmorphism + UI 優化) ---
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
            background: rgba(0, 0, 0, 0.6);
            pointer-events: none; z-index: 0;
        }}
        </style>
        ''', unsafe_allow_html=True)

set_bg_hack('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局文字 */
    .stApp, p, h1, h2, h3, h4, span, div, label, li {
        color: #ffffff !important;
        text-shadow: none !important;
    }
    #MainMenu, footer, header {visibility: hidden;}

    /* 卡片樣式 */
    .glass-card {
        background: rgba(25, 25, 25, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    /* 輸入框 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #fff !important;
        border: 1px solid #FFD700 !important;
        border-radius: 12px;
    }
    
    /* 週期按鈕 */
    div[data-testid="stRadio"] > div {
        display: flex; flex-direction: row; flex-wrap: nowrap; overflow-x: auto; gap: 6px; padding-bottom: 5px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 4px 12px !important;
        min-width: 45px;
        text-align: center;
        flex-shrink: 0;
    }
    div[data-testid="stRadio"] label p { font-size: 13px !important; font-weight: normal !important; }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] p {
        color: #000 !important; font-weight: bold !important;
    }

    /* 報價與按鈕 */
    .price-big { font-size: 2.8rem; font-weight: 800; margin: 5px 0; line-height: 1.1; }
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; }
    
    /* 左右並排按鈕專用 */
    .stLinkButton a, .stButton button {
        display: flex; justify-content: center; align-items: center;
        width: 100%; height: 48px;
        border-radius: 12px; font-weight: bold;
        text-decoration: none;
        margin: 0;
    }
    .stLinkButton a {
        background: #6e00ff !important; color: white !important;
    }
    .stButton button {
        background: rgba(255,255,255,0.15); color: white;
        border: 1px solid rgba(255,255,255,0.3);
    }
    .stButton button:hover { border-color: #FFD700; color: #FFD700; background: rgba(255,255,255,0.25); }

    /* Plotly 圖表背景透明化，讓玻璃質感透出來 */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
    /* 大數據分數條 */
    .score-bar {
        height: 10px; width: 100%; background: #444; border-radius: 5px; overflow: hidden; margin-top:5px;
    }
    .score-fill { height: 100%; border-radius: 5px; transition: width 0.5s; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 資料與邏輯引擎 ---

@st.cache_data(ttl=86400) 
def get_chinese_name_from_yahoo(stock_id):
    if not stock_id[0].isdigit(): return None
    try:
        clean_id = stock_id.split('.')[0]
        url = f"https://tw.stock.yahoo.com/quote/{clean_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            start = r.text.find('<title>')
            end = r.text.find('</title>')
            if start != -1 and end != -1:
                title = r.text[start+7:end]
                if "(" in title: return title.split('(')[0].strip()
    except: pass
    return None

@st.cache_data(ttl=300)
def smart_search_stock(query):
    query = query.strip().upper()
    def try_fetch(ticker):
        try:
            s = yf.Ticker(ticker)
            if not s.history(period="5d").empty: return ticker, s.info
        except: pass
        return None, None

    found_ticker, found_info = None, None
    if query.isdigit():
        t, i = try_fetch(f"{query}.TW")
        if t: found_ticker, found_info = t, i
        else:
            t, i = try_fetch(f"{query}.TWO")
            if t: found_ticker, found_info = t, i
    elif ".TW" in query: found_ticker, found_info = try_fetch(query)
    else: found_ticker, found_info = try_fetch(query)

    stock_name = found_ticker
    if found_ticker:
        if ".TW" in found_ticker:
            cn_name = get_chinese_name_from_yahoo(found_ticker)
            if cn_name: stock_name = cn_name
            elif found_info and 'longName' in found_info: stock_name = found_info['longName']
        else:
            if found_info and 'longName' in found_info: stock_name = found_info['longName']
            
    return found_ticker, stock_name, found_info

@st.cache_data(ttl=300)
def get_stock_data_hybrid(ticker, interval, period_days=365):
    is_tw = ".TW" in ticker or ".TWO" in ticker
    is_intraday = interval in ["1m", "5m", "30m", "60m"]
    
    if is_tw and not is_intraday:
        try:
            stock_id = ticker.split('.')[0]
            dl = DataLoader(token=FINMIND_TOKEN)
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            if not df.empty:
                df = df.rename(columns={'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'})
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                if interval == "1wk": df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                elif interval == "1mo": df = df.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                return df
        except: pass
            
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
        
        def map_name(n):
            if '外資' in n: return '外資'
            if '投信' in n: return '投信'
            if '自營' in n: return '自營商'
            return '其他'
        df['type'] = df['name'].apply(map_name)
        df['net'] = (df['buy'] - df['sell']) / 1000
        pivot = df.pivot_table(index='date', columns='type', values='net', aggfunc='sum').fillna(0)
        return pivot.sort_index(ascending=False)
    except: return None

@st.cache_data(ttl=300)
def get_news_rss(ticker):
    """[爬蟲] Google News RSS"""
    try:
        q = ticker.replace(".TW", " TW").replace(".TWO", " TWO")
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall('.//item')[:8]:
            news.append({
                'title': item.find('title').text,
                'link': item.find('link').text,
                'date': item.find('pubDate').text[:16]
            })
        return news
    except: return []

def calculate_indicators(df):
    if df is None or len(df) < 5: return df
    if 'Volume' not in df.columns: df['Volume'] = 0
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def run_backtest(df):
    """[回測] 簡單均線策略"""
    bt_df = df.copy()
    bt_df['Signal'] = 0
    # 策略：MA5 > MA20 持有 (1)，否則空手 (0)
    bt_df.loc[bt_df['MA5'] > bt_df['MA20'], 'Signal'] = 1
    bt_df['Daily_Ret'] = bt_df['Close'].pct_change()
    bt_df['Strategy_Ret'] = bt_df['Signal'].shift(1) * bt_df['Daily_Ret']
    
    cum_ret = (1 + bt_df['Strategy_Ret']).cumprod()
    total_ret = (cum_ret.iloc[-1] - 1) * 100
    
    # 簡單統計
    win_days = len(bt_df[bt_df['Strategy_Ret'] > 0])
    total_trade_days = len(bt_df[bt_df['Signal'].shift(1) == 1])
    win_rate = (win_days / total_trade_days * 100) if total_trade_days > 0 else 0
    
    return total_ret, win_rate, bt_df

def calculate_big_data_score(df, chips_df):
    """[大數據] 計算多空分數 (0-100)"""
    score = 50 # 基礎分
    latest = df.iloc[-1]
    
    # 技術面 (佔 60%)
    if latest['Close'] > latest['MA20']: score += 15 # 站上月線
    if latest['MA5'] > latest['MA20']: score += 10 # 均線多排
    if latest['K'] > latest['D']: score += 10 # KD 金叉
    elif latest['K'] < 20: score += 5 # 超賣反彈機會
    
    # 籌碼面 (佔 40%) - 僅台股有效
    if chips_df is not None and not chips_df.empty:
        last_chip = chips_df.iloc[0]
        f = last_chip.get('外資', 0)
        t = last_chip.get('投信', 0)
        if f > 0: score += 10
        if t > 0: score += 15 # 投信權重較高
        if f > 0 and t > 0: score += 5 # 土洋合擊
        
    return min(100, max(0, score))

# --- 4. UI 主程式 ---

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Ultimate</h2>", unsafe_allow_html=True)

# 搜尋區
c1, c2 = st.columns([2.5, 1.5])
with c1:
    query = st.text_input("搜股", placeholder="輸入代號 (4903, 2330, AI)...")
    if query:
        with st.spinner("🕷️ 智能搜尋..."):
            t, n, i = smart_search_stock(query)
            if t:
                st.session_state.current_ticker = t
                st.session_state.current_name = n
                st.session_state.current_info = i
                st.rerun()
            else:
                st.error(f"❌ 找不到：{query}")
with c2:
    watch_select = st.selectbox("⭐ 我的自選", ["(切換股票)"] + st.session_state.watchlist)
    if watch_select != "(切換股票)":
        st.session_state.current_ticker = watch_select
        t, n, i = smart_search_stock(watch_select)
        st.session_state.current_name = n
        st.session_state.current_info = i

target = st.session_state.current_ticker
display_name = st.session_state.get('current_name', target)
info = st.session_state.get('current_info', {})

if target:
    # 預載日線
    df_daily = get_stock_data_hybrid(target, "1d", 365)
    
    if df_daily is not None and not df_daily.empty:
        df_daily = calculate_indicators(df_daily)
        chips_df = get_institutional_chips(target)
        
        # 報價區
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        yahoo_url = f"https://finance.yahoo.com/quote/{target}"
        if ".TW" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TW','')}"
        elif ".TWO" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TWO','')}"

        # Info Card
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size:1.4rem; font-weight:bold;">{display_name}</div>
                    <div style="font-size:0.9rem; opacity:0.7;">{target}</div>
                </div>
                <div style="text-align:right;">
                    <div class="{color_cls}" style="font-size:1.2rem; font-weight:bold;">
                        {arrow} {abs(change):.2f} ({abs(pct):.2f}%)
                    </div>
                </div>
            </div>
            <div class="{color_cls} price-big">{latest['Close']:.2f}</div>
            <div style="font-size:0.8rem; opacity:0.8;">
                量: {int(latest['Volume']/1000):,} K | K: {latest['K']:.1f} | D: {latest['D']:.1f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 按鈕區 (左右並排)
        b1, b2 = st.columns([1, 1])
        with b1: st.link_button("🔗 Yahoo 股市", yahoo_url)
        with b2:
            if target in st.session_state.watchlist:
                if st.button("🗑️ 移除自選"): toggle_watchlist(); st.rerun()
            else:
                if st.button("❤️ 加入自選"): toggle_watchlist(); st.rerun()

        # 分頁功能
        tabs = st.tabs(["📈 K線圖", "📊 大數據分析", "📰 新聞", "🔙 策略回測", "🏛️ 籌碼"])
        
        with tabs[0]:
            # K線圖 (含十字線、獨立KD、縮放)
            t_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            sel_p = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = t_map[sel_p]
            p_days = 5 if interval in ["1m", "5m"] else 365
            
            with st.spinner("繪製專業圖表..."):
                df_chart = get_stock_data_hybrid(target, interval, p_days)
                if df_chart is not None:
                    df_chart = calculate_indicators(df_chart)
                    
                    # 建立雙子圖 (上方 K線, 下方 KD)
                    fig = make_subplots(
                        rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3], vertical_spacing=0.03,
                        subplot_titles=(f"{target} K線走勢", "KD 指標")
                    )
                    
                    # Row 1: K線 + 均線
                    fig.add_trace(go.Candlestick(
                        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
                        name="K線", increasing_line_color='#ff5252', decreasing_line_color='#00e676'
                    ), row=1, col=1)
                    
                    if 'MA5' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='cyan', width=1), name='MA5'), row=1, col=1)
                    if 'MA20' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)

                    # Row 2: KD
                    if 'K' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['K'], line=dict(color='#ff5252', width=1.5), name='K'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['D'], line=dict(color='#00e676', width=1.5), name='D'), row=2, col=1)
                        # 加入 80/20 參考線
                        fig.add_hline(y=80, line_dash="dot", line_color="gray", row=2, col=1)
                        fig.add_hline(y=20, line_dash="dot", line_color="gray", row=2, col=1)

                    # 樣式設定 (十字線、縮放)
                    fig.update_layout(
                        height=550, margin=dict(l=10, r=40, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20, 20, 20, 0.7)',
                        font=dict(color='#eee'), showlegend=False,
                        dragmode='pan', # 預設拖曳平移
                        hovermode='x unified' # 統一顯示十字線資訊
                    )
                    
                    # 十字線 (Crosshair) 設定
                    axes_dict = dict(
                        showspikes=True, spikemode='across', spikesnap='cursor', 
                        showline=True, spikedash='dash', spikecolor="rgba(255,255,255,0.5)", spikethickness=1,
                        gridcolor='rgba(255,255,255,0.1)'
                    )
                    fig.update_xaxes(**axes_dict, row=1, col=1)
                    fig.update_yaxes(**axes_dict, row=1, col=1)
                    fig.update_xaxes(**axes_dict, row=2, col=1)
                    fig.update_yaxes(**axes_dict, row=2, col=1)
                    
                    # 啟用滑鼠滾輪縮放
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                else:
                    st.warning("無資料")

        with tabs[1]:
            # 大數據戰情分析
            score = calculate_big_data_score(df_daily, chips_df)
            color = "#ff5252" if score >= 60 else "#00e676" if score <= 40 else "#FFFF00"
            sentiment = "🔥 極度看多" if score >= 80 else "📈 偏多操作" if score >= 60 else "⚖️ 多空震盪" if score >= 40 else "📉 偏空修正"
            
            summary = info.get('longBusinessSummary', '')[:100] + "..." if info.get('longBusinessSummary') else "無公司簡介"

            st.markdown(f"""
            <div class="glass-card">
                <h3>📊 大數據戰力評分：<span style="color:{color}">{score} 分</span></h3>
                <div class="score-bar"><div class="score-fill" style="width:{score}%; background-color:{color};"></div></div>
                <p style="margin-top:10px; font-weight:bold;">{sentiment}</p>
                <hr style="border-color:#555">
                <p><b>🏢 公司題材：</b>{summary}</p>
                <p><b>💡 智能解讀：</b></p>
                <ul>
                    <li>技術面：股價 {'站上' if latest['Close']>latest['MA20'] else '跌破'} 月線，KD指標 {latest['K']:.1f}/{latest['D']:.1f}。</li>
                    <li>籌碼面：{'FinMind 數據顯示有法人進駐' if score > 60 else '法人動向不明或偏保守'}。</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with tabs[2]:
            # 個股新聞
            st.markdown(f"#### 📰 {display_name} 最新消息")
            news_items = get_news_rss(target)
            if news_items:
                for n in news_items:
                    st.markdown(f"""
                    <div style="border-bottom:1px solid #333; padding:10px;">
                        <a href="{n['link']}" target="_blank" style="color:#4FC3F7; text-decoration:none; font-size:1.1rem; font-weight:bold;">{n['title']}</a>
                        <div style="color:#888; font-size:0.8rem; margin-top:5px;">{n['date']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暫無相關新聞")

        with tabs[3]:
            # 回測系統
            st.markdown("#### 🔙 均線策略回測 (MA5 黃金交叉 MA20)")
            ret, win, bt_data = run_backtest(df_daily)
            
            c_res1, c_res2 = st.columns(2)
            ret_color = "#ff5252" if ret > 0 else "#00e676"
            c_res1.markdown(f"<div class='glass-card' style='text-align:center'>總報酬率<br><span style='color:{ret_color};font-size:1.5rem'>{ret:.1f}%</span></div>", unsafe_allow_html=True)
            c_res2.markdown(f"<div class='glass-card' style='text-align:center'>交易勝率<br><span style='color:#FFD700;font-size:1.5rem'>{win:.1f}%</span></div>", unsafe_allow_html=True)
            
            with st.expander("查看詳細交易數據"):
                st.dataframe(bt_data[['Close', 'MA5', 'MA20', 'Signal', 'Strategy_Ret']].tail(30), use_container_width=True)

        with tabs[4]:
            # 籌碼 (FinMind)
            if chips_df is not None:
                st.markdown("<div class='glass-card'><h4>🏛️ 三大法人買賣超</h4></div>", unsafe_allow_html=True)
                st.dataframe(chips_df.head(20).style.format("{:.0f}"), use_container_width=True)
            else:
                st.info("⚠️ 僅台股支援籌碼數據")

