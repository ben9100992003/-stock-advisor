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

# --- 0. 設定與金鑰 (已啟用您的 Token) ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide")

# --- 2. 背景圖片與 CSS 設定 ---
def get_base64_of_bin_file(bin_file):
    """讀取圖片並轉為 base64 編碼"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    """設定背景圖片"""
    if not os.path.exists(png_file):
        return
        
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

# 嘗試載入背景
set_png_as_page_bg('bg.png')

# 其餘 CSS 樣式 (終極優化版)
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 1. 分析報告容器 --- */
    .glass-container {
        background-color: rgba(0, 0, 0, 0.85); /* 深黑半透明，凸顯白字 */
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
    }
    .glass-container h3 { 
        color: #FFD700 !important; /* 金色標題 */
        border-bottom: 2px solid rgba(255,255,255,0.2); 
        padding-bottom: 15px; 
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px black; 
        font-weight: 800;
    }
    .glass-container p, .glass-container li { 
        color: #f0f0f0 !important; 
        font-size: 1.15rem; 
        line-height: 1.8; 
        margin-bottom: 12px;
        font-weight: 500;
    }
    .glass-container b { color: #fff; font-weight: 700; }
    
    /* 策略建議框 */
    .strategy-box {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 6px solid #ff4b4b;
        padding: 20px;
        margin-top: 25px;
        border-radius: 8px;
    }

    /* --- 2. 側邊欄卡片 --- */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* --- 3. 數據指標卡片 (Metric) --- */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 30, 30, 0.9) !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(5px);
    }
    div[data-testid="stMetricLabel"] p {
        color: #cccccc !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }

    /* --- 4. Tab 分頁標籤 --- */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 1.2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px black;
    }
    
    /* 一般文字與標題 */
    .stMarkdown p, .stCaption { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    h1, h2 { text-shadow: 3px 3px 6px #000000; color: #fff !important; font-weight: 900; }
    
    /* Yahoo 按鈕 */
    .stLinkButton a {
        background-color: #420066 !important;
        color: white !important;
        border: 1px solid #888 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明",
    "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2382.TW": "廣達", "3231.TW": "緯創",
    "2409.TW": "友達", "3481.TW": "群創", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜"
}

@st.cache_data(ttl=3600)
def get_top_volume_stocks():
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        latest_trade_date = dl.taiwan_stock_daily_adj(
            stock_id="2330", 
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ).iloc[-1]['date']
        df = dl.taiwan_stock_daily_adj(start_date=latest_trade_date)
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(15)
        return top_df['stock_id'].tolist()
    except:
        return ["2330", "2317", "2603", "2609", "3231", "2454"] 

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    """使用 Token 抓取 FinMind 法人資料 (包含歷史數據用於繪圖)"""
    if ".TW" not in ticker: return None
    
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader(token=FINMIND_API_TOKEN)
    
    try:
        # 抓取過去 60 天，確保有足夠數據畫圖
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        
        if df.empty: return None
        
        # 計算買賣超 (buy - sell)
        df['net'] = df['buy'] - df['sell']
        
        # 整理成日期為 Index 的 DataFrame
        dates = sorted(df['date'].unique())
        result_list = []
        
        for d in dates:
            day_df = df[df['date'] == d]
            def get_net(key):
                v = day_df[day_df['name'].str.contains(key)]['net'].sum()
                return int(v / 1000) # 換算成張
            
            result_list.append({
                'Date': d,
                'Foreign': get_net('外資'),
                'Trust': get_net('投信'),
                'Dealer': get_net('自營')
            })
            
        result_df = pd.DataFrame(result_list)
        return result_df
        
    except Exception as e:
        print(f"FinMind Error: {e}")
        return None

# --- 4. 技術指標與大盤分析函式 ---

def calculate_indicators(df):
    # 均線系統 (MA) - 支援到 240 日 (年線)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean() # 半年線
    df['MA240'] = df['Close'].rolling(240).mean() # 年線
    
    # 布林通道 (20, 2)
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
    
    # 成交量均線
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
    # KD 指標 (9,3,3)
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    ema_u = u.ewm(com=13, adjust=False).mean()
    ema_d = d.ewm(com=13, adjust=False).mean()
    rs = ema_u / ema_d
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
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
        change = price - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        ma20 = latest['MA20']
        k, d = latest['K'], latest['D']
        
        status = "震盪整理"
        color = "#ffffff"
        comment = "市場觀望氣氛濃，建議保守操作。"
        
        if price > ma20:
            if k > d:
                status = "多頭強勢"
                color = "#ff4b4b"
                comment = "站穩月線且 KD 金叉，動能強勁，可積極選股。"
            else:
                status = "多頭回檔"
                color = "#ff9100"
                comment = "短線 KD 修正中，留意月線支撐力道。"
        else:
            if k < d:
                status = "空方修正"
                color = "#00c853"
                comment = "跌破月線且 KD 死叉，趨勢偏弱，多看少做。"
            else:
                status = "跌深反彈"
                color = "#ffff00"
                comment = "KD 低檔背離向上，醞釀反彈，但上方仍有壓。"
                
        return {
            "price": price, "change": change, "pct": pct,
            "status": status, "color": color, "comment": comment
        }
    except:
        return None

# --- 5. 深度分析報告 (加強版) ---
def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    vol = latest['Volume']
    vol_ma5 = latest['VOL_MA5']
    ma5, ma10, ma20, ma60, ma120 = latest['MA5'], latest['MA10'], latest['MA20'], latest['MA60'], latest['MA120']
    k, d = latest['K'], latest['D']
    rsi = latest['RSI']
    
    # 1. 趨勢架構分析 (更細膩)
    trend_html = f"<b>{name} ({ticker})</b> 今日收盤價為 <b>{price:.2f}</b> 元。"
    
    if price > ma5 and ma5 > ma10 and ma10 > ma20 and ma20 > ma60:
        trend_html += " 均線呈現標準的<b>「多頭排列」</b>，股價沿 5 日線噴出，屬於強勢攻擊型態。下方季線 (MA60) 與半年線 (MA120) 皆向上，長線保護短線，拉回皆是買點。"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20 and ma20 < ma60:
        trend_html += " 均線呈現標準的<b>「空頭排列」</b>，上方層層反壓，反彈至 10 日或月線皆可能遭遇解套賣壓，不宜躁進。"
    elif price > ma20:
        trend_html += " 股價目前站穩<b>「月線 (MA20)」</b>之上，中期趨勢維持多方控盤。"
        if price < ma5:
            trend_html += " 唯短線跌破 5 日線，攻擊動能稍歇，需觀察是否能守穩 10 日線支撐，進行強勢整理。"
    else:
        trend_html += " 股價目前跌破<b>「月線 (MA20)」</b>，短線轉弱進入整理。"
        if price > ma60:
            trend_html += " 但仍守在<b>「季線 (MA60)」</b>這條生命線之上，長線多頭架構尚未完全破壞，可視為漲多後的良性回檔。"
        else:
            trend_html += " 且同時跌破季線，中期趨勢有轉空疑慮，需盡快站回季線否則整理時間將拉長。"

    # 2. 籌碼面解讀 (讀取最新一筆)
    inst_html = ""
    if inst_df is not None and not inst_df.empty:
        # 取最新一天的資料
        latest_inst = inst_df.iloc[-1]
        f_val = latest_inst['Foreign']
        t_val = latest_inst['Trust']
        d_val = latest_inst['Dealer']
        total = f_val + t_val + d_val
        date_str = latest_inst['Date']
        
        # 計算近期累計 (例如近5日)
        recent_df = inst_df.tail(5)
        f_sum_5 = recent_df['Foreign'].sum()
        t_sum_5 = recent_df['Trust'].sum()
        
        buy_sell_text = "買超" if total > 0 else "賣超"
        color_style = "#ff4b4b" if total > 0 else "#00c853"
        
        inst_html += f"籌碼方面，截至 {date_str}，三大法人單日合計<span style='color:{color_style}'><b>{buy_sell_text} {abs(total):,} 張</b></span>。"
        
        if f_val > 2000:
            inst_html += " 其中<b>外資</b>大舉敲進，展現強烈作多意願。"
        elif f_val < -2000:
            inst_html += " 其中<b>外資</b>大幅調節，需留意提款壓力。"
            
        if f_sum_5 > 10000:
            inst_html += " 觀察近五日，外資呈現連續性買盤，波段籌碼安定。"
        elif f_sum_5 < -10000:
            inst_html += " 觀察近五日，外資持續站在賣方，上方套牢壓力沈重。"
            
        if t_val > 500 or t_sum_5 > 2000:
            inst_html += " <b>投信</b>近期買盤積極，籌碼趨於集中，可能有作帳或認養題材發酵。"
    else:
        inst_html = "目前暫無最新的法人買賣超數據，建議稍後再確認。"

    # 3. 技術指標訊號
    tech_html = f"技術指標部分，KD 值目前為 ({k:.1f}, {d:.1f})，"
    if k > d:
        tech_html += "呈現<b>「黃金交叉」</b>向上，短線買盤進駐，動能轉強。"
        if k < 20:
            tech_html += " 且 KD 位於低檔超賣區交叉，這通常是強力的<b>底部反轉訊號</b>，反彈機率高。"
    else:
        tech_html += "呈現<b>「死亡交叉」</b>向下，短線面臨獲利了結賣壓，動能轉弱。"
        if k > 80:
            tech_html += " 且 KD 位於高檔區交叉向下，需留意<b>假突破真拉回</b>的風險。"
            
    if rsi > 75:
        tech_html += f" RSI 指標來到 {rsi:.1f}，已進入<b>超買區</b>，短線隨時可能出現技術性修正，不宜過度追高。"
    elif rsi < 25:
        tech_html += f" RSI 指標來到 {rsi:.1f}，已進入<b>超賣區</b>，乖離過大，隨時有機會出現跌深反彈。"

    # 4. 總結建議
    advice = ""
    adv_color = "#ffffff"
    
    # 根據均線位置設定支撐壓力
    support = ma20 if price > ma20 else ma60
    if price < ma60: support = ma120
    
    if price > ma20 and k > d:
        advice = f"綜合研判：趨勢偏多。目前技術面與籌碼面皆有利多方，建議順勢操作。短線防守點可設在月線 {ma20:.1f}。"
        adv_color = "#ff4b4b" # 紅
    elif price < ma20 and k < d:
        advice = f"綜合研判：趨勢偏空。短線型態轉弱，建議保守觀望或減碼操作，等待股價重新站回月線 {ma20:.1f} 再行佈局。"
        adv_color = "#00c853" # 綠
    else:
        advice = f"綜合研判：區間震盪。目前多空勢力拉鋸，建議在季線 {ma60:.1f} 與月線 {ma20:.1f} 之間進行區間操作，高出低進。"
        adv_color = "#ffff00" # 黃

    html_report = f"""
    <div class="glass-container">
        <h3>📊 武吉拉深度完整分析</h3>
        <p><b>1. 趨勢結構：</b><br>{trend_html}</p>
        <p><b>2. 籌碼解讀：</b><br>{inst_html}</p>
        <p><b>3. 關鍵指標：</b><br>{tech_html}</p>
        <hr style="border-top: 1px dashed #aaa;">
        <div class="strategy-box">
            <p style="font-size: 1.2rem; font-weight: bold; color: {adv_color} !important; margin:0;">
                💡 {advice}
            </p>
        </div>
    </div>
    """
    return html_report

# --- 6. 主程式介面 ---

with st.sidebar:
    st.header("🦖 武吉拉選股")
    
    with st.spinner("正在掃描市場..."):
        hot_stocks_list = get_top_volume_stocks()
        
    all_hot_stocks = hot_stocks_list + ["NVDA", "TSLA", "AAPL", "AMD", "PLTR"]
    
    options = [f"{STOCK_NAMES.get(t, t)} ({t})" for t in all_hot_stocks]
    sel_opt = st.selectbox("🔥 熱門成交 Top 15", options=options)
    sel_ticker = sel_opt.split("(")[-1].replace(")", "")

    st.markdown("---")
    
    # 大盤分析區塊
    st.subheader("🌍 每日大盤")
    idx_tab1, idx_tab2 = st.tabs(["🇹🇼 台股", "🇺🇸 美股"])
    
    with idx_tab1:
        tw = analyze_market_index("^TWII")
        if tw:
            st.markdown(f"""
            <div class="market-summary-box">
                <div style="font-size:1.2rem; font-weight:bold; color:{tw['color']}">
                    加權: {tw['price']:.0f} <span style="font-size:0.8rem">({tw['change']:+.0f})</span>
                </div>
                <div style="margin-top:5px;">
                    <b>{tw['status']}</b><br><span style="color:#ddd;font-size:0.85rem">{tw['comment']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with idx_tab2:
        us = analyze_market_index("^IXIC")
        if us:
            st.markdown(f"""
            <div class="market-summary-box" style="border-left: 4px solid #00BFFF;">
                <div style="font-size:1.2rem; font-weight:bold; color:{us['color']}">
                    Nasdaq: {us['price']:.0f} <span style="font-size:0.8rem">({us['change']:+.0f})</span>
                </div>
                <div style="margin-top:5px;">
                    <b>{us['status']}</b><br><span style="color:#ddd;font-size:0.85rem">{us['comment']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    user_input = st.text_input("輸入代號 (如 2330)", value="")
    target = user_input.upper() if user_input else sel_ticker
    if target.isdigit(): target += ".TW" 

    st.link_button(f"前往 Yahoo ({target})", f"https://tw.stock.yahoo.com/quote/{target}", use_container_width=True)

# 右側主畫面
try:
    # 抓取 2 年資料以計算半年線/年線
    stock = yf.Ticker(target)
    df = stock.history(period="2y")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 使用 FinMind 抓取法人資料 (優先權最高)
        inst_df = get_institutional_data_finmind(target)
        # 如果是台股但 FinMind 沒抓到，才嘗試 Yahoo 爬蟲 (但因為有金鑰，通常 FinMind 最穩)
        if inst_df is None and ".TW" in target:
             inst_df = get_institutional_data_yahoo(target)
        
        # 標題
        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        st.markdown(f"<h1 style='margin-bottom:0; text-shadow: 2px 2px 4px #000;'>{name} ({target})</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{color}; margin-top:0; text-shadow: 1px 1px 2px #000;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        # 顯示分析報告 (HTML 版)
        report_html = generate_narrative_report(name, target, latest, inst_df, df)
        st.markdown(report_html, unsafe_allow_html=True)
        
        # --- 專業 K 線圖 (Yahoo 白底風格) ---
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.02, 
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=("", "", "")
        )
        
        # 1. 主圖：K線 + 均線
        # K 線
        fig.add_trace(go.Candlestick(
            x=df.index.strftime('%Y-%m-%d'), 
            open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
            name='K線', 
            increasing_line_color='#c0392b', increasing_fillcolor='#c0392b', # 實心紅
            decreasing_line_color='#27ae60', decreasing_fillcolor='#27ae60'  # 實心綠
        ), row=1, col=1)
        
        # 均線 (仿 Yahoo 色系: 藍/紫/橘/黃/褐)
        ma_settings = [
            ('MA5', 'blue', 1), ('MA10', 'purple', 1), ('MA20', '#ff9800', 1.5),
            ('MA60', '#2ecc71', 1.5), ('MA120', 'brown', 1), ('MA240', 'gray', 1)
        ]
        for ma_name, color, width in ma_settings:
            if ma_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index.strftime('%Y-%m-%d'), y=df[ma_name], 
                    line=dict(color=color, width=width), 
                    name=f'{ma_name} ({latest[ma_name]:.2f})'
                ), row=1, col=1)

        # 2. 副圖一：成交量
        colors_vol = ['#c0392b' if r['Open'] < r['Close'] else '#27ae60' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(
            x=df.index.strftime('%Y-%m-%d'), 
            y=df['Volume'], 
            marker_color=colors_vol, 
            name='成交量'
        ), row=2, col=1)

        # 3. 副圖二：KD 指標
        fig.add_trace(go.Scatter(
            x=df.index.strftime('%Y-%m-%d'), y=df['K'], 
            line=dict(color='#2980b9', width=1.2), name=f'K9 ({latest["K"]:.1f})'
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index.strftime('%Y-%m-%d'), y=df['D'], 
            line=dict(color='#e67e22', width=1.2), name=f'D9 ({latest["D"]:.1f})'
        ), row=3, col=1)
        
        # 設定圖表樣式 (白色背景 + 網格)
        fig.update_layout(
            template="plotly_white",
            height=900, 
            xaxis_rangeslider_visible=False,
            xaxis3_rangeslider_visible=False,
            paper_bgcolor='white', # 強制白底
            plot_bgcolor='white',
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(color='black')),
            margin=dict(l=50, r=20, t=30, b=50),
            font=dict(color='black') # 字體全黑
        )
        
        # 增加網格線清晰度
        grid_color = "#eee"
        fig.update_xaxes(showgrid=True, gridcolor=grid_color, linecolor='#333')
        fig.update_yaxes(showgrid=True, gridcolor=grid_color, linecolor='#333')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 底部 Tab 區塊
        tab1, tab2 = st.tabs(["📉 詳細指標", "🏛️ 法人籌碼"])
        
        with tab1:
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("RSI (14)", f"{latest['RSI']:.1f}")
            t2.metric("K (9)", f"{latest['K']:.1f}")
            t3.metric("D (9)", f"{latest['D']:.1f}")
            t4.metric("MACD", f"{latest['MACD']:.2f}")
            
        with tab2:
            if inst_df is not None and not inst_df.empty:
                st.subheader("🏛️ 法人買賣變化 (近60日)")
                fig_inst = go.Figure()
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#2980b9'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#8e44ad'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#f39c12'))
                
                fig_inst.update_layout(
                    barmode='group', 
                    template="plotly_white", 
                    height=300, 
                    paper_bgcolor='white', 
                    plot_bgcolor='white', 
                    xaxis=dict(autorange="reversed"),
                    font=dict(color='black'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_inst, use_container_width=True)
            else:
                st.info("此股票無法人籌碼資料 (或非台股)。")

except Exception as e:
    st.error(f"系統忙碌中，請稍後再試: {e}")
