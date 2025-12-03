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
import json
import textwrap

# --- 0. 設定與金鑰 ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"
GEMINI_API_KEY = "AIzaSyB6Y_RNa5ZXdBjy_qIwxDULlD69Nv9PUp8"

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
    if not os.path.exists(png_file): 
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(to bottom right, #141e30, #243b55); }
        </style>
        """, unsafe_allow_html=True)
        return

    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str: return
    
    page_bg_img = """
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{0}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* 背景深色遮罩 */
    .stApp::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.6); pointer-events: none; z-index: 0;
    }}
    </style>
    """.format(bin_str)
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* 全局設定 */
    .stApp { font-family: "Microsoft JhengHei", "sans-serif"; color: #333; }
    h1, h2, h3, h4, h5, h6 { color: #333; }
    
    /* --- 卡片通用設定 (灰白色背景) --- */
    .quote-card, .content-card, .kd-card, .market-summary-box, .ai-chat-box, .light-card {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 16px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px; border: 1px solid #eee;
        position: relative; z-index: 1;
        color: #333 !important;
    }
    
    /* 強制卡片內文字顏色 */
    .quote-card *, .content-card *, .kd-card *, .market-summary-box *, .ai-chat-box *, .light-card * {
        text-shadow: none !important;
        color: #333; 
    }

    /* --- 股票報價卡片 --- */
    .stock-tag {
        display: inline-block; padding: 4px 12px; border-radius: 4px;
        font-size: 0.85rem; font-weight: bold; margin-bottom: 8px;
        background-color: #fff3e0; color: #f57c00 !important; /* 交易中 橘色 */
    }
    
    .price-large {
        font-size: 3.5rem !important; font-weight: 700; line-height: 1.1; margin: 0;
        white-space: nowrap; /* 防止價格換行 */
    }
    
    .price-info-row { 
        display: flex; align-items: center; gap: 15px; margin-bottom: 15px;
        flex-wrap: nowrap !important;
    }
    
    .price-change-block { 
        display: flex; flex-direction: column; justify-content: center;
        font-size: 1.1rem; font-weight: 600; line-height: 1.4; min-width: 80px;
    }
    
    /* 紅漲綠跌定義 */
    .text-up { color: #e53935 !important; }
    .text-down { color: #43a047 !important; }
    .text-flat { color: #757575 !important; }

    /* 數據表格樣式 (Table) */
    table.quote-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        table-layout: fixed; /* 固定佈局，確保欄位平均 */
    }
    table.quote-table td {
        padding: 12px 8px; /* 增加一點間距 */
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        font-size: 1rem;
    }
    table.quote-table .label {
        color: #666;
        font-weight: 500;
        float: left;
    }
    table.quote-table .value {
        font-weight: 700;
        color: #000;
        float: right;
    }
    /* 表格中間的分隔線 */
    .border-right {
        border-right: 1px solid #eee;
    }
    /* 最後一列不顯示底線 */
    table.quote-table tr:last-child td {
        border-bottom: none;
    }

    /* --- 3. K線選擇器 (強制左右滑動 & 膠囊樣式) --- */
    .stRadio > div[role="radiogroup"] {
        background-color: #ffffff !important; /* 白色背景 */
        border-radius: 30px !important; 
        padding: 8px 12px !important;
        display: flex !important; 
        flex-direction: row !important; 
        gap: 8px !important;
        overflow-x: auto !important; /* 核心：開啟水平滾動 */
        white-space: nowrap !important; /* 核心：禁止換行 */
        flex-wrap: nowrap !important; /* 核心：禁止 Flex 換行 */
        border: 1px solid #ddd;
        scrollbar-width: none; /* Firefox 隱藏捲軸 */
        width: 100%;
        align-items: center;
        -webkit-overflow-scrolling: touch; /* iOS 滑動優化 */
    }
    .stRadio > div[role="radiogroup"]::-webkit-scrollbar { display: none; /* Chrome 隱藏捲軸 */ }
    
    .stRadio div[role="radiogroup"] > label {
        flex: 0 0 auto !important; /* 禁止壓縮按鈕 */
        min-width: 60px !important; /* 設定最小寬度，強迫溢出 */
        background-color: transparent !important; 
        border: none !important;
        padding: 6px 14px !important; 
        border-radius: 20px !important;
        cursor: pointer; 
        transition: all 0.2s;
        margin: 0 !important;
        text-align: center;
    }
    
    /* 文字樣式 */
    .stRadio div[role="radiogroup"] > label p { 
        color: #555 !important; font-weight: 600; font-size: 0.95rem; margin: 0; padding: 0;
        white-space: nowrap !important;
    }
    
    /* 選中樣式 (紅底白字) */
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #e53935 !important;
        box-shadow: 0 2px 6px rgba(229, 57, 53, 0.4);
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p { color: #fff !important; font-weight: bold; }

    /* --- 其他元件 --- */
    .stTextInput input {
        background-color: #fff !important; color: #333 !important;
        border: 1px solid #ccc !important; border-radius: 8px;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #fff !important; color: #333 !important;
        border-color: #ccc !important;
    }
    
    .stButton button {
        border-radius: 12px; height: 100%; width: 100%;
        padding: 0.5rem 0; background-color: #fff;
        border: 1px solid #ccc; color: #333; font-weight: bold;
    }
    
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.5); border-radius: 10px; padding: 5px; gap: 5px; overflow-x: auto; white-space: nowrap; }
    .stTabs button { border-radius: 8px; flex: 0 0 auto; background: transparent; border: none; }
    .stTabs button[aria-selected="true"] { background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stTabs button p { color: #555 !important; font-weight: 600; }
    .stTabs button[aria-selected="true"] p { color: #e53935 !important; }

    h1 { text-shadow: 0 2px 4px rgba(0,0,0,0.5); color: #fff !important; text-align: center; font-weight: 900; }
    .ai-msg-user span { background-color: #e3f2fd; color: #333 !important; padding: 10px 15px; border-radius: 15px 15px 0 15px; border: 1px solid #bbdefb; }
    .ai-msg-bot span { background-color: #f5f5f5; color: #333 !important; padding: 10px 15px; border-radius: 15px 15px 15px 0; border: 1px solid #e0e0e0; }
    
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
    
    /* 隱藏 Radio 預設圓點 */
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] > p { display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接與邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "3231.TW": "緯創", "2356.TW": "英業達", "2376.TW": "技嘉", "2301.TW": "光寶科",
    "4903.TWO": "聯光通", "8110.TW": "華東", "6187.TWO": "萬潤", "3131.TWO": "弘塑",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "MSFT": "微軟"
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

# 產生 Yahoo 股市連結
def get_yahoo_stock_url(ticker):
    if ".TW" in ticker:
        return f"https://tw.stock.yahoo.com/quote/{ticker.replace('.TW', '')}"
    elif ".TWO" in ticker:
        return f"https://tw.stock.yahoo.com/quote/{ticker.replace('.TWO', '')}"
    else:
        return f"https://finance.yahoo.com/quote/{ticker}"

def call_gemini_api(prompt):
    if not GEMINI_API_KEY: return "⚠️ 未設定 Gemini API Key，無法使用 AI 功能。"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200: return response.json()['candidates'][0]['content']['parts'][0]['text']
        else: return f"AI 回應錯誤: {response.status_code} - 請檢查 API Key 或網路連線。"
    except Exception as e: return f"連線錯誤: {e}"

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# --- 回測邏輯 ---
def run_backtest(df, strategy_type, initial_capital=100000):
    df = df.copy()
    df['Signal'] = 0
    if strategy_type == "MA 均線策略 (MA5穿過MA20)":
        df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, -1)
    elif strategy_type == "KD 策略 (黃金交叉)":
        df['Signal'] = np.where(df['K'] > df['D'], 1, -1)
    
    df['Action'] = df['Signal'].diff()
    capital = initial_capital
    position = 0 
    df['Total_Assets'] = initial_capital
    trades = []
    
    for i in range(1, len(df)):
        price = df['Close'].iloc[i]
        date = df.index[i]
        if df['Signal'].iloc[i] == 1 and df['Signal'].iloc[i-1] != 1:
            if capital > 0:
                shares = int(capital // price)
                if shares > 0:
                    cost = shares * price
                    capital -= cost
                    position += shares
                    trades.append({'日期': date, '動作': '買進', '價格': price, '股數': shares, '餘額': capital})
        elif df['Signal'].iloc[i] == -1 and df['Signal'].iloc[i-1] != -1:
            if position > 0:
                revenue = position * price
                capital += revenue
                trades.append({'日期': date, '動作': '賣出', '價格': price, '股數': position, '餘額': capital})
                position = 0
        df.iloc[i, df.columns.get_loc('Total_Assets')] = capital + (position * price)
        
    final_assets = df['Total_Assets'].iloc[-1]
    return_rate = ((final_assets - initial_capital) / initial_capital) * 100
    return df, trades, final_assets, return_rate

def generate_narrative_report(name, ticker, latest, inst_df, df, info):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    tech_trend = "盤整"
    if price > ma5 and ma5 > ma10 and ma10 > ma20: tech_trend = "多頭排列"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20: tech_trend = "空頭排列"
    elif price > ma20: tech_trend = "站上月線"
    else: tech_trend = "跌破月線"

    kd_status = "黃金交叉" if k > d else "死亡交叉"
    kd_color = "text-up" if k > d else "text-down"
    kd_desc = f"KD 指標 ({k:.1f}/{d:.1f}) 呈現 <b class='{kd_color}'>{kd_status}</b>。"
    
    inst_table_html = "<tr><td colspan='4'>暫無資料</td></tr>"
    inst_desc = "暫無法人數據。"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        f_val, t_val, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f_val + t_val + d_val
        color_total = 'text-up' if total > 0 else 'text-down'
        inst_desc = f"法人單日合計 <b class='{color_total}'>{'買超' if total>0 else '賣超'} {abs(total):,} 張</b>。"
        
        inst_table_html = f"""
        <tr>
            <td>{last['Date']}</td>
            <td class="{'text-up' if f_val>0 else 'text-down'}">{f_val:,}</td>
            <td class="{'text-up' if t_val>0 else 'text-down'}">{t_val:,}</td>
            <td class="{'text-up' if d_val>0 else 'text-down'}">{d_val:,}</td>
            <td class="{'text-up' if total>0 else 'text-down'}"><b>{total:,}</b></td>
        </tr>
        """

    sector = info.get('sector', '科技')
    summary = info.get('longBusinessSummary', '暫無詳細說明。')[:150] + "..."
    theme_text = f"<b>{name}</b> 屬於 {sector} 產業。{summary}"
    
    support = ma10 if price > ma10 else ma20
    resistance = ma5 if price < ma5 else price * 1.05
    
    if price > ma20 and k > d:
        action = "偏多操作"
        entry = f"拉回至 5 日線 {ma5:.2f} 附近佈局"
        exit_pt = f"跌破月線 {ma20:.2f} 停損"
    elif price < ma20 and k < d:
        action = "保守觀望"
        entry = f"等待站回月線 {ma20:.2f}"
        exit_pt = f"反彈至月線 {ma20:.2f} 減碼"
    else:
        action = "區間震盪"
        entry = f"箱型下緣 {support:.2f} 低接"
        exit_pt = f"箱型上緣 {resistance:.2f} 獲利"

    return f"""
    <div class="content-card">
        <h3>📊 {name} ({ticker}) 綜合分析報告</h3>
        <h4>1. 技術指標分析</h4>
        <table class="analysis-table">
            <tr><td><b>收盤價</b></td><td>{price:.2f}</td><td><b>MA5</b></td><td>{ma5:.2f}</td></tr>
            <tr><td><b>MA20</b></td><td>{ma20:.2f}</td><td><b>KD</b></td><td>{k:.1f}/{d:.1f}</td></tr>
            <tr><td colspan="4"><b>趨勢判讀：</b>{tech_trend}。{kd_desc}</td></tr>
        </table>
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
        
        status = "多頭強勢" if price > ma20 and k > d else "多頭回檔" if price > ma20 else "空方修正"
        color = "#e53935" if k > d else "#f57c00" if price > ma20 else "#43a047"
        comment = f"KD({k:.1f}/{d:.1f})。市場氣氛：{status}。"
        return {"price": price, "change": change, "status": status, "color": color, "comment": comment}
    except: return None

