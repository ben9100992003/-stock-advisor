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

# --- 2. CSS 樣式 (核心：白底黑字 + 橫向捲動) ---
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

set_png_as_page_bg('bg.png')

st.markdown("""
    <style>
    /* 全局基礎設定 */
    .stApp { color: #000000; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 核心：通用白卡樣式 --- */
    .white-card {
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        border: 1px solid #fff;
    }
    
    /* 強制卡片內所有文字變黑 */
    .white-card *, .white-card h2, .white-card h3, .white-card h4, .white-card p, .white-card span, .white-card div {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* --- A. 搜尋框 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stTextInput label { color: #ffffff !important; text-shadow: 2px 2px 4px #000; font-weight: bold; font-size: 1.1rem; }

    /* --- B. 報價卡片 --- */
    .stock-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
    .stock-title { font-size: 1.6rem !important; font-weight: 900 !important; }
    .stock-id { font-size: 1.1rem !important; color: #666 !important; }
    
    .price-container { display: flex; align-items: baseline; gap: 10px; margin-bottom: 15px; }
    .price-big { font-size: 3.5rem !important; font-weight: 800 !important; line-height: 1; }
    .price-change { font-size: 1.2rem !important; font-weight: 700 !important; }
    
    .stats-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 8px 20px;
        border-top: 1px solid #eee; padding-top: 10px;
    }
    .stat-row { display: flex; justify-content: space-between; }
    .stat-label { font-size: 0.9rem !important; color: #666 !important; }
    .stat-val { font-weight: bold !important; font-size: 1rem !important; }

    /* --- C. 橫向捲動選單 (Horizontal Scroll Menu) --- */
    .stRadio > div {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* 強制不換行 */
        overflow-x: auto !important;  /* 允許左右滑動 */
        gap: 8px !important;
        background-color: #ffffff !important;
        padding: 10px 5px !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        -webkit-overflow-scrolling: touch; /* 手機滑動流暢 */
    }
    /* 隱藏捲軸但保留功能 */
    .stRadio > div::-webkit-scrollbar { display: none; }
    
    .stRadio div[role="radiogroup"] > label {
        flex: 0 0 auto !important; /* 寬度自動，不壓縮 */
        padding: 6px 16px !important;
        border-radius: 20px !important;
        background-color: #f0f0f0 !important;
        border: 1px solid #ddd !important;
        margin: 0 !important;
        transition: all 0.2s;
    }
    .stRadio div[role="radiogroup"] > label p {
        color: #333 !important; font-weight: bold !important; font-size: 0.9rem !important; margin: 0 !important;
    }
    /* 選中狀態 */
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #333 !important;
        border-color: #333 !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        color: #fff !important;
    }

    /* --- D. 圖表容器 --- */
    .chart-container {
        background-color: #fff !important;
        border-radius: 12px;
        padding: 5px;
        margin-bottom: 20px;
    }
    
    /* --- E. 分析與籌碼 --- */
    .analysis-section h4 {
        color: #004a99 !important; margin-top: 15px; margin-bottom: 8px; font-weight: 800 !important;
    }
    .analysis-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 0.95rem; }
    .analysis-table th { background: #f5f5f5; padding: 8px; text-align: center; border: 1px solid #ddd; }
    .analysis-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }

    /* 隱藏預設元件 */
    [data-testid="stMetric"] { display: none; }
    .js-plotly-plot .plotly .main-svg { background: white !important; border-radius: 8px; }
    h1 { text-shadow: 3px 3px 8px #000; color: white !important; margin-bottom: 15px; font-weight: 900; text-align: center; }
    
    /* 連結按鈕 */
    .stLinkButton a { background-color: #fff !important; color: #000 !important; border: 1px solid #ccc !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料處理邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航",
    "3231.TW": "緯創", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "4903.TWO": "聯光通", "8110.TW": "華東", "6187.TWO": "萬潤", "3131.TWO": "弘塑",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "TSM": "台積電 ADR"
}

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

def generate_report_html(name, ticker, latest, inst_df, info):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    # 技術面
    tech_trend = "盤整"
    tech_desc = ""
    if price > ma5 and ma5 > ma10 and ma10 > ma20:
        tech_trend = "強勢多頭"
        tech_desc = "均線多頭排列，股價沿 5 日線強攻。"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20:
        tech_trend = "弱勢空頭"
        tech_desc = "均線空頭排列，上方反壓沉重。"
    elif price > ma20:
        tech_trend = "多方控盤"
        tech_desc = "站穩月線，中期趨勢偏多。"
    else:
        tech_trend = "空方控盤"
        tech_desc = "跌破月線，短線轉弱。"
        
    kd_status = "黃金交叉" if k > d else "死亡交叉"
    
    # 籌碼面
    inst_html = "<tr><td colspan='5'>暫無資料</td></tr>"
    inst_msg = "暫無數據"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        total = last['Foreign'] + last['Trust'] + last['Dealer']
        inst_msg = f"三大法人合計 {'買超' if total>0 else '賣超'} {abs(total):,} 張"
        
        inst_html = f"""
        <tr>
            <td>{last['Date']}</td>
            <td style="color:{'#e53935' if last['Foreign']>0 else '#43a047'}">{last['Foreign']:,}</td>
            <td style="color:{'#e53935' if last['Trust']>0 else '#43a047'}">{last['Trust']:,}</td>
            <td style="color:{'#e53935' if last['Dealer']>0 else '#43a047'}">{last['Dealer']:,}</td>
            <td style="color:{'#e53935' if total>0 else '#43a047'}"><b>{total:,}</b></td>
        </tr>
        """

    # 建議
    action = "觀望"
    entry_pt = f"{ma10:.2f}"
    exit_pt = f"{ma5:.2f}"
    if price > ma20 and k > d:
        action = "偏多操作"
        entry_pt = f"拉回 {ma5:.2f} 不破"
        exit_pt = f"跌破 {ma20:.2f}"
    elif price < ma20 and k < d:
        action = "保守操作"
        entry_pt = f"站回 {ma20:.2f}"
        exit_pt = f"反彈 {ma10:.2f}"
        
    return f"""
    <div class="white-card">
        <h3 style="color:#000; border-bottom:2px solid #FFD700; padding-bottom:5px;">📊 武吉拉深度分析</h3>
        
        <div class="analysis-section">
            <h4>1. 技術面判讀</h4>
            <p><b>趨勢：</b><span style="color:#2962ff">{tech_trend}</span>。{tech_desc}</p>
            <p><b>KD指標：</b>{k:.1f}/{d:.1f} ({kd_status})</p>
        </div>

        <div class="analysis-section">
            <h4>2. 籌碼面解析</h4>
            <p>{inst_msg}</p>
            <table class="analysis-table">
                <thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營</th><th>合計</th></tr></thead>
                <tbody>{inst_html}</tbody>
            </table>
        </div>

        <div class="analysis-section">
            <h4>3. 操作建議 ({action})</h4>
            <ul>
                <li><b>🟢 進場參考：</b>{entry_pt}</li>
                <li><b>🔴 停損參考：</b>{exit_pt}</li>
            </ul>
        </div>
    </div>
    """

# --- 5. UI 主程式 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 卡片 A：搜尋
target_input = st.text_input("🔍 請輸入代號 (如: 2330, NVDA)", value="2330")

if target_input:
    with st.spinner("搜尋中..."):
        target, name = resolve_ticker(target_input)
        if not target:
            st.error("❌ 找不到代號，請確認輸入是否正確。")
            st.stop()
else:
    target, name = "2330.TW", "台積電"

try:
    stock = yf.Ticker(target)
    
    # 卡片 B：報價
    df_fast = stock.history(period="5d")
    if not df_fast.empty:
        latest_fast = df_fast.iloc[-1]
        prev = df_fast['Close'].iloc[-2]
        price = latest_fast['Close']
        chg = price - prev
        pct = (chg / prev) * 100
        color = "#e53935" if chg >= 0 else "#43a047"
        arrow = "▲" if chg >= 0 else "▼"
        
        st.markdown(f"""
        <div class="white-card quote-card">
            <div class="stock-header">
                <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
            </div>
            <div class="price-container">
                <div class="price-big" style="color:{color}">{price:.2f}</div>
                <div class="price-change" style="color:{color}">{arrow} {abs(chg):.2f} ({abs(pct):.2f}%)</div>
            </div>
            <div class="stats-grid">
                <div class="stat-row"><span class="stat-label">最高</span><span class="stat-val" style="color:#e53935">{latest_fast['High']:.2f}</span></div>
                <div class="stat-row"><span class="stat-label">昨收</span><span class="stat-val">{prev:.2f}</span></div>
                <div class="stat-row"><span class="stat-label">最低</span><span class="stat-val" style="color:#43a047">{latest_fast['Low']:.2f}</span></div>
                <div class="stat-row"><span class="stat-label">開盤</span><span class="stat-val">{latest_fast['Open']:.2f}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 卡片 C：週期選單 (橫向滑動)
    interval_map = {"1分": "1m", "5分": "5m", "10分": "5m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
    period = st.radio("K線週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
    
    # 卡片 D：K 線圖
    interval = interval_map[period]
    period_len = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
    if interval == "1m": period_len = "7d"
    
    df = stock.history(period=period_len, interval=interval)
    if period == "10分": df = df.resample('10min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
    
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    
    st.markdown('<div class="white-card chart-container">', unsafe_allow_html=True)
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
    
    # K線
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
    # 均線
    for ma, c in [('MA5','#2962ff'), ('MA10','#aa00ff'), ('MA20','#ff6d00'), ('MA60','#00c853'), ('MA120','#795548')]:
        if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
        
    # 成交量
    colors = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
    
    # KD
    fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#2962ff', width=1.2), name='K'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff6d00', width=1.2), name='D'), row=3, col=1)
    
    # 設定顯示範圍：最近 45 根 (大K線)
    if len(df) > 45:
        fig.update_xaxes(range=[df.index[-45], df.index[-1]], row=1, col=1)
        
    # 互動設定
    fig.update_layout(
        template="plotly_white", height=650, 
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.01, x=0),
        dragmode='pan', hovermode='x unified',
        xaxis=dict(rangeslider_visible=False), yaxis=dict(fixedrange=False),
        paper_bgcolor='white', plot_bgcolor='white'
    )
    # 十字線
    for r in [1,2,3]:
        fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)
        fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

    # 卡片 E：分析與籌碼
    inst_df = get_institutional_data_finmind(target)
    if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
    st.markdown(generate_report_html(name, target, latest, inst_df, df, info), unsafe_allow_html=True)

except Exception as e:
    st.error(f"讀取資料錯誤，請稍後再試。({e})")


