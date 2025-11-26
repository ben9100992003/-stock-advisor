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

# --- 2. CSS 樣式 (核心：亮色玻璃擬態 + App 佈局) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

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

st.markdown("""
    <style>
    /* 全局字體設定為深色，適應亮色卡片 */
    .stApp { color: #333333; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 1. 頂部報價卡片 (App Card Style) --- */
    .quote-card {
        background-color: rgba(255, 255, 255, 0.95); /* 極高不透明度的白底 */
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
    
    .quote-header {
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;
    }
    .stock-id-badge {
        background-color: #f0f0f0; color: #666; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold;
    }
    
    .price-big {
        font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin: 10px 0;
    }
    .price-change {
        font-size: 1.2rem; font-weight: bold; margin-left: 10px;
    }
    
    /* 四格數據網格 */
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 15px;
        font-size: 0.95rem;
    }
    .stat-item {
        display: flex; justify-content: space-between;
        color: #555;
    }
    .stat-value {
        font-weight: bold; color: #000;
    }

    /* --- 2. 搜尋框優化 --- */
    .stSelectbox label { color: #ffffff !important; text-shadow: 1px 1px 2px black; font-weight: bold; }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px; /* 圓潤搜尋框 */
        border: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }

    /* --- 3. 分析報告 & 內容容器 (白底) --- */
    .content-card {
        background-color: rgba(255, 255, 255, 0.92);
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: #333 !important;
    }
    .content-card h3 { color: #000 !important; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .content-card p, .content-card li { color: #444 !important; line-height: 1.6; font-size: 1.05rem; }
    .content-card b { color: #000; }
    
    /* --- 4. K 線圖控制列 --- */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 0px;
        background-color: #f5f5f5;
        padding: 2px; border-radius: 8px;
        overflow-x: auto;
    }
    .stRadio div[role="radiogroup"] > label {
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 6px;
        margin: 0;
        color: #555 !important;
        font-weight: bold;
        border: none;
    }
    /* 選中狀態 (Streamlit 預設會變色，這裡微調文字) */
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        color: #000 !important;
    }

    /* --- 5. 底部固定按鈕列 (模擬 App) --- */
    .bottom-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #ffffff;
        padding: 10px 20px;
        display: flex; justify-content: space-around;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 9999;
    }
    .action-btn {
        flex: 1; margin: 0 5px; padding: 12px;
        text-align: center; border-radius: 8px;
        font-weight: bold; cursor: pointer;
        color: white; font-size: 1rem;
    }
    .btn-green { background-color: #26a69a; }
    .btn-red { background-color: #ef5350; }
    
    /* 調整主畫面底部邊距，避免被按鈕擋住 */
    .block-container { padding-bottom: 80px; }
    
    /* 指標卡片微調 */
    [data-testid="stMetric"] {
        background-color: #f9f9f9 !important;
        border: 1px solid #eee !important;
        box-shadow: none !important;
    }
    [data-testid="stMetricLabel"] p { color: #666 !important; }
    [data-testid="stMetricValue"] div { color: #000 !important; text-shadow: none !important; }
    
    /* 隱藏連結按鈕預設樣式 */
    .stLinkButton a { color: #2962ff !important; text-decoration: none; font-weight: bold; }
    
    /* Tab 樣式優化 (白底黑字) */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab-list"] button { color: #ccc; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color: #fff !important; border-bottom-color: #fff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電", "2382.TW": "廣達",
    "2412.TW": "中華電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2303.TW": "聯電",
    "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "2344.TW": "華邦電", "2408.TW": "南亞科", "2337.TW": "旺宏", "2409.TW": "友達", "3481.TW": "群創",
    "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00929.TW": "復華台灣科技優息", 
    "00919.TW": "群益台灣精選高息", "00940.TW": "元大台灣價值高息", "00632R.TW": "元大台灣50反1",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "NFLX": "網飛", "TSM": "台積電 ADR"
}

@st.cache_data(ttl=3600)
def get_market_hot_stocks():
    hot_tw = ["2330", "2317", "2603", "2609", "3231", "2454", "2382", "2303", "2615", "3231"]
    hot_us = ["NVDA", "TSLA", "AAPL", "AMD", "PLTR", "MSFT", "AMZN", "META", "GOOGL", "AVGO"]
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        latest_trade_date = dl.taiwan_stock_daily_adj(stock_id="2330", start_date=(datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')).iloc[-1]['date']
        df = dl.taiwan_stock_daily_adj(start_date=latest_trade_date)
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(15)
        if not top_df.empty: hot_tw = top_df['stock_id'].tolist()
    except: pass
    return hot_tw, hot_us

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
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
    except: return None

@st.cache_data(ttl=300)
def get_institutional_data_yahoo(ticker):
    if ".TW" not in ticker: return None
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
    except: return None

# --- 4. 技術指標 ---
def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['MA240'] = df['Close'].rolling(240).mean()
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    df['VOL_MA20'] = df['Volume'].rolling(20).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma5, ma20 = latest['MA5'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭" if price > ma20 else "空頭"
    
    inst_text = "籌碼中性"
    if inst_df is not None and not inst_df.empty:
        total = inst_df.iloc[-1][['Foreign', 'Trust', 'Dealer']].sum()
        if total > 1000: inst_text = "法人買超"
        elif total < -1000: inst_text = "法人賣超"
        
    kd_sig = "黃金交叉" if k > d else "死亡交叉"
    
    advice = "觀望"
    if price > ma20 and k > d: advice = "偏多操作"
    elif price < ma20 and k < d: advice = "偏空操作"
    
    return f"""
    <div class="content-card">
        <h3>📊 武吉拉深度分析</h3>
        <p><b>1. 趨勢：</b>{trend}格局。收盤 {price:.2f}，月線 {ma20:.2f}。</p>
        <p><b>2. 籌碼：</b>{inst_text}。</p>
        <p><b>3. 指標：</b>KD {kd_sig} (K:{k:.1f})。</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.2rem; font-weight: bold; color: #2962ff;">💡 建議：{advice}</p>
    </div>
    """

# --- 5. UI 介面 ---

# 1. 頂部搜尋與標題
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px; color:white;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入數據..."):
    hot_tw, hot_us = get_market_hot_stocks()

# 搜尋建議
search_options = []
for t in hot_tw: search_options.append(f"🇹🇼 {STOCK_NAMES.get(f'{t}.TW', t)} ({t}.TW)")
for t in hot_us: search_options.append(f"🇺🇸 {STOCK_NAMES.get(t, t)} ({t})")

c_search, c_hot = st.columns([3, 1])
with c_search:
    target_input = st.text_input("🔍 輸入代號或名稱搜尋 (如: 2330, AAPL)", value="")
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + search_options)

# 決定 Target
target = "2330.TW"
if hot_stock != "(請選擇)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input: 
    target = target_input.upper()
    if target.isdigit() and len(target) >= 4: target += ".TW"

# 2. 抓取個股資料
try:
    stock = yf.Ticker(target)
    info = stock.info
    name = STOCK_NAMES.get(target, info.get('longName', target))
    
    # 3. 頂部報價卡片 (Quote Card)
    # 先抓最新即時報價
    df_fast = stock.history(period="5d")
    if not df_fast.empty:
        latest_fast = df_fast.iloc[-1]
        prev_close = df_fast['Close'].iloc[-2]
        price = latest_fast['Close']
        change = price - prev_close
        pct = (change / prev_close) * 100
        color = "#ef5350" if change >= 0 else "#26a69a" # 台股紅漲綠跌
        arrow = "▲" if change >= 0 else "▼"
        
        # Yahoo 截圖風格卡片
        st.markdown(f"""
        <div class="quote-card">
            <div class="quote-header">
                <div style="font-size: 1.5rem; font-weight: bold; color:#333;">{name} <span style="font-size:1rem; color:#888;">({target})</span></div>
                <div class="stock-id-badge">上市/上櫃</div>
            </div>
            <div style="display:flex; align-items:baseline;">
                <div class="price-big" style="color:{color};">{price:.2f}</div>
                <div class="price-change" style="color:{color};">{arrow} {abs(change):.2f} ({abs(pct):.2f}%)</div>
            </div>
            <div class="stats-grid">
                <div class="stat-item"><span>最高</span><span class="stat-value" style="color:#ef5350;">{latest_fast['High']:.2f}</span></div>
                <div class="stat-item"><span>昨收</span><span class="stat-value">{prev_close:.2f}</span></div>
                <div class="stat-item"><span>最低</span><span class="stat-value" style="color:#26a69a;">{latest_fast['Low']:.2f}</span></div>
                <div class="stat-item"><span>開盤</span><span class="stat-value">{latest_fast['Open']:.2f}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 4. 功能分頁 (仿 App Tabs)
    tab1, tab2, tab3 = st.tabs(["📈 K 線分析", "📝 深度報告", "🏛️ 法人籌碼"])
    
    with tab1:
        # K 線操作區
        c_period, _ = st.columns([3, 1])
        with c_period:
            # 週期按鈕 (在圖表上方)
            interval_map = {"分時": "1m", "日": "1d", "週": "1wk", "月": "1mo", "60分": "60m"}
            period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            
        interval = interval_map[period_label]
        data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
        
        # 抓取詳細資料
        df = stock.history(period=data_period, interval=interval)
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        # K 線圖 (白底, Yahoo 風格)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
        
        # 上層: K 線 + 均線
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#ef5350', decreasing_line_color='#26a69a'), row=1, col=1)
        ma_colors = {'MA5':'#1f77b4', 'MA10':'#9467bd', 'MA20':'#ff7f0e', 'MA60':'#bcbd22', 'MA120':'#8c564b', 'MA240':'#7f7f7f'}
        for ma, c in ma_colors.items():
            if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
            
        # 中層: 成交量
        colors_vol = ['#ef5350' if r['Open'] < r['Close'] else '#26a69a' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
        if 'VOL_MA5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['VOL_MA5'], line=dict(color='#1f77b4', width=1), name='MV5'), row=2, col=1)

        # 下層: KD
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.2), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.2), name='D9'), row=3, col=1)
        if 'J' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['J'], line=dict(color='#bcbd22', width=1), name='J9'), row=3, col=1)

        # Layout: 白底, 格線, 無滑桿(改用滑鼠拖曳)
        fig.update_layout(
            template="plotly_white", height=700,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", y=1.01, x=0),
            dragmode='pan', hovermode='x unified',
            paper_bgcolor='white', plot_bgcolor='white'
        )
        # Range Slider 放在最底部
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
        fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.05, row=3, col=1)
        
        # 格線
        grid_style = dict(showgrid=True, gridcolor='#f0f0f0')
        fig.update_xaxes(**grid_style); fig.update_yaxes(**grid_style)
        
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        
    with tab2:
        # 深度報告
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
        st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)
        
        # 詳細指標數據
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KD (K/D)", f"{latest['K']:.1f} / {latest['D']:.1f}")
        c2.metric("RSI", f"{latest['RSI']:.1f}")
        c3.metric("MACD", f"{latest['MACD']:.2f}")
        c4.metric("乖離率", f"{latest['BIAS_20']:.2f}%")

    with tab3:
        # 法人籌碼
        if inst_df is not None and not inst_df.empty:
            st.markdown("### 🏛️ 三大法人買賣超 (近30日)")
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#1f77b4'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#9467bd'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#e377c2'))
            fig_inst.update_layout(barmode='group', template="plotly_white", height=400, xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_inst, use_container_width=True)
            st.dataframe(inst_df.sort_values('Date', ascending=False).head(10), use_container_width=True)
        else:
            st.info("無法人籌碼資料 (可能為美股或資料源異常)")

except Exception as e:
    st.error(f"無法取得資料，請確認代號是否正確。({e})")

# --- 6. 底部固定按鈕列 (模擬 App) ---
st.markdown("""
<div class="bottom-bar">
    <div class="action-btn btn-green">定期投資申購</div>
    <div class="action-btn btn-red">個股下單</div>
</div>
""", unsafe_allow_html=True)