# --- UI 介面 ---
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

with st.spinner("載入數據..."):
    hot_tw, hot_us = get_market_hot_stocks()

# 修改為 3 欄，搜尋 | 快選 | 重新整理
c_search, c_hot, c_btn = st.columns([2.5, 1.2, 0.5])
with c_search:
    target_input = st.text_input("🔍 搜尋代號/名稱 (如: 4903, 2330, NVDA)", value="2330")
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + [f"{t}.TW" for t in hot_tw] + hot_us)
with c_btn:
    st.write("") # 排版用，讓按鈕垂直對齊
    st.write("") 
    if st.button("🔄", help="重新整理數據"):
        st.cache_data.clear()
        st.rerun()

target = "2330.TW" 
if hot_stock != "(請選擇)": target = hot_stock.split("(")[-1].replace(")", "")
if target_input:
    resolved_ticker, resolved_name = resolve_ticker(target_input)
    if resolved_ticker: target = resolved_ticker; name = resolved_name
    else: st.error(f"❌ 找不到股票代號：{target_input}。"); target = None

with st.expander("🌍 查看今日大盤情緒 (台股 / 美股)", expanded=False):
    t1, t2 = st.tabs(["🇹🇼 台股加權", "🇺🇸 美股那斯達克"])
    with t1:
        tw = analyze_market_index("^TWII")
        if tw: st.markdown(f"<div class='market-summary-box'><div style='color:{tw['color']};font-weight:bold;font-size:1.2rem'>{tw['price']:.0f} ({tw['change']:+.0f})</div><div>{tw['status']} - {tw['comment']}</div></div>", unsafe_allow_html=True)
    with t2:
        us = analyze_market_index("^IXIC")
        if us: st.markdown(f"<div class='market-summary-box' style='border-left:4px solid #00BFFF'><div style='color:{us['color']};font-weight:bold;font-size:1.2rem'>{us['price']:.0f} ({us['change']:+.0f})</div><div>{us['status']} - {us['comment']}</div></div>", unsafe_allow_html=True)

