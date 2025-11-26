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
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    if not os.path.exists(png_file): return
    bin_str = get_base64_of_bin_file(png_file)
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
    
    /* 頂部搜尋區塊優化 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.95);
        color: #000;
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
    
    /* 側邊欄卡片 (大盤) */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* 詳細指標卡片 */
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
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

# 擴充股票代號對照表 (包含更多熱門股)
STOCK_NAMES = {
    # 半導體
    "2330.TW": "台積電", "2454.TW": "聯發科", "2303.TW": "聯電", "3711.TW": "日月光投控", "3034.TW": "聯詠",
    "2379.TW": "瑞昱", "2344.TW": "華邦電", "2408.TW": "南亞科", "2337.TW": "旺宏", "3443.TW": "創意",
    # AI/電腦週邊
    "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達",
    "2376.TW": "技嘉", "2301.TW": "光寶科", "2357.TW": "華碩", "2324.TW": "仁寶", "3017.TW": "奇鋐",
    # 航運
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "2605.TW": "新興", "2606.TW": "裕民", "2637.TW": "慧洋-KY",
    # 金融
    "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金", "2884.TW": "玉山金",
    "2892.TW": "第一金", "2885.TW": "元大金", "2880.TW": "華南金", "2883.TW": "開發金", "2890.TW": "永豐金",
    # 傳產/其他
    "2412.TW": "中華電", "1216.TW": "統一", "2002.TW": "中鋼", "1101.TW": "台泥", "1102.TW": "亞泥",
    "1605.TW": "華新", "2308.TW": "台達電", "2409.TW": "友達", "3481.TW": "群創", "3008.TW": "大立光",
    # ETF
    "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00929.TW": "復華台灣科技優息", 
    "00919.TW": "群益台灣精選高息", "00940.TW": "元大台灣價值高息", "00632R.TW": "元大台灣50反1", "006208.TW": "富邦台50",
    # 美股
    "NVDA": "輝達 (NVIDIA)", "TSLA": "特斯拉 (Tesla)", "AAPL": "蘋果 (Apple)", "AMD": "超微 (AMD)", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "NFLX": "網飛", "TSM": "台積電 ADR",
    "AVGO": "博通", "QCOM": "高通", "INTC": "英特爾", "SMCI": "美超微", "ARM": "安謀", "MU": "美光"
}

@st.cache_data(ttl=3600)
def get_top_volume_stocks():
    """取得熱門股代號列表"""
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        latest_trade_date = dl.taiwan_stock_daily_adj(
            stock_id="2330", 
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ).iloc[-1]['date']
        df = dl.taiwan_stock_daily_adj(start_date=latest_trade_date)
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(30)
        return top_df['stock_id'].tolist()
    except:
        return ["2330", "2317", "2603", "2609", "3231", "2454"] 

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    """使用 Token 抓取 FinMind 法人資料"""
    if ".TW" not in ticker: return None
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader(token=FINMIND_API_TOKEN)
    try:
        start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d') # 抓長一點確保圖表連續
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        
        # 整理資料
        df['net'] = df['buy'] - df['sell']
        
        # Pivot Table 轉成日期為 Index 的格式
        pivot_df = df.pivot_table(index='date', columns='name', values='net', aggfunc='sum').fillna(0)
        
        # 轉換單位為「張」並重命名欄位
        pivot_df = pivot_df / 1000
        
        # 確保有三個欄位
        for col in ['外資', '投信', '自營商']:
            is_exist = False
            for c in pivot_df.columns:
                if col in c: 
                    pivot_df.rename(columns={c: col}, inplace=True)
                    is_exist = True
                    break
            if not is_exist: pivot_df[col] = 0
            
        # 只要保留需要的欄位
        final_df = pivot_df[['外資', '投信', '自營商']].copy()
        final_df.columns = ['Foreign', 'Trust', 'Dealer']
        final_df.index = pd.to_datetime(final_df.index)
        
        return final_df
    except Exception as e:
        # print(f"FinMind Error: {e}")
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
            
        # 轉換日期格式並設為 Index
        df_clean['Date'] = df_clean['Date'].apply(lambda x: f"{datetime.now().year}/{x}" if len(str(x))<=5 else x)
        df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        df_clean.set_index('Date', inplace=True)
        
        return df_clean.sort_index()[['Foreign', 'Trust', 'Dealer']]
    except:
        return None

# --- 4. 技術指標與大盤分析 ---

