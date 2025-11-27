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

# FinMind API Token (用於抓取精準的台股籌碼)
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

# --- 3. 核心邏輯：爬蟲與資料獲取 ---

@st.cache_data(ttl=86400) # 名稱快取一天
def get_chinese_name_from_yahoo(stock_id):
    """
    [爬蟲] 直接爬取 Yahoo 股市的標題來取得最準確的中文名稱
    """
    # 僅針對台股數字代號
    if not stock_id[0].isdigit(): return None
    
    try:
        # 去掉 .TW/.TWO
        clean_id = stock_id.split('.')[0]
        url = f"https://tw.stock.yahoo.com/quote/{clean_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=3)
        
        # 簡單解析 HTML title
        # 格式通常是: <title>台積電(2330) - 個股走勢...</title>
        if r.status_code == 200:
            start = r.text.find('<title>')
            end = r.text.find('</title>')
            if start != -1 and end != -1:
                title = r.text[start+7:end]
                # 提取中文部分： "台積電(2330)" -> "台積電"
                if "(" in title:
                    name = title.split('(')[0].strip()
                    return name
    except: pass
    return None

@st.cache_data(ttl=300)
def smart_search_stock(query):
    """
    [智能搜股] 解決找不到股票的問題
    1. 判斷是否為數字 -> 嘗試上市/上櫃
    2. 檢查 yfinance 資料是否存在
    3. 抓取中文名稱
    """
    query = query.strip().upper()
    
    def try_fetch(ticker):
        try:
            s = yf.Ticker(ticker)
            # 必須有歷史資料才算有效
            h = s.history(period="5d")
            if not h.empty:
                return ticker, s.info
        except: pass
        return None, None

    found_ticker = None
    found_info = None

    # A. 數字代號 (台股)
    if query.isdigit():
        # 1. 嘗試上市
        t, i = try_fetch(f"{query}.TW")
        if t: 
            found_ticker, found_info = t, i
        else:
            # 2. 嘗試上櫃 (解決 4903 找不到的問題)
            t, i = try_fetch(f"{query}.TWO")
            if t: found_ticker, found_info = t, i
    
    # B. 已有後綴 (如 2330.TW)
    elif ".TW" in query:
        found_ticker, found_info = try_fetch(query)
        
    # C. 美股/英文 (如 AI, NVDA)
    else:
        found_ticker, found_info = try_fetch(query)

    # 如果找到了，嘗試優化名稱 (爬蟲)
    stock_name = found_ticker
    if found_ticker:
        # 如果是台股，優先用爬蟲抓中文名
        if ".TW" in found_ticker:
            cn_name = get_chinese_name_from_yahoo(found_ticker)
            if cn_name: stock_name = cn_name
            elif found_info and 'longName' in found_info: stock_name = found_info['longName']
        else:
            # 美股用 info
            if found_info and 'longName' in found_info: stock_name = found_info['longName']
            
    return found_ticker, stock_name, found_info

@st.cache_data(ttl=300)
def get_institutional_chips(ticker):
    """
    [籌碼] 使用 FinMind 抓取外資/投信/自營商
    """
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split('.')[0]
    
    try:
        dl = DataLoader(token=FINMIND_TOKEN)
        # 抓最近 30 天
        start_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        
        # 整理數據
        def map_name(n):
            if '外資' in n or 'Foreign' in n: return '外資'
            if '投信' in n: return '投信'
            if '自營' in n: return '自營商'
            return '其他'
            
        df['type'] = df['name'].apply(map_name)
        df['net'] = (df['buy'] - df['sell']) / 1000 # 換算張數
        
        # 轉成寬表格
        pivot = df.pivot_table(index='date', columns='type', values='net', aggfunc='sum').fillna(0)
        pivot = pivot.sort_index(ascending=False)
        return pivot
    except: return None

def calculate_indicators(df):
    if df is None or len(df) < 20: return df
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def get_detailed_analysis(ticker, name, df, chips_df, info):
    """
    [詳細分析報告生成]
    """
    latest = df.iloc[-1]
    close = latest['Close']
    ma5 = latest.get('MA5', 0)
    ma10 = latest.get('MA10', 0)
    ma20 = latest.get('MA20', 0)
    k = latest.get('K', 50)
    d = latest.get('D', 50)
    
    # 1. 趨勢判斷
    trend = "震盪"
    trend_color = "#FFFF00"
    if close > ma20 and ma5 > ma10: 
        trend = "多頭強勢"
        trend_color = "#ff5252"
    elif close < ma20 and ma5 < ma10: 
        trend = "空方控盤"
        trend_color = "#00e676"
    
    # 2. KD 訊號
    kd_sig = "中性"
    if k > d and k < 80: kd_sig = "黃金交叉 (偏多)"
    elif k < d and k > 20: kd_sig = "死亡交叉 (偏空)"
    
    # 3. 籌碼解讀 (最近一日)
    chip_msg = "無籌碼資料 (美股)"
    if chips_df is not None and not chips_df.empty:
        last_chip = chips_df.iloc[0] # 最近一天
        f_buy = last_chip.get('外資', 0)
        t_buy = last_chip.get('投信', 0)
        
        if f_buy > 0 and t_buy > 0: chip_msg = "土洋同步買超，籌碼安定。"
        elif f_buy < 0 and t_buy < 0: chip_msg = "土洋同步賣超，壓力大。"
        elif t_buy > 0: chip_msg = "投信進場護盤/佈局。"
        elif f_buy > 0: chip_msg = "外資買盤回補。"
        else: chip_msg = "法人動向不明顯。"
        
    # 4. 產業題材
    summary = info.get('longBusinessSummary', '')
    sector = info.get('sector', '未知產業')
    if len(summary) > 100: summary = summary[:100] + "..."
    elif not summary: summary = "暫無詳細資料。"

    return f"""
    <div class="glass-card">
        <h3>📝 {name} 戰情分析</h3>
        <p><b>🏢 產業地位：</b>{sector}</p>
        <p style="font-size:0.9rem; opacity:0.8">{summary}</p>
        <hr style="border-color:rgba(255,255,255,0.2)">
        
        <h4>📊 技術面診斷</h4>
        <table class="analysis-table" style="width:100%">
            <tr>
                <td>趨勢</td>
                <td><span style="color:{trend_color}; font-weight:bold">{trend}</span> (股價 vs 月線)</td>
            </tr>
            <tr>
                <td>KD 指標</td>
                <td>K={k:.1f}, D={d:.1f} <br> <b>{kd_sig}</b></td>
            </tr>
            <tr>
                <td>關鍵均線</td>
                <td>MA5: {ma5:.1f} / MA20: {ma20:.1f}</td>
            </tr>
        </table>
        
        <h4 style="margin-top:15px">🏛️ 籌碼面解讀</h4>
        <p>{chip_msg}</p>
    </div>
    """

