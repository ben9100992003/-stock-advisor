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

# --- 2. CSS 樣式 ---
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
    .stApp { color: #333; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 1. 頂部報價卡片 */
    .quote-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }
    .stock-title { font-size: 1.4rem; font-weight: bold; color: #000; margin-bottom: 5px; }
    .stock-id { font-size: 1rem; color: #666; }
    .price-big { font-size: 3.2rem; font-weight: 800; line-height: 1; margin: 10px 0; }
    .price-change { font-size: 1.1rem; font-weight: bold; }
    .stats-grid { display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.9rem; color: #555; }
    .stat-box { text-align: right; }
    .stat-label { color: #888; font-size: 0.8rem; }
    .stat-val { color: #000; font-weight: bold; }

    /* 2. 內容卡片 */
    .content-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        color: #000 !important;
    }
    .content-card h3 { color: #000 !important; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .content-card p, .content-card li { color: #333 !important; font-size: 1rem; line-height: 1.6; }
    .content-card b { color: #000; }

    /* 3. 搜尋框 */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #000;
        border: 2px solid #eee;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        font-size: 1.2rem;
    }

    /* 4. KD 指標卡片 */
    .kd-card {
        background-color: #fff;
        border-left: 6px solid #2962ff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .kd-title { font-size: 1.3rem; font-weight: bold; color: #444; }
    .kd-val { font-size: 2rem; font-weight: 900; color: #000; }
    .kd-tag { padding: 6px 15px; border-radius: 20px; color: white; font-weight: bold; font-size: 1rem; }

    /* 5. Tab 與週期按鈕 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; font-size: 1.1rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #FFD700 !important; }
    
    .stRadio > div {
        display: flex; flex-direction: row; gap: 0px;
        background-color: #f0f0f0;
        padding: 4px; border-radius: 8px;
        width: 100%;
        justify-content: space-between;
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
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 新聞樣式 */
    .news-item {
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }
    .news-item a {
        text-decoration: none;
        color: #333 !important;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .news-item a:hover { color: #2962ff !important; }
    .news-meta {
        font-size: 0.85rem;
        color: #888;
        margin-top: 5px;
    }

    /* 隱藏預設 Metric */
    [data-testid="stMetric"] { display: none; }
    
    /* 連結按鈕 */
    .stLinkButton a { 
        background-color: #fff !important; 
        color: #333 !important; 
        border: 1px solid #ccc !important; 
        font-weight: bold !important; 
    }
    
    /* 標題 */
    h1, h2 { text-shadow: 2px 2px 5px #000; color: white !important; }
    
    /* Plotly Tooltip */
    .plotly-notifier { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接與搜尋邏輯 (全域搜尋版) ---

@st.cache_data(ttl=3600)
def resolve_ticker(user_input):
    """
    智慧解析代號，支援台股上市/上櫃/興櫃與美股
    回傳: (valid_ticker, stock_name) or (None, None)
    """
    user_input = user_input.strip().upper()
    
    # 1. 嘗試純數字 (預設台股)
    if user_input.isdigit():
        # 先試 .TW (上市)
        ticker_tw = f"{user_input}.TW"
        stock = yf.Ticker(ticker_tw)
        try:
            # 測試抓取最新價格確認是否存在
            hist = stock.history(period="1d")
            if not hist.empty:
                name = stock.info.get('longName', stock.info.get('shortName', ticker_tw))
                return ticker_tw, name
        except: pass
        
        # 再試 .TWO (上櫃) - 解決 4903 找不到的問題
        ticker_two = f"{user_input}.TWO"
        stock = yf.Ticker(ticker_two)
        try:
            hist = stock.history(period="1d")
            if not hist.empty:
                name = stock.info.get('longName', stock.info.get('shortName', ticker_two))
                return ticker_two, name
        except: pass
        
        return None, None # 真的找不到

    # 2. 嘗試美股或已帶後綴的代號
    else:
        stock = yf.Ticker(user_input)
        try:
            hist = stock.history(period="1d")
            if not hist.empty:
                name = stock.info.get('longName', stock.info.get('shortName', user_input))
                return user_input, name
        except: pass
        
        return None, None

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    
    # FinMind 代號不需要後綴
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
        
        # 強制日期格式為 YYYY/MM/DD
        pivot_df['Date'] = pd.to_datetime(pivot_df['Date']).dt.strftime('%Y/%m/%d')
        
        return pivot_df
    except Exception as e:
        return None

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
        if ".TW" not in ticker and ".TWO" not in ticker and len(ticker) < 5:
             query_ticker = f"{ticker} stock"
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
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma20 = latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭" if price > ma20 else "空頭"
    inst_text = "籌碼中性"
    inst_detail = ""
    
    if inst_df is not None and not inst_df.empty:
        last_row = inst_df.iloc[-1]
        f_val, t_val, d_val = last_row['Foreign'], last_row['Trust'], last_row['Dealer']
        total = f_val + t_val + d_val
        
        if total > 1000: inst_text = "法人買超"
        elif total < -1000: inst_text = "法人賣超"
        
        inst_detail = f"外資: {f_val:,} / 投信: {t_val:,} / 自營: {d_val:,}"
        
    kd_sig = "黃金交叉" if k > d else "死亡交叉"
    advice = "偏多操作" if price > ma20 and k > d else "保守觀望"
    
    return f"""
    <div class="content-card">
        <h3>📊 武吉拉深度分析</h3>
        <p><b>1. 趨勢：</b>{trend}格局。收盤 {price:.2f}，月線 {ma20:.2f}。</p>
        <p><b>2. 籌碼：</b>{inst_text}。<br><span style='font-size:0.9rem;color:#666;'>({inst_detail})</span></p>
        <p><b>3. 指標：</b>KD {kd_sig} (K:{k:.1f})。</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.2rem; font-weight: bold; color: #2962ff;">💡 建議：{advice}</p>
    </div>
    """

# --- 5. UI 介面 ---

st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 搜尋區塊
target_input = st.text_input("🔍 請輸入股票代號 (例如: 4903, 2330, NVDA)", value="2330")

# --- 處理搜尋邏輯 ---
if target_input:
    with st.spinner("正在搜尋資料..."):
        target, name = resolve_ticker(target_input)
        
    if not target:
        st.error(f"❌ 找不到股票代號：{target_input}。請確認代號是否正確，台股(上市/上櫃)輸入數字即可。")
    else:
        # 抓取資料
        stock = yf.Ticker(target)
        
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
        tab1, tab2, tab3, tab4 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞"])
        
        with tab1:
            # 週期按鈕
            interval_map = {
                "1分": "1m", "5分": "5m", "10分": "5m", 
                "30分": "30m", "60分": "60m", 
                "日": "1d", "週": "1wk", "月": "1mo"
            }
            period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            
            interval = interval_map[period_label]
            data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
            if interval == "1m": data_period = "7d"
            
            df = stock.history(period=data_period, interval=interval)
            
            if period_label == "10分":
                agg = {'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}
                df = df.resample('10min').agg(agg).dropna()

            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # K 線圖
            fig = make_subplots(
                rows=3, cols=1, 
                shared_xaxes=True, 
                row_heights=[0.6, 0.2, 0.2], 
                vertical_spacing=0.02
            )
            
            # 1. 主圖
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#ef5350', decreasing_line_color='#26a69a'), row=1, col=1)
            for ma, c in [('MA5','#1f77b4'), ('MA10','#9467bd'), ('MA20','#ff7f0e'), ('MA60','#bcbd22'), ('MA120','#8c564b')]:
                if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)

            # 2. 成交量
            colors_vol = ['#ef5350' if r['Open'] < r['Close'] else '#26a69a' for i, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
            if 'VOL_MA5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['VOL_MA5'], line=dict(color='#1f77b4', width=1), name='MV5'), row=2, col=1)

            # 3. KD
            fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.2), name='K9'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.2), name='D9'), row=3, col=1)

            # 設定預設顯示範圍
            if len(df) > 0:
                end_idx = df.index[-1]
                if interval in ["1m", "5m", "10m", "30m", "60m"]:
                    start_idx = end_idx - timedelta(days=1)
                    if start_idx < df.index[0]: start_idx = df.index[0]
                else:
                    if len(df) > 45: start_idx = df.index[-45]
                    else: start_idx = df.index[0]
                fig.update_xaxes(range=[start_idx, end_idx], row=1, col=1)

            # Layout
            fig.update_layout(
                template="plotly_white", height=700,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=1.01, x=0),
                dragmode='pan', 
                hovermode='x unified',
                xaxis=dict(rangeslider_visible=False, tickformat="%Y/%m/%d"),
                yaxis=dict(fixedrange=False) 
            )
            
            # 設定十字線
            for row in [1, 2, 3]:
                fig.update_xaxes(
                    showspikes=True, spikemode='across', spikesnap='cursor', 
                    showline=True, spikedash='dash', spikecolor="grey", spikethickness=1,
                    rangeslider_visible=False, 
                    row=row, col=1
                )
                fig.update_yaxes(
                    showspikes=True, spikemode='across', spikesnap='cursor', 
                    showline=True, spikedash='dash', spikecolor="grey", spikethickness=1,
                    row=row, col=1
                )
                
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False, 'doubleClick': 'reset+autosize'})
            
            # KD 卡片
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
            if inst_df is None and (".TW" in target or ".TWO" in target): inst_df = get_institutional_data_yahoo(target)
            st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)

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
            else:
                st.info("無法人籌碼資料")
                
        with tab4:
            st.markdown("<div class='content-card'><h3>📰 個股相關新聞</h3></div>", unsafe_allow_html=True)
            news_list = get_google_news(target)
            if news_list:
                for news in news_list:
                    st.markdown(f"""
                    <div class="content-card news-item">
                        <a href="{news['link']}" target="_blank">{news['title']}</a>
                        <div class="news-meta">{news['pubDate']} | {news['source']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暫無相關新聞")
