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

# --- 2. CSS 樣式 (核心：強制白底黑字 + 佈局修復) ---
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
    
    /* 遮罩層：讓背景稍微暗一點，凸顯白卡 */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.3);
        pointer-events: none;
        z-index: 0;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 設定背景
set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局重置 */
    .stApp { color: #333; font-family: "Microsoft JhengHei", "Heiti TC", sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* --- 卡片通用樣式 (White Card) --- */
    .quote-card, .content-card, .kd-card, .market-box {
        background-color: rgba(255, 255, 255, 0.98) !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        border: 1px solid #f0f0f0;
        position: relative;
        z-index: 1;
    }
    
    /* 強制所有卡片內的文字變黑 */
    .quote-card *, .content-card *, .kd-card *, .market-box * {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* --- 1. 報價卡片排版 (Grid Layout) --- */
    .quote-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 10px;
    }
    .stock-name { font-size: 1.8rem !important; font-weight: 900 !important; margin: 0; line-height: 1.2; }
    .stock-code { font-size: 1.1rem !important; color: #666 !important; font-weight: normal; }
    
    .price-row {
        display: flex; align-items: flex-end; gap: 15px; margin: 10px 0;
    }
    .big-price { 
        font-size: 4.5rem !important; 
        font-weight: 800 !important; 
        line-height: 1; 
        letter-spacing: -2px;
    }
    .price-info {
        display: flex; flex-direction: column; justify-content: flex-end;
        font-size: 1.2rem !important; font-weight: 700 !important;
    }
    
    /* 四格數據 */
    .grid-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px 20px;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px dashed #ddd;
    }
    .stat-item { display: flex; justify-content: space-between; align-items: center; }
    .stat-label { font-size: 0.95rem !important; color: #777 !important; }
    .stat-value { font-size: 1.1rem !important; font-weight: 700 !important; }
    
    /* 顏色工具 */
    .up-red { color: #e53935 !important; }
    .down-green { color: #43a047 !important; }

    /* --- 2. 搜尋框優化 --- */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: bold; font-size: 1.1rem;
        border: 2px solid #FFD700 !important;
        border-radius: 12px;
    }
    .stTextInput label { 
        color: #ffffff !important; 
        text-shadow: 2px 2px 4px #000; 
        font-size: 1.1rem; font-weight: bold;
    }
    
    /* --- 3. Tab 樣式 --- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px; padding: 5px;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem !important; font-weight: 700 !important; color: #666 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #fff !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {
        color: #000 !important;
    }

    /* --- 4. 週期按鈕 (橫向滑動) --- */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 5px;
        background-color: #fff; padding: 5px; border-radius: 20px;
        overflow-x: auto; white-space: nowrap;
        border: 1px solid #eee;
    }
    .stRadio div[role="radiogroup"] > label {
        flex: 0 0 auto; padding: 5px 15px; border-radius: 15px;
        background-color: #f5f5f5; margin-right: 5px; border: 1px solid #eee;
    }
    .stRadio div[role="radiogroup"] > label p {
        font-size: 0.9rem !important; font-weight: bold !important; color: #555 !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #333 !important; border-color: #333 !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        color: #fff !important;
    }
    
    /* 隱藏干擾元素 */
    [data-testid="stMetric"] { display: none; }
    
    /* 標題 */
    h1 { text-shadow: 3px 3px 8px #000; color: white !important; text-align: center; margin-bottom: 20px; }
    
    /* Plotly */
    .js-plotly-plot .plotly .main-svg { background: white !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料處理核心 ---

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
        # 優先嘗試上市
        ticker_tw = f"{user_input}.TW"
        try:
            s = yf.Ticker(ticker_tw)
            if not s.history(period="1d").empty: return ticker_tw, s.info.get('longName', ticker_tw)
        except: pass
        # 再嘗試上櫃
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
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    return df

# --- 4. 分析報告 ---
def generate_analysis(name, ticker, latest, inst_df, info):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    # 判斷
    trend = "盤整"
    if price > ma5 > ma10 > ma20: trend = "多頭排列"
    elif price < ma5 < ma10 < ma20: trend = "空頭排列"
    elif price > ma20: trend = "站上月線"
    else: trend = "跌破月線"
    
    kd_st = "黃金交叉" if k > d else "死亡交叉"
    
    # 籌碼
    inst_txt = "無數據"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        tot = last['Foreign'] + last['Trust'] + last['Dealer']
        inst_txt = f"法人合計 {'買超' if tot>0 else '賣超'} {abs(tot):,} 張"

    # 建議
    act = "觀望"
    if price > ma20 and k > d: act = "偏多操作"
    elif price < ma20 and k < d: act = "保守應對"
    
    return f"""
    <div class="content-card">
        <h3>📊 {name} ({ticker}) 專業分析</h3>
        <p><b>1. 技術面：</b>{trend}。KD指標 ({k:.1f}/{d:.1f}) 呈現 <span style="color:{'#e53935' if k>d else '#43a047'}"><b>{kd_st}</b></span>。</p>
        <p><b>2. 籌碼面：</b>{inst_txt}。</p>
        <p><b>3. 題材面：</b>{info.get('sector','科技')}類股。{info.get('longBusinessSummary','').split('。')[0]}。</p>
        <hr style="border-top: 1px dashed #ccc;">
        <p style="font-size:1.1rem; font-weight:bold; color:#004a99;">💡 操作建議：{act}</p>
        <ul style="margin-top:5px;">
            <li><b>進場參考：</b>回測 5日線 {ma5:.2f} 不破。</li>
            <li><b>出場參考：</b>跌破 月線 {ma20:.2f} 停損。</li>
        </ul>
    </div>
    """

# --- 5. 主介面 ---
st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入中..."):
    hot_tw, hot_us = get_market_hot_stocks()

c1, c2 = st.columns([3, 1])
with c1:
    target_input = st.text_input("🔍 搜尋代號 (如: 4903, 2330, NVDA)", value="2330")
with c2:
    hot_stock = st.selectbox("🔥 熱門", ["(選股)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

target = "2330.TW"
if hot_stock != "(選股)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input:
    with st.spinner("搜尋中..."):
        res_t, res_n = resolve_ticker(target_input)
        if res_t: target = res_t
        else: st.error("❌ 找不到股票")

if target:
    try:
        stock = yf.Ticker(target)
        info = stock.info
        name = STOCK_NAMES.get(target, info.get('longName', target))
        
        # 報價數據
        df_fast = stock.history(period="5d")
        if not df_fast.empty:
            latest = df_fast.iloc[-1]
            prev = df_fast['Close'].iloc[-2]
            price = latest['Close']
            chg = price - prev
            pct = (chg / prev) * 100
            color = "up-red" if chg >= 0 else "down-green"
            clr_code = "#e53935" if chg >= 0 else "#43a047"
            arrow = "▲" if chg >= 0 else "▼"
            
            # 報價卡片
            st.markdown(f"""
            <div class="quote-card">
                <div class="quote-header">
                    <div class="stock-name">{name} <span class="stock-code">({target})</span></div>
                </div>
                <div class="price-row">
                    <div class="big-price" style="color:{clr_code}">{price:.2f}</div>
                    <div class="price-info" style="color:{clr_code}">
                        <div>{arrow} {abs(chg):.2f}</div>
                        <div>({abs(pct):.2f}%)</div>
                    </div>
                </div>
                <div class="grid-stats">
                    <div class="stat-item"><span class="stat-label">最高</span><span class="stat-val" style="color:#e53935">{latest['High']:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">最低</span><span class="stat-val" style="color:#43a047">{latest['Low']:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">昨收</span><span class="stat-val">{prev:.2f}</span></div>
                    <div class="stat-item"><span class="stat-label">開盤</span><span class="stat-val">{latest['Open']:.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2, tab3, tab4 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞"])
            
            with tab1:
                p_map = {"1分":"1m", "5分":"5m", "30分":"30m", "日":"1d", "週":"1wk", "月":"1mo"}
                sel_p = st.radio("週期", list(p_map.keys()), horizontal=True, label_visibility="collapsed")
                
                interval = p_map[sel_p]
                period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
                if interval == "1m": period = "7d"
                
                df = stock.history(period=period, interval=interval)
                if not df.empty:
                    df = calculate_indicators(df)
                    last = df.iloc[-1]
                    
                    # K線圖
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
                    
                    # 1. K線
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線", increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
                    for ma, c in [('MA5','#2962ff'), ('MA10','#aa00ff'), ('MA20','#ff6d00'), ('MA60','#00c853')]:
                         if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)

                    # 2. 成交量
                    colors = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Vol'), row=2, col=1)

                    # 3. KD
                    fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#2962ff', width=1), name='K'), row=3, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff6d00', width=1), name='D'), row=3, col=1)

                    # 設定範圍: 最近 30 根
                    if len(df) > 30:
                        fig.update_xaxes(range=[df.index[-30], df.index[-1]], row=1, col=1)

                    fig.update_layout(
                        template="plotly_white", height=650, margin=dict(l=10,r=10,t=10,b=10),
                        showlegend=False, dragmode='pan', hovermode='x unified',
                        xaxis=dict(rangeslider_visible=False)
                    )
                    # 十字線
                    for r in [1,2,3]:
                        fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)
                        fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)
                        
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                    
                    # KD 卡片
                    st.markdown(f"""
                    <div class="quote-card kd-card">
                        <div class="kd-title">KD (9,3,3)</div>
                        <div style="text-align:right;">
                            <div class="kd-val">{last['K']:.1f} / {last['D']:.1f}</div>
                            <div style="color:{'#e53935' if last['K']>last['D'] else '#43a047'}; font-weight:bold;">
                                {'黃金交叉' if last['K']>last['D'] else '死亡交叉'}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with tab2:
                inst_df = get_institutional_data_finmind(target)
                if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
                st.markdown(generate_analysis(name, target, latest, inst_df, df, info), unsafe_allow_html=True)

            with tab3:
                if inst_df is not None and not inst_df.empty:
                    st.markdown("<div class='quote-card'><h3>🏛️ 法人買賣超</h3>", unsafe_allow_html=True)
                    fig_inst = go.Figure()
                    fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#2962ff'))
                    fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#aa00ff'))
                    fig_inst.update_layout(barmode='group', template="plotly_white", height=300, margin=dict(l=10,r=10,t=10,b=10))
                    st.plotly_chart(fig_inst, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else: st.info("無籌碼資料")

            with tab4:
                st.markdown("<div class='quote-card'><h3>📰 新聞</h3>", unsafe_allow_html=True)
                news = get_google_news(target)
                for n in news:
                    st.markdown(f"<div class='news-item'><a href='{n['link']}' target='_blank'>{n['title']}</a><div class='news-meta'>{n['pubDate']}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"讀取錯誤: {e}")


