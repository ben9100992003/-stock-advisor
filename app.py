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
    
    .recommendation-box, .analysis-text {
        background-color: rgba(20, 20, 20, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: #ffffff !important;
    }
    
    .recommendation-box { border-left: 6px solid #ff4b4b; }

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
    """第一層：Yahoo 爬蟲"""
    if ".TW" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        r = requests.get(url, headers=headers)
        r.encoding = 'utf-8'
        
        # 強制解析表格
        dfs = pd.read_html(r.text)
        if not dfs: return None
        
        target_df = None
        for df in dfs:
            # 尋找關鍵字
            if any('外資' in str(col) for col in df.columns) and any('日期' in str(col) for col in df.columns):
                target_df = df
                break
        
        if target_df is None or target_df.empty: return None
        
        # 欄位標準化
        target_df.columns = [str(c).replace(' ', '') for c in target_df.columns]
        date_col = next((c for c in target_df.columns if '日期' in c), None)
        f_col = next((c for c in target_df.columns if '外資' in c and '持股' not in c), None)
        t_col = next((c for c in target_df.columns if '投信' in c), None)
        d_col = next((c for c in target_df.columns if '自營' in c), None)

        if not date_col or not f_col: return None

        df_clean = target_df[[date_col, f_col, t_col, d_col]].copy()
        df_clean.columns = ['Date', 'Foreign', 'Trust', 'Dealer']
        
        # 數據清洗
        def clean_num(x):
            if isinstance(x, (int, float)): return int(x)
            if isinstance(x, str):
                x = x.replace(',', '').replace('+', '').replace('nan', '0')
                try: return int(x)
                except: return 0
            return 0
            
        for col in ['Foreign', 'Trust', 'Dealer']:
            df_clean[col] = df_clean[col].apply(clean_num)
            
        # 確保日期格式 (Yahoo 可能是 11/25，需加上年份)
        def clean_date(d):
            if isinstance(d, str) and '/' in d and len(d) <= 5:
                return f"{datetime.now().year}/{d}"
            return d
        
        df_clean['Date'] = df_clean['Date'].apply(clean_date)
        
        # 回傳前 30 筆
        return df_clean.head(30)

    except Exception as e:
        # print(f"Yahoo Error: {e}") 
        return None

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    """第二層：FinMind 備援 (如果 Yahoo 失敗)"""
    if not FINMIND_AVAILABLE or ".TW" not in ticker: return None
    
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader()
    try:
        start_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None

        # 轉成寬表格格式 (Pivot) 模擬 Yahoo 格式
        # FinMind: date, name(外資/投信..), buy, sell
        df['net'] = df['buy'] - df['sell']
        
        # 建立日期清單
        dates = sorted(df['date'].unique(), reverse=True)
        result_data = []
        
        for d in dates:
            day_df = df[df['date'] == d]
            
            def get_net(key):
                v = day_df[day_df['name'].str.contains(key)]['net'].sum()
                return int(v / 1000) # FinMind 單位是股，轉張
            
            result_data.append({
                'Date': d,
                'Foreign': get_net('外資'),
                'Trust': get_net('投信'),
                'Dealer': get_net('自營')
            })
            
        return pd.DataFrame(result_data).head(30)
    except:
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
def generate_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    ma20 = latest['MA20']
    k, d = latest['K'], latest['D']
    
    trend = "多頭強勢 🔥" if price > ma20 else "空方修正 🧊"
    if price > latest['MA5'] and price > ma20 and price > latest['MA60']: trend = "全面噴發 🚀"
    
    # 法人數據處理
    inst_text = "資料讀取中..."
    source_text = ""
    
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[0]
        f_val, t_val, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f_val + t_val + d_val
        
        inst_text = f"""
        外資: <span style='color:{'#ff4b4b' if f_val>0 else '#00c853'}'>{f_val:,}</span> 張 | 
        投信: <span style='color:{'#ff4b4b' if t_val>0 else '#00c853'}'>{t_val:,}</span> 張 | 
        自營: <span style='color:{'#ff4b4b' if d_val>0 else '#00c853'}'>{d_val:,}</span> 張 
        (合計: {total:,} 張)
        """
        source_text = f"(資料來源: Yahoo/FinMind | 日期: {last['Date']})"
    else:
        inst_text = "無法取得法人資料 (系統連線異常)"
    
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
        <p style="font-size:0.8em; color:#aaa;">{source_text}</p>
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
        
        # 雙重保險抓取法人資料
        inst_df = get_institutional_data_yahoo(target)
        if inst_df is None:
            inst_df = get_institutional_data_finmind(target)
        
        change = latest['Close'] - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if change >= 0 else "#00c853"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"<h1 style='margin-bottom:0;'>{display_name} ({target})</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{color}; margin-top:0;'>{latest['Close']:.2f} <small>({change:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        st.markdown(generate_report(display_name, target, latest, inst_df, df), unsafe_allow_html=True)
        
        # 技術面 K 線圖
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
        
        # 底部 Tab 區塊
        tab1, tab2 = st.tabs(["📉 詳細指標", "🏛️ 法人籌碼"])
        
        with tab1:
            t1, t2, t3 = st.columns(3)
            t1.metric("RSI (14)", f"{latest['RSI']:.1f}")
            t2.metric("K (9)", f"{latest['K']:.1f}")
            t3.metric("D (9)", f"{latest['D']:.1f}")
            
        with tab2:
            if inst_df is not None and not inst_df.empty:
                # 顯示法人買賣變化圖表 (Bar Chart)
                st.subheader("法人買賣變化 (近30日)")
                fig_inst = go.Figure()
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#4285F4')) # 藍
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#A142F4')) # 紫
                fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商', marker_color='#FBBC05')) # 黃/橘
                
                fig_inst.update_layout(
                    barmode='group',
                    template="plotly_white",
                    height=400,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor='rgba(255, 255, 255, 1)',
                    plot_bgcolor='rgba(255, 255, 255, 1)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                # 如果是 Yahoo 來源，最新的在上面，需要反轉畫圖順序
                fig_inst.update_xaxes(autorange="reversed")
                st.plotly_chart(fig_inst, use_container_width=True)
                
                # 顯示最新數據 Metrics
                m1, m2, m3 = st.columns(3)
                last = inst_df.iloc[0]
                def c_val(v): return "normal" if v > 0 else "inverse"
                m1.metric("外資", f"{last['Foreign']:,}", delta=f"{last['Foreign']:,}", delta_color=c_val(last['Foreign']))
                m2.metric("投信", f"{last['Trust']:,}", delta=f"{last['Trust']:,}", delta_color=c_val(last['Trust']))
                m3.metric("自營商", f"{last['Dealer']:,}", delta=f"{last['Dealer']:,}", delta_color=c_val(last['Dealer']))
                st.caption(f"資料來源: Yahoo/FinMind | 日期: {last['Date']}")
            else:
                st.info("目前無法人資料或非台股標的。")

except Exception as e:
    st.error(f"發生錯誤: {e}")


