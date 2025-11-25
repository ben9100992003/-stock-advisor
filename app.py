import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os

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
    
    /* 霧面玻璃卡片效果 */
    .metric-card, .recommendation-box, .analysis-text {
        background-color: rgba(20, 20, 20, 0.85) !important; /* 加深背景色以凸顯文字 */
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

# --- 3. FinMind 資料串接 (防呆與邏輯優化) ---
try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False

@st.cache_data(ttl=3600) # 快取 1 小時
def get_top_volume_stocks():
    """
    抓取台股「真實」當日熱門成交量排行 Top 15
    """
    if not FINMIND_AVAILABLE:
        # 備案：如果抓不到，回傳固定清單
        return ["2330", "2317", "2603", "2609", "3231", "2618", "00940", "00919", "2454", "2303"]
    
    try:
        dl = DataLoader()
        # 抓取最近交易日 (往回找 7 天內一定有開市的一天)
        latest_trade_date = dl.taiwan_stock_daily_adj(
            stock_id="2330", 
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ).iloc[-1]['date']
        
        # 抓取該日所有股票成交資訊
        df = dl.taiwan_stock_daily_adj(start_date=latest_trade_date)
        
        # 排序成交量 (Trading_Volume) 並取前 15 名
        top_df = df.sort_values(by='Trading_Volume', ascending=False).head(15)
        return top_df['stock_id'].tolist()
    except:
        return ["2330", "2317", "2603", "2609", "3231", "2454"] # 連線失敗時的備案

@st.cache_data(ttl=300)
def get_institutional_data_robust(ticker):
    """
    強效版法人資料抓取：死命必達，直到找到資料為止
    """
    if not FINMIND_AVAILABLE or ".TW" not in ticker: return None
    
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader()
    
    try:
        # 一次抓過去 14 天，確保能跨過連假
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        
        if df.empty: return None

        # 從最新的一天開始往回找，直到找到「非零」的數據
        dates = sorted(df['date'].unique(), reverse=True)
        
        for d in dates:
            day_df = df[df['date'] == d]
            
            # 計算買賣超 (buy - sell)
            def get_net(name_keyword):
                rows = day_df[day_df['name'].str.contains(name_keyword)]
                if rows.empty: return 0
                return rows['buy'].sum() - rows['sell'].sum()

            f_net = get_net('外資')
            t_net = get_net('投信')
            d_net = get_net('自營')
            
            # 只要有一天資料不是全 0，就當作是這天的資料
            if f_net != 0 or t_net != 0 or d_net != 0:
                return {
                    'date': d,
                    'foreign': int(f_net / 1000), # 換算張
                    'trust': int(t_net / 1000),
                    'dealer': int(d_net / 1000)
                }
        return None
    except:
        return None

# --- 4. 技術指標運算 ---
def calculate_indicators(df):
    # MA
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    
    # KD (9,3,3)
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
    
    # MACD
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
    
    # 趨勢判斷
    trend = "多頭強勢 🔥" if price > ma20 else "空方修正 🧊"
    if price > latest['MA5'] and price > ma20 and price > latest['MA60']: trend = "全面噴發 🚀"
    
    # 法人文字
    inst_text = "資料更新中..."
    if inst_data:
        total = inst_data['foreign'] + inst_data['trust'] + inst_data['dealer']
        inst_text = f"""
        外資: <span style='color:{'#ff4b4b' if inst_data['foreign']>0 else '#00c853'}'>{inst_data['foreign']:,}</span> 張 | 
        投信: <span style='color:{'#ff4b4b' if inst_data['trust']>0 else '#00c853'}'>{inst_data['trust']:,}</span> 張 | 
        自營: <span style='color:{'#ff4b4b' if inst_data['dealer']>0 else '#00c853'}'>{inst_data['dealer']:,}</span> 張 
        (合計: {total:,} 張)
        """
    
    # 操作建議
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

# 側邊欄
with st.sidebar:
    st.header("🦖 武吉拉選股")
    
    # 自動抓取熱門股
    with st.spinner("正在掃描市場熱門股..."):
        hot_stocks_list = get_top_volume_stocks()
        
    # 加上美股熱門
    all_hot_stocks = hot_stocks_list + ["NVDA", "TSLA", "AAPL", "AMD", "PLTR"]
    
    selected_ticker = st.selectbox("🔥 本日熱門成交 Top 15", options=all_hot_stocks)
    
    st.markdown("---")
    user_input = st.text_input("或輸入代號 (如 2330)", value="")
    
    # 決定最終代號
    target = user_input.upper() if user_input else selected_ticker
    if target.isdigit(): target += ".TW" # 自動補 .TW

    # Yahoo 按鈕
    st.link_button(f"前往 Yahoo 股市 ({target})", f"https://tw.stock.yahoo.com/quote/{target}", use_container_width=True)

# 執行數據抓取
try:
    stock = yf.Ticker(target)
    df = stock.history(period="6mo")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        info = stock.info
        name = info.get('longName', target)
        
        # 抓取法人 (防呆版)
        inst_data = get_institutional_data_robust(target)
        
        # 標題區 (帶顏色)
        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"<h1 style='margin-bottom:0;'>{name}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{color}; margin-top:0;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        # 生成報告
        st.markdown(generate_report(name, target, latest, inst_data, df), unsafe_allow_html=True)
        
        # K線圖
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        # K線
        fig.add_trace(go.Candlestick(x=df.index.strftime('%Y-%m-%d'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        # 均線
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA5'], line=dict(color='orange', width=1), name='MA5'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA20'], line=dict(color='cyan', width=1), name='MA20'), row=1, col=1)
        # 成交量
        colors = ['#ff4b4b' if r['Open'] < r['Close'] else '#00c853' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index.strftime('%Y-%m-%d'), y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # 底部數據表
        t1, t2, t3 = st.columns(3)
        t1.metric("RSI (14)", f"{latest['RSI']:.1f}")
        t2.metric("K (9)", f"{latest['K']:.1f}")
        t3.metric("D (9)", f"{latest['D']:.1f}")

except Exception as e:
    st.error(f"發生錯誤: {e}")
