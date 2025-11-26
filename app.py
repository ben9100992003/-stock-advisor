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

# 其餘 CSS 樣式 (終極顯影版)
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 1. 分析報告容器 (上方) --- */
    .glass-container {
        background-color: rgba(0, 0, 0, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(8px);
    }
    .glass-container h3 { color: #ffcc00 !important; border-bottom: 2px solid rgba(255,255,255,0.2); padding-bottom: 10px; text-shadow: 2px 2px 4px black; }
    .glass-container p { color: #f0f0f0 !important; font-size: 1.1rem; line-height: 1.6; }
    .glass-container b { color: #fff; }

    /* --- 2. 側邊欄卡片 --- */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* --- 3. 數據指標卡片 (下方 Metric) - 關鍵修復 --- */
    div[data-testid="stMetric"] {
        background-color: rgba(20, 20, 20, 0.85) !important; /* 半透明黑底 */
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(5px);
    }
    
    /* 標籤文字 (如 RSI, K, D) */
    div[data-testid="stMetricLabel"] p {
        color: #bbbbbb !important; /* 亮灰色 */
        font-size: 1rem !important;
        font-weight: bold !important;
    }
    
    /* 數值文字 (如 47.9) */
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important; /* 純白 */
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.6); /* 發光特效 */
    }

    /* --- 4. Tab 分頁標籤 --- */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 1.1rem;
        font-weight: bold;
        text-shadow: 1px 1px 2px black;
    }
    
    /* 一般文字與標題 */
    .stMarkdown p, .stCaption { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    h1, h2, h3 { text-shadow: 2px 2px 8px #000000; color: #fff !important; }
    
    /* Yahoo 按鈕優化 */
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

    except Exception as e:
        return None

# --- 4. 技術指標與大盤分析函式 ---

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
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
                comment = "指數站穩月線且 KD 黃金交叉，多方控盤，可積極操作。"
            else:
                status = "多頭回檔"
                color = "#ff9100"
                comment = "指數雖在月線之上但面臨技術性修正，留意月線支撐。"
        else:
            if k < d:
                status = "空方修正"
                color = "#00c853"
                comment = "指數跌破月線且 KD 死亡交叉，趨勢偏弱，現金為王。"
            else:
                status = "跌深反彈"
                color = "#ffff00"
                comment = "KD 低檔黃金交叉，短線醞釀反彈，但上方壓力仍重。"
                
        return {
            "price": price, "change": change, "pct": pct,
            "status": status, "color": color, "comment": comment
        }
    except:
        return None

# --- 5. 深度分析報告 (HTML 生成版) ---
def generate_narrative_report(name, ticker, latest, inst_data_dict, df):
    price = latest['Close']
    vol = latest['Volume']
    ma5, ma20, ma60 = latest['MA5'], latest['MA20'], latest['MA60']
    k, d = latest['K'], latest['D']
    
    # 趨勢敘述
    trend_html = ""
    if price > ma20:
        trend_html = f"<b>{name} ({ticker})</b> 目前股價站穩月線之上，顯示中期趨勢具備支撐。"
        if price > ma5 and ma5 > ma20:
            trend_html += " 短線沿著 5 日均線強勢上攻，多頭架構完整。"
    else:
        trend_html = f"<b>{name} ({ticker})</b> 股價跌破月線，短線進入整理修正階段。"
        if price < ma60:
            trend_html += " 且目前位於季線之下，上方套牢賣壓沈重，需等待落底訊號。"

    # 籌碼敘述
    inst_html = "籌碼方面，"
    if inst_data_dict:
        f_val = inst_data_dict['Foreign']
        t_val = inst_data_dict['Trust']
        total = f_val + t_val + inst_data_dict['Dealer']
        date_str = inst_data_dict['Date']
        
        buy_sell_color = "#ff4b4b" if total > 0 else "#00c853"
        buy_sell_text = "買超" if total > 0 else "賣超"
        
        inst_html += f"截至 {date_str}，三大法人合計 <span style='color:{buy_sell_color}'>{buy_sell_text} {abs(total):,} 張</span>。"
        if f_val > 1000: inst_html += " 其中外資展現買盤誠意，為推升股價主力。"
        elif f_val < -1000: inst_html += " 唯外資近期調節動作頻頻，需留意提款壓力。"
        
        if t_val > 500: inst_html += " 值得注意的是，投信正積極佈局，可能與季底作帳行情有關。"
    else:
        inst_html += "暫無最新法人買賣超數據 (通常於下午 3 點後更新)，建議稍後再確認。"

    # 技術指標敘述
    kd_status = "黃金交叉" if k > d else "死亡交叉"
    kd_color = "#ff4b4b" if k > d else "#00c853"
    tech_html = f"技術指標部分，KD 目前數值為 ({k:.1f}, {d:.1f})，呈現 <span style='color:{kd_color}'><b>{kd_status}</b></span>。"
    
    if k > d: tech_html += " 短線動能轉強，有利多方表態。"
    else: tech_html += " 短線動能轉弱，可能面臨回檔整理。"
        
    if latest['RSI'] > 70: tech_html += " <br>⚠️ RSI 指標進入高檔區，慎防追高風險。"
    elif latest['RSI'] < 30: tech_html += " <br>✅ RSI 指標進入超賣區，隨時有機會出現技術性反彈。"

    # 總結建議
    advice = ""
    adv_color = "#ffffff"
    if price > ma20 and k > d:
        advice = "綜合研判：趨勢偏多。建議沿 5 日線操作，若拉回不破月線可視為買點。"
        adv_color = "#ff4b4b" # 紅
    elif price < ma20 and k < d:
        advice = "綜合研判：趨勢偏空。建議保守觀望，等待股價重新站回月線再行佈局。"
        adv_color = "#00c853" # 綠
    else:
        advice = "綜合研判：區間震盪。目前多空拉鋸，建議在月線與季線之間區間操作。"
        adv_color = "#ffff00" # 黃

    # 組合 HTML
    html_report = f"""
    <div class="glass-container">
        <h3>📊 武吉拉深度完整分析</h3>
        <p><b>1. 趨勢結構：</b><br>{trend_html}</p>
        <p><b>2. 籌碼解讀：</b><br>{inst_html}</p>
        <p><b>3. 關鍵指標：</b><br>{tech_html}</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.2rem; font-weight: bold; color: {adv_color} !important;">
            💡 {advice}
        </p>
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
    stock = yf.Ticker(target)
    df = stock.history(period="6mo")
    
    if df.empty:
        st.error(f"找不到 {target} 的資料，請確認代號。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 抓取法人 (強化版)
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
        
        # K 線圖 (文字強制白色)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.2, 0.3], vertical_spacing=0.03)
        
        # K線
        fig.add_trace(go.Candlestick(x=df.index.strftime('%Y-%m-%d'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#ff4b4b', decreasing_line_color='#00c853'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA5'], line=dict(color='#2962ff', width=1), name='MA5'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA20'], line=dict(color='#ff6d00', width=1), name='MA20'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['MA60'], line=dict(color='#ffd600', width=1), name='MA60'), row=1, col=1)
        
        # 成交量
        colors = ['#ff4b4b' if r['Open'] < r['Close'] else '#00c853' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index.strftime('%Y-%m-%d'), y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        # KD
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['K'], line=dict(color='#2962ff', width=1), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index.strftime('%Y-%m-%d'), y=df['D'], line=dict(color='#ff6d00', width=1), name='D9'), row=3, col=1)
        
        # 圖表版面設定 (強制字體白色)
        fig.update_layout(
            template="plotly_dark",
            height=800,
            xaxis_rangeslider_visible=False,
            xaxis3_rangeslider_visible=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            font=dict(color='white') # 全域字體白色
        )
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
                    template="plotly_dark", 
                    height=300, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    xaxis=dict(autorange="reversed"),
                    font=dict(color='white')
                )
                st.plotly_chart(fig_inst, use_container_width=True)

except Exception as e:
    st.error(f"系統忙碌中，請稍後再試: {e}")
