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

# --- 2. CSS 樣式 (核心：白卡片懸浮風格) ---
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
    /* 全局字體深色 (適應白底卡片) */
    .stApp { color: #333; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 1. 頂部報價卡片 (仿 Yahoo App) --- */
    .quote-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }
    
    .stock-title { font-size: 1.4rem; font-weight: bold; color: #000; margin-bottom: 5px; }
    .stock-id { font-size: 1rem; color: #666; }
    
    .price-big {
        font-size: 3.2rem; font-weight: 800; line-height: 1; margin: 10px 0;
    }
    .price-change { font-size: 1.1rem; font-weight: bold; }
    
    .stats-grid {
        display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.9rem; color: #555;
    }
    .stat-box { text-align: right; }
    .stat-label { color: #888; font-size: 0.8rem; }
    .stat-val { color: #000; font-weight: bold; }

    /* --- 2. 內容卡片 (分析、K線容器) --- */
    .content-card {
        background-color: rgba(255, 255, 255, 0.95); /* 不透明白底 */
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        color: #000 !important;
    }
    .content-card h3 { color: #000 !important; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .content-card p, .content-card li { color: #333 !important; font-size: 1rem; line-height: 1.6; }
    .content-card b { color: #000; }

    /* --- 3. 搜尋框優化 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #000;
        border: 2px solid #eee;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* --- 4. Metric 指標卡片 (改為白底樣式) --- */
    [data-testid="stMetric"] {
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: none !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetricLabel"] p { color: #666 !important; font-weight: bold; }
    [data-testid="stMetricValue"] div { color: #000 !important; text-shadow: none !important; }

    /* --- 5. Tab 樣式 (適應深色背景的標題) --- */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; /* Tab 標題維持白色，因為在背景上 */
        font-size: 1.1rem;
        font-weight: bold;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {
        color: #FFD700 !important; /* 選中變金色 */
    }
    
    /* 標題 */
    h1, h2 { text-shadow: 2px 2px 5px #000; color: white !important; }
    
    /* 連結按鈕 */
    .stLinkButton a { 
        background-color: #fff !important; 
        color: #333 !important; 
        border: 1px solid #ccc !important;
        font-weight: bold;
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
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜"
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
        return df_clean.head(30)
    except: return None

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
    
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['Close'].ewm(span=12).mean()
    exp26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    
    return df

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma5, ma20 = latest['MA5'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭" if price > ma20 else "空頭"
    trend_detail = "站穩月線，趨勢偏多。" if price > ma20 else "跌破月線，短線轉弱。"
    
    inst_text = "籌碼中性"
    if inst_df is not None and not inst_df.empty:
        total = inst_df.iloc[-1][['Foreign', 'Trust', 'Dealer']].sum()
        if total > 1000: inst_text = "法人買超，籌碼安定"
        elif total < -1000: inst_text = "法人賣超，壓力浮現"
        
    kd_sig = "黃金交叉" if k > d else "死亡交叉"
    advice = "偏多操作" if price > ma20 and k > d else "保守觀望"
    
    return f"""
    <div class="content-card">
        <h3>📊 武吉拉深度分析</h3>
        <p><b>1. 趨勢結構：</b>{trend_detail} 收盤 {price:.2f}，月線 {ma20:.2f}。</p>
        <p><b>2. 籌碼解讀：</b>{inst_text}。</p>
        <p><b>3. 指標訊號：</b>KD {kd_sig} (K:{k:.1f})。</p>
        <hr>
        <p style="font-size: 1.2rem; font-weight: bold; color: #2962ff;">💡 建議：{advice}</p>
    </div>
    """

# --- 5. UI 介面 ---

st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("資料更新中..."):
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
    name = STOCK_NAMES.get(target, stock.info.get('longName', target))

    # 抓取資料
    df = stock.history(period="2y") # 抓夠長才能算年線
    if df.empty:
        st.error("找不到資料。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change = latest['Close'] - prev_close
        pct = (change / prev_close) * 100
        color = "#ff0000" if change >= 0 else "#009900"
        
        # --- 頂部報價卡片 (仿 Yahoo) ---
        st.markdown(f"""
        <div class="quote-card">
            <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
            <div style="display:flex; align-items:baseline;">
                <div class="price-big" style="color:{color}">{latest['Close']:.2f}</div>
                <div class="price-change" style="color:{color}"> {'▲' if change>=0 else '▼'} {abs(change):.2f} ({abs(pct):.2f}%)</div>
            </div>
            <div class="stats-grid">
                <div class="stat-box"><div class="stat-label">最高</div><div class="stat-val" style="color:#ff0000">{latest['High']:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">最低</div><div class="stat-val" style="color:#009900">{latest['Low']:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">昨收</div><div class="stat-val">{prev_close:.2f}</div></div>
                <div class="stat-box"><div class="stat-label">開盤</div><div class="stat-val">{latest['Open']:.2f}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- 分頁功能 ---
        tab1, tab2, tab3 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼"])
        
        with tab1:
            # K 線圖
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.01)
            
            # 1. 主圖
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name='K線', increasing_line_color='#ff0000', decreasing_line_color='#009900'
            ), row=1, col=1)
            
            ma_list = [('MA5','#1f77b4'), ('MA10','#9467bd'), ('MA20','#ff7f0e'), ('MA60','#bcbd22'), ('MA120','#8c564b'), ('MA240','#7f7f7f')]
            for ma, c in ma_list:
                fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)

            # 2. 成交量
            colors_vol = ['#ff0000' if r['Open'] < r['Close'] else '#009900' for i, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['VOL_MA5'], line=dict(color='#1f77b4', width=1), name='MV5'), row=2, col=1)

            # 3. KD
            fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.2), name='K9'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.2), name='D9'), row=3, col=1)
            
            # 預設顯示範圍 (最近 60 天 -> 解決密度問題)
            last_date = df.index[-1]
            start_view = last_date - timedelta(days=90) # 約 60 根 K 線
            
            fig.update_xaxes(range=[start_view, last_date], row=1, col=1) # 預設縮放
            
            # 底部 Range Slider (仿 Yahoo)
            fig.update_xaxes(
                rangeslider_visible=False, row=1, col=1
            )
            fig.update_xaxes(
                rangeslider_visible=True,
                rangeslider_thickness=0.08,
                row=3, col=1
            )
            
            fig.update_layout(
                template="plotly_white", height=700,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=1.01, x=0),
                hovermode='x unified',
                dragmode='pan', # 手指拖曳平移
            )
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True}) # 滾輪縮放

        with tab2:
            # 分析報告 (白卡片)
            inst_df = get_institutional_data_finmind(target)
            if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
            st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)
            
            st.subheader("詳細指標")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("KD", f"{latest['K']:.1f}/{latest['D']:.1f}")
            c2.metric("RSI", f"{latest['RSI']:.1f}")
            c3.metric("MACD", f"{latest['MACD']:.2f}")
            c4.metric("成交量", f"{int(latest['Volume']/1000):,}張")

        with tab3:
            if inst_df is not None and not inst_df.empty:
                st.markdown(f"<div class='content-card'><h3>🏛️ 三大法人買賣超 (近30日)</h3></div>", unsafe_allow_html=True)
                fig_inst = go.Figure()
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#1f77b4'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#9467bd'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#e377c2'))
                fig_inst.update_layout(barmode='group', template="plotly_white", height=400, xaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_inst, use_container_width=True)
            else:
                st.info("無法人資料")

except Exception as e:
    st.error(f"讀取錯誤: {e}")


