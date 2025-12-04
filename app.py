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
import io 

# --- 0. 設定與金鑰 ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"
# 已更新為您 cURL 範例中提供的新 API Key: AIzaSyBwuqBJRb3T5uKjI6Fzi4iphWDtALrFgsk
GEMINI_API_KEY = "AIzaSyBwuqBJRb3T5uKjI6Fzi4iphWDtALrFgsk" 

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="武吉拉 Wujila", 
    page_icon="🦖", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

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
    
    /* --- 卡片通用設定 --- */
    .quote-card, .content-card, .kd-card, .market-summary-box, .ai-chat-box, .light-card {
        background-color: rgba(255, 255, 255, 0.96) !important; /* 提高不透明度 */
        border-radius: 16px; 
        padding: 20px; /* 稍微減少 padding 避免擠壓 */
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 20px; 
        border: 1px solid #fff;
        position: relative; z-index: 1;
        color: #333 !important;
        width: 100%;
        box-sizing: border-box;
    }
    
    /* 優化卡片內文排版 */
    .content-card p {
        line-height: 1.8;
        text-align: justify;
        margin-bottom: 12px;
        color: #333 !important; /* 強制深色字體 */
    }

    /* --- AI 對話氣泡樣式 --- */
    .ai-msg-bot, .ai-msg-user, .ai-msg-error, .ai-msg-info {
        background-color: #f8f9fa !important;
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        color: #212529 !important;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .ai-msg-user { border-left: 5px solid #2196f3; background-color: #e3f2fd !important; }
    .ai-msg-bot { border-left: 5px solid #4caf50; background-color: #ffffff !important; }
    .ai-msg-error { border-left: 5px solid #f44336; background-color: #fff5f5 !important; color: #d32f2f !important; }
    .ai-msg-info { border-left: 5px solid #ff9800; background-color: #fff8e1 !important; }

    /* --- AI 回測深色卡片 --- */
    .ai-backtest-card {
        background-color: #050505 !important;
        border-radius: 24px 24px 0 0; /* 下方圓角由圖表接手 */
        padding: 25px;
        color: white !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        margin-bottom: 0px; /* 貼合圖表 */
        border: 1px solid #222;
        border-bottom: none;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        overflow: hidden;
    }
    
    .ai-header-row {
        display: flex; justify-content: space-between; align-items: flex-start;
        margin-bottom: 25px;
        flex-wrap: wrap; 
        gap: 15px;
    }
    
    .ai-title-group { display: flex; gap: 15px; align-items: center; }
    
    .ai-icon-box {
        width: 48px; height: 48px;
        background: #0066ff;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; color: white;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
        flex-shrink: 0;
    }
    
    .ai-title-text h3 { 
        color: white !important; margin: 0; 
        font-size: 1.3rem; font-weight: 700; letter-spacing: 0.5px; 
    }
    .ai-title-text p { 
        color: #888 !important; margin: 0; 
        font-size: 0.85rem; margin-top: 2px; font-weight: 500; 
    }
    
    .ai-score-group { text-align: right; flex-grow: 1; }
    .ai-score-val { 
        font-size: 2.8rem; font-weight: 800; 
        background: linear-gradient(to right, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        font-family: 'Arial', sans-serif;
    }
    .ai-score-label { 
        color: #888; font-size: 0.8rem; 
        margin-top: 5px; letter-spacing: 1px; text-transform: uppercase; 
    }
    
    .ai-pred-row {
        display: flex; gap: 15px; margin-bottom: 10px; flex-wrap: wrap;
    }
    .ai-pred-box {
        flex: 1;
        min-width: 140px; 
        background: #11141c;
        border-radius: 16px;
        padding: 15px 20px;
        border: 1px solid #222;
        display: flex; flex-direction: column;
    }
    .pred-title { color: #888; font-size: 0.9rem; margin-bottom: 5px; }
    .pred-num { font-size: 1.8rem; font-weight: 700; letter-spacing: 0.5px; font-family: 'Roboto Mono', monospace;}
    .color-green { color: #4ade80 !important; }
    .color-red { color: #f87171 !important; }
    
    /* 修正文字顏色 */
    .quote-card *, .content-card *, .kd-card *, .market-summary-box *, .ai-chat-box *, .light-card * {
        text-shadow: none !important;
        color: #333; 
    }
    .text-up { color: #e53935 !important; }
    .text-down { color: #43a047 !important; }
    .text-flat { color: #333 !important; }
    
    /* 報價卡片佈局優化 */
    .quote-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 5px; flex-wrap: wrap; }
    .stock-name { font-size: 1.8rem; font-weight: 900; color: #222; }
    .stock-id { font-size: 1.2rem; color: #888; font-weight: 500; }
    .price-row { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; flex-wrap: wrap; }
    .main-price { font-size: 4.2rem; line-height: 1; font-weight: 700; letter-spacing: -1px; }
    .change-info { display: flex; flex-direction: column; justify-content: center; font-size: 1.1rem; font-weight: 600; line-height: 1.4; }
    .market-tag {
        display: inline-block; padding: 3px 12px; border: 1px solid #ddd;
        border-radius: 20px; color: #666; font-size: 0.9rem;
        background-color: #f9f9f9; margin-bottom: 20px;
    }
    .detail-grid {
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); /* 縮小最小寬度 */
        column-gap: 20px; row-gap: 10px; font-size: 1.1rem;
    }
    .detail-item { display: flex; justify-content: flex-start; align-items: center; gap: 8px; }
    .detail-label { color: #888; min-width: 40px; }
    .detail-value { font-weight: 700; font-family: 'Roboto', sans-serif; }

    /* 表格優化 */
    .table-container { overflow-x: auto; width: 100%; -webkit-overflow-scrolling: touch; }
    table.analysis-table { width: 100%; min-width: 500px; border-collapse: collapse; } 
    table.analysis-table td, table.analysis-table th { padding: 10px; border-bottom: 1px solid #eee; text-align: left; white-space: nowrap; }

    .stRadio > div[role="radiogroup"] {
        background-color: #ffffff !important; border-radius: 30px !important; 
        padding: 8px 12px !important; display: flex !important; flex-direction: row !important; 
        gap: 8px !important; overflow-x: auto !important; white-space: nowrap !important;
        border: 1px solid #ddd; scrollbar-width: none; width: 100%; align-items: center;
    }
    .stRadio div[role="radiogroup"] > label {
        flex: 0 0 auto !important; min-width: 60px !important; background-color: transparent !important; 
        border: none !important; padding: 6px 14px !important; border-radius: 20px !important;
        cursor: pointer; margin: 0 !important; text-align: center;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #e53935 !important; box-shadow: 0 2px 6px rgba(229, 57, 53, 0.4);
    }
    .stRadio div[role="radiogroup"] > label p { color: #555 !important; font-weight: 600; margin: 0; }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p { color: #fff !important; }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div { background-color: #fff !important; color: #333 !important; }
    .stButton button { background-color: #fff; color: #333; border: 1px solid #ccc; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.8); border-radius: 10px; padding: 5px; gap: 5px; overflow-x: auto; }
    .stTabs button[aria-selected="true"] { background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stTabs button[aria-selected="true"] p { color: #e53935 !important; }

    h1 { text-shadow: 0 2px 4px rgba(0,0,0,0.5); color: #fff !important; text-align: center; font-weight: 900; }
    
    .news-item { padding: 15px 0; border-bottom: 1px solid #eee; }
    .news-item a { text-decoration: none; color: #0056b3 !important; font-weight: 700; }
    .news-meta { font-size: 0.9rem !important; color: #666 !important; }
    
    /* 推薦卡片樣式 */
    .recommend-card {
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 12px;
        border: 1px solid #ddd;
        background-color: #f9f9f9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .recommend-card h5 { font-size: 1.1rem; color: #007bff; margin-top: 0; margin-bottom: 5px; }
    .recommend-card p { font-size: 0.95rem; color: #555; margin-bottom: 0; }
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
        latest_date = (datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')
        # 嘗試使用更穩定的方式獲取熱門股，如果FinMind失敗則使用預設
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

def get_yahoo_stock_url(ticker):
    if ".TW" in ticker:
        return f"https://tw.stock.yahoo.com/quote/{ticker.replace('.TW', '')}"
    elif ".TWO" in ticker:
        return f"https://tw.stock.yahoo.com/quote/{ticker.replace('.TWO', '')}"
    else:
        return f"https://finance.yahoo.com/quote/{ticker}"

# 修改 AI API 呼叫，加入超級完整的模型清單 (地毯式搜索)
def call_gemini_api(prompt):
    if not GEMINI_API_KEY or "YOUR_NEW_GEMINI_API_KEY" in GEMINI_API_KEY: 
        return "⚠️ **錯誤：GEMINI API 金鑰未設定或使用預設值。請更新金鑰。**"
    
    # 擴充模型清單，涵蓋最新與最舊的穩定版本
    models_to_try = [
        "gemini-2.0-flash",       # 最新模型 (來自 cURL 範例)
        "gemini-1.5-flash",       # 標準 Flash
        "gemini-1.5-flash-latest",# Flash 最新
        "gemini-1.5-pro",         # Pro 版本
        "gemini-pro"              # 最通用名稱
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
    
    last_error = ""
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            
            # 檢查 API 錯誤訊息是否包含 Key 過期
            if response.status_code == 400 and "expired" in response.text:
                 return "⚠️ **API 錯誤：金鑰已過期 (400)。請前往 Google AI Studio 申請新的金鑰。**"
            
            if response.status_code == 200: 
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 404:
                last_error = f"模型 {model} 未找到 (404)，嘗試下一個..."
                continue 
            elif response.status_code == 403:
                last_error = f"API 權限錯誤 (403): Key 無法存取 {model}。"
                continue
            else:
                last_error = f"AI 回應錯誤: {response.status_code} - {response.text}"
                continue
        except requests.exceptions.Timeout:
            last_error = "AI 連線逾時。"
            continue
        except Exception as e: 
            last_error = f"連線錯誤: {e}"
            continue

    return f"AI 服務暫時無法使用。所有模型嘗試失敗。最後錯誤: {last_error}"

@st.cache_data(ttl=86400, show_spinner=False)
def get_ai_translated_summary(summary_text):
    if not summary_text or summary_text == "暫無詳細說明。":
        return "暫無詳細說明。"
    
    prompt = f"""
    請將以下公司介紹翻譯成流暢、完整的繁體中文。
    重點：
    1. 保留所有關鍵資訊，不要刪減。
    2. 語氣專業。
    
    原文：
    {summary_text}
    """
    try:
        models_to_try = ["gemini-1.5-flash", "gemini-pro"]
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 400 and "expired" in response.text:
                 return "⚠️ 翻譯功能錯誤：金鑰已過期。"
                 
            if response.status_code == 200:
                result = response.json()['candidates'][0]['content']['parts'][0]['text']
                if result: return result
        return summary_text
    except:
        return summary_text
        
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_stock_recommendations():
    # 針對 JSON 輸出，採用專注於穩定性的模型清單
    models_to_try = ["gemini-1.5-flash", "gemini-pro"] 
    
    prompt = """
    你是一位專業的股市分析師「武吉拉」。請根據當前全球市場趨勢和熱門題材，推薦最具潛力的股票。
    
    請以JSON格式輸出結果。
    - 推薦台股 (TW) 3 檔。
    - 推薦美股 (US) 3 檔。
    - 每檔股票需包含：代號、名稱、潛力題材 (簡短的中文說明)。
    
    JSON Schema:
    {
      "recommendations": [
        {
          "market": "TW",
          "stocks": [
            {"ticker": "2330.TW", "name": "台積電", "theme": "AI晶片供應鏈領頭羊，受惠於高速運算與資料中心需求爆發。"},
            null
          ]
        },
        {
          "market": "US",
          "stocks": [
            {"ticker": "NVDA", "name": "輝達", "theme": "壟斷全球AI加速器市場，下一代Blackwell架構持續推動業績成長。"},
            null
          ]
        }
      ]
    }
    """
    
    last_error = ""
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "recommendations": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "market": {"type": "STRING"},
                                    "stocks": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "ticker": {"type": "STRING"},
                                                "name": {"type": "STRING"},
                                                "theme": {"type": "STRING"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } 
        try: # 修正後的縮排
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 400 and "expired" in response.text:
                return {"error": "API Key expired"}
            
            if response.status_code == 200:
                json_text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                return json.loads(json_text)
            
        except requests.exceptions.Timeout:
            last_error = f"推薦模型 {model} 連線逾時。"
            continue
        except json.JSONDecodeError:
            last_error = f"模型 {model} 輸出格式錯誤，嘗試下一個..."
            continue
        except Exception as e:
            last_error = f"模型 {model} 發生未知錯誤: {e}"
            continue
                
    return {"error": last_error}


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
    
    winning_trades = 0
    total_completed_trades = 0
    entry_price = 0
    
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
                    entry_price = price
                    trades.append({'日期': date, '動作': '買進', '價格': price, '股數': shares, '餘額': capital})
        elif df['Signal'].iloc[i] == -1 and df['Signal'].iloc[i-1] != -1:
            if position > 0:
                revenue = position * price
                capital += revenue
                
                if price > entry_price:
                    winning_trades += 1
                total_completed_trades += 1
                
                trades.append({'日期': date, '動作': '賣出', '價格': price, '股數': position, '餘額': capital})
                position = 0
        df.iloc[i, df.columns.get_loc('Total_Assets')] = capital + (position * price)
        
    final_assets = df['Total_Assets'].iloc[-1]
    return_rate = ((final_assets - initial_capital) / initial_capital) * 100
    win_rate = (winning_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
    
    return df, trades, final_assets, return_rate, win_rate

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
</tr>"""

    sector = info.get('sector', '科技')
    raw_summary = info.get('longBusinessSummary', '暫無詳細說明。')
    
    # 呼叫 AI 翻譯與摘要
    summary = get_ai_translated_summary(raw_summary)
    
    theme_text = f"<b>{name}</b> 屬於 {sector} 產業。<br><br>{summary}"
    
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

    return f"""<div class="content-card">
<h3>📊 {name} ({ticker}) 綜合分析報告</h3>
<h4>1. 技術指標分析</h4>
<div class="table-container">
<table class="analysis-table">
<tr><td><b>收盤價</b></td><td>{price:.2f}</td><td><b>MA5</b></td><td>{ma5:.2f}</td></tr>
<tr><td><b>MA20</b></td><td>{ma20:.2f}</td><td><b>KD</b></td><td>{k:.1f}/{d:.1f}</td></tr>
<tr><td colspan="4"><b>趨勢判讀：</b>{tech_trend}。{kd_desc}</td></tr>
</table>
</div>
<h4>2. 三大法人籌碼分析</h4>
<div class="table-container">
<table class="analysis-table">
<thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營商</th><th>合計</th></tr></thead>
<tbody>{inst_table_html}</tbody>
</table>
</div>
<p><b>籌碼解讀：：</b>{inst_desc}</p>
<h4>3. 公司題材與願景</h4>
<p>{theme_text}</p>
<h4>4. 💡 進出場價格建議 ({action})</h4>
<ul><li><b>🟢 進場參考：：</b>{entry}</li><li><b>🔴 出場參考：：</b>{exit_pt}</li></ul>
</div>"""

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

# 調整搜尋欄位比例
c_search, c_hot, c_btn = st.columns([3, 1.5, 0.5])
with c_search:
    target_input = st.text_input("🔍 搜尋代號/名稱 (如: 4903, 2330, NVDA)", value="2330")
with c_hot:
    hot_stock = st.selectbox("🔥 熱門快選", ["(請選擇)"] + [f"{t}.TW" for t in hot_tw] + hot_us)
with c_btn:
    st.write("") 
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

# --- 觸發 AI 自動分析的邏輯 (放在主流程中) ---
if 'last_target' not in st.session_state: st.session_state['last_target'] = None
if 'ai_analysis' not in st.session_state: st.session_state['ai_analysis'] = None

# 如果目標股票改變，或者尚未分析過，就清空並準備分析
if st.session_state['last_target'] != target:
    st.session_state['last_target'] = target
    st.session_state['ai_analysis'] = None

# 如果 AI 分析結果是空的，則執行分析
if st.session_state['ai_analysis'] is None:
    try:
        temp_stock = yf.Ticker(target)
        temp_hist = temp_stock.history(period="5d")
        if not temp_hist.empty:
            temp_hist = calculate_indicators(temp_hist)
            t_latest = temp_hist.iloc[-1]
            
            auto_prompt = f"""
            請擔任專業股市分析師「武吉拉」，對 {name} ({target}) 進行今日的綜合分析。
            目前的技術數據：收盤價 {t_latest['Close']:.2f}，MA5={t_latest['MA5']:.2f}，MA20={t_latest['MA20']:.2f}，KD指標 K={t_latest['K']:.1f}/D={t_latest['D']:.1f}。
            請簡潔說明：1. 技術面趨勢 2. 籌碼面或市場消息（若有） 3. 短線操作建議。
            語氣請專業、客觀且親切。
            """
            with st.spinner(f"🤖 AI 正在分析 {name} 的最新數據，請稍候..."):
                result = call_gemini_api(auto_prompt)
                
                # --- 關鍵修正：儲存結果或錯誤訊息 ---
                st.session_state['ai_analysis'] = result
    except:
        st.session_state['ai_analysis'] = "分析暫時無法使用，請稍後再試。"

with st.expander("🌍 查看今日大盤情緒 (台股 / 美股)", expanded=False):
    t1, t2 = st.tabs(["🇹🇼 台股加權", "🇺🇸 美股那斯達克"])
    with t1:
        us_index = analyze_market_index("^TWII") # 應為 TWII
        if us_index: st.markdown(f"<div class='market-summary-box'><div style='color:{us_index['color']};font-weight:bold;font-size:1.2rem'>{us_index['price']:.0f} ({us_index['change']:+.0f})</div><div>{us_index['status']} - {us_index['comment']}</div></div>", unsafe_allow_html=True)
    with t2:
        us_index = analyze_market_index("^IXIC")
        if us_index: st.markdown(f"<div class='market-summary-box' style='border-left:4px solid #00BFFF'><div style='color:{us_index['color']};font-weight:bold;font-size:1.2rem'>{us_index['price']:.0f} ({us_index['change']:+.0f})</div><div>{us_index['status']} - {us_index['comment']}</div></div>", unsafe_allow_html=True)

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
            
            color_class = "text-up" if change >= 0 else "text-down"
            arrow = "▲" if change >= 0 else "▼"
            yahoo_url = get_yahoo_stock_url(target)
            
            market_tag = "上市"
            if ".TWO" in target: market_tag = "上櫃"
            elif ".TW" not in target: market_tag = "美股"

            def get_color(val, ref):
                if val > ref: return "text-up"
                elif val < ref: return "text-down"
                else: return "text-flat"
            
            c_high = get_color(latest_fast['High'], prev_close)
            c_low = get_color(latest_fast['Low'], prev_close)
            c_open = get_color(latest_fast['Open'], prev_close)
            
            quote_html = f"""<div class="quote-card">
<div class="quote-header">
<span class="stock-name"><a href="{yahoo_url}" target="_blank" style="text-decoration:none; color:inherit;">{name}</a></span>
<span class="stock-id">{target.replace('.TW','').replace('.TWO','')}</span>
</div>
<div class="price-row">
<div class="main-price {color_class}">{latest_fast['Close']:.2f}</div>
<div class="change-info {color_class}">
<div>{arrow} {abs(change):.2f}</div>
<div>{arrow} {abs(pct):.2f}%</div>
</div>
</div>
<div><span class="market-tag">{market_tag}</span></div>
<div class="detail-grid">
<div class="detail-item"><span class="detail-label">最高</span><span class="detail-value {c_high}">{latest_fast['High']:.2f}</span></div>
<div class="detail-item"><span class="detail-label">昨收</span><span class="detail-value text-flat">{prev_close:.2f}</span></div>
<div class="detail-item"><span class="detail-label">最低</span><span class="detail-value {c_low}">{latest_fast['Low']:.2f}</span></div>
<div class="detail-item"><span class="detail-label">開盤</span><span class="detail-value {c_open}">{latest_fast['Open']:.2f}</span></div>
</div>
</div>"""
            st.markdown(quote_html, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab_rec, tab5, tab6 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞", "🚀 股票推薦", "🤖 AI 投顧", "🔄 回測"])
        
        with tab1:
            interval_map = {"1分": "1m", "5分": "5m", "15分": "15m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
            period_label = st.radio("週期", list(interval_map.keys()), horizontal=True, label_visibility="collapsed")
            
            interval = interval_map[period_label]
            is_intraday = interval in ["1m", "5m", "15m", "30m", "60m"]
            
            data_period = "1d" if is_intraday else ("2y" if interval == "1d" else "5y")
            
            df = stock.history(period=data_period, interval=interval)
            
            if not df.empty:
                df = calculate_indicators(df)
                latest = df.iloc[-1]
                
                plot_df = df.copy()
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
                
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

                fig.update_layout(
                    template="plotly_white",
                    height=600, margin=dict(l=10, r=10, t=10, b=10), 
                    legend=dict(orientation="h", y=1.01, x=0, font=dict(color="black")),
                    dragmode='pan', hovermode='x unified', 
                    xaxis=dict(rangeslider_visible=False), 
                    yaxis=dict(fixedrange=True),
                    yaxis2=dict(fixedrange=True),
                    yaxis3=dict(fixedrange=True),
                    paper_bgcolor='rgba(255,255,255,0.95)', plot_bgcolor='white',
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
                
                fig_inst.update_layout(
                    barmode='group', template="plotly_white", height=400,
                    margin=dict(t=0, b=10, l=10, r=10),
                    paper_bgcolor='rgba(255,255,255,0.95)', plot_bgcolor='white', 
                    font=dict(color='black'), 
                    yaxis=dict(fixedrange=True, zeroline=True, zerolinecolor='#333', gridcolor='#e0e0e0'), 
                    dragmode='pan',
                    xaxis=dict(autorange="reversed", showgrid=True, gridcolor='#e0e0e0', fixedrange=False)
                )
                
                st.plotly_chart(fig_inst, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                
                table_html = "<div class='table-container'><table class='analysis-table' style='width:100%'><thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營商</th></tr></thead><tbody>"
                for _, row in inst_df.sort_values('Date', ascending=False).head(10).iterrows():
                    table_html += f"<tr><td>{row['Date']}</td><td class='{'text-up' if row['Foreign']>0 else 'text-down'}'>{row['Foreign']:,}</td><td class='{'text-up' if row['Trust']>0 else 'text-down'}'>{row['Trust']:,}</td><td class='{'text-up' if row['Dealer']>0 else 'text-down'}'>{row['Dealer']:,}</td></tr>"
                table_html += "</tbody></table></div>"
                
                final_table_html = f"<div class='content-card'><h3>📊 詳細數據</h3>{table_html}</div>"
                st.markdown(final_table_html, unsafe_allow_html=True)

            else: st.info("無法人籌碼資料")

        with tab4:
            news_list = get_google_news(target)
            news_html_content = ""
            for news in news_list:
                news_html_content += f"""<div class='news-item'>
<a href='{news['link']}' target='_blank'>{news['title']}</a>
<div class='news-meta'>{news['pubDate']} | {news['source']}</div>
</div>"""
            
            final_news_html = f"""<div class='light-card'>
<h3>📰 個股相關新聞</h3>
{news_html_content}
</div>"""
            st.markdown(final_news_html, unsafe_allow_html=True)
            
        with tab_rec: # 🚀 股票推薦 Tab 邏輯
            st.markdown("<div class='content-card'><h3>🚀 AI 股票大推薦</h3><p>根據當前市場熱門題材，由 AI 分析師為您推薦潛力標的。</p>", unsafe_allow_html=True)
            
            with st.spinner("🤖 正在生成推薦列表，請稍候..."):
                recommendations = get_ai_stock_recommendations()
            
            if recommendations and 'recommendations' in recommendations:
                for market_rec in recommendations['recommendations']:
                    market = market_rec['market']
                    stocks = market_rec['stocks']
                    
                    st.markdown(f"<h4>{market} 🎯 市場焦點 ({'台股' if market=='TW' else '美股'})</h4>", unsafe_allow_html=True)
                    
                    for stock in stocks:
                        rec_card = f"""
                        <div class='recommend-card'>
                            <h5>{stock['name']} ({stock['ticker']})</h5>
                            <p><b>✨ 潛力題材：</b>{stock['theme']}</p>
                        </div>
                        """
                        st.markdown(rec_card, unsafe_allow_html=True)
            elif recommendations and 'error' in recommendations and 'expired' in recommendations['error']:
                 st.markdown("<div class='ai-msg-error'>⚠️ <b>API 錯誤：金鑰已過期！請立即更新金鑰以使用 AI 服務。</b></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ai-msg-error'>⚠️ <b>AI 推薦服務暫時無法取得數據，請確認您的 API Key 權限或稍後重試。</b></div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab5:
            st.markdown("<div class='content-card'><h3>🤖 AI 智能投顧</h3>", unsafe_allow_html=True)
            
            # AI 分析結果顯示區 (強制白卡)
            if st.session_state['ai_analysis']:
                # 檢查是否為錯誤訊息 (如果之前有錯誤，現在顯示並提供重試按鈕)
                if st.session_state['ai_analysis'].startswith("AI 服務暫時無法使用") or "錯誤" in st.session_state['ai_analysis']:
                     st.markdown(f"<div class='ai-msg-error'>⚠️ {st.session_state['ai_analysis']}</div>", unsafe_allow_html=True)
                     # 加入重試按鈕
                     if st.button("🔄 重試自動分析", key="retry_ai"):
                         st.session_state['ai_analysis'] = None
                         st.rerun()
                else:
                    st.markdown(f"<div class='ai-msg-bot'><span>🦖 <b>{name} 自動分析報告：：</b><br>{st.session_state['ai_analysis']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-msg-info'>⏳ AI 正在分析 {name} 的最新數據，請稍候...</div>", unsafe_allow_html=True)

            # 對話區塊
            st.markdown("</div>", unsafe_allow_html=True) # 結束第一個 content-card
            st.markdown("<div class='content-card'><h4>💬 還有其他問題嗎？歡迎隨時提問：</h4>", unsafe_allow_html=True)
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
                    if "錯誤" in ai_response or "無法使用" in ai_response:
                        st.markdown(f"<div class='ai-msg-error'>❌ {ai_response}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='ai-msg-user'>👤 {user_query}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='ai-msg-bot'>🦖 {ai_response}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True) # 結束第二個 content-card

        with tab6:
            st.markdown("<div class='content-card'><h3>🔄 歷史回測模擬</h3><p>使用日線資料進行簡單策略回測 (初始資金: 500,000)</p></div>", unsafe_allow_html=True)
            
            # --- 固定參數與自動回測 ---
            initial_capital = 500000
            strategy = "KD 策略 (黃金交叉)"
            
            # 直接執行回測
            backtest_df = stock.history(period="1y", interval="1d")
            
            # 簡單的錯誤處理防止當機
            if backtest_df.empty:
                st.error("無法取得回測資料")
            else:
                backtest_df = calculate_indicators(backtest_df)
                res_df, trades, final_assets, return_rate, win_rate = run_backtest(backtest_df, strategy, initial_capital)
                
                # 計算支撐與壓力 (簡單模擬)
                recent_high = backtest_df['High'].tail(20).max()
                recent_low = backtest_df['Low'].tail(20).min()
                
                # --- 圖表改為深色透明，並移除背景格線 ---
                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(x=res_df.index, y=res_df['Total_Assets'], mode='lines', name='總資產', line=dict(color='#007bff', width=3)))
                fig_bt.update_layout(
                    template="plotly_dark",
                    height=200, 
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='#050505', # 配合深色卡片背景
                    plot_bgcolor='#050505',  # 配合深色卡片背景
                    showlegend=False,
                    xaxis=dict(visible=False), 
                    # 修正重點：稍微顯示格線，讓圖表有意義
                    yaxis=dict(showgrid=True, gridcolor='#222', visible=True, side='right'),
                )
                
                # --- 復刻深色卡片 HTML (上方資訊) ---
                backtest_html = f"""<div class="ai-backtest-card">
<div class="ai-header-row">
<div class="ai-title-group">
<div class="ai-icon-box">📊</div>
<div class="ai-title-text">
<h3>AI 大數據回測</h3>
<p>Pattern Matching</p>
</div>
</div>
<div class="ai-score-group">
<div class="ai-score-val">{int(win_rate)}%</div>
<div class="ai-score-label">上漲機率</div>
</div>
</div>
<div class="ai-pred-row">
<div class="ai-pred-box">
<div class="pred-title">支撐預測</div>
<div class="pred-num color-green">{recent_low:.0f}</div>
</div>
<div class="ai-pred-box">
<div class="pred-title">壓力預測</div>
<div class="pred-num color-red">{recent_high:.0f}</div>
</div>
</div>
</div>"""
                st.markdown(backtest_html, unsafe_allow_html=True)
                
                # --- 獨立顯示圖表 (使用 staticPlot=True) ---
                st.markdown('<div style="margin-top: -25px; border-radius: 0 0 24px 24px; overflow: hidden; border: 1px solid #222; border-top: none;">', unsafe_allow_html=True)
                st.plotly_chart(fig_bt, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 文字報告
                color_ret = "text-up" if return_rate > 0 else "text-down"
                st.markdown(f"""
                <div class="market-summary-box" style="margin-bottom: 20px; margin-top: 20px;">
                    <div style="font-size: 1.2rem;">最終資產: <b>{int(final_assets):,}</b> 元</div>
                    <div style="font-size: 1.5rem;">報酬率: <b class="{color_ret}">{return_rate:.2f}%</b></div>
                    <div>總交易次數: {len(trades)} 次</div>
                </div>
                """, unsafe_allow_html=True)
                
                if trades:
                    st.write("📝 近期交易明細：")
                    trades_df = pd.DataFrame(trades)
                    trades_df['日期'] = pd.to_datetime(trades_df['日期']).dt.strftime('%Y-%m-%d')
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("此期間無觸發交易訊號。")

    except Exception as e:
        st.error(f"無法取得資料，請確認代號是否正確。({e})")