def calculate_indicators(df):
    # 均線
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['MA240'] = df['Close'].rolling(240).mean()
    
    # 布林通道
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
    
    # 成交量均線
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
    # KD
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # RSI
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
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
            
        return {"price": price, "change": change, "pct": pct, "status": status, "color": color, "comment": f"均線{price>ma20}月線，KD{k>d}交叉"}
    except:
        return None

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma5, ma20, ma60 = latest['MA5'], latest['MA20'], latest['MA60']
    k, d = latest['K'], latest['D']
    vol, vol_ma5 = latest['Volume'], latest['VOL_MA5']
    
    trend = "多頭" if price > ma20 else "空頭"
    trend_detail = "股價站穩月線之上，趨勢偏多。" if price > ma20 else "股價跌破月線，短線轉弱。"
    if price > ma5 and ma5 > ma20: trend_detail += " 且沿 5 日線強勢上攻。"
    
    inst_text = "籌碼中性"
    if inst_df is not None and not inst_df.empty:
        # 確保是 DataFrame 且有數據
        if len(inst_df) > 0:
            last = inst_df.iloc[-1]
            total = last['Foreign'] + last['Trust'] + last['Dealer']
            if total > 2000: inst_text = "法人大舉買超，籌碼強勢"
            elif total < -2000: inst_text = "法人調節賣超，籌碼鬆動"
            else: inst_text = "法人買賣超幅度不大，觀望氣氛濃"
        
    kd_sig = "黃金交叉" if k > d else "死亡交叉"
    vol_sig = "價漲量增" if vol > vol_ma5 * 1.2 and price > df['Open'].iloc[-1] else "量縮整理"
    
    return f"""
    <div class="glass-container">
        <h3>📊 武吉拉深度分析</h3>
        <p><b>1. 趨勢結構：</b>{trend_detail} 目前收盤 {price:.2f}，支撐看月線 {ma20:.2f}。</p>
        <p><b>2. 量價分析：</b>今日呈現 <b>{vol_sig}</b> 格局。</p>
        <p><b>3. 籌碼解讀：</b>{inst_text}。</p>
        <p><b>4. 技術指標：</b>KD 指標 ({k:.1f}, {d:.1f}) 呈現 <b>{kd_sig}</b>。</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.2rem; font-weight: bold; color: #ffcc00;">💡 建議：{ '偏多操作' if price>ma20 and k>d else '保守觀望' }</p>
    </div>
    """

# --- 5. UI 介面 (頂部搜尋版) ---

# 標題
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px;'>🦖 武吉拉 Wujila 投資決策系統</h1>", unsafe_allow_html=True)

# 1. 搜尋與過濾邏輯
with st.spinner("正在掃描市場熱門股..."):
    hot_tickers = get_top_volume_stocks()

# 建立完整的搜尋選項清單 (中文名稱 + 代號)
search_options = []

# A. 加入熱門股 (加上 🔥 標記)
for t in hot_tickers:
    t_key = f"{t}.TW" if t.isdigit() else t
    name = STOCK_NAMES.get(t_key, t)
    search_options.append(f"🔥 {name} ({t_key})")

# B. 加入其他權值股 (避免重複)
seen_tickers = set(hot_tickers)
for t_key, name in STOCK_NAMES.items():
    raw_ticker = t_key.replace(".TW", "")
    if raw_ticker not in seen_tickers:
        search_options.append(f"{name} ({t_key})")

# C. 預設選項 (台積電)
default_index = 0
for i, opt in enumerate(search_options):
    if "2330" in opt:
        default_index = i
        break

# 頂部搜尋框
selected_search = st.selectbox(
    "🔍 請輸入股票代號或中文名稱搜尋 (例如：2330, 台積電, NVDA)",
    options=search_options,
    index=default_index
)

# 解析選擇的代號
target = selected_search.split("(")[-1].replace(")", "")

# 如果使用者自己輸入代號 (selectbox 找不到時會變 manual entry 邏輯需另外處理，但在 Streamlit 預設只能選)
# 這裡我們假設使用者如果想查不在清單的，會用下方的 input
# 但為了方便，我們把下拉選單當作主要入口。如果使用者真的找不到，可以在下方 input 輸入

# --- 大盤指數展開區 (Expander) ---
with st.expander("🌍 查看今日大盤盤勢 (台股 / 美股)", expanded=False):
    t1, t2 = st.tabs(["🇹🇼 台股加權", "🇺🇸 美股那斯達克"])
    with t1:
        tw = analyze_market_index("^TWII")
        if tw: st.markdown(f"<div class='market-summary-box'><div style='color:{tw['color']};font-weight:bold;font-size:1.2rem'>{tw['price']:.0f} ({tw['change']:+.0f})</div><div>{tw['status']} - {tw['comment']}</div></div>", unsafe_allow_html=True)
    with t2:
        us = analyze_market_index("^IXIC")
        if us: st.markdown(f"<div class='market-summary-box' style='border-left:4px solid #00BFFF'><div style='color:{us['color']};font-weight:bold;font-size:1.2rem'>{us['price']:.0f} ({us['change']:+.0f})</div><div>{us['status']} - {us['comment']}</div></div>", unsafe_allow_html=True)

