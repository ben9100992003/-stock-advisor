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
import xml.etree.ElementTree as ET 

# --- 0. 設定與金鑰 ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS 樣式 (視覺核心修復) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_png_as_page_bg(png_file):
    # 如果找不到圖片，使用深色背景作為備案，確保不會全白
    if not os.path.exists(png_file): 
        st.markdown('<style>.stApp {background-color: #1a1a1a;}</style>', unsafe_allow_html=True)
        return
        
    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str: return
    
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 請確保同目錄下有此圖片，或更換為您想用的圖片
set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* ----------------------------------------------------------------
       1. 全局重置與字體顏色 (強制黑字)
       ---------------------------------------------------------------- */
    /* 隱藏預設選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 針對主要內容容器設定 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* 所有文字預設黑色，除了特定標題 */
    .stMarkdown p, .stMarkdown li, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown span {
        color: #000000 !important;
        text-shadow: none !important;
    }
    
    /* ----------------------------------------------------------------
       2. 白底卡片系統 (Layer 2)
       ---------------------------------------------------------------- */
    .content-card, .quote-card, .kd-card, .market-summary-box {
        background-color: #ffffff !important;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: 1px solid #e0e0e0;
    }

    /* ----------------------------------------------------------------
       3. 橫向滑動按鈕組 (K線週期選單) - 手機優化關鍵
       ---------------------------------------------------------------- */
    /* 鎖定 Radio 按鈕容器 */
    [data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap; /* 禁止換行 */
        overflow-x: auto;  /* 允許橫向滑動 */
        gap: 8px;
        padding-bottom: 10px; /* 預留滑動條空間 */
        -webkit-overflow-scrolling: touch; /* 讓 iOS 滑動更順暢 */
    }

    /* 隱藏醜醜的滑動條 (Chrome/Safari) */
    [data-testid="stRadio"] > div::-webkit-scrollbar {
        height: 4px;
    }
    [data-testid="stRadio"] > div::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 4px;
    }

    /* 按鈕本體樣式 (未選中) */
    [data-testid="stRadio"] label {
        background-color: #f0f0f0 !important;
        color: #333 !important;
        border: 1px solid #ccc;
        border-radius: 20px;
        padding: 8px 16px !important;
        min-width: 60px; /* 確保按鈕有最小寬度，好點擊 */
        text-align: center;
        margin-right: 0 !important;
        white-space: nowrap; /* 文字不換行 */
        transition: all 0.2s;
        cursor: pointer;
    }

    /* 按鈕文字 */
    [data-testid="stRadio"] label p {
        font-weight: bold !important;
        font-size: 1rem !important;
        margin: 0 !important;
        color: #333 !important;
    }

    /* 選中狀態 (Checked) */
    [data-testid="stRadio"] label[data-checked="true"] {
        background-color: #222 !important; /* 深黑色背景 */
        border-color: #FFD700 !important; /* 金邊 */
    }
    
    [data-testid="stRadio"] label[data-checked="true"] p {
        color: #FFD700 !important; /* 金字 */
    }

    /* ----------------------------------------------------------------
       4. 輸入框與 SelectBox 優化
       ---------------------------------------------------------------- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important; /* 金框 */
        border-radius: 12px;
        font-weight: bold;
    }
    /* 輸入框上方的 Label */
    .stTextInput label, .stSelectbox label {
        color: #ffffff !important;
        font-size: 1.1rem;
        font-weight: bold;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }

    /* ----------------------------------------------------------------
       5. 卡片內部細節
       ---------------------------------------------------------------- */
    /* 報價大字 */
    .price-big { font-size: 3.5rem !important; font-weight: 800; line-height: 1.1; margin: 10px 0; }
    .stock-title { font-size: 1.5rem; font-weight: 900; color: #000; }
    .stock-id { font-size: 1rem; color: #666 !important; }
    
    /* 統計網格 */
    .stats-grid { display: flex; justify-content: space-between; border-top: 1px solid #eee; padding-top: 10px; margin-top: 10px; }
    .stat-label { font-size: 0.8rem; color: #888 !important; display: block; }
    .stat-val { font-size: 1.1rem; font-weight: bold; color: #000 !important; }

    /* 分析報告標題 */
    h3 { 
        border-bottom: 3px solid #FFD700; 
        padding-bottom: 8px; 
        margin-bottom: 15px;
        color: #000 !important;
    }
    
    /* 表格樣式 */
    .analysis-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
    .analysis-table td, .analysis-table th { 
        border: 1px solid #eee; padding: 8px; text-align: center; color: #000 !important; 
    }
    .analysis-table th { background-color: #f9f9f9; font-weight: bold; }

    /* KD 卡片特化 */
    .kd-card { display: flex; justify-content: space-between; align-items: center; border-left-width: 8px; border-left-style: solid; }
    .kd-val { font-size: 1.8rem; font-weight: 900; color: #000 !important; }
    
    /* ----------------------------------------------------------------
       6. Tab 樣式
       ---------------------------------------------------------------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255,255,255,0.1);
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: nowrap;
        background-color: transparent;
        border: none;
        color: #fff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff !important;
        border-radius: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    /* 選中 Tab 的文字變黑 */
    .stTabs [aria-selected="true"] p {
        color: #000 !important;
    }
    /* 未選中 Tab 的文字變白 (因為在哥吉拉背景上) */
    .stTabs [aria-selected="false"] p {
        color: #fff !important;
        opacity: 0.8;
    }

    /* ----------------------------------------------------------------
       7. 標題與圖表修復
       ---------------------------------------------------------------- */
    h1 { 
        text-shadow: 3px 3px 8px #000; 
        color: #FFFFFF !important; /* 只有主標題保持白色 */
        margin-bottom: 10px; 
        font-weight: 900; 
        text-align: center;
    }
    
    /* Plotly 圖表容器 - 強制白底，避免透明 */
    .js-plotly-plot .plotly .main-svg {
        background: #ffffff !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 (維持原樣，僅做錯誤處理優化) ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "3231.TW": "緯創", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "4903.TWO": "聯光通", "8110.TW": "華東", "6187.TWO": "萬潤", "3131.TWO": "弘塑",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "TSM": "台積電 ADR"
}

@st.cache_data(ttl=3600)
def get_market_hot_stocks():
    hot_tw = ["2330", "2317", "2603", "2609", "3231", "2454", "2382", "2303", "2615", "3231"]
    hot_us = ["NVDA", "TSLA", "AAPL", "AMD", "PLTR", "MSFT", "AMZN", "META", "GOOGL", "AVGO"]
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        latest_date = dl.taiwan_stock_daily_adj(stock_id="2330", start_date=(datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')).iloc[-1]['date']
        df = dl.taiwan_stock_daily_adj(start_date=latest_date)
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(15)
        if not top_df.empty: hot_tw = top_df['stock_id'].tolist()
    except: pass
    return hot_tw, hot_us

@st.cache_data(ttl=300)
def resolve_ticker(user_input):
    user_input = user_input.strip().upper()
    if user_input.isdigit():
        ticker_tw = f"{user_input}.TW"
        try:
            s = yf.Ticker(ticker_tw)
            if not s.history(period="1d").empty: return ticker_tw, s.info.get('longName', ticker_tw)
        except: pass
        
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

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split(".")[0]
    dl = DataLoader(token=FINMIND_API_TOKEN)
    try:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        
        def normalize_name(n):
            if '外資' in n or 'Foreign' in n: return 'Foreign'
            if '投信' in n or 'Trust' in n: return 'Trust'
            if '自營' in n or 'Dealer' in n: return 'Dealer'
            return 'Other'
        df['norm_name'] = df['name'].apply(normalize_name)
        df['net'] = df['buy'] - df['sell']
        
        pivot_df = df.pivot_table(index='date', columns='norm_name', values='net', aggfunc='sum').fillna(0)
        for col in ['Foreign', 'Trust', 'Dealer']:
            if col not in pivot_df.columns: pivot_df[col] = 0
            
        pivot_df = (pivot_df / 1000).astype(int)
        pivot_df = pivot_df.reset_index()
        pivot_df = pivot_df.rename(columns={'date': 'Date'})
        pivot_df['Date'] = pd.to_datetime(pivot_df['Date']).dt.strftime('%Y/%m/%d')
        return pivot_df
    except: return None

@st.cache_data(ttl=300)
def get_institutional_data_yahoo(ticker):
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        dfs = pd.read_html(r.text)
        target_df = None
        for df in dfs:
            if any('外資' in str(c) for c in df.columns): target_df = df; break
        if target_df is None: return None
        new_cols = {}
        for c in target_df.columns:
            s = str(c)
            if '日期' in s: new_cols[c] = 'Date'
            elif '外資' in s: new_cols[c] = 'Foreign'
            elif '投信' in s: new_cols[c] = 'Trust'
            elif '自營' in s: new_cols[c] = 'Dealer'
        target_df = target_df.rename(columns=new_cols)
        if 'Date' not in target_df.columns: return None
        df_clean = target_df.copy()
        def clean(x):
            if isinstance(x, str): return int(x.replace(',','').replace('+',''))
            return int(x) if isinstance(x, (int, float)) else 0
        for c in ['Foreign', 'Trust', 'Dealer']:
            if c in df_clean.columns: df_clean[c] = df_clean[c].apply(clean)
            else: df_clean[c] = 0
        df_clean['Date'] = df_clean['Date'].apply(lambda x: f"{datetime.now().year}/{x}" if len(x)<=5 else x)
        df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        df_clean.set_index('Date', inplace=True)
        res = df_clean.sort_index().reset_index()[['Date', 'Foreign', 'Trust', 'Dealer']].head(30)
        res['Date'] = res['Date'].dt.strftime('%Y/%m/%d')
        return res
    except: return None

@st.cache_data(ttl=300)
def get_google_news(ticker):
    try:
        query = f"{ticker} stock" if len(ticker)<5 else ticker.replace(".TW", " TW").replace(".TWO", " TWO")
        url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        resp = requests.get(url)
        root = ET.fromstring(resp.content)
        news_list = []
        for item in root.findall('.//item')[:10]:
            news_list.append({
                'title': item.find('title').text,
                'link': item.find('link').text,
                'pubDate': item.find('pubDate').text,
                'source': item.find('source').text if item.find('source') is not None else 'Google News'
            })
        return news_list
    except: return []

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def generate_narrative_report(name, ticker, latest, inst_df, df, info):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    # 邏輯生成 (維持不變)
    tech_trend = "盤整"
    tech_desc = ""
    if price > ma5 and ma5 > ma10 and ma10 > ma20:
        tech_trend = "多頭排列"
        tech_desc = "均線結構良好，顯示股價處於健康的上漲趨勢中。"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20:
        tech_trend = "空頭排列"
        tech_desc = "短線趨勢偏弱，上方壓力重重。"
    elif price > ma20:
        tech_trend = "站上月線"
        tech_desc = "中期趨勢偏多，唯短線可能震盪。"
    else:
        tech_trend = "跌破月線"
        tech_desc = "短線轉弱，需觀察季線支撐。"

    kd_status = "黃金交叉" if k > d else "死亡交叉"
    kd_desc = f"KD 指標 ({k:.1f}/{d:.1f}) 呈現 <b>{kd_status}</b>。"
    
    inst_table_html = "<tr><td colspan='4'>暫無資料</td></tr>"
    inst_desc = "暫無法人數據。"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        f_val, t_val, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f_val + t_val + d_val
        inst_desc = f"法人單日合計 <b>{'買超' if total>0 else '賣超'} {abs(total):,} 張</b>。"
        if f_val > 0 and t_val > 0: inst_desc += " 土洋同步看多，有利股價推升。"
        elif f_val < 0 and t_val < 0: inst_desc += " 土洋同步調節，籌碼面承壓。"
        
        inst_table_html = f"""
        <tr>
            <td>{last['Date']}</td>
            <td style="color:{'#e53935' if f_val>0 else '#43a047'}">{f_val:,}</td>
            <td style="color:{'#e53935' if t_val>0 else '#43a047'}">{t_val:,}</td>
            <td style="color:{'#e53935' if d_val>0 else '#43a047'}">{d_val:,}</td>
            <td style="color:{'#e53935' if total>0 else '#43a047'}"><b>{total:,}</b></td>
        </tr>
        """

    sector = info.get('sector', '科技')
    summary = info.get('longBusinessSummary', '暫無詳細說明。')[:120] + "..."
    theme_text = f"<b>{name}</b> 屬於 {sector} 產業。{summary}"
    
    support = ma10 if price > ma10 else ma20
    resistance = ma5 if price < ma5 else price * 1.05
    
    if price > ma20 and k > d:
        action = "偏多操作"
        entry = f"拉回至 5 日線 {ma5:.2f} 附近不破可佈局。"
        exit_pt = f"跌破月線 {ma20:.2f} 嚴設停損。"
    elif price < ma20 and k < d:
        action = "保守觀望"
        entry = f"等待站回月線 {ma20:.2f} 再考慮進場。"
        exit_pt = f"反彈至月線 {ma20:.2f} 遇壓可減碼。"
    else:
        action = "區間震盪"
        entry = f"箱型下緣 {support:.2f} 附近嘗試低接。"
        exit_pt = f"箱型上緣 {resistance:.2f} 附近獲利了結。"

    return f"""
    <div class="content-card">
        <h3>📊 {name} ({ticker}) 分析報告</h3>
        
        <h4>1. 技術指標分析</h4>
        <table class="analysis-table">
            <tr><td><b>收盤價</b></td><td>{price:.2f}</td><td><b>MA5</b></td><td>{ma5:.2f}</td></tr>
            <tr><td><b>MA20</b></td><td>{ma20:.2f}</td><td><b>KD</b></td><td>{k:.1f}/{d:.1f}</td></tr>
            <tr><td colspan="4"><b>趨勢：</b>{tech_trend}。{tech_desc} {kd_desc}</td></tr>
        </table>
        
        <h4>2. 三大法人籌碼</h4>
        <table class="analysis-table">
            <thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營</th><th>合計</th></tr></thead>
            <tbody>{inst_table_html}</tbody>
        </table>
        <p><b>籌碼：</b>{inst_desc}</p>
        
        <h4>3. 公司題材</h4>
        <p>{theme_text}</p>
        
        <h4>4. 💡 操作建議 ({action})</h4>
        <ul>
            <li><b>🟢 進場：</b>{entry}</li>
            <li><b>🔴 出場：</b>{exit_pt}</li>
        </ul>
        <p style="font-size:0.8rem; color:#888;">* 投資有風險，分析僅供參考。</p>
    </div>
    """

def analyze_market_index(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="6mo")
        if df.empty: return None
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        price = latest['Close']
        k, d = latest['K'], latest['D']
        change = price - df['Close'].iloc[-2]
        
        if price > latest['MA20']:
            status = "多頭強勢" if k > d else "多頭回檔"
            color = "#e53935" if k > d else "#ff9800"
        else:
            status = "空方修正" if k < d else "跌深反彈"
            color = "#43a047" if k < d else "#777"
            
        comment = f"KD:{k:.0f}/{d:.0f}"
        return {"price": price, "change": change, "status": status, "color": color, "comment": comment}
    except: return None

# --- 4. UI 主程式 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入熱門股..."):
    hot_tw, hot_us = get_market_hot_stocks()

# 搜尋區塊 (白底)
with st.container():
    c1, c2 = st.columns([3, 1])
    with c1:
        target_input = st.text_input("🔍 搜尋代號", value="2330")
    with c2:
        hot_stock = st.selectbox("🔥 熱門", ["(選股)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

# 搜尋邏輯
target = "2330.TW"
if hot_stock != "(選股)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input and target_input != "2330":
    t, n = resolve_ticker(target_input)
    if t: target = t; name = n
    else: st.error("❌ 查無此股"); target = None

# 大盤 (Expander)
with st.expander("🌍 今日大盤 (點擊展開)", expanded=False):
    c_tw, c_us = st.columns(2)
    with c_tw:
        tw = analyze_market_index("^TWII")
        if tw: st.markdown(f"<div class='market-summary-box'><b>台股加權</b><br><span style='color:{tw['color']};font-size:1.2rem'>{tw['price']:.0f} ({tw['change']:+.0f})</span><br>{tw['status']}</div>", unsafe_allow_html=True)
    with c_us:
        us = analyze_market_index("^IXIC")
        if us: st.markdown(f"<div class='market-summary-box'><b>那斯達克</b><br><span style='color:{us['color']};font-size:1.2rem'>{us['price']:.0f} ({us['change']:+.0f})</span><br>{us['status']}</div>", unsafe_allow_html=True)

if target:
    try:
        stock = yf.Ticker(target)
        info = stock.info
        if 'name' not in locals(): name = STOCK_NAMES.get(target, info.get('longName', target))
        
        # 取得數據
        df_fast = stock.history(period="5d")
        latest_fast = df_fast.iloc[-1]
        prev_close = df_fast['Close'].iloc[-2]
        price = latest_fast['Close']
        change = price - prev_close
        pct = (change / prev_close) * 100
        color = "#e53935" if change >= 0 else "#43a047"
        
        # --- 卡片 B: 報價卡片 ---
        st.markdown(f"""
        <div class="quote-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                <div>
                    <div class="stock-title">{name} <span class="stock-id">{target}</span></div>
                    <div class="price-big" style="color:{color};">{price:.2f}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.5rem; font-weight:bold; color:{color};">
                        {'▲' if change>=0 else '▼'} {abs(change):.2f} ({abs(pct):.2f}%)
                    </div>
                </div>
            </div>
            <div class="stats-grid">
                <div><span class="stat-label">最高</span><span class="stat-val" style="color:#e53935">{latest_fast['High']:.2f}</span></div>
                <div><span class="stat-label">最低</span><span class="stat-val" style="color:#43a047">{latest_fast['Low']:.2f}</span></div>
                <div><span class="stat-label">成交量</span><span class="stat-val">{latest_fast['Volume']/1000:.0f}K</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📈 K線圖", "📝 分析報告", "🏛️ 法人籌碼", "📰 新聞"])
        
        with tab1:
            # --- 卡片 C: 橫向滑動週期按鈕 ---
            # 使用 Streamlit Radio，但透過 CSS 強制變成橫向 Scroll
            st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
            interval_map = {"1分": "1m", "5分": "5m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
            period_label = st.radio("選擇週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 處理資料
            interval = interval_map[period_label]
            data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
            if interval == "1m": data_period = "7d"
            
            with st.spinner("繪製圖表中..."):
                df = stock.history(period=data_period, interval=interval)
                if df.empty:
                    st.warning("⚠️ 查無此週期資料")
                else:
                    if period_label == "10分": df = df.resample('10min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                    df = calculate_indicators(df)
                    latest = df.iloc[-1]
                    
                    # --- 卡片 D: Plotly K線圖 ---
                    # 建立圖表：確保底色為白，紅漲綠跌
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.02)
                    
                    # K線 (台灣: 紅漲綠跌)
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                        name='K線', increasing_line_color='#e53935', decreasing_line_color='#43a047'
                    ), row=1, col=1)
                    
                    # 均線
                    colors = {'MA5':'#1f77b4', 'MA10':'#ff7f0e', 'MA20':'#9467bd', 'MA60':'#2ca02c'}
                    for ma, c in colors.items():
                        if ma in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
                    
                    # KD
                    fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#e53935', width=1), name='K'), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#43a047', width=1), name='D'), row=2, col=1)
                    
                    # 設定顯示範圍 (Zoom to last 45 candles)
                    if len(df) > 45:
                        fig.update_xaxes(range=[df.index[-45], df.index[-1]], row=1, col=1)
                    
                    # 版面設定 (Mobile Friendly)
                    fig.update_layout(
                        height=500, # 固定高度
                        margin=dict(l=10, r=10, t=10, b=10),
                        template="plotly_white", # 強制白底
                        showlegend=False,
                        dragmode='pan', # 手機拖曳
                        hovermode='x unified',
                        xaxis_rangeslider_visible=False
                    )
                    
                    # 隱藏上方工具列 ModeBar，避免手機誤觸
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                    
                    # KD 卡片
                    k, d = latest['K'], latest['D']
                    kd_col = "#e53935" if k > d else "#43a047"
                    st.markdown(f"""
                    <div class="kd-card" style="border-left-color: {kd_col};">
                        <div><span style="font-weight:bold; color:#555;">KD 指標 (9,3,3)</span></div>
                        <div class="kd-val">{k:.1f} <span style="font-size:1rem; color:#888;">/</span> {d:.1f}</div>
                    </div>""", unsafe_allow_html=True)

        with tab2:
            # --- 卡片 E: 分析報告 ---
            inst_df = get_institutional_data_finmind(target)
            if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
            st.markdown(generate_narrative_report(name, target, latest, inst_df, df, info), unsafe_allow_html=True)

        with tab3:
            inst_df = get_institutional_data_finmind(target)
            if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
            if inst_df is not None and not inst_df.empty:
                st.markdown(f"<div class='content-card'><h3>🏛️ 法人買賣超</h3></div>", unsafe_allow_html=True)
                st.dataframe(inst_df.sort_values('Date', ascending=False).head(15), use_container_width=True)
            else:
                st.info("暫無資料")

        with tab4:
            st.markdown("<div class='content-card'><h3>📰 新聞</h3></div>", unsafe_allow_html=True)
            news_list = get_google_news(target)
            for news in news_list:
                st.markdown(f"<div style='padding:10px; border-bottom:1px solid #eee;'><a href='{news['link']}' target='_blank' style='font-size:1.1rem; font-weight:bold; color:#0056b3; text-decoration:none;'>{news['title']}</a><br><span style='font-size:0.8rem; color:#666;'>{news['pubDate']}</span></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"系統繁忙或查無資料: {e}")