st.markdown("---")

if target:
    try:
        stock = yf.Ticker(target)
        info = stock.info
        if 'name' not in locals(): name = STOCK_NAMES.get(target, info.get('longName', target))
        
        df_fast = stock.history(period="5d")
        if not df_fast.empty:
            latest_fast = df_fast.iloc[-1]
            prev_close = df_fast['Close'].iloc[-2]
            change = latest_fast['Close'] - prev_close
            pct = (change / prev_close) * 100
            
            # 漲是紅 (#e53935), 跌是綠 (#43a047)
            color_class = "text-up" if change >= 0 else "text-down"
            arrow = "▲" if change >= 0 else "▼"
            yahoo_url = get_yahoo_stock_url(target)
            
            # 使用 HTML Table 確保報價資訊整齊排列 ("表格化")
            quote_html = textwrap.dedent(f"""
            <div class="quote-card">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <div class="stock-tag">交易中</div>
                        <div class="stock-title" style="font-size:1.5rem; font-weight:bold;">
                            <a href="{yahoo_url}" target="_blank" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:5px;">
                                {name} <span style="font-size:1rem; color:#888;">{target}</span>
                                <span style="font-size:0.8rem; background:#eee; padding:2px 6px; border-radius:4px; color:#555;">Yahoo 🔗</span>
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="price-info-row">
                    <div class="price-large {color_class}">{latest_fast['Close']:.2f}</div>
                    <div class="price-change-block {color_class}">
                        <div>{arrow} {abs(change):.2f}</div>
                        <div>{abs(pct):.2f}%</div>
                    </div>
                </div>
                
                <table class="quote-table">
                    <tr>
                        <td class="border-right">
                            <span class="label">最高</span>
                            <span class="value text-up">{latest_fast['High']:.2f}</span>
                        </td>
                        <td style="padding-left: 15px;">
                            <span class="label">昨收</span>
                            <span class="value">{prev_close:.2f}</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="border-right">
                            <span class="label">最低</span>
                            <span class="value text-down">{latest_fast['Low']:.2f}</span>
                        </td>
                        <td style="padding-left: 15px;">
                            <span class="label">開盤</span>
                            <span class="value">{latest_fast['Open']:.2f}</span>
                        </td>
                    </tr>
                </table>
            </div>
            """)
            st.markdown(quote_html, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞", "🤖 AI 投顧", "🔄 回測"])
        
        with tab1:
            # 左右滑動的按鈕 (亮白色風格，解決看不清楚問題)
            interval_map = {"1分": "1m", "5分": "5m", "15分": "15m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
            period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            
            interval = interval_map[period_label]
            is_intraday = interval in ["1m", "5m", "15m", "30m", "60m"]
            data_period = "5d" if is_intraday else ("2y" if interval == "1d" else "5y")
            
            df = stock.history(period=data_period, interval=interval)
            
            if not df.empty:
                df = calculate_indicators(df)
                latest = df.iloc[-1]
                
                plot_df = df.copy()
                if is_intraday:
                    last_date = df.index[-1].date()
                    plot_df = df[df.index.date == last_date]
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
                
                # K線圖: 漲紅跌綠
                fig.add_trace(go.Candlestick(
                    x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], 
                    name='K線', increasing_line_color='#e53935', decreasing_line_color='#43a047'
                ), row=1, col=1)
                
                for ma, c in [('MA5','#2196f3'), ('MA10','#9c27b0'), ('MA20','#ff9800'), ('MA60','#795548')]:
                    if ma in plot_df.columns: fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
                
                colors_vol = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in plot_df.iterrows()]
                fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['K'], line=dict(color='#2196f3', width=1.5), name='K9'), row=3, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['D'], line=dict(color='#ff9800', width=1.5), name='D9'), row=3, col=1)

                if not is_intraday and len(plot_df) > 60:
                    fig.update_xaxes(range=[plot_df.index[-60], plot_df.index[-1]], row=1, col=1)

                # 減少邊距，去除圖表周圍的空白
                fig.update_layout(
                    template="plotly_white",
                    height=600, margin=dict(l=10, r=10, t=10, b=10), 
                    legend=dict(orientation="h", y=1.01, x=0, font=dict(color="black")),
                    dragmode='pan', hovermode='x unified', 
                    xaxis=dict(rangeslider_visible=False), 
                    yaxis=dict(fixedrange=True),
                    yaxis2=dict(fixedrange=True),
                    yaxis3=dict(fixedrange=True),
                    paper_bgcolor='rgba(255,255,255,0.95)', plot_bgcolor='white', # 修正背景顏色
                    font=dict(color='black')
                )
                
                grid_color = "#e0e0e0"
                for row in [1, 2, 3]:
                    fig.update_xaxes(showgrid=True, gridcolor=grid_color, row=row, col=1)
                    fig.update_yaxes(showgrid=True, gridcolor=grid_color, row=row, col=1)
                
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            
            kd_color_style = "text-up" if latest['K'] > latest['D'] else "text-down"
            kd_text = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
            kd_border_color = "#e53935" if latest['K'] > latest['D'] else "#43a047"
            
            st.markdown(f"""<div class="kd-card" style="border-left: 6px solid {kd_border_color};"><div class="kd-title">KD 指標 (9,3,3)</div><div style="text-align:right;"><div class="kd-val">{latest['K']:.1f} / {latest['D']:.1f}</div><div class="kd-tag {kd_color_style}" style="background-color:transparent; font-size:1.1rem;">{kd_text}</div></div></div>""", unsafe_allow_html=True)

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
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#2196f3'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#9c27b0'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#e53935'))
                
                # 修復圖表重複參數錯誤並優化顯示
                fig_inst.update_layout(
                    barmode='group', template="plotly_white", height=400,
                    margin=dict(t=0, b=10, l=10, r=10), # 移除上方空白
                    paper_bgcolor='rgba(255,255,255,0.95)', plot_bgcolor='white', 
                    font=dict(color='black'), 
                    yaxis=dict(fixedrange=True, zeroline=True, zerolinecolor='#333', gridcolor='#e0e0e0'), 
                    dragmode='pan', # 允許拖曳平移 (左右移動)
                    xaxis=dict(autorange="reversed", showgrid=True, gridcolor='#e0e0e0', fixedrange=False) # 允許 X 軸移動
                )
                
                st.markdown("<div class='content-card'>", unsafe_allow_html=True)
                st.plotly_chart(fig_inst, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                
                # 增加 overflow-x: auto 以支援表格左右滑動
                table_html = "<div style='overflow-x: auto;'><table class='analysis-table' style='width:100%'><thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營商</th></tr></thead><tbody>"
                for _, row in inst_df.sort_values('Date', ascending=False).head(10).iterrows():
                    table_html += f"<tr><td>{row['Date']}</td><td class='{'text-up' if row['Foreign']>0 else 'text-down'}'>{row['Foreign']:,}</td><td class='{'text-up' if row['Trust']>0 else 'text-down'}'>{row['Trust']:,}</td><td class='{'text-up' if row['Dealer']>0 else 'text-down'}'>{row['Dealer']:,}</td></tr>"
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("無法人籌碼資料")

        with tab4:
            st.markdown("<div class='content-card'><h3>📰 個股相關新聞</h3>", unsafe_allow_html=True)
            news_list = get_google_news(target)
            for news in news_list:
                st.markdown(f"<div class='news-item'><a href='{news['link']}' target='_blank'>{news['title']}</a><div class='news-meta'>{news['pubDate']} | {news['source']}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab5:
            st.markdown("<div class='ai-chat-box'><h3>🤖 AI 智能投顧</h3>", unsafe_allow_html=True)
            
            # --- AI 自動分析邏輯 ---
            if 'last_target' not in st.session_state: st.session_state['last_target'] = None
            if 'ai_analysis' not in st.session_state: st.session_state['ai_analysis'] = None

            if st.session_state['last_target'] != target:
                st.session_state['last_target'] = target
                st.session_state['ai_analysis'] = None
            
            if st.session_state['ai_analysis'] is None:
                # 預先顯示正在分析的 UI，避免畫面空白
                st.info(f"正在為您分析 {name} 的各項數據，請稍候...")
                try:
                    auto_prompt = f"""
                    請擔任專業股市分析師「武吉拉」，對 {name} ({target}) 進行今日的綜合分析。
                    目前的技術數據：收盤價 {latest['Close']:.2f}，MA5={latest['MA5']:.2f}，MA20={latest['MA20']:.2f}，KD指標 K={latest['K']:.1f}/D={latest['D']:.1f}。
                    請簡潔說明：1. 技術面趨勢 2. 籌碼面或市場消息（若有） 3. 短線操作建議。
                    語氣請專業、客觀且親切。
                    """
                    result = call_gemini_api(auto_prompt)
                    st.session_state['ai_analysis'] = result
                    st.rerun() # 重新執行以顯示結果
                except Exception as e:
                    st.error(f"AI 分析連線失敗，請稍後再試。({e})")
            
            if st.session_state['ai_analysis']:
                st.markdown(f"<div class='ai-msg-bot'><span>🦖 <b>{name} 自動分析報告：</b><br>{st.session_state['ai_analysis']}</span></div>", unsafe_allow_html=True)
            
            st.markdown("<p style='margin-top:15px; border-top:1px solid #ccc; padding-top:10px;'>💬 還有其他問題嗎？歡迎隨時提問：</p>", unsafe_allow_html=True)
            
            user_query = st.text_input("", placeholder="例如：這檔股票適合長期持有嗎？", key="ai_query")
            if user_query:
                with st.spinner("AI 正在思考您的問題..."):
                    prompt = f"""
                    你是一位專業的股市分析師「武吉拉」。請針對 {name} ({target}) 回答使用者的問題。
                    目前股價 {latest['Close']:.2f}，MA5 {latest['MA5']:.2f}，MA20 {latest['MA20']:.2f}。
                    KD指標 K={latest['K']:.1f}, D={latest['D']:.1f}。
                    使用者問題：{user_query}
                    請用繁體中文回答，語氣專業且親切。
                    """
                    ai_response = call_gemini_api(prompt)
                    st.markdown(f"<div class='ai-msg-user'><span>👤 {user_query}</span></div><div class='ai-msg-bot'><span>🦖 {ai_response}</span></div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        with tab6:
            st.markdown("<div class='content-card'><h3>🔄 歷史回測模擬</h3><p>使用日線資料進行簡單策略回測</p></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: initial_capital = st.number_input("初始資金", value=100000, step=10000)
            with c2: strategy = st.selectbox("選擇策略", ["MA 均線策略 (MA5穿過MA20)", "KD 策略 (黃金交叉)"])
            
            if st.button("開始回測"):
                backtest_df = stock.history(period="1y", interval="1d")
                backtest_df = calculate_indicators(backtest_df)
                res_df, trades, final_assets, return_rate = run_backtest(backtest_df, strategy, initial_capital)
                
                color_ret = "text-up" if return_rate > 0 else "text-down"
                st.markdown(f"""
                <div class="market-summary-box" style="margin-bottom: 20px;">
                    <div style="font-size: 1.2rem;">最終資產: <b>{int(final_assets):,}</b> 元</div>
                    <div style="font-size: 1.5rem;">報酬率: <b class="{color_ret}">{return_rate:.2f}%</b></div>
                    <div>總交易次數: {len(trades)} 次</div>
                </div>
                """, unsafe_allow_html=True)
                
                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(x=res_df.index, y=res_df['Total_Assets'], mode='lines', name='總資產', line=dict(color='#FFD700', width=2)))
                fig_bt.update_layout(title="資產成長曲線", template="plotly_white", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='black'))
                st.plotly_chart(fig_bt, use_container_width=True)
                
                if trades:
                    st.write("📝 近期交易明細：")
                    trades_df = pd.DataFrame(trades)
                    trades_df['日期'] = pd.to_datetime(trades_df['日期']).dt.strftime('%Y-%m-%d')
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("此期間無觸發交易訊號。")

    except Exception as e:
        st.error(f"無法取得資料，請確認代號是否正確。({e})")


