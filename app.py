import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os
import requests # 新增 requests 用於爬取 Yahoo

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
        return # 檔案不存在就不設定
        
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

# 嘗試載入背景 (請確認 GitHub 上有上傳名為 bg.png 的檔案)
set_png_as_page_bg('bg.png')

# 其餘 CSS 樣式
st.markdown("""
    <style>
    /* 若無背景圖，預設為深色 */
    .stApp {
        color: #ffffff;
    }
    
    /* 隱藏選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 霧面玻璃卡片效果 (通用) */
    .recommendation-box, .analysis-text {
        background-color: rgba(20, 20, 20, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: #ffffff !important;
    }
    
    .recommendation-box {
        border-left: 6px solid #ff4b4b;
    }

    /* --- 關鍵修復：強制底部數據指標 (Metric) 樣式 --- */
    [data-testid="stMetric"] {
        background-color: rgba(30, 30, 30, 0.9) !important; /* 深黑底板 */
        padding: 15px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5) !important;
        text-align: center;
    }
    
    /* 標籤文字 (RSI, K, D) */
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
        font-size: 1rem !important;
        font-weight: bold !important;
    }
    
    /* 數值文字 (47.9, 21.7...) */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3); /* 發光效果 */
    }

    /* 強制 Tab 與文字顏色 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 900;
        font-size: 1.1rem;
    }
    .stMarkdown p, .stCaption {
        color: #f0f0f0 !important;
    }
    
    /* 標題陰影 */
    h1, h2, h3 {
        text-shadow: 2px 2px 4px #000000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

# FinMind 用於熱門股排行 (因為 Yahoo 沒開放熱門股 API)
try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False

# 股票代號與中文名稱對照表
STOCK_NAMES = {
    # 台股熱門
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海",
    "3231.TW": "緯創", "2382.TW": "廣達", "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金",
    "2618.TW": "長榮航", "2610.TW": "華航", "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息",
    "2354.TW": "鴻準", "3481.TW": "群創", "2409.TW": "友達", "2888.TW": "新光金",
    # 美股熱門
    "NVDA": "輝達 (NVIDIA)", "TSLA": "特斯拉 (Tesla)", "AAPL": "蘋果 (Apple)", "AMD": "超微 (AMD)", "PLTR": "Palantir",
    "MSFT": "微軟 (Microsoft)", "GOOGL": "谷歌 (Alphabet)", "AMZN": "亞馬遜 (Amazon)", "META": "Meta", "NFLX": "網飛 (Netflix)",
    "INTC": "英特爾 (Intel)", "TSM": "台積電 ADR", "QCOM": "高通 (Qualcomm)", "AVGO": "博通 (Broadcom)"
}

@st.cache_data(ttl=3600) # 快取 1 小時
def get_top_volume_stocks():
    """
    抓取台股「真實」當日熱門成交量排行 Top 15 (來源: FinMind)
    """
    if not FINMIND_AVAILABLE:
        return ["2330", "2317", "2603", "2609", "3231", "2618", "00940", "00919", "2454", "2303"]
    
    try:
        dl = DataLoader()
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
    """
    從 Yahoo 股市網頁直接爬取法人買賣超 (單位: 張)
    """
    if ".TW" not in ticker: return None
    
    try:
        # Yahoo 頁面 URL
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # 發送請求
        r = requests.get(url, headers=headers)
        
        # 使用 pandas 解析 HTML 表格
        dfs = pd.read_html(r.text)
        
        if not dfs: return None
        
        # 尋找含有 "外資" 欄位的表格
        target_df = None
        for df in dfs:
            # Yahoo 表格欄位通常包含 '日期', '外資買賣超', ...
            if any('外資' in str(col) for col in df.columns):
                target_df = df
                break
        
        if target_df is None or target_df.empty: return None
        
        # 取得最新一筆資料 (通常是第一列)
        latest = target_df.iloc[0]
        
        # 輔助函式：處理數值 (移除逗號，轉整數)
        def parse_val(val):
            try:
                if isinstance(val, (int, float)): return int(val)
                if isinstance(val, str):
                    return int(val.replace(',', '').replace('+', ''))
            except:
                return 0
            return 0

        # 找出對應的欄位名稱 (Yahoo 欄位有時候會變，模糊比對)
        cols = target_df.columns
        f_col = next((c for c in cols if '外資' in str(c) and '持股' not in str(c)), None)
        t_col = next((c for c in cols if '投信' in str(c)), None)
        d_col = next((c for c in cols if '自營' in str(c)), None)
        date_col = next((c for c in cols if '日期' in str(c)), None)

        if not f_col: return None

        data = {
            'date': str(latest[date_col]) if date_col else datetime.now().strftime('%Y/%m/%d'),
            'foreign': parse_val(latest[f_col]),
            'trust': parse_val(latest[t_col]) if t_col else 0,
            'dealer': parse_val(latest[d_col]) if d_col else 0
        }
        
        # Yahoo 網頁上的單位通常直接是「張」，不需除以 1000
        return data

    except Exception as e:
        # print(f"Yahoo scraping error: {e}") # 除錯用
        return None

# --- 4. 技術指標運算 ---
def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    ema_u = u.ewm(com=13, adjust=False).mean()
    ema_d = d.ewm(com=13, adjust=False).mean()
    rs = ema_u / ema_d
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# --- 5. 分析報告生成 ---
def generate_report(name, ticker, latest, inst_data, df):
    price = latest['Close']
    ma20 = latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭強勢 🔥" if price > ma20 else "空方修正 🧊"
    if price > latest['MA5'] and price > ma20 and price > latest['MA60']: trend = "全面噴發 🚀"
    
    inst_text = "資料更新中..."
    if inst_data:
        total = inst_data['foreign'] + inst_data['trust'] + inst_data['dealer']
        inst_text = f"""
        外資: <span style='color:{'#ff4b4b' if inst_data['foreign']>0 else '#00c853'}'>{inst_data['foreign']:,}</span> 張 | 
        投信: <span style='color:{'#ff4b4b' if inst_data['trust']>0 else '#00c853'}'>{inst_data['trust']:,}</span> 張 | 
        自營: <span style='color:{'#ff4b4b' if inst_data['dealer']>0 else '#00c853'}'>{inst_data['dealer']:,}</span> 張 
        (合計: {total:,} 張)
        """
    else:
        inst_text = "無法取得今日法人資料 (Yahoo 來源連線中...)"
    
    action = "觀望"
    if price > ma20 and k > d: action = "偏多操作 (拉回找買點)"
    elif price < ma20 and k < d: action = "偏空操作 (反彈找賣點)"
    elif k > 80: action = "高檔警戒 (勿追高)"
    elif k < 20: action = "超跌醞釀反彈"

    html = f"""
    <div class="analysis-text">
        <h3>📊 {name} ({ticker}) 深度診斷</h3>
        <p><b>【趨勢燈號】</b>：{trend}</p>
        <p><b>【價量結構】</b>：收盤 {price:.2f}，成交量 {int(latest['Volume']/1000):,} 張。</p>
        <p><b>【法人籌碼】</b>：{inst_text}</p>
        <p><b>【關鍵指標】</b>：KD({k:.1f}/{d:.1f}) {'黃金交叉' if k>d else '死亡交叉'} | RSI: {latest['RSI']:.1f}</p>
        <p><b>【支撐壓力】</b>：月線 {ma20:.2f} 為重要多空分水嶺。</p>
        <hr>
        <p style="font-size:1.2rem; color:#ffeb3b !important;"><b>💡 武吉拉建議：{action}</b></p>
    </div>
    """
    return html

# --- 6. 主程式邏輯 ---

with st.sidebar:
    st.header("🦖 武吉拉選股")
    
    with st.spinner("正在掃描市場熱門股..."):
        hot_stocks_list = get_top_volume_stocks()
        
    all_hot_stocks = hot_stocks_list + ["NVDA", "TSLA", "AAPL", "AMD", "PLTR"]
    
    options_with_names = []
    for ticker in all_hot_stocks:
        ticker_key = f"{ticker}.TW" if ticker.isdigit() else ticker
        name = STOCK_NAMES.get(ticker_key, ticker) 
        options_with_names.append(f"{name} ({ticker})")

    selected_option = st.selectbox("🔥 本日熱門成交 Top 15", options=options_with_names)
    selected_ticker = selected_option.split("(")[-1].replace(")", "")

    st.markdown("---")
    user_input = st.text_input("或輸入代號 (如 2330, NVDA)", value="")
    
    target = user_input.upper() if user_input else selected_ticker
    if target.isdigit(): target += ".TW" 

    st.link_button(f"前往 Yahoo 股市 ({target})", f"https://tw.stock.yahoo.com/quote/{target}", use_container_width=True)

try:
    stock = yf.Ticker(target)
    df = stock.history(period="6mo")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        display_name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 改用 Yahoo 爬蟲抓取法人資料
        inst_data = get_institutional_data_yahoo(target)
        
        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"<h1 style='margin-bottom:0;'>{display_name} ({target})</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{color}; margin-top:0;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        st.markdown(generate_report(display_name, target, latest, inst_data, df), unsafe_allow_html=True)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index.strftime('%Y-%m-%d'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA5'], line=dict(color='orange', width=1), name='MA5'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA20'], line=dict(color='cyan', width=1), name='MA20'), row=1, col=1)
        colors = ['#ff4b4b' if r['Open'] < r['Close'] else '#00c853' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index.strftime('%Y-%m-%d'), y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        fig.update_layout(
            template="plotly_white",
            height=500, 
            xaxis_rangeslider_visible=False, 
            margin=dict(l=0, r=0, t=0, b=0), 
            paper_bgcolor='rgba(255, 255, 255, 1)', 
            plot_bgcolor='rgba(255, 255, 255, 1)' 
        )
        st.plotly_chart(fig, use_container_width=True)
        
        t1, t2, t3 = st.columns(3)
        t1.metric("RSI (14)", f"{latest['RSI']:.1f}")
        t2.metric("K (9)", f"{latest['K']:.1f}")
        t3.metric("D (9)", f"{latest['D']:.1f}")

except Exception as e:
    st.error(f"發生錯誤: {e}")
