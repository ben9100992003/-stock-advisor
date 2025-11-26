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

# --- 0. 設定與金鑰 ---
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

# 其餘 CSS 樣式 (終極顯影版)
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 分析報告容器 --- */
    .glass-container {
        background-color: rgba(0, 0, 0, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
    }
    .glass-container h3 { 
        color: #ffcc00 !important; 
        border-bottom: 2px solid rgba(255,255,255,0.2); 
        padding-bottom: 15px; 
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px black; 
    }
    .glass-container p { 
        color: #f0f0f0 !important; 
        font-size: 1.1rem; 
        line-height: 1.8; 
        margin-bottom: 12px;
    }
    .glass-container b { color: #fff; font-weight: 700; }
    .glass-container .strategy-box {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        margin-top: 20px;
        border-radius: 5px;
    }

    /* --- 側邊欄卡片 --- */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* --- 數據指標卡片 (Metric) --- */
    div[data-testid="stMetric"] {
        background-color: rgba(20, 20, 20, 0.85) !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(5px);
    }
    div[data-testid="stMetricLabel"] p {
        color: #bbbbbb !important;
        font-size: 1rem !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
    }

    /* --- Tab 與文字 --- */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 1.1rem;
        font-weight: bold;
        text-shadow: 1px 1px 2px black;
    }
    .stMarkdown p, .stCaption { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    h1, h2, h3 { text-shadow: 2px 2px 8px #000000; color: #fff !important; }
    
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

try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明",
    "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2382.TW": "廣達", "3231.TW": "緯創",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir"
}

@st.cache_data(ttl=3600)
def get_top_volume_stocks():
    if not FINMIND_AVAILABLE:
        return ["2330", "2317", "2603", "2609", "3231", "2618", "00940", "00919", "2454", "2303"]
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
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
def get_institutional_data_yahoo(ticker):
    if ".TW" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://tw.stock.yahoo.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        r = requests.get(url, headers=headers)
        r.encoding = 'utf-8'
        
        dfs = pd.read_html(r.text)
        if not dfs: return None
        
        target_df = None
        for df in dfs:
            cols_str = " ".join([str(c) for c in df.columns])
            if '日期' in cols_str and ('外資' in cols_str or '買賣超' in cols_str):
                target_df = df
                break
        
        if target_df is None or target_df.empty: return None
        
        new_cols = {}
        for col in target_df.columns:
            c_str = str(col)
            if '日期' in c_str: new_cols[col] = 'Date'
            elif '外資' in c_str and '持股' not in c_str: new_cols[col] = 'Foreign'
            elif '投信' in c_str: new_cols[col] = 'Trust'
            elif '自營' in c_str: new_cols[col] = 'Dealer'
            
        target_df = target_df.rename(columns=new_cols)
        
        if 'Date' not in target_df.columns or 'Foreign' not in target_df.columns:
            return None

        df_clean = target_df.copy()
        
        def clean_num(x):
            if isinstance(x, (int, float)): return int(x)
            if isinstance(x, str):
                x = x.replace(',', '').replace('+', '').replace('nan', '0')
                try: return int(x)
                except: return 0
            return 0
            
        for col in ['Foreign', 'Trust', 'Dealer']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(clean_num)
            else:
                df_clean[col] = 0
            
        def clean_date(d):
            if isinstance(d, str) and '/' in d and len(d) <= 5:
                return f"{datetime.now().year}/{d}"
            return d
        
        df_clean['Date'] = df_clean['Date'].apply(clean_date)
        return df_clean.head(30)

    except Exception:
        return None

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    if not FINMIND_AVAILABLE or ".TW" not in ticker: return None
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader()
    if FINMIND_API_TOKEN:
        dl = DataLoader(token=FINMIND_API_TOKEN)
    try:
        start_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        df['net'] = df['buy'] - df['sell']
        dates = sorted(df['date'].unique(), reverse=True)
        result_data = []
        for d in dates:
            day_df = df[df['date'] == d]
            def get_net(key):
                v = day_df[day_df['name'].str.contains(key)]['net'].sum()
                return int(v / 1000) 
            result_data.append({
                'Date': d, 'Foreign': get_net('外資'), 'Trust': get_net('投信'), 'Dealer': get_net('自營')
            })
        return pd.DataFrame(result_data).head(30)
    except:
        return None

# --- 4. 技術指標與大盤分析函式 ---

def calculate_indicators(df):
    # 均線系統 (MA)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean() # 半年線
    
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

# --- 5. 深度分析報告 (加強描述版) ---
def generate_narrative_report(name, ticker, latest, inst_data_dict, df):
    price = latest['Close']
    vol = latest['Volume']
    vol_ma5 = latest['VOL_MA5']
    ma5, ma10, ma20, ma60, ma120 = latest['MA5'], latest['MA10'], latest['MA20'], latest['MA60'], latest['MA120']
    k, d = latest['K'], latest['D']
    rsi = latest['RSI']
    
    # 1. 趨勢架構分析
    trend_html = f"<b>{name} ({ticker})</b> 今日收盤價為 {price:.2f} 元。"
    
    if price > ma5 and ma5 > ma20 and ma20 > ma60:
        trend_html += " 目前均線呈現<b>「多頭排列」</b>，股價沿著 5 日線強勢上攻，屬於強者恆強的格局。下方季線 (MA60) 趨勢向上，長線保護短線效果顯著。"
    elif price < ma5 and ma5 < ma20 and ma20 < ma60:
        trend_html += " 目前均線呈現<b>「空頭排列」</b>，股價受制於層層均線反壓，上方壓力沈重。任何反彈至月線附近皆可能面臨解套賣壓。"
    elif price > ma20:
        trend_html += " 股價目前站穩<b>「月線 (MA20)」</b>之上，中期趨勢維持多方控盤。"
        if price < ma5:
            trend_html += " 唯短線跌破 5 日線，動能稍有轉弱，需觀察是否能守穩 10 日線或月線支撐。"
    else:
        trend_html += " 股價目前位於<b>「月線 (MA20)」</b>之下，短線趨勢偏弱，屬於整理修正階段。"
        if price > ma60:
            trend_html += " 但仍守在季線 (MA60) 之上，長線多頭架構尚未完全破壞，可視為漲多拉回。"

    # 2. 籌碼面解讀
    inst_html = ""
    if inst_data_dict:
        f_val = inst_data_dict['Foreign']
        t_val = inst_data_dict['Trust']
        total = f_val + t_val + inst_data_dict['Dealer']
        date_str = inst_data_dict['Date']
        
        buy_sell_text = "買超" if total > 0 else "賣超"
        color_style = "#ff4b4b" if total > 0 else "#00c853"
        
        inst_html += f"籌碼方面，截至 {date_str}，三大法人合計<span style='color:{color_style}'><b>{buy_sell_text} {abs(total):,} 張</b></span>。"
        
        if f_val > 2000:
            inst_html += " 其中<b>外資</b>買盤積極，為推升股價的主要推手，顯示國際資金對後市看法樂觀。"
        elif f_val < -2000:
            inst_html += " 值得留意的是，<b>外資</b>近期調節動作頻頻，需提防提款賣壓湧現。"
            
        if t_val > 500:
            inst_html += " 另外，<b>投信</b>連續買超佈局，籌碼趨於集中，有利於股價籌碼沈澱。"
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
    
    support = ma20 if price > ma20 else ma60
    resistance = ma5 if price < ma5 else (ma20 if price < ma20 else price * 1.1)

    if price > ma20 and k > d:
        advice = f"綜合研判：趨勢偏多。目前技術面與籌碼面皆有利多方，建議順勢操作。防守點可設在月線 {support:.1f}。"
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
    # 抓取 2 年資料以計算年線
    stock = yf.Ticker(target)
    df = stock.history(period="2y")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 抓取法人
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None:
             inst_df = get_institutional_data_yahoo(target)
        
        latest_inst_dict = inst_df.iloc[0].to_dict() if inst_df is not None and not inst_df.empty else None

        # 標題
        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        st.markdown(f"<h1 style='margin-bottom:0; text-shadow: 2px 2px 4px #000;'>{name} ({target})</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{color}; margin-top:0; text-shadow: 1px 1px 2px #000;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        # 顯示分析報告 (HTML 版)
        report_html = generate_narrative_report(name, target, latest, latest_inst_dict, df)
        st.markdown(report_html, unsafe_allow_html=True)
        
        # --- 專業 K 線圖 (Yahoo 風格) ---
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
            increasing_line_color='#ff4b4b', increasing_fillcolor='#ff4b4b',
            decreasing_line_color='#00c853', decreasing_fillcolor='#00c853'
        ), row=1, col=1)
        
        # 均線 (仿 Yahoo 色系)
        ma_configs = [
            ('MA5', 'blue', 1), 
            ('MA10', 'purple', 1), 
            ('MA20', 'orange', 1.5), # 月線加粗
            ('MA60', 'green', 1.5),  # 季線加粗
            ('MA120', 'brown', 1)    # 半年線
        ]
        for ma_name, ma_color, ma_width in ma_configs:
            fig.add_trace(go.Scatter(
                x=df.index.strftime('%Y-%m-%d'), y=df[ma_name], 
                line=dict(color=ma_color, width=ma_width), 
                name=f'{ma_name} ({latest[ma_name]:.2f})'
            ), row=1, col=1)

        # 2. 副圖一：成交量
        colors_vol = ['#ff4b4b' if r['Open'] < r['Close'] else '#00c853' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(
            x=df.index.strftime('%Y-%m-%d'), 
            y=df['Volume'], 
            marker_color=colors_vol, 
            name='成交量'
        ), row=2, col=1)

        # 3. 副圖二：KD 指標
        fig.add_trace(go.Scatter(
            x=df.index.strftime('%Y-%m-%d'), y=df['K'], 
            line=dict(color='#2962ff', width=1.2), name=f'K9 ({latest["K"]:.1f})'
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index.strftime('%Y-%m-%d'), y=df['D'], 
            line=dict(color='#ff6d00', width=1.2), name=f'D9 ({latest["D"]:.1f})'
        ), row=3, col=1)
        
        # 設定圖表樣式 (白色背景 + 格線)
        fig.update_layout(
            template="plotly_white",
            height=900, # 加高圖表
            xaxis_rangeslider_visible=False,
            xaxis3_rangeslider_visible=False,
            paper_bgcolor='rgba(255, 255, 255, 0.95)', # 純白背景
            plot_bgcolor='rgba(255, 255, 255, 0.95)',
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
            margin=dict(l=50, r=20, t=30, b=50)
        )
        
        # 顯示圖表
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
                st.subheader("🏛️ 法人買賣變化")
                fig_inst = go.Figure()
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#4285F4'))
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#A142F4'))
                fig_inst.update_layout(
                    barmode='group', 
                    template="plotly_white", 
                    height=300, 
                    paper_bgcolor='rgba(255, 255, 255, 0.95)', 
                    plot_bgcolor='rgba(255, 255, 255, 0.95)', 
                    xaxis=dict(autorange="reversed"),
                    font=dict(color='black')
                )
                st.plotly_chart(fig_inst, use_container_width=True)

except Exception as e:
    st.error(f"系統忙碌中，請稍後再試: {e}")