# --- 4. UI 主程式 ---

st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>🦖 武吉拉 Wujila Pro</h2>", unsafe_allow_html=True)

# 搜尋區
c1, c2 = st.columns([2.5, 1.5])
with c1:
    # 支援代號直接搜尋
    query = st.text_input("搜股 (輸入 4903, 2330, AI...)", placeholder="代號自動辨識...")
    if query:
        with st.spinner("🕷️ 智能搜股中..."):
            t, n, i = smart_search_stock(query)
            if t:
                st.session_state.current_ticker = t
                st.session_state.current_name = n # 存起來避免重複爬
                st.session_state.current_info = i
                st.rerun()
            else:
                st.error(f"❌ 遍歷 Yahoo 資料庫仍找不到：{query}")

with c2:
    watch_select = st.selectbox("⭐ 我的自選", ["(切換股票)"] + st.session_state.watchlist)
    if watch_select != "(切換股票)":
        st.session_state.current_ticker = watch_select
        # 切換自選時也要更新名稱
        t, n, i = smart_search_stock(watch_select)
        st.session_state.current_name = n
        st.session_state.current_info = i

# 取得當前股票資訊
target = st.session_state.current_ticker
# 優先使用存的中文名，沒有則用代號
display_name = st.session_state.get('current_name', target)
display_info = st.session_state.get('current_info', {})

if target:
    # 預載資料
    df_daily = yf.Ticker(target).history(period="3mo", interval="1d")
    df_daily = calculate_indicators(df_daily)
    
    if not df_daily.empty:
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        change = latest['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        
        color_cls = "price-up" if change >= 0 else "price-down"
        arrow = "▲" if change >= 0 else "▼"
        
        # Yahoo 連結
        yahoo_url = f"https://finance.yahoo.com/quote/{target}"
        if ".TW" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TW','')}"
        elif ".TWO" in target: yahoo_url = f"https://tw.stock.yahoo.com/quote/{target.replace('.TWO','')}"

        # --- A. 報價卡片 (顯示中文名) ---
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size:1.4rem; opacity:1; font-weight:bold;">{display_name}</div>
                    <div style="font-size:0.9rem; opacity:0.7;">{target}</div>
                </div>
                <div style="text-align:right;">
                    <div class="{color_cls}" style="font-size:1.2rem; font-weight:bold;">
                        {arrow} {abs(change):.2f} ({abs(pct):.2f}%)
                    </div>
                </div>
            </div>
            <div class="{color_cls} price-big">{latest['Close']:.2f}</div>
            <div style="font-size:0.8rem; opacity:0.8; display:flex; gap:15px;">
                <span>量: {int(latest['Volume']/1000):,} K</span>
                <span>MA5: {latest['MA5']:.2f}</span>
                <span>MA20: {latest['MA20']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- B. 操作按鈕 (左右並排) ---
        b1, b2 = st.columns(2)
        with b1:
            st.link_button("🔗 Yahoo 股市", yahoo_url)
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
            
            # 資料抓取
            period = "1d" if interval in ["1m", "5m", "30m", "60m"] else "1y"
            df_chart = yf.Ticker(target).history(period=period, interval=interval)
            
            if not df_chart.empty:
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
                # 網格
                grid_c = 'rgba(255,255,255,0.1)'
                fig.update_xaxes(showgrid=True, gridcolor=grid_c, row=1, col=1)
                fig.update_yaxes(showgrid=True, gridcolor=grid_c, row=1, col=1)
                fig.update_yaxes(showgrid=True, gridcolor=grid_c, row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("此週期暫無資料")

        with tabs[1]:
            # 生成詳細分析報告
            chips_df = get_institutional_chips(target)
            html_report = get_detailed_analysis(target, display_name, df_daily, chips_df, display_info)
            st.markdown(html_report, unsafe_allow_html=True)
            
        with tabs[2]:
            # 籌碼表格
            chips_df = get_institutional_chips(target)
            if chips_df is not None:
                st.markdown("<div class='glass-card'><h4>🏛️ 三大法人買賣超 (張)</h4></div>", unsafe_allow_html=True)
                # 格式化表格
                st.dataframe(chips_df.head(20).style.format("{:.0f}"), use_container_width=True)
                st.caption("* 數據來源: FinMind (延遲更新)")
            else:
                st.info("⚠️ 無籌碼資料 (僅支援台股)")

