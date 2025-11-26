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

# --- 2. CSS 樣式 (強制顯色修復版) ---
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

st.markdown("""
    <style>
    /* 全局設定：主要文字顏色 */
    .stApp { color: #333333; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 1. 頂部報價卡片 (強制黑字) --- */
    .quote-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    /* 強制卡片內所有文字為黑色，避免被深色模式影響 */
    .quote-card div, .quote-card span, .quote-card p {
        color: #000000 !important;
    }
    .stock-title { font-size: 1.5rem !important; font-weight: 900 !important; margin-bottom: 5px; }
    .stock-id { font-size: 1.1rem !important; color: #555 !important; }
    .price-big { font-size: 3.5rem !important; font-weight: 800 !important; line-height: 1; margin: 10px 0; }
    .price-change { font-size: 1.2rem !important; font-weight: bold !important; }
    
    .stats-grid { display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.9rem; border-top: 1px solid #eee; padding-top: 10px;}
    .stat-box { text-align: right; }
    .stat-label { color: #666 !important; font-size: 0.85rem !important; }
    .stat-val { color: #000 !important; font-weight: bold !important; font-size: 1.1rem !important; }

    /* --- 2. 內容卡片 (分析、K線容器) (強制黑字) --- */
    .content-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .content-card h3 { 
        color: #000000 !important; 
        border-bottom: 2px solid #ddd; 
        padding-bottom: 10px; 
        font-weight: 800 !important;
    }
    .content-card p, .content-card li, .content-card div { 
        color: #222222 !important; 
        font-size: 1.05rem !important; 
        line-height: 1.6 !important; 
    }
    .content-card b { color: #000000 !important; font-weight: 900 !important; }

    /* --- 3. 搜尋框優化 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 10px;
        font-weight: bold;
    }
    .stTextInput label { color: #ffffff !important; text-shadow: 1px 1px 2px black; }

    /* --- 4. KD 指標卡片 --- */
    .kd-card {
        background-color: #ffffff;
        border-left: 8px solid #2962ff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .kd-title { font-size: 1.3rem !important; font-weight: bold !important; color: #333 !important; }
    .kd-val { font-size: 2.2rem !important; font-weight: 900 !important; color: #000 !important; }
    .kd-tag { padding: 6px 15px; border-radius: 20px; color: white !important; font-weight: bold; font-size: 1rem; }

    /* --- 5. Tab 與週期按鈕 --- */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; font-size: 1.2rem !important; font-weight: bold !important; text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #FFD700 !important; }
    
    /* 週期按鈕樣式 (仿 App 膠囊) */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 0px;
        background-color: #f0f0f0;
        padding: 4px; border-radius: 25px;
        width: 100%;
        justify-content: space-between;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);
    }
    .stRadio div[role="radiogroup"] > label {
        flex: 1;
        text-align: center;
        background-color: transparent;
        padding: 8px 0;
        border-radius: 20px;
        margin: 0;
        color: #666 !important;
        font-weight: bold;
        border: none;
        display: flex; justify-content: center;
        cursor: pointer;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #26a69a !important;
        color: #fff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    /* 隱藏預設 Metric */
    [data-testid="stMetric"] { display: none; }
    
    /* 連結按鈕 */
    .stLinkButton a { background-color: #fff !important; color: #333 !important; border: 1px solid #ccc !important; font-weight: bold; }
    
    /* 標題 */
    h1 { text-shadow: 3px 3px 6px #000; color: white !important; font-weight: 900; margin-bottom: 20px; }
    h2 { text-shadow: 2px 2px 5px #000; color: white !important; }
    
    /* Plotly 圖表文字顏色強制為黑 */
    .js-plotly-plot .plotly .main-svg {
        background: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電", "2382.TW": "廣達",
    "2412.TW": "中華電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2303.TW": "聯電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
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
        return df_clean.sort_index().reset_index()[['Date', 'Foreign', 'Trust', 'Dealer']].head(30)
    except: return None

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
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
    advice = "偏多操作" if price > ma20 and k > d else "保守觀望"
    
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

st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入數據..."):
    hot_tw, hot_us = get_market_hot_stocks()

c_search, c_hot = st.columns([3, 1])
with c_search:
    target_input = st.text_input("🔍 搜尋股票 (輸入代號或名稱，如: 2330, NVDA)", value="")
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

target = "2330.TW"
if hot_stock != "(請選擇)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input: 
    target = target_input.upper()
    if target.isdigit() and len(target) >= 4: target += ".TW"

try:
    stock = yf.Ticker(target)
    info = stock.info
    name = STOCK_NAMES.get(target, info.get('longName', target))
    
    # 頂部報價卡片
    df_fast = stock.history(period="5d")
    if not df_fast.empty:
        latest_fast = df_fast.iloc[-1]
        prev_close = df_fast['Close'].iloc[-2]
        price = latest_fast['Close']
        change = price - prev_close
        pct = (change / prev_close) * 100
        color = "#ef5350" if change >= 0 else "#26a69a"
        
        st.markdown(f"""
        <div class="quote-card">
            <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
            <div style="display:flex; align-items:baseline;">
                <div class="price-big" style="color:{color};">{price:.2f}</div>
                <div class="price-change" style="color:{color};"> {'▲' if change>=0 else '▼'} {abs(change):.2f} ({abs(pct):.2f}%)</div>
            </div>
            <div class="stats-grid">
                <div class="stat-box"><div class="stat-label">最高</div><div class="stat-val" style="color:#ef5350;">{latest_fast['High']:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">最低</div><div class="stat-val" style="color:#26a69a;">{latest_fast['Low']:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">昨收</div><div class="stat-val">{prev_close:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">開盤</div><div class="stat-val">{latest_fast['Open']:.2f}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 分頁
    tab1, tab2, tab3 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼"])
    
    with tab1:
        # 週期按鈕
        interval_map = {"分時": "1m", "日": "1d", "週": "1wk", "月": "1mo", "60分": "60m"}
        period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
        
        interval = interval_map[period_label]
        data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
        
        df = stock.history(period=data_period, interval=interval)
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        # K 線圖 (極簡操作版)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.01)
        
        # 1. 主圖 (增加十字線)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#ef5350', decreasing_line_color='#26a69a'), row=1, col=1)
        for ma, c in [('MA5','#1f77b4'), ('MA10','#ff9800'), ('MA20','#9c27b0'), ('MA60','#795548'), ('MA120','#607d8b')]:
            if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)

        # 2. 成交量
        colors_vol = ['#ef5350' if r['Open'] < r['Close'] else '#26a69a' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)

        # 3. KD
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.2), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.2), name='D9'), row=3, col=1)

        # 設定預設範圍：最近 45 根
        if len(df) > 45:
            fig.update_xaxes(range=[df.index[-45], df.index[-1]], row=1, col=1)

        # Layout: 極簡設定
        fig.update_layout(
            template="plotly_white", height=600,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", y=1.01, x=0),
            dragmode='pan', # 手指拖曳平移
            hovermode='x unified', # 顯示十字線與數值
            xaxis=dict(rangeslider_visible=False), # 移除下方 Slider
            yaxis=dict(fixedrange=False) # Y軸可動
        )
        
        # 十字線設定
        for row in [1, 2, 3]:
            fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', row=row, col=1)
            fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', row=row, col=1)
        
        # 強制移除所有子圖 Slider
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=3, col=1)
        
        # 手機雙擊放大 (Autosize)
        config = {
            'scrollZoom': True, 
            'displayModeBar': False,
            'doubleClick': 'reset+autosize' # 雙擊重置/放大
        }
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        # 只顯示 KD 卡片
        kd_color = "#ef5350" if latest['K'] > latest['D'] else "#26a69a"
        kd_text = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
        st.markdown(f"""
        <div class="kd-card" style="border-left: 6px solid {kd_color};">
            <div class="kd-title">KD 指標 (9,3,3)</div>
            <div style="text-align:right;">
                <div class="kd-val">{latest['K']:.1f} / {latest['D']:.1f}</div>
                <div class="kd-tag" style="background-color:{kd_color};">{kd_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
        st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)

    with tab3:
        if inst_df is not None and not inst_df.empty:
            st.markdown(f"<div class='content-card'><h3>🏛️ 三大法人買賣超 (近30日)</h3></div>", unsafe_allow_html=True)
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#1f77b4'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#9c27b0'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#e91e63'))
            fig_inst.update_layout(barmode='group', template="plotly_white", height=400, xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_inst, use_container_width=True)
            st.dataframe(inst_df.sort_values('Date', ascending=False).head(10), use_container_width=True)
        else:
            st.info("無法人籌碼資料")

except Exception as e:
    st.error(f"無法取得資料，請確認代號是否正確。({e})")


