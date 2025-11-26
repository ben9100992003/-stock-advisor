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

# 其餘 CSS 樣式
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 卡片通用樣式 */
    .recommendation-box, .analysis-text, .market-summary-box {
        background-color: rgba(20, 20, 20, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: #ffffff !important;
    }
    
    .recommendation-box { border-left: 6px solid #ff4b4b; }
    
    /* 側邊欄的大盤分析小卡 */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
    }

    /* 強制 Metric 樣式 */
    [data-testid="stMetric"] {
        background-color: rgba(30, 30, 30, 0.9) !important;
        padding: 15px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5) !important;
        text-align: center;
    }
    
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
        font-size: 1rem !important;
        font-weight: bold !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
    }

    /* Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 900;
        font-size: 1.1rem;
    }
    .stMarkdown p, .stCaption { color: #f0f0f0 !important; }
    h1, h2, h3 { text-shadow: 2px 2px 4px #000000; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海",
    "3231.TW": "緯創", "2382.TW": "廣達", "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金",
    "2618.TW": "長榮航", "2610.TW": "華航", "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息",
    "2354.TW": "鴻準", "3481.TW": "群創", "2409.TW": "友達", "2888.TW": "新光金",
    "NVDA": "輝達 (NVIDIA)", "TSLA": "特斯拉 (Tesla)", "AAPL": "蘋果 (Apple)", "AMD": "超微 (AMD)", "PLTR": "Palantir",
    "MSFT": "微軟 (Microsoft)", "GOOGL": "谷歌 (Alphabet)", "AMZN": "亞馬遜 (Amazon)", "META": "Meta", "NFLX": "網飛 (Netflix)",
    "INTC": "英特爾 (Intel)", "TSM": "台積電 ADR", "QCOM": "高通 (Qualcomm)", "AVGO": "博通 (Broadcom)"
}

@st.cache_data(ttl=3600)
def get_top_volume_stocks():
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
    if ".TW" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers)
        r.encoding = 'utf-8'
        dfs = pd.read_html(r.text)
        if not dfs: return None
        
        target_df = None
        for df in dfs:
            if any('外資' in str(col) for col in df.columns) and any('日期' in str(col) for col in df.columns):
                target_df = df
                break
        
        if target_df is None or target_df.empty: return None
        
        target_df.columns = [str(c).replace(' ', '') for c in target_df.columns]
        date_col = next((c for c in target_df.columns if '日期' in c), None)
        f_col = next((c for c in target_df.columns if '外資' in c and '持股' not in c), None)
        t_col = next((c for c in target_df.columns if '投信' in c), None)
        d_col = next((c for c in target_df.columns if '自營' in c), None)

        if not date_col or not f_col: return None

        df_clean = target_df[[date_col, f_col, t_col, d_col]].copy()
        df_clean.columns = ['Date', 'Foreign', 'Trust', 'Dealer']
        
        def clean_num(x):
            if isinstance(x, (int, float)): return int(x)
            if isinstance(x, str):
                x = x.replace(',', '').replace('+', '').replace('nan', '0')
                try: return int(x)
                except: return 0
            return 0
            
        for col in ['Foreign', 'Trust', 'Dealer']:
            df_clean[col] = df_clean[col].apply(clean_num)
            
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
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    
    # 布林通道 (20, 2)
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
    
    # 成交量均線
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
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
    df['Hist'] = df['MACD'] - df['Signal']
    
    return df

def analyze_market_index(ticker_symbol):
    """大盤指數自動分析"""
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="3mo")
        if df.empty: return None
        
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        price = latest['Close']
        change = price - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        ma20 = latest['MA20']
        k, d = latest['K'], latest['D']
        
        # 趨勢判斷文字生成
        status = "盤整"
        color = "#ffffff"
        comment = ""
        
        if price > ma20:
            if k > d:
                status = "多頭強勢"
                color = "#ff4b4b"
                comment = "指數站上月線且 KD 黃金交叉，短線動能強勁，偏多操作。"
            else:
                status = "多頭回檔"
                color = "#ff9100"
                comment = "雖在月線之上但 KD 修正中，留意支撐是否有守。"
        else:
            if k < d:
                status = "空方修正"
                color = "#00c853"
                comment = "指數跌破月線且 KD 死亡交叉，趨勢偏弱，建議保守觀望。"
            else:
                status = "跌深反彈"
                color = "#ffff00"
                comment = "KD 低檔交叉向上，醞釀反彈，但上方月線仍有壓。"
                
        return {
            "price": price,
            "change": change,
            "pct": pct,
            "status": status,
            "color": color,
            "comment": comment,
            "ma20": ma20
        }
    except:
        return None

# --- 5. 深度分析報告生成 (核心升級) ---
def generate_report(name, ticker, latest, inst_data_dict, df):
    price = latest['Close']
    vol = latest['Volume']
    vol_ma5 = latest['VOL_MA5']
    
    ma5 = latest['MA5']
    ma20 = latest['MA20']
    ma60 = latest['MA60']
    
    k, d = latest['K'], latest['D']
    rsi = latest['RSI']
    macd_hist = latest['Hist']
    
    bb_up = latest['BB_UP']
    bb_lo = latest['BB_LO']
    
    # 1. 結構判斷
    trend_str = ""
    if price > ma20 and ma20 > ma60:
        trend_str = "多頭排列格局，中長線趨勢向上。"
    elif price < ma20 and ma20 < ma60:
        trend_str = "空頭排列格局，上方層層賣壓。"
    elif price > ma20:
        trend_str = "站上月線，短線嘗試轉強。"
    else:
        trend_str = "跌破月線，短線整理修正。"
        
    # 2. 動能分析
    momentum_str = ""
    if macd_hist > 0 and k > d:
        momentum_str = "MACD 紅柱與 KD 金叉共振，上漲動能強勁。"
    elif macd_hist < 0 and k < d:
        momentum_str = "MACD 綠柱與 KD 死叉共振，下跌動能增強。"
    elif k > 80:
        momentum_str = "KD 指標進入高檔鈍化區，需留意短線過熱回檔。"
    elif k < 20:
        momentum_str = "KD 指標進入低檔超賣區，隨時有反彈機會。"
    else:
        momentum_str = "技術指標呈現中性震盪。"

    # 3. 籌碼分析
    inst_text = "資料更新中..."
    inst_conclusion = "籌碼動向不明。"
    if inst_data_dict:
        f_val = inst_data_dict['Foreign']
        t_val = inst_data_dict['Trust']
        d_val = inst_data_dict['Dealer']
        total = f_val + t_val + d_val
        
        inst_text = f"""
        外資: <span style='color:{'#ff4b4b' if f_val>0 else '#00c853'}'>{f_val:,}</span> 張 | 
        投信: <span style='color:{'#ff4b4b' if t_val>0 else '#00c853'}'>{t_val:,}</span> 張 | 
        自營: <span style='color:{'#ff4b4b' if d_val>0 else '#00c853'}'>{d_val:,}</span> 張 
        (合計: {total:,} 張)
        """
        
        if total > 2000: inst_conclusion = "法人大舉買進，籌碼面偏多。"
        elif total < -2000: inst_conclusion = "法人調節賣出，籌碼面偏空。"
        elif t_val > 500: inst_conclusion = "投信積極佈局，關注作帳行情。"
        else: inst_conclusion = "法人買賣超幅度不大，觀望氣氛濃。"
    else:
        inst_text = "無法取得今日法人資料 (Yahoo 來源連線中...)"

    # 4. 價量分析
    vol_str = ""
    if vol > 1.5 * vol_ma5:
        vol_str = "今日出量攻擊，顯示買盤積極。" if price > df['Open'].iloc[-1] else "今日爆量下殺，恐有主力出貨嫌疑。"
    elif vol < 0.6 * vol_ma5:
        vol_str = "今日量縮整理，市場觀望氣氛濃厚。"
    else:
        vol_str = "成交量維持常態水平。"

    # 5. 綜合建議
    strategy = ""
    action_color = "#ffffff"
    
    if price > ma20 and k > d:
        strategy = f"多頭強勢。建議沿 5 日線 ({ma5:.1f}) 操作，跌破月線 ({ma20:.1f}) 停利。"
        action_color = "#ff4b4b" # 紅
    elif price < ma20 and k < d:
        strategy = f"空方走勢。壓力看月線 ({ma20:.1f})，支撐看布林下軌 ({bb_lo:.1f})，勿輕易摸底。"
        action_color = "#00c853" # 綠
    elif price > bb_up:
        strategy = "股價觸及布林上軌，短線乖離過大，不宜追高，可分批獲利。"
        action_color = "#ff9100" # 橘
    elif price < bb_lo:
        strategy = "股價觸及布林下軌，短線乖離過大，可留意搶反彈機會。"
        action_color = "#ffff00" # 黃
    else:
        strategy = f"區間震盪。建議在月線 ({ma20:.1f}) 與季線 ({ma60:.1f}) 之間來回操作。"

    # 組合成 HTML 報告
    html = f"""
    <div class="analysis-text">
        <h3 style="border-bottom: 2px solid #555; padding-bottom: 10px;">🦖 武吉拉深度完整分析</h3>
        
        <p><b>1. 趨勢結構：</b><br>
        {trend_str}</p>
        
        <p><b>2. 資金動能：</b><br>
        {momentum_str} {vol_str}</p>
        
        <p><b>3. 籌碼解讀：</b><br>
        {inst_conclusion}<br>
        <span style="font-size:0.9em; color:#ccc;">{inst_text}</span></p>
        
        <p><b>4. 關鍵點位：</b><br>
        壓力：布林上軌 {bb_up:.2f} | 支撐：月線 {ma20:.2f}</p>
        
        <hr style="border-top: 1px dashed #666;">
        <p style="font-size:1.3rem; font-weight:bold; color:{action_color} !important;">
        💡 操作策略：{strategy}
        </p>
    </div>
    """
    return html

# --- 6. 主程式介面 ---

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
    
    # --- 每日大盤盤勢分析區塊 ---
    st.subheader("🌍 每日大盤盤勢分析")
    
    idx_tab1, idx_tab2 = st.tabs(["🇹🇼 台股盤勢", "🇺🇸 美股盤勢"])
    
    with idx_tab1:
        tw_data = analyze_market_index("^TWII")
        if tw_data:
            st.markdown(f"""
            <div class="market-summary-box">
                <div style="font-size:1.2rem; font-weight:bold; color:{tw_data['color']}">
                    加權指數: {tw_data['price']:.0f}
                    <span style="font-size:0.8rem">({tw_data['change']:+.0f} / {tw_data['pct']:+.2f}%)</span>
                </div>
                <div style="margin-top:5px;">
                    <b>狀態：{tw_data['status']}</b><br>
                    <span style="font-size:0.85rem; color:#ddd;">{tw_data['comment']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("資料讀取中...")

    with idx_tab2:
        us_data = analyze_market_index("^IXIC") # Nasdaq
        if us_data:
            st.markdown(f"""
            <div class="market-summary-box" style="border-left: 4px solid #00BFFF;">
                <div style="font-size:1.2rem; font-weight:bold; color:{us_data['color']}">
                    Nasdaq: {us_data['price']:.0f}
                    <span style="font-size:0.8rem">({us_data['change']:+.0f} / {us_data['pct']:+.2f}%)</span>
                </div>
                <div style="margin-top:5px;">
                    <b>狀態：{us_data['status']}</b><br>
                    <span style="font-size:0.85rem; color:#ddd;">{us_data['comment']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("資料讀取中...")
            
    st.markdown("---")
    # --- 大盤區塊結束 ---

    user_input = st.text_input("或輸入代號 (如 2330, NVDA)", value="")
    
    target = user_input.upper() if user_input else selected_ticker
    if target.isdigit(): target += ".TW" 

    st.link_button(f"前往 Yahoo 股市 ({target})", f"https://tw.stock.yahoo.com/quote/{target}", use_container_width=True)

# 右側主畫面：個股分析
try:
    stock = yf.Ticker(target)
    df = stock.history(period="6mo")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        display_name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 雙重保險抓取法人資料
        inst_df = get_institutional_data_yahoo(target)
        if inst_df is None:
            inst_df = get_institutional_data_finmind(target)
        
        # 準備最新法人數據
        latest_inst_dict = None
        if inst_df is not None and not inst_df.empty:
            latest_inst_dict = inst_df.iloc[0].to_dict()

        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"<h1 style='margin-bottom:0;'>{display_name} ({target})</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{color}; margin-top:0;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        st.markdown(generate_report(display_name, target, latest, latest_inst_dict, df), unsafe_allow_html=True)
        
        # K 線圖
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index.strftime('%Y-%m-%d'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA5'], line=dict(color='orange', width=1), name='MA5'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA20'], line=dict(color='cyan', width=1), name='MA20'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['BB_UP'], line=dict(color='gray', width=1, dash='dot'), name='布林上軌'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['BB_LO'], line=dict(color='gray', width=1, dash='dot'), name='布林下軌'), row=1, col=1)
        
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
        
        # 法人圖表區
        st.markdown("### 🏛️ 法人籌碼變化 (近30日)")
        if inst_df is not None and not inst_df.empty:
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#4285F4'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#A142F4'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#FBBC05'))
            
            fig_inst.update_layout(
                barmode='group',
                template="plotly_white",
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(255, 255, 255, 1)',
                plot_bgcolor='rgba(255, 255, 255, 1)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_inst.update_xaxes(autorange="reversed")
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            st.info("此股票無法人籌碼資料。")

except Exception as e:
    st.error(f"發生錯誤: {e}")
