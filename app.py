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

# --- 0. 設定與金鑰 (FinMind) ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide")

# --- 2. 背景圖片與 CSS 設定 ---
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
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg('bg.png')

# CSS 樣式
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 搜尋框優化 */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.95);
        color: #000;
        font-size: 1.1rem;
        font-weight: bold;
        border: 2px solid #FFD700;
        border-radius: 8px;
    }
    
    /* 分析報告容器 */
    .glass-container {
        background-color: rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
    }
    .glass-container h3 { color: #FFD700 !important; border-bottom: 1px solid #555; padding-bottom: 10px; }
    .glass-container p, .glass-container li { color: #f0f0f0 !important; font-size: 1.15rem; line-height: 1.8; }
    
    /* 側邊欄卡片 */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* 指標卡片 */
    .indicator-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        color: #000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        border: 1px solid #ccc;
    }
    .indicator-title { font-size: 0.95rem; font-weight: bold; color: #555; margin-bottom: 5px; }
    .indicator-value { font-size: 1.6rem; font-weight: 800; color: #000; }
    .indicator-tag { 
        display: inline-block; padding: 3px 10px; border-radius: 15px; 
        font-size: 0.85rem; font-weight: bold; color: white; margin-top: 5px;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; font-size: 1.1rem; font-weight: bold; text-shadow: 1px 1px 2px black;
    }
    
    /* 按鈕 */
    .stLinkButton a { background-color: #420066 !important; color: white !important; border: 1px solid #888 !important; }
    
    /* 隱藏預設 Metric */
    [data-testid="stMetric"] { display: none; }
    
    /* 標題 */
    h1, h2 { text-shadow: 2px 2px 5px #000; }
    
    /* 週期按鈕優化 */
    .stRadio > div {
        display: flex;
        flex-direction: row;
        gap: 10px;
        background-color: rgba(0,0,0,0.6);
        padding: 10px;
        border-radius: 8px;
        overflow-x: auto;
        justify-content: center;
    }
    .stRadio label { color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

# 內建對照表 (僅供顯示中文名稱)
STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電", "2382.TW": "廣達",
    "2412.TW": "中華電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2303.TW": "聯電",
    "1216.TW": "統一", "2002.TW": "中鋼", "2886.TW": "兆豐金", "2884.TW": "玉山金", "2892.TW": "第一金",
    "1101.TW": "台泥", "1102.TW": "亞泥", "1301.TW": "台塑", "1303.TW": "南亞", "1326.TW": "台化",
    "2912.TW": "統一超", "3008.TW": "大立光", "5871.TW": "中租-KY", "5876.TW": "上海商銀", "2880.TW": "華南金",
    "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "2357.TW": "華碩", "2324.TW": "仁寶", "3017.TW": "奇鋐", "3037.TW": "欣興", "2379.TW": "瑞昱",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "2605.TW": "新興", "2606.TW": "裕民", "2637.TW": "慧洋-KY", "1605.TW": "華新", 
    "2409.TW": "友達", "3481.TW": "群創", "2344.TW": "華邦電", "2408.TW": "南亞科", "2337.TW": "旺宏",
    "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00929.TW": "復華台灣科技優息", 
    "00919.TW": "群益台灣精選高息", "00940.TW": "元大台灣價值高息", "00632R.TW": "元大台灣50反1", "006208.TW": "富邦台50",
    "00713.TW": "元大台灣高息低波", "00939.TW": "統一台灣高息動能",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "NFLX": "網飛", "TSM": "台積電 ADR",
    "AVGO": "博通", "QCOM": "高通", "INTC": "英特爾", "SMCI": "美超微", "ARM": "安謀", "MU": "美光"
}

@st.cache_data(ttl=3600)
def get_market_hot_stocks():
    """取得台美股熱門交易清單"""
    hot_tw = ["2330", "2317", "2603", "2609", "3231", "2454", "2382", "2303", "2615", "3231"]
    hot_us = ["NVDA", "TSLA", "AAPL", "AMD", "PLTR", "MSFT", "AMZN", "META", "GOOGL", "AVGO"]
    
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        latest_trade_date = dl.taiwan_stock_daily_adj(
            stock_id="2330", 
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ).iloc[-1]['date']
        df = dl.taiwan_stock_daily_adj(start_date=latest_trade_date)
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(15)
        if not top_df.empty:
            hot_tw = top_df['stock_id'].tolist()
    except: pass
    
    return hot_tw, hot_us

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    """FinMind 法人資料抓取"""
    if ".TW" not in ticker: return None
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader(token=FINMIND_API_TOKEN)
    
    try:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        
        df['net'] = df['buy'] - df['sell']
        pivot_df = df.pivot_table(index='date', columns='name', values='net', aggfunc='sum').fillna(0)
        
        rename_map = {}
        for col in pivot_df.columns:
            if '外資' in col: rename_map[col] = 'Foreign'
            elif '投信' in col: rename_map[col] = 'Trust'
            elif '自營' in col: rename_map[col] = 'Dealer'
            
        pivot_df = pivot_df.rename(columns=rename_map)
        for col in ['Foreign', 'Trust', 'Dealer']:
            if col not in pivot_df.columns: pivot_df[col] = 0
            
        pivot_df = (pivot_df / 1000).astype(int)
        pivot_df = pivot_df.reset_index()
        pivot_df = pivot_df.rename(columns={'date': 'Date'})
        
        return pivot_df
    except:
        return None

@st.cache_data(ttl=300)
def get_institutional_data_yahoo(ticker):
    """Yahoo 爬蟲備援"""
    if ".TW" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        dfs = pd.read_html(r.text)
        target_df = None
        for df in dfs:
            if any('外資' in str(c) for c in df.columns):
                target_df = df
                break
        if target_df is None: return None
        
        new_cols = {}
        for c in target_df.columns:
            s = str(c)
            if '日期' in s: new_cols[c] = 'Date'
            elif '外資' in s and '持股' not in s: new_cols[c] = 'Foreign'
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
        return df_clean.sort_index().reset_index()[['Date', 'Foreign', 'Trust', 'Dealer']].head(30)
    except:
        return None

# --- 4. 技術指標與大盤分析 ---

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['MA240'] = df['Close'].rolling(240).mean()
    
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    df['BIAS_20'] = (df['Close'] - df['MA20']) / df['MA20'] * 100
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['Close'].ewm(span=12).mean()
    exp26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    return df

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
        
        if price > ma20:
            status = "多頭強勢" if k > d else "多頭回檔"
            color = "#ff4b4b" if k > d else "#ff9100"
        else:
            status = "空方修正" if k < d else "跌深反彈"
            color = "#00c853" if k < d else "#ffff00"
        comment = f"KD指標({k:.1f}/{d:.1f})。市場氣氛：{status}。"
        return {"price": price, "change": change, "pct": pct, "status": status, "color": color, "comment": comment}
    except: return None

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma5, ma20, ma60 = latest['MA5'], latest['MA20'], latest['MA60']
    k, d = latest['K'], latest['D']
    vol, vol_ma5 = latest['Volume'], latest['VOL_MA5']
    bias_20 = latest['BIAS_20']
    
    trend_html = f"<b>{name} ({ticker})</b> 收盤 <b>{price:.2f}</b>。"
    if price > ma20:
        trend_html += " 股價站穩<b>月線</b>之上，多方控盤。"
        if price > ma60: trend_html += " 且位於<b>季線</b>之上，中長線保護短線。"
    else:
        trend_html += " 股價跌破<b>月線</b>，短線轉弱。"
    
    if bias_20 > 10: trend_html += " 唯<b>月線乖離率</b>過大 (>10%)，需留意拉回。"
    elif bias_20 < -10: trend_html += " 唯<b>月線乖離率</b>過低 (<-10%)，醞釀反彈。"

    vol_html = "量價方面，"
    if vol > 1.5 * vol_ma5:
        vol_status = "價漲量增" if price > df['Open'].iloc[-1] else "爆量長黑"
        vol_html += f"今日呈現<b>「{vol_status}」</b>，交投熱絡。"
    elif vol < 0.6 * vol_ma5:
        vol_html += "今日呈現<b>「量縮整理」</b>，觀望氣氛濃。"
    else:
        vol_html += "成交量維持常態，供需穩定。"

    inst_html = "籌碼方面，"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        total = last['Foreign'] + last['Trust'] + last['Dealer']
        buy_sell = "買超" if total > 0 else "賣超"
        color = "#ff4b4b" if total > 0 else "#00c853"
        inst_html += f"法人單日合計<span style='color:{color}'><b>{buy_sell} {abs(total):,} 張</b></span>。"
        
        recent_10 = inst_df.tail(10)
        f_sum = recent_10['Foreign'].sum()
        if f_sum > 10000: inst_html += " 近10日外資累計大買，波段籌碼安定。"
        elif f_sum < -10000: inst_html += " 近10日外資累計大賣，上方套牢壓力重。"
    else:
        inst_html += "暫無最新數據。"

    tech_html = f"指標方面，KD ({k:.1f}, {d:.1f}) "
    if k > d: tech_html += "呈現<b>黃金交叉</b>，動能轉強。"
    else: tech_html += "呈現<b>死亡交叉</b>，動能轉弱。"
    
    if latest['RSI'] > 75: tech_html += " RSI 進入<b>超買區</b>，勿追高。"
    
    advice = "觀望"
    adv_color = "#ffffff"
    if price > ma20 and k > d:
        advice = "趨勢偏多，順勢操作，沿 5 日線持有。"
        adv_color = "#ff4b4b"
    elif price < ma20 and k < d:
        advice = "趨勢偏空，保守觀望，靜待落底。"
        adv_color = "#00c853"
    else:
        advice = "區間震盪，建議在季線與月線間操作。"
        adv_color = "#ffff00"

    return f"""
    <div class="glass-container">
        <h3>📊 武吉拉大數據深度分析</h3>
        <p><b>1. 趨勢與乖離：</b><br>{trend_html}</p>
        <p><b>2. 量價結構：</b><br>{vol_html}</p>
        <p><b>3. 籌碼大數據：</b><br>{inst_html}</p>
        <p><b>4. 技術指標：</b><br>{tech_html}</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.2rem; font-weight: bold; color: {adv_color};">💡 建議：{advice}</p>
    </div>
    """

# --- 5. UI 介面 (Top Search) ---

st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px;'>🦖 武吉拉 Wujila 投資決策系統</h1>", unsafe_allow_html=True)

# 1. 熱門股與搜尋
with st.spinner("大數據運算中..."):
    hot_tw, hot_us = get_market_hot_stocks()

# 萬用搜尋框 (不再使用下拉選單，改為文字輸入，更靈活)
c_search, c_hot = st.columns([3, 1])
with c_search:
    target_input = st.text_input("🔍 請輸入任意股票代號 (如: 2618, 0050, AMD, NFLX)", value="")

# 熱門股快速按鈕 (點擊自動填入)
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

# 決定目標代號
target = "2330.TW" # 預設
if hot_stock != "(請選擇)": target = hot_stock
if target_input: 
    target = target_input.upper()
    # 自動判斷台美股
    if target.isdigit() and len(target) >= 4: target += ".TW"

# --- 大盤指數展開區 ---
with st.expander("🌍 查看今日大盤情緒 (台股 / 美股)", expanded=False):
    t1, t2 = st.tabs(["🇹🇼 台股加權", "🇺🇸 美股那斯達克"])
    with t1:
        tw = analyze_market_index("^TWII")
        if tw: st.markdown(f"<div class='market-summary-box'><div style='color:{tw['color']};font-weight:bold;font-size:1.2rem'>{tw['price']:.0f} ({tw['change']:+.0f})</div><div>{tw['status']} - {tw['comment']}</div></div>", unsafe_allow_html=True)
    with t2:
        us = analyze_market_index("^IXIC")
        if us: st.markdown(f"<div class='market-summary-box' style='border-left:4px solid #00BFFF'><div style='color:{us['color']};font-weight:bold;font-size:1.2rem'>{us['price']:.0f} ({us['change']:+.0f})</div><div>{us['status']} - {us['comment']}</div></div>", unsafe_allow_html=True)

st.markdown("---")

# --- K 線週期與連結區 ---
try:
    stock = yf.Ticker(target)
    # 嘗試抓取名稱
    name = STOCK_NAMES.get(target, None)
    if not name:
        # 若無快取，嘗試從 Info 抓
        try: name = stock.info.get('longName', target)
        except: name = target

    # 標題區 (標題下方即選單)
    c_header, c_menu = st.columns([1, 2])
    with c_menu:
        # 週期選單
        interval_map = {"日K": "1d", "週K": "1wk", "月K": "1mo", "60分": "60m", "30分": "30m", "15分": "15m", "5分": "5m"}
        selected_interval_label = st.radio("K 線週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
        interval = interval_map[selected_interval_label]
        data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "60d"

    df = stock.history(period=data_period, interval=interval)
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號是否正確。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        chg = latest['Close'] - df['Close'].iloc[-2]
        pct = (chg / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if chg >= 0 else "#00c853"
        
        with c_header:
            st.markdown(f"<h2 style='text-shadow:2px 2px 4px black; margin:0;'>{name} ({target})</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color:{color};text-shadow:1px 1px 2px black; margin:0;'>{latest['Close']:.2f} <small>({chg:+.2f} / {pct:+.2f}%)</small></h3>", unsafe_allow_html=True)
            st.link_button(f"Yahoo 股市", f"https://tw.stock.yahoo.com/quote/{target}")

        # 抓取法人
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
        
        # --- K 線圖 (Range Slider 優化) ---
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
        
        # 主圖
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#ff0000', decreasing_line_color='#009900'), row=1, col=1)
        
        ma_list = [('MA5','blue'), ('MA10','purple'), ('MA20','orange'), ('MA60','green'), ('MA120','brown')]
        if interval in ["1d", "1wk", "1mo"]: ma_list.append(('MA240','gray'))
            
        for ma, c in ma_list:
            if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
            
        # 成交量
        colors = ['#ff0000' if r['Open'] < r['Close'] else '#009900' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        # KD
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#0099FF', width=1.2), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#FF9900', width=1.2), name='D9'), row=3, col=1)
        
        # 底部滑桿 (Range Slider) 設定
        fig.update_xaxes(
            rangeslider_visible=False, # 主圖隱藏，統一用最下方
            row=1, col=1
        )
        # 在最底層 (KD) 開啟滑桿
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeslider_thickness=0.08, # 高度適中
            row=3, col=1
        )
        
        fig.update_layout(template="plotly_white", height=900, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.01), dragmode='pan')
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        
        # 報告
        st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)
        
        # 詳細指標
        st.subheader("📊 詳細指標解讀")
        c1, c2, c3, c4 = st.columns(4)
        
        def indicator_box(title, value, condition, good_text, bad_text, neutral_text="中性"):
            color = "#ff4b4b" if condition == "good" else "#00c853" if condition == "bad" else "#888"
            text = good_text if condition == "good" else bad_text if condition == "bad" else neutral_text
            return f"""<div class="indicator-card" style="border-top: 5px solid {color};"><div class="indicator-title">{title}</div><div class="indicator-value">{value}</div><div class="indicator-tag" style="background-color:{color};">{text}</div></div>"""

        with c1:
            cond = "good" if latest['K'] > latest['D'] else "bad"
            st.markdown(indicator_box("KD 指標", f"{latest['K']:.1f}", cond, "黃金交叉 🟢", "死亡交叉 🔴"), unsafe_allow_html=True)
        with c2:
            cond = "bad" if latest['RSI'] > 70 else "good" if latest['RSI'] < 30 else "neutral"
            st.markdown(indicator_box("RSI 強弱", f"{latest['RSI']:.1f}", cond, "超賣反彈 🟢", "超買警戒 🔴"), unsafe_allow_html=True)
        with c3:
            cond = "good" if latest['MACD'] > latest['Signal'] else "bad"
            st.markdown(indicator_box("MACD", f"{latest['MACD']:.2f}", cond, "多方控盤 🟢", "空方控盤 🔴"), unsafe_allow_html=True)
        with c4:
            cond = "good" if latest['Close'] > latest['MA20'] else "bad"
            st.markdown(indicator_box("月線乖離", f"{(latest['Close']-latest['MA20']):.1f}", cond, "站上月線 🟢", "跌破月線 🔴"), unsafe_allow_html=True)

        # 法人圖表
        if inst_df is not None and not inst_df.empty:
            st.subheader("🏛️ 法人籌碼 (近60日)")
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#2980b9'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#8e44ad'))
            fig_inst.update_layout(barmode='group', template="plotly_white", height=300, xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            if ".TW" in target: st.info(f"⚠️ 無法取得法人資料 (資料源暫時異常)")

except Exception as e:
    st.error(f"發生錯誤: {e}")