st.markdown("---")

# --- K 線週期與連結區 ---
col_k, col_link = st.columns([3, 1])
with col_k:
    interval_map = {"日K": "1d", "週K": "1wk", "月K": "1mo", "60分": "60m", "30分": "30m", "15分": "15m", "5分": "5m"}
    selected_interval_label = st.radio("K 線週期", list(interval_map.keys()), horizontal=True)
    interval = interval_map[selected_interval_label]
    data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "60d"
with col_link:
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button(f"前往 Yahoo 股市", f"https://tw.stock.yahoo.com/quote/{target}", use_container_width=True)

# --- 3. 主畫面數據分析 ---
try:
    # 嘗試抓取名稱 (如果不在列表內)
    stock = yf.Ticker(target)
    info = stock.info
    name = STOCK_NAMES.get(target, info.get('longName', target))
    
    df = stock.history(period=data_period, interval=interval)
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號是否正確。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        chg = latest['Close'] - df['Close'].iloc[-2]
        pct = (chg / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if chg >= 0 else "#00c853"
        
        # 股票標題
        st.markdown(f"<h1 style='text-shadow:2px 2px 4px black; margin:0;'>{name} ({target})</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{color};text-shadow:1px 1px 2px black; margin:0;'>{latest['Close']:.2f} <small>({chg:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        # 抓取法人 (優先 FinMind)
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
        
        # 分析報告
        st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)
        
        # --- K 線圖 (啟用 Crosshair + SpikeLines + HoverUnified) ---
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
        
        # 主圖
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#c0392b', decreasing_line_color='#27ae60'), row=1, col=1)
        
        ma_list = [('MA5','blue'), ('MA10','purple'), ('MA20','orange'), ('MA60','green'), ('MA120','brown')]
        if interval in ["1d", "1wk", "1mo"]: ma_list.append(('MA240','gray'))
            
        for ma, c in ma_list:
            if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
            
        # 成交量
        colors = ['#c0392b' if r['Open'] < r['Close'] else '#27ae60' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        # KD
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#2980b9', width=1.2), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#e67e22', width=1.2), name='D9'), row=3, col=1)
        
        # Range Selector (上方按鈕) + Range Slider (下方滑桿) + 十字準線 (SpikeLines)
        fig.update_xaxes(
            rangeslider_visible=True, # 啟用下方滑桿
            rangeslider_thickness=0.05, # 調整滑桿高度
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=3, label="3月", step="month", stepmode="backward"),
                    dict(count=6, label="半年", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all", label="全部")
                ]),
                font=dict(color="black"), bgcolor="#f0f0f0"
            ),
            # 十字線設定
            showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash',
            row=1, col=1
        )
        
        # 設定滑鼠模式：x unified (一次看所有指標)
        fig.update_layout(
            template="plotly_white", height=900, 
            margin=dict(l=10, r=10, t=10, b=10), 
            legend=dict(orientation="h", y=1.02),
            hovermode="x unified", # 關鍵：讓鼠標變成十字並顯示所有資訊
            dragmode='pan' 
        )
        
        # 啟用滑鼠滾輪縮放
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
        
        # --- 詳細指標 ---
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

        # 法人圖表 (與 K 線日期對齊)
        if inst_df is not None and not inst_df.empty:
            st.subheader("🏛️ 法人籌碼 (與 K 線對齊)")
            
            # 合併 K 線與法人資料 (以 K 線日期為主，補 0)
            merged_df = df[['Close']].join(inst_df, how='left').fillna(0)
            
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=merged_df.index, y=merged_df['Foreign'], name='外資', marker_color='#2980b9'))
            fig_inst.add_trace(go.Bar(x=merged_df.index, y=merged_df['Trust'], name='投信', marker_color='#8e44ad'))
            fig_inst.add_trace(go.Bar(x=merged_df.index, y=merged_df['Dealer'], name='自營商', marker_color='#f39c12'))
            
            # 設定與 K 線相同的 Range Selector
            fig_inst.update_xaxes(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1月", step="month", stepmode="backward"),
                        dict(count=3, label="3月", step="month", stepmode="backward"),
                        dict(step="all", label="全部")
                    ]),
                    font=dict(color="black"), bgcolor="#f0f0f0"
                )
            )
            
            fig_inst.update_layout(
                barmode='group', 
                template="plotly_white", 
                height=400, 
                hovermode="x unified",
                legend=dict(orientation="h", y=1.02)
            )
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            if ".TW" in target: st.info(f"⚠️ 無法取得法人資料 (資料源暫時異常)")

except Exception as e:
    st.error(f"發生錯誤: {e}")
