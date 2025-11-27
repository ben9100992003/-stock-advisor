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
st.set_page_config(page_title="武吉拉 Wujila Pro+", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# 您的 FinMind Token
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

# --- 2. 視覺樣式 (Glassmorphism) ---
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

    /* 報價 */
    .price-big { font-size: 2.8rem; font-weight: 800; margin: 5px 0; line-height: 1.1; }
    .price-up { color: #ff5252 !important; }
    .price-down { color: #00e676 !important; }
    
    /* 按鈕樣式 */
    .stButton button {
        width: 100%; height: 48px;
        background: rgba(255,255,255,0.15); color: white;
        border-radius: 12px; border: 1px solid rgba(255,255,255,0.3);
        font-weight: bold;
    }
    .stButton button:hover { border-color: #FFD700; color: #FFD700; background: rgba(255,255,255,0.25); }
    
    .stLinkButton a {
        display: flex; justify-content: center; align-items: center;
        width: 100%; height: 48px;
        background: #6e00ff !important; color: white !important;
        border-radius: 12px; text-decoration: none; font-weight: bold;
    }

    /* Plotly 背景 */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
    /* 分析表格 */
    .analysis-table td { padding: 5px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- 3. 資料引擎 (FinMind + Yahoo 混合) ---

@st.cache_data(ttl=86400) 
def get_chinese_name_from_yahoo(stock_id):
    """[爬蟲] 抓取中文名稱"""
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
    """[智能搜股] 支援代號/英文/中文"""
    query = query.strip().upper()
    def try_fetch(ticker):
        try:
            s = yf.Ticker(ticker)
            h = s.history(period="5d")
            if not h.empty: return ticker, s.info
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
    """
    [混合資料引擎]
    1. 如果是台股日線/週線 -> 優先用 FinMind (使用您的 Token)
    2. 如果是台股分時(1m/5m) -> 用 Yahoo (FinMind 日線無分時)
    3. 如果是美股 -> 用 Yahoo
    """
    is_tw = ".TW" in ticker or ".TWO" in ticker
    is_intraday = interval in ["1m", "5m", "30m", "60m"]
    
    # --- 情境 A: 台股日線/長線 (使用 FinMind) ---
    if is_tw and not is_intraday:
        try:
            stock_id = ticker.split('.')[0]
            dl = DataLoader(token=FINMIND_TOKEN)
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            
            # 抓取股價
            df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            
            if not df.empty:
                # 格式轉換為 Yahoo 格式以相容後續計算
                df = df.rename(columns={
                    'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'
                })
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                
                # FinMind 沒有調整後股價，若需要可改用 taiwan_stock_daily_adj
                # 這裡為了 K 線圖真實性，使用原始股價
                
                # Resample 如果需要週/月線
                if interval == "1wk":
                    df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                elif interval == "1mo":
                    df = df.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                
                return df
        except Exception as e:
            pass # 失敗則自動降級回 Yahoo
            
    # --- 情境 B: 台股分時 或 美股 (使用 Yahoo) ---
    try:
        yf_period = "1d" if is_intraday else ("1y" if period_days < 500 else "2y")
        stock = yf.Ticker(ticker)
        df = stock.history(period=yf_period, interval=interval)
        if df.empty: return None
        return df
    except: return None

@st.cache_data(ttl=300)
def get_institutional_chips(ticker):
    """[籌碼] 使用 FinMind Token 抓取"""
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
        pivot = pivot.sort_index(ascending=False)
        return pivot
    except: return None

@st.cache_data(ttl=3600)
def get_financial_per(ticker):
    """[基本面] 使用 FinMind 抓取本益比/殖利率"""
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split('.')[0]
    try:
        dl = DataLoader(token=FINMIND_TOKEN)
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_per_pbr(stock_id=stock_id, start_date=start_date)
        if not df.empty:
            return df.iloc[-1] # 回傳最新一筆
    except: pass
    return None

def calculate_indicators(df):
    if df is None or len(df) < 5: return df
    # 確保有 Volume 欄位
    if 'Volume' not in df.columns: df['Volume'] = 0
    
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def get_detailed_analysis(ticker, name, df, chips_df, fin_data, info):
    """詳細分析報告 (整合 FinMind 數據)"""
    latest = df.iloc[-1]
    close = latest['Close']
    ma5 = latest.get('MA5', 0)
    ma10 = latest.get('MA10', 0)
    ma20 = latest.get('MA20', 0)
    k = latest.get('K', 50)
    d = latest.get('D', 50)
    
    # 趨勢
    trend = "震盪"
    trend_color = "#FFFF00"
    if close > ma20 and ma5 > ma10: trend = "多頭強勢"; trend_color = "#ff5252"
    elif close < ma20 and ma5 < ma10: trend = "空方控盤"; trend_color = "#00e676"
    
    # KD
    kd_sig = "中性"
    if k > d and k < 80: kd_sig = "黃金交叉 (偏多)"
    elif k < d and k > 20: kd_sig = "死亡交叉 (偏空)"
    
    # 籌碼
    chip_msg = "無籌碼資料 (美股)"
    if chips_df is not None and not chips_df.empty:
        last = chips_df.iloc[0]
        f = last.get('外資', 0)
        t = last.get('投信', 0)
        if f > 0 and t > 0: chip_msg = "土洋同步買超，籌碼安定。"
        elif f < 0 and t < 0: chip_msg = "土洋同步賣超，壓力大。"
        elif t > 0: chip_msg = "投信佈局中。"
        elif f > 0: chip_msg = "外資回補中。"
        else: chip_msg = "法人動向不明顯。"
        
    # 基本面 (FinMind)
    per_info = "N/A"
    yield_info = "N/A"
    if fin_data is not None:
        if 'PER' in fin_data and fin_data['PER'] > 0: per_info = f"{fin_data['PER']:.1f} 倍"
        if 'dividend_yield' in fin_data: yield_info = f"{fin_data['dividend_yield']:.1f} %"
        
    summary = info.get('longBusinessSummary', '')[:100] + "..." if info.get('longBusinessSummary') else "暫無詳細資料"

    return f"""
    <div class="glass-card">
        <h3>📝 {name} 戰情室</h3>
        <p><b>🏢 產業：</b>{info.get('sector', '未知')}</p>
        <div style="display:flex; gap:15px; margin-bottom:10px;">
            <div style="background:rgba(255,255,255,0.1); padding:8px; border-radius:8px;">本益比: <b>{per_info}</b></div>
            <div style="background:rgba(255,255,255,0.1); padding:8px; border-radius:8px;">殖利率: <b>{yield_info}</b></div>
        </div>
        <p style="font-size:0.9rem; opacity:0.8">{summary}</p>
        <hr style="border-color:rgba(255,255,255,0.2)">
        
        <h4>📊 技術面</h4>
        <table class="analysis-table" style="width:100%">
            <tr><td>趨勢</td><td><span style="color:{trend_color}; font-weight:bold">{trend}</span></td></tr>
            <tr><td>KD</td><td>K={k:.1f}, D={d:.1f} ({kd_sig})</td></tr>
            <tr><td>均線</td><td>MA5: {ma5:.1f} / MA20: {ma20:.1f}</td></tr>
        </table>
        
        <h4 style="margin-top:15px">🏛️ 籌碼面 (FinMind)</h4>
        <p>{chip_msg}</p>
    </div>
    """

# --- 4. UI 主程式 ---

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Wujila Pro+</h2>", unsafe_allow_html=True)

c1, c2 = st.columns([2.5, 1.5])
with c1:
    query = st.text_input("搜股 (輸入代號如 4903, 2330...)", placeholder="代號自動辨識...")
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
display_info = st.session_state.get('current_info', {})

if target:
    # 預設日線 (使用混合引擎)
    df_daily = get_stock_data_hybrid(target, "1d", 365)
    
    if df_daily is not None and not df_daily.empty:
        df_daily = calculate_indicators(df_daily)
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        yahoo_url = f"https://finance.yahoo.com/quote/{target}"
        if ".TW" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TW','')}"
        elif ".TWO" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TWO','')}"

        # --- A. 報價卡片 ---
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
                量: {int(latest['Volume']/1000):,} K | 高: {latest['High']:.2f} | 低: {latest['Low']:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- B. 操作按鈕 ---
        b1, b2 = st.columns(2)
        with b1: st.link_button("🔗 Yahoo 股市", yahoo_url)
        with b2:
            if target in st.session_state.watchlist:
                if st.button("🗑️ 移除自選"): toggle_watchlist(); st.rerun()
            else:
                if st.button("❤️ 加入自選"): toggle_watchlist(); st.rerun()

        # --- C. 功能分頁 ---
        tabs = st.tabs(["📈 K線圖", "📝 詳細分析", "🏛️ 法人籌碼"])
        
        with tabs[0]:
            t_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            sel_p = st.radio("週期", list(t_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = t_map[sel_p]
            
            # 使用混合引擎抓資料
            # 1分/5分: 抓 1-5 天; 日線: 抓 1 年
            p_days = 5 if interval in ["1m", "5m"] else 365
            with st.spinner("抓取 FinMind / Yahoo 資料..."):
                df_chart = get_stock_data_hybrid(target, interval, p_days)
            
            if df_chart is not None and not df_chart.empty:
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

                fig.update_layout(
                    height=450, margin=dict(l=10, r=40, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20, 20, 20, 0.7)',
                    font=dict(color='#eee'), xaxis_rangeslider_visible=False, showlegend=False, dragmode='pan'
                )
                grid_c = 'rgba(255,255,255,0.1)'
                fig.update_xaxes(showgrid=True, gridcolor=grid_c, row=1, col=1)
                fig.update_yaxes(showgrid=True, gridcolor=grid_c, row=1, col=1)
                fig.update_yaxes(showgrid=True, gridcolor=grid_c, row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("此週期暫無資料")

        with tabs[1]:
            # 基本面資料 (FinMind)
            fin_data = get_financial_per(target)
            chips_df = get_institutional_chips(target)
            
            html_report = get_detailed_analysis(target, display_name, df_daily, chips_df, fin_data, display_info)
            st.markdown(html_report, unsafe_allow_html=True)
            
        with tabs[2]:
            chips_df = get_institutional_chips(target)
            if chips_df is not None:
                st.markdown("<div class='glass-card'><h4>🏛️ 三大法人買賣超 (張)</h4></div>", unsafe_allow_html=True)
                st.dataframe(chips_df.head(20).style.format("{:.0f}"), use_container_width=True)
                st.caption("* 數據來源: FinMind")
            else:
                st.info("⚠️ 美股無法人籌碼資料")

