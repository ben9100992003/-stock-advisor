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

# --- 2. CSS 樣式 (核心：仿 App 白卡風格) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str:
        # 如果找不到圖，用預設深色背景，避免報錯
        st.markdown('<style>.stApp {background-color: #111;}</style>', unsafe_allow_html=True)
        return
    
    page_bg_img = """
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{0}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* 遮罩層讓文字更清楚 */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.3);
        pointer-events: none;
        z-index: 0;
    }}
    </style>
    """.format(bin_str)
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 設定背景
set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局強制設定 */
    .stApp { font-family: "Microsoft JhengHei", sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* --- 核心容器：懸浮白卡 --- */
    .white-card {
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        position: relative;
        z-index: 1;
    }
    
    /* --- 強制黑字 (解決看不見問題) --- */
    .white-card, .white-card p, .white-card h1, .white-card h2, .white-card h3, .white-card h4, 
    .white-card span, .white-card div, .white-card li, .white-card b {
        color: #000000 !important;
        text-shadow: none !important;
    }
    
    /* 1. 報價卡片排版 */
    .stock-header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }
    .stock-name { font-size: 1.8rem; font-weight: 900; margin: 0; }
    .stock-symbol { font-size: 1.2rem; color: #666 !important; font-weight: normal; }
    
    .price-row { display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }
    .price-main { font-size: 4rem; font-weight: 800; line-height: 1; letter-spacing: -1px; }
    .price-detail { display: flex; flex-direction: column; font-weight: 700; font-size: 1.2rem; }
    
    .grid-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 5px 20px; font-size: 0.95rem; }
    .grid-item { display: flex; justify-content: space-between; border-bottom: 1px dashed #eee; padding: 4px 0; }
    .lbl { color: #666 !important; }
    .val { font-weight: 700; }

    /* 2. 搜尋框優化 */
    .stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.9) !important;
        color: #000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 12px;
        font-weight: bold;
    }
    .stTextInput label { color: #fff !important; text-shadow: 1px 1px 3px black; font-size: 1.1rem; }

    /* 3. Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255,255,255,0.9); border-radius: 12px; padding: 5px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] button p {
        color: #555 !important; font-weight: 700; font-size: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {
        color: #000 !important;
    }

    /* 4. 週期按鈕 (Radio) */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 5px;
        background-color: #fff; padding: 5px; border-radius: 20px;
        width: 100%; overflow-x: auto; border: 1px solid #eee;
    }
    .stRadio div[role="radiogroup"] > label {
        flex: 1; text-align: center; padding: 6px 0; border-radius: 15px; 
        margin: 0; border: none; cursor: pointer; min-width: 50px;
        background-color: transparent;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #333 !important;
    }
    .stRadio div[role="radiogroup"] > label p { color: #555 !important; font-weight: bold; }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p { color: #fff !important; }

    /* 5. KD 卡片 */
    .kd-box {
        border-left: 6px solid #2962ff;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        display: flex; justify-content: space-between; align-items: center;
        margin-top: 10px;
    }
    
    /* 隱藏預設 */
    [data-testid="stMetric"] { display: none; }
    .stLinkButton a { background-color: #fff !important; color: #000 !important; border: 1px solid #ccc !important; font-weight: bold; }
    
    /* Plotly 背景 */
    .js-plotly-plot .plotly .main-svg { background: white !important; border-radius: 12px; }
    
    /* 標題 */
    h1 { text-shadow: 3px 3px 8px #000; color: white !important; margin-bottom: 20px; font-weight: 900; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料處理邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航",
    "3231.TW": "緯創", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "4903.TWO": "聯光通", "8110.TW": "華東", "6187.TWO": "萬潤", "3131.TWO": "弘塑",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "MSFT": "微軟"
}

@st.cache_data(ttl=3600)
def get_market_hot_stocks():
    # 預設熱門股
    hot_tw = ["2330", "2317", "2603", "2609", "3231", "2454", "2382", "2303", "2615", "3231"]
    hot_us = ["NVDA", "TSLA", "AAPL", "AMD", "PLTR", "MSFT", "AMZN", "META", "GOOGL", "AVGO"]
    try:
        # 嘗試從 FinMind 抓取真實熱門股
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
        for suffix in [".TW", ".TWO"]:
            ticker = f"{user_input}{suffix}"
            try:
                s = yf.Ticker(ticker)
                if not s.history(period="1d").empty: return ticker, s.info.get('longName', ticker)
            except: pass
        return None, None
    else:
        try:
            s = yf.Ticker(user_input)
            if not s.history(period="1d").empty: return user_input, s.info.get('longName', user_input)
        except: pass
        return None, None

@st.cache_data(ttl=300)
def get_institutional_data(ticker):
    """優先 FinMind，失敗轉 Yahoo"""
    if ".TW" not in ticker and ".TWO" not in ticker: return None, "US"
    
    # FinMind
    try:
        stock_id = ticker.split(".")[0]
        dl = DataLoader(token=FINMIND_API_TOKEN)
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if not df.empty:
            df['net'] = df['buy'] - df['sell']
            def normalize(n):
                if '外資' in n: return 'Foreign'
                if '投信' in n: return 'Trust'
                if '自營' in n: return 'Dealer'
                return 'Other'
            df['norm'] = df['name'].apply(normalize)
            pivot = df.pivot_table(index='date', columns='norm', values='net', aggfunc='sum').fillna(0)
            for c in ['Foreign', 'Trust', 'Dealer']: 
                if c not in pivot.columns: pivot[c] = 0
            
            pivot = (pivot / 1000).astype(int)
            pivot = pivot.reset_index().rename(columns={'date': 'Date'})
            return pivot, "FinMind"
    except: pass
    
    # Yahoo Fallback (爬蟲)
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0'}
        dfs = pd.read_html(requests.get(url, headers=headers).text)
        target_df = None
        for d in dfs:
            if any('外資' in str(c) for c in d.columns): target_df = d; break
        
        if target_df is not None:
            new_cols = {}
            for c in target_df.columns:
                if '日期' in str(c): new_cols[c] = 'Date'
                elif '外資' in str(c): new_cols[c] = 'Foreign'
                elif '投信' in str(c): new_cols[c] = 'Trust'
                elif '自營' in str(c): new_cols[c] = 'Dealer'
            
            df = target_df.rename(columns=new_cols)
            
            # 清洗數據
            def clean(x):
                if isinstance(x, str): return int(x.replace(',','').replace('+',''))
                return int(x)
            for c in ['Foreign', 'Trust', 'Dealer']:
                if c in df.columns: df[c] = df[c].apply(clean)
                else: df[c] = 0
            
            df['Date'] = df['Date'].apply(lambda x: f"{datetime.now().year}/{x}" if len(str(x))<=5 else x)
            return df.head(30), "Yahoo"
    except: pass
    
    return None, "None"

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

def generate_report_html(name, ticker, latest, inst_df):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    # 技術面
    trend = "多頭" if price > ma20 else "空頭"
    trend_text = f"股價{'站上' if price>ma20 else '跌破'}月線，趨勢{'偏多' if price>ma20 else '轉弱'}。"
    kd_stat = "黃金交叉" if k > d else "死亡交叉"
    
    # 籌碼面
    inst_html = "暫無資料"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1] if 'Date' in inst_df.columns else inst_df.iloc[0]
        # 確保取值正確 (FinMind 為時間序，Yahoo 為倒序，統一取最新)
        if 'Date' in inst_df.columns:
             # 簡單判斷：如果第一筆日期比最後一筆大，則是倒序
             d1 = str(inst_df['Date'].iloc[0])
             d2 = str(inst_df['Date'].iloc[-1])
             if d1 > d2: last = inst_df.iloc[0] # Yahoo
             else: last = inst_df.iloc[-1] # FinMind
             
        f, t, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f + t + d_val
        inst_html = f"""
        法人單日 {'買超' if total>0 else '賣超'} <b style="color:{'#e53935' if total>0 else '#43a047'}">{abs(total):,}</b> 張。<br>
        (外資 {f:,} / 投信 {t:,} / 自營 {d_val:,})
        """

    # 建議
    action = "偏多操作" if price > ma20 and k > d else "保守觀望"
    entry = f"{ma5:.2f}"
    exit_p = f"{ma20:.2f}"

    return f"""
    <div class="white-card">
        <h3 style="border-bottom:3px solid #FFD700; padding-bottom:10px;">📊 綜合分析報告</h3>
        <p><b>1. 技術趨勢：</b>{trend}格局。{trend_text}</p>
        <p><b>2. 指標訊號：</b>KD ({k:.1f}/{d:.1f}) 呈現 <b>{kd_stat}</b>。</p>
        <p><b>3. 籌碼動向：</b>{inst_html}</p>
        <hr style="margin:15px 0; border-top:1px dashed #ccc;">
        <p style="font-size:1.2rem; font-weight:bold; color:#2962ff;">💡 建議：{action}</p>
        <ul style="font-size:0.95rem;">
            <li>🟢 支撐參考：{entry}</li>
            <li>🔴 壓力參考：{exit_p}</li>
        </ul>
    </div>
    """

# --- 4. UI 主程式 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入數據..."):
    hot_tw, hot_us = get_market_hot_stocks()

c1, c2 = st.columns([3, 1])
with c1:
    target_input = st.text_input("🔍 搜尋代號 (如: 2330, NVDA)", value="2330")
with c2:
    hot_stock = st.selectbox("🔥 熱門", ["(選股)"] + [f"{t}.TW" for t in hot_tw] + hot_us)

target = "2330.TW"
if hot_stock != "(選股)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input:
    with st.spinner("搜尋中..."):
        res_t, res_n = resolve_ticker(target_input)
        if res_t: target = res_t; name = res_n
        else: st.error("❌ 找不到代號"); target = None

if target:
    try:
        stock = yf.Ticker(target)
        info = stock.info
        name = STOCK_NAMES.get(target, info.get('longName', target))
        
        # A. 報價卡片
        df_fast = stock.history(period="5d")
        if not df_fast.empty:
            latest_fast = df_fast.iloc[-1]
            prev = df_fast['Close'].iloc[-2]
            price = latest_fast['Close']
            chg = price - prev
            pct = (chg / prev) * 100
            c_txt = "#e53935" if chg >= 0 else "#43a047"
            arrow = "▲" if chg >= 0 else "▼"
            
            st.markdown(f"""
            <div class="white-card">
                <div class="quote-header">
                    <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
                </div>
                <div class="price-container">
                    <div class="price-big" style="color:{c_txt}">{price:.2f}</div>
                    <div class="price-change" style="color:{c_txt}">{arrow} {abs(chg):.2f} ({abs(pct):.2f}%)</div>
                </div>
                <div class="stats-grid">
                    <div class="grid-item"><span class="lbl">最高</span><span class="val" style="color:#e53935">{latest_fast['High']:.2f}</span></div>
                    <div class="grid-item"><span class="lbl">最低</span><span class="val" style="color:#43a047">{latest_fast['Low']:.2f}</span></div>
                    <div class="grid-item"><span class="lbl">昨收</span><span class="val">{prev:.2f}</span></div>
                    <div class="grid-item"><span class="lbl">開盤</span><span class="val">{latest_fast['Open']:.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # B. 分頁內容
        t1, t2, t3 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼"])
        
        with t1:
            # 週期按鈕
            p_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
            p_label = st.radio("週期", list(p_map.keys()), horizontal=True, label_visibility="collapsed")
            interval = p_map[p_label]
            
            # 決定資料長度
            d_period = "2y"
            if interval in ["1m", "5m", "30m", "60m"]: d_period = "5d"
            
            df = stock.history(period=d_period, interval=interval)
            
            # 資料處理 (分時聚合)
            if p_label == "10分": 
                 df = df.resample('10min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

            if not df.empty:
                df = calculate_indicators(df)
                latest = df.iloc[-1]

                # 繪製 K 線圖
                st.markdown('<div class="white-card" style="padding:5px;">', unsafe_allow_html=True)
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
                
                # K線 & MA
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K", increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
                for ma, c in [('MA5','#2962ff'), ('MA10','#aa00ff'), ('MA20','#ff6d00')]:
                    if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
                
                # Volume
                colors = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Vol'), row=2, col=1)
                
                # KD
                fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#2962ff', width=1), name='K'), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff6d00', width=1), name='D'), row=3, col=1)
                
                # 設定顯示範圍 (最近 40 根)
                if len(df) > 40:
                    fig.update_xaxes(range=[df.index[-40], df.index[-1]], row=1, col=1)
                
                # 樣式調整
                fig.update_layout(
                    height=600, margin=dict(l=10,r=10,t=10,b=10), 
                    paper_bgcolor='white', plot_bgcolor='white',
                    showlegend=False, hovermode='x unified',
                    dragmode='pan', xaxis=dict(rangeslider_visible=False), yaxis=dict(fixedrange=False)
                )
                
                # 十字線
                for r in [1,2,3]:
                    fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)
                    fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="#999", row=r, col=1)

                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
                
                # KD 數值卡
                k_val, d_val = latest['K'], latest['D']
                k_col = "#e53935" if k_val > d_val else "#43a047"
                st.markdown(f"""
                <div class="white-card kd-box">
                    <div class="kd-title">KD 指標 (9,3,3)</div>
                    <div style="text-align:right;">
                        <div class="kd-val">{k_val:.1f} / {d_val:.1f}</div>
                        <div style="color:{k_col}; font-weight:bold;">{'黃金交叉' if k_val>d_val else '死亡交叉'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 分析與籌碼
        inst_df, source = get_institutional_data(target)
        
        with t2:
            st.markdown(generate_report_html(name, target, latest, inst_df, df, info), unsafe_allow_html=True)
            
        with t3:
            if inst_df is not None and not inst_df.empty:
                st.markdown(f"<div class='white-card'><h3>🏛️ 三大法人 (近30日)</h3></div>", unsafe_allow_html=True)
                # 這裡可以再加圖表，先顯示表格
                st.dataframe(inst_df.head(15), use_container_width=True)
            else:
                st.info("無法人資料 (可能是美股或 ETF)")

    except Exception as e:
        st.error(f"讀取錯誤，請確認代號。({e})")


