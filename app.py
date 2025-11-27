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

# --- 2. CSS 樣式 (視覺終極修復) ---
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

set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局字體設定 */
    .stApp { color: #333; font-family: "Microsoft JhengHei", sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 核心修復：卡片背景不透明度 --- */
    .quote-card, .content-card, .kd-card, .market-summary-box {
        background-color: rgba(255, 255, 255, 0.98) !important; /* 98% 不透明白底 */
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3); /* 加深陰影讓卡片浮起來 */
        margin-bottom: 20px;
        border: 1px solid #fff;
    }
    
    /* 強制卡片內文字為深黑色，解決看不見的問題 */
    .quote-card *, .content-card *, .kd-card *, .market-summary-box *, 
    .content-card h3, .content-card h4, .content-card p, .content-card li,
    .quote-card div, .quote-card span {
        color: #222222 !important;
        text-shadow: none !important;
    }

    /* --- 1. 報價卡片 (排版整齊化) --- */
    .stock-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px;
    }
    .stock-title { font-size: 1.6rem !important; font-weight: 900 !important; margin: 0; }
    .stock-id { font-size: 1.1rem !important; color: #666 !important; font-weight: normal; }
    
    .price-row {
        display: flex; align-items: baseline; gap: 15px; margin-bottom: 20px;
    }
    .price-big { font-size: 4rem !important; font-weight: 800 !important; line-height: 1; letter-spacing: -2px;}
    .price-change { font-size: 1.4rem !important; font-weight: 700 !important; }
    
    /* 四格數據排版 */
    .stats-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px 30px; /* 行距與列距 */
    }
    .stat-item {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px dashed #eee; padding-bottom: 5px;
    }
    .stat-label { font-size: 1rem !important; color: #777 !important; font-weight: 500; }
    .stat-val { font-weight: 700 !important; font-size: 1.1rem !important; }

    /* --- 2. 搜尋框 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 12px;
        font-size: 1.1rem;
        padding: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .stTextInput label { 
        color: #ffffff !important; 
        text-shadow: 2px 2px 4px #000; 
        font-weight: bold; font-size: 1.1rem; 
    }

    /* --- 3. KD 指標卡片 --- */
    .kd-card {
        border-left: 8px solid #2962ff;
        display: flex; align-items: center; justify-content: space-between;
        margin-top: 10px;
    }
    .kd-title { font-size: 1.3rem !important; font-weight: bold !important; }
    .kd-val { font-size: 2rem !important; font-weight: 800 !important; }

    /* --- 4. Tab 與 按鈕 --- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px; padding: 6px; gap: 8px;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #666 !important; font-weight: 700; font-size: 1.05rem; text-shadow: none !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {
        color: #000 !important;
    }

    /* 週期按鈕 (Radio) */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 5px;
        background-color: #fff; padding: 6px; border-radius: 20px;
        width: 100%; overflow-x: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #eee;
    }
    .stRadio div[role="radiogroup"] > label {
        flex: 1; text-align: center; padding: 8px 0;
        border-radius: 15px; margin: 0; border: none; cursor: pointer;
        min-width: 50px;
    }
    .stRadio div[role="radiogroup"] > label p {
        color: #555 !important; font-weight: bold; font-size: 0.95rem;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #333 !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        color: #fff !important;
    }

    /* 隱藏預設 Metric */
    [data-testid="stMetric"] { display: none; }
    
    /* 分析報告標題 */
    .content-card h3 { 
        border-bottom: 3px solid #FFD700; padding-bottom: 10px; font-size: 1.5rem !important;
    }

    /* 主標題 */
    h1 { text-shadow: 3px 3px 8px #000; color: white !important; margin-bottom: 20px; font-weight: 900; }
    
    /* Plotly 背景 */
    .js-plotly-plot .plotly .main-svg { background: white !important; border-radius: 12px; }
    
    /* 新聞 */
    .news-item { padding: 15px 0; border-bottom: 1px solid #eee; }
    .news-item a { text-decoration: none; color: #0056b3 !important; font-weight: 700; font-size: 1.1rem; }
    
    /* 連結按鈕 */
    .stLinkButton a { background-color: #fff !important; color: #333 !important; border: 1px solid #ccc !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航",
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
        query_ticker = ticker.replace(".TW", " TW").replace(".TWO", " TWO")
        if ".TW" not in ticker and ".TWO" not in ticker and len(ticker) < 5: query_ticker = f"{ticker} stock"
        url = f"https://news.google.com/rss/search?q={query_ticker}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
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
    df['MA240'] = df['Close'].rolling(240).mean()
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
    
    # 1. 技術面
    tech_trend = "盤整"
    tech_desc = ""
    if price > ma5 and ma5 > ma10 and ma10 > ma20:
        tech_trend = "多頭排列"
        tech_desc = "短線趨勢強勁，股價沿 5 日線攀升。"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20:
        tech_trend = "空頭排列"
        tech_desc = "上方壓力重重，反彈宜減碼。"
    elif price > ma20:
        tech_trend = "站上月線"
        tech_desc = "中期偏多，唯短線可能震盪。"
    else:
        tech_trend = "跌破月線"
        tech_desc = "短線轉弱，需觀察支撐。"

    kd_status = "黃金交叉" if k > d else "死亡交叉"
    kd_desc = f"KD 指標 ({k:.1f}/{d:.1f}) 呈現<b>{kd_status}</b>。"
    
    # 2. 籌碼面
    inst_table_html = "<tr><td colspan='4'>暫無資料</td></tr>"
    inst_desc = "暫無法人數據。"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        f_val, t_val, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f_val + t_val + d_val
        inst_desc = f"三大法人單日合計 <b>{'買超' if total>0 else '賣超'} {abs(total):,} 張</b>。"
        
        inst_table_html = f"""
        <tr>
            <td>{last['Date']}</td>
            <td style="color:{'#e53935' if f_val>0 else '#43a047'}">{f_val:,}</td>
            <td style="color:{'#e53935' if t_val>0 else '#43a047'}">{t_val:,}</td>
            <td style="color:{'#e53935' if d_val>0 else '#43a047'}">{d_val:,}</td>
            <td style="color:{'#e53935' if total>0 else '#43a047'}"><b>{total:,}</b></td>
        </tr>
        """

    # 3. 題材
    sector = info.get('sector', '科技')
    summary = info.get('longBusinessSummary', '暫無詳細說明。')[:120] + "..."
    theme_text = f"<b>{name}</b> 屬於 {sector} 產業。{summary}"
    
    # 4. 建議
    support = ma10 if price > ma10 else ma20
    resistance = ma5 if price < ma5 else price * 1.05
    action = "觀望"
    entry = ""
    exit_pt = ""
    
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
        <h3>📊 {name} ({ticker}) 綜合分析報告</h3>
        <h4>1. 技術指標分析</h4>
        <p><b>趨勢判讀：</b>{tech_trend}。{tech_desc} {kd_desc}</p>
        <h4>2. 三大法人籌碼分析</h4>
        <table class="analysis-table">
            <thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營商</th><th>合計</th></tr></thead>
            <tbody>{inst_table_html}</tbody>
        </table>
        <p><b>籌碼解讀：</b>{inst_desc}</p>
        <h4>3. 公司題材與願景</h4>
        <p>{theme_text}</p>
        <h4>4. 💡 進出場價格建議 ({action})</h4>
        <ul><li><b>🟢 進場參考：</b>{entry}</li><li><b>🔴 出場參考：</b>{exit_pt}</li></ul>
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
        ma20 = latest['MA20']
        k, d = latest['K'], latest['D']
        change = price - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        
        status = "震盪"
        color = "#555"
        if price > ma20:
            status = "多頭" if k > d else "回檔"
            color = "#e53935" if k > d else "#ff9800"
        else:
            status = "空方" if k < d else "反彈"
            color = "#43a047" if k < d else "#fdd835"
            
        comment = f"KD指標({k:.1f}/{d:.1f})。市場氣氛：{status}。"
        return {"price": price, "change": change, "pct": pct, "status": status, "color": color, "comment": comment}
    except: return None

# --- 5. UI 介面 ---

st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入數據..."):
    hot_tw, hot_us = get_market_hot_stocks()

c_search, c_hot = st.columns([3, 1])
with c_search:
    target_input = st.text_input("🔍 搜尋代號/名稱 (如: 4903, 2330)", value="2330")
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

target = "2330.TW"
if hot_stock != "(請選擇)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input:
    with st.spinner("正在搜尋資料..."):
        resolved_ticker, resolved_name = resolve_ticker(target_input)
        if resolved_ticker:
            target = resolved_ticker
            name = resolved_name
        else:
            st.error(f"❌ 找不到股票代號：{target_input}。")
            target = None

if target:
    try:
        stock = yf.Ticker(target)
        info = stock.info
        if 'name' not in locals(): name = STOCK_NAMES.get(target, info.get('longName', target))
        
        # 頂部報價卡片
        df_fast = stock.history(period="5d")
        if not df_fast.empty:
            latest_fast = df_fast.iloc[-1]
            prev_close = df_fast['Close'].iloc[-2]
            price = latest_fast['Close']
            change = price - prev_close
            pct = (change / prev_close) * 100
            
            # 紅漲綠跌 (台股標準)
            color = "#e53935" if change >= 0 else "#43a047"
            arrow = "▲" if change >= 0 else "▼"
            
            st.markdown(f"""
            <div class="quote-card">
                <div class="quote-header">
                    <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
                </div>
                <div class="price-container">
                    <div class="price-big" style="color:{color};">{price:.2f}</div>
                    <div class="price-change" style="color:{color};"> {arrow} {abs(change):.2f} ({abs(pct):.2f}%)</div>
                </div>
                <div class="stats-grid">
                    <div class="stat-item"><span class="stat-label">最高</span><span class="stat-val" style="color:#e53935;">{latest_fast['High']:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">最低</span><span class="stat-val" style="color:#43a047;">{latest_fast['Low']:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">昨收</span><span class="stat-val">{prev_close:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">開盤</span><span class="stat-val">{latest_fast['Open']:.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 分頁
        tab1, tab2, tab3, tab4 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞"])
        
        with tab1:
            interval_map = {"1分": "1m", "5分": "5m", "10分": "5m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
            period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            
            interval = interval_map[period_label]
            data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
            if interval == "1m": data_period = "7d"
            
            df = stock.history(period=data_period, interval=interval)
            if period_label == "10分": df = df.resample('10min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
            
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # K 線圖
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
            for ma, c in [('MA5','#1f77b4'), ('MA10','#9467bd'), ('MA20','#ff7f0e'), ('MA60','#bcbd22'), ('MA120','#8c564b')]:
                if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
            
            colors_vol = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.2), name='K9'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.2), name='D9'), row=3, col=1)

            # 設定預設範圍：最近 15 根 (放大)
            if len(df) > 15:
                fig.update_xaxes(range=[df.index[-15], df.index[-1]], row=1, col=1)

            fig.update_layout(
                template="plotly_white", height=650, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.01, x=0),
                dragmode='pan', hovermode='x unified', xaxis=dict(rangeslider_visible=False)
            )
            # 十字線 (Spikes)
            for row in [1, 2, 3]:
                fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", spikethickness=1, rangeslider_visible=False, row=row, col=1)
                fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", spikethickness=1, row=row, col=1)
                
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            
            kd_color = "#e53935" if latest['K'] > latest['D'] else "#43a047"
            kd_text = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
            st.markdown(f"""<div class="kd-card" style="border-left: 6px solid {kd_color};"><div class="kd-title">KD 指標 (9,3,3)</div><div style="text-align:right;"><div class="kd-val">{latest['K']:.1f} / {latest['D']:.1f}</div><div class="kd-tag" style="background-color:{kd_color};">{kd_text}</div></div></div>""", unsafe_allow_html=True)

        with tab2:
            inst_df = get_institutional_data_finmind(target)
            if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
            st.markdown(generate_narrative_report(name, target, latest, inst_df, df, info), unsafe_allow_html=True)

        with tab3:
            inst_df = get_institutional_data_finmind(target)
            if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
            if inst_df is not None and not inst_df.empty:
                st.markdown(f"<div class='content-card'><h3>🏛️ 三大法人買賣超 (近30日)</h3></div>", unsafe_allow_html=True)
                fig_inst = go.Figure()
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#1f77b4'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#9467bd'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#e91e63'))
                fig_inst.update_layout(barmode='group', template="plotly_white", height=400, xaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_inst, use_container_width=True)
                st.dataframe(inst_df.sort_values('Date', ascending=False).head(10), use_container_width=True)
            else: st.info("無法人籌碼資料")

        with tab4:
            st.markdown("<div class='content-card'><h3>📰 個股相關新聞</h3></div>", unsafe_allow_html=True)
            news_list = get_google_news(target)
            for news in news_list:
                st.markdown(f"<div class='news-item'><a href='{news['link']}' target='_blank'>{news['title']}</a><div class='news-meta'>{news['pubDate']} | {news['source']}</div></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"無法取得資料，請確認代號是否正確。({e})")


