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

# --- 0. 設定與金鑰 (FinMind) ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide")

# --- 2. 背景圖片與 CSS 設定 ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    if not os.path.exists(png_file): return
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

set_png_as_page_bg('bg.png')

# CSS 樣式
st.markdown("""
    <style>
    .stApp { color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 分析報告容器 */
    .glass-container {
        background-color: rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
    }
    .glass-container h3 { color: #FFD700 !important; border-bottom: 1px solid #555; padding-bottom: 10px; }
    .glass-container p, .glass-container li { color: #f0f0f0 !important; font-size: 1.15rem; line-height: 1.8; }
    
    /* 側邊欄 */
    .market-summary-box {
        padding: 15px;
        font-size: 0.9rem;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        background-color: rgba(30, 30, 30, 0.95);
        border-radius: 8px;
    }

    /* 詳細指標卡片 */
    .indicator-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        color: #000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        border: 1px solid #ccc;
    }
    .indicator-title { font-size: 0.95rem; font-weight: bold; color: #555; margin-bottom: 5px; }
    .indicator-value { font-size: 1.6rem; font-weight: 800; color: #000; }
    .indicator-tag { 
        display: inline-block; padding: 3px 10px; border-radius: 15px; 
        font-size: 0.85rem; font-weight: bold; color: white; margin-top: 5px;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; font-size: 1.1rem; font-weight: bold; text-shadow: 1px 1px 2px black;
    }
    
    /* 按鈕 */
    .stLinkButton a { background-color: #420066 !important; color: white !important; border: 1px solid #888 !important; }
    
    /* 隱藏預設 Metric */
    [data-testid="stMetric"] { display: none; }
    
    /* 標題 */
    h1, h2 { text-shadow: 2px 2px 5px #000; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料串接邏輯 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2603.TW": "長榮", "2609.TW": "陽明",
    "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金", "2382.TW": "廣達", "3231.TW": "緯創",
    "2409.TW": "友達", "3481.TW": "群創", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "2344.TW": "華邦電", "2408.TW": "南亞科", "2337.TW": "旺宏",
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
    """使用 Token 抓取 FinMind 法人資料"""
    if ".TW" not in ticker: return None
    stock_id = ticker.replace(".TW", "")
    dl = DataLoader(token=FINMIND_API_TOKEN)
    try:
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        df['net'] = df['buy'] - df['sell']
        dates = sorted(df['date'].unique())
        result_list = []
        for d in dates:
            day_df = df[df['date'] == d]
            def get_net(key):
                v = day_df[day_df['name'].str.contains(key)]['net'].sum()
                return int(v / 1000)
            result_list.append({
                'Date': d,
                'Foreign': get_net('外資'),
                'Trust': get_net('投信'),
                'Dealer': get_net('自營')
            })
        return pd.DataFrame(result_list)
    except:
        return None

@st.cache_data(ttl=300)
def get_institutional_data_yahoo(ticker):
    """Yahoo 爬蟲備援"""
    if ".TW" not in ticker: return None
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        dfs = pd.read_html(r.text)
        target_df = None
        for df in dfs:
            if any('外資' in str(c) for c in df.columns):
                target_df = df
                break
        if target_df is None: return None
        
        new_cols = {}
        for c in target_df.columns:
            s = str(c)
            if '日期' in s: new_cols[c] = 'Date'
            elif '外資' in s and '持股' not in s: new_cols[c] = 'Foreign'
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
        return df_clean.head(30)
    except:
        return None

# --- 4. 技術指標與大盤分析 ---

def calculate_indicators(df):
    # 均線
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['MA240'] = df['Close'].rolling(240).mean()
    
    # 布林通道
    df['STD'] = df['Close'].rolling(20).std()
    df['BB_UP'] = df['MA20'] + 2 * df['STD']
    df['BB_LO'] = df['MA20'] - 2 * df['STD']
    
    # 成交量均線
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    
    # KD
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # RSI
    delta = df['Close'].diff()
    u = delta.clip(lower=0)
    d = -1 * delta.clip(upper=0)
    rs = u.ewm(com=13).mean() / d.ewm(com=13).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = df['Close'].ewm(span=12).mean()
    exp26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
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
        ma20 = latest['MA20']
        k, d = latest['K'], latest['D']
        
        change = price - df['Close'].iloc[-2]
        pct = (change / df['Close'].iloc[-2]) * 100
        
        if price > ma20:
            status = "多頭強勢" if k > d else "多頭回檔"
            color = "#ff4b4b" if k > d else "#ff9100"
        else:
            status = "空方修正" if k < d else "跌深反彈"
            color = "#00c853" if k < d else "#ffff00"
            
        return {"price": price, "change": change, "pct": pct, "status": status, "color": color, "comment": f"均線{price>ma20}月線，KD{k>d}交叉"}
    except:
        return None

def generate_narrative_report(name, ticker, latest, inst_df, df):
    price = latest['Close']
    vol = latest['Volume']
    vol_ma5 = latest['VOL_MA5']
    ma5, ma10, ma20, ma60, ma120 = latest['MA5'], latest['MA10'], latest['MA20'], latest['MA60'], latest['MA120']
    k, d = latest['K'], latest['D']
    rsi = latest['RSI']
    
    # 1. 趨勢架構 (深度解析)
    trend_html = f"<b>{name} ({ticker})</b> 收盤價 <b>{price:.2f}</b>。"
    
    if price > ma5 and ma5 > ma10 and ma10 > ma20 and ma20 > ma60:
        trend_html += " 目前呈現<b>「標準多頭排列」</b>，五日、十日、月線、季線全數向上發散，股價沿五日線強勢噴出，屬於<b>「強者恆強」</b>的攻擊型態。下方均線支撐強勁，拉回皆是找買點的機會。"
    elif price < ma5 and ma5 < ma10 and ma10 < ma20 and ma20 < ma60:
        trend_html += " 目前呈現<b>「標準空頭排列」</b>，股價受制於層層均線反壓，上方套牢賣壓沈重。任何反彈至十日線或月線附近，皆容易遭遇解套賣壓，不宜貿然搶進。"
    elif price > ma20:
        trend_html += " 股價目前穩守<b>「月線 (MA20)」</b>之上，中期趨勢維持多方控盤。"
        if price < ma5:
            trend_html += " 唯短線跌破五日線，攻擊動能稍歇，需觀察是否能在十日線附近止穩，進行強勢整理後再攻。"
        else:
            trend_html += " 且短線動能充沛，隨時有機會挑戰前波高點。"
    else:
        trend_html += " 股價目前跌破<b>「月線 (MA20)」</b>，短線轉弱進入整理修正。"
        if price > ma60:
            trend_html += " 但仍力守<b>「季線 (MA60)」</b>這條生命線，長線多頭架構尚未破壞，此處可視為漲多後的良性回檔，季線附近具備強力支撐。"
        else:
            trend_html += " 且進一步跌破季線，中期趨勢有轉空疑慮，若無法在三日內站回，整理時間恐將拉長。"

    # 2. 量價結構
    vol_html = "量價方面，"
    if vol > 1.5 * vol_ma5:
        if price > df['Open'].iloc[-1]:
            vol_html += "今日呈現<b>「價漲量增」</b>，多方追價意願高，主力大舉進場，有利後市。"
        else:
            vol_html += "今日呈現<b>「爆量長黑」</b>，高檔出現大量拋售，恐有主力出貨嫌疑，需提高警覺。"
    elif vol < 0.6 * vol_ma5:
        vol_html += "今日呈現<b>「量縮整理」</b>，市場觀望氣氛濃厚，等待變盤訊號。"
    else:
        vol_html += "成交量維持常態水平，量價結構穩定。"

    # 3. 籌碼面解讀
    inst_html = "籌碼方面，"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        total = last['Foreign'] + last['Trust'] + last['Dealer']
        f_val = last['Foreign']
        t_val = last['Trust']
        
        buy_sell_text = "買超" if total > 0 else "賣超"
        color_style = "#ff4b4b" if total > 0 else "#00c853"
        
        inst_html += f"外資、投信、自營商合計<span style='color:{color_style}'><b>{buy_sell_text} {abs(total):,} 張</b></span>。"
        if f_val > 2000: inst_html += " 其中<b>外資</b>大舉買進，顯示國際資金對後市看法樂觀。"
        elif f_val < -2000: inst_html += " 唯<b>外資</b>站在賣方調節，需留意提款壓力。"
        
        if t_val > 500: inst_html += " <b>投信</b>買盤積極，籌碼趨於集中，有利於股價穩定。"
    else:
        inst_html += "暫無最新法人數據。"

    # 4. 技術指標
    tech_html = f"指標方面，KD ({k:.1f}, {d:.1f}) "
    if k > d:
        tech_html += "呈現<b>「黃金交叉」</b>，短線動能轉強。"
        if k < 20: tech_html += " 且位於低檔超賣區交叉，為強力的<b>底部反轉訊號</b>。"
    else:
        tech_html += "呈現<b>「死亡交叉」</b>，短線動能轉弱。"
        if k > 80: tech_html += " 且位於高檔鈍化區交叉向下，需提防<b>假突破真拉回</b>。"

    # 5. 綜合建議
    advice = ""
    adv_color = "#ffffff"
    if price > ma20 and k > d:
        advice = "趨勢偏多。技術面與籌碼面皆有利，建議順勢操作，沿五日線持有。"
        adv_color = "#ff4b4b"
    elif price < ma20 and k < d:
        advice = "趨勢偏空。短線轉弱，建議保守觀望，等待重新站回月線再佈局。"
        adv_color = "#00c853"
    else:
        advice = "區間震盪。多空拉鋸中，建議在季線與月線之間進行區間操作。"
        adv_color = "#ffff00"

    return f"""
    <div class="glass-container">
        <h3>📊 武吉拉深度完整分析</h3>
        <p><b>1. 趨勢結構：</b><br>{trend_html}</p>
        <p><b>2. 量價分析：</b><br>{vol_html}</p>
        <p><b>3. 籌碼解讀：</b><br>{inst_html}</p>
        <p><b>4. 關鍵指標：</b><br>{tech_html}</p>
        <hr style="border-top: 1px dashed #aaa;">
        <p style="font-size: 1.3rem; font-weight: bold; color: {adv_color};">💡 建議：{advice}</p>
    </div>
    """

# --- 6. UI 介面 ---

with st.sidebar:
    st.header("🦖 武吉拉選股")
    
    # K 線週期選擇
    interval_map = {"日K": "1d", "週K": "1wk", "月K": "1mo", "60分": "60m", "30分": "30m", "15分": "15m", "5分": "5m"}
    selected_interval_label = st.radio("K 線週期", list(interval_map.keys()), horizontal=True)
    interval = interval_map[selected_interval_label]
    data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "60d" # 分時資料限制

    with st.spinner("掃描熱門股..."):
        hot_list = get_top_volume_stocks()
    
    all_hot = hot_list + ["NVDA", "TSLA", "AAPL", "AMD", "PLTR"]
    opts = [f"{STOCK_NAMES.get(t, t)} ({t})" for t in all_hot]
    sel_opt = st.selectbox("🔥 熱門成交 Top 15", options=opts)
    sel_ticker = sel_opt.split("(")[-1].replace(")", "")
    
    st.markdown("---")
    
    # 大盤分析
    st.subheader("🌍 每日大盤")
    t1, t2 = st.tabs(["🇹🇼 台股", "🇺🇸 美股"])
    with t1:
        tw = analyze_market_index("^TWII")
        if tw: st.markdown(f"<div class='market-summary-box'><div style='color:{tw['color']};font-weight:bold;font-size:1.2rem'>{tw['price']:.0f} ({tw['change']:+.0f})</div><div>{tw['status']}</div></div>", unsafe_allow_html=True)
    with t2:
        us = analyze_market_index("^IXIC")
        if us: st.markdown(f"<div class='market-summary-box' style='border-left:4px solid #00BFFF'><div style='color:{us['color']};font-weight:bold;font-size:1.2rem'>{us['price']:.0f} ({us['change']:+.0f})</div><div>{us['status']}</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    user_in = st.text_input("輸入代號", value="")
    target = user_in.upper() if user_in else sel_ticker
    if target.isdigit(): target += ".TW"
    st.link_button(f"前往 Yahoo ({target})", f"https://tw.stock.yahoo.com/quote/{target}")

try:
    stock = yf.Ticker(target)
    df = stock.history(period=data_period, interval=interval)
    
    if df.empty:
        st.error(f"找不到 {target} 的資料。")
    else:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        name = STOCK_NAMES.get(target, stock.info.get('longName', target))
        
        # 抓取法人
        inst_df = get_institutional_data_finmind(target)
        if inst_df is None and ".TW" in target: inst_df = get_institutional_data_yahoo(target)
        
        # 標題
        chg = latest['Close'] - df['Close'].iloc[-2]
        pct = (chg / df['Close'].iloc[-2]) * 100
        color = "#ff4b4b" if chg >= 0 else "#00c853"
        st.markdown(f"<h1 style='text-shadow:2px 2px 4px black'>{name} ({target})</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{color};text-shadow:1px 1px 2px black'>{latest['Close']:.2f} <small>({chg:+.2f} / {pct:+.2f}%)</small></h2>", unsafe_allow_html=True)
        
        # 報告
        st.markdown(generate_narrative_report(name, target, latest, inst_df, df), unsafe_allow_html=True)
        
        # --- 旗艦級 K 線圖 (Yahoo 風格) ---
        # 設定三層子圖：價(60%)、量(20%)、KD(20%)
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.02, 
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=("", "", "")
        )
        
        # 1. 主圖：K線 + 6條均線
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
            name='K線', increasing_line_color='#ff0000', decreasing_line_color='#009900'
        ), row=1, col=1)
        
        # Yahoo 風格均線配色
        ma_colors = {
            'MA5': '#0099FF',   # 藍
            'MA10': '#9933FF',  # 紫
            'MA20': '#FF9900',  # 橘
            'MA60': '#FFCC00',  # 黃/綠
            'MA120': '#996633', # 褐
            'MA240': '#808080'  # 灰
        }
        
        for ma, color in ma_colors.items():
            if ma in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[ma], 
                    line=dict(color=color, width=1.2), 
                    name=f'{ma}'
                ), row=1, col=1)

        # 2. 副圖一：成交量
        colors_vol = ['#ff0000' if r['Open'] < r['Close'] else '#009900' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], 
            marker_color=colors_vol, name='成交量'
        ), row=2, col=1)

        # 3. 副圖二：KD 指標
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#0099FF', width=1.2), name='K9'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#FF9900', width=1.2), name='D9'), row=3, col=1)
        
        # 設定範圍按鈕 (Range Selector) - 仿 Yahoo 快捷鍵
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=3, label="3月", step="month", stepmode="backward"),
                    dict(count=6, label="半年", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all", label="全部")
                ]),
                font=dict(color="black"),
                bgcolor="#f0f0f0"
            ),
            row=1, col=1
        )
        
        # 版面設定 (白底黑字)
        fig.update_layout(
            template="plotly_white",
            height=900, 
            xaxis_rangeslider_visible=False,
            xaxis3_rangeslider_visible=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(color='black')),
            margin=dict(l=50, r=20, t=30, b=50),
            font=dict(color='black')
        )
        
        # 加強網格線
        grid_style = dict(showgrid=True, gridcolor='#eeeeee', gridwidth=1)
        fig.update_xaxes(**grid_style)
        fig.update_yaxes(**grid_style)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 詳細指標卡片 ---
        st.subheader("📊 詳細指標解讀")
        c1, c2, c3, c4 = st.columns(4)
        
        def indicator_box(title, value, condition, good_text, bad_text, neutral_text="中性"):
            color = "#ff4b4b" if condition == "good" else "#00c853" if condition == "bad" else "#888"
            text = good_text if condition == "good" else bad_text if condition == "bad" else neutral_text
            return f"""
            <div class="indicator-card" style="border-top: 5px solid {color};">
                <div class="indicator-title">{title}</div>
                <div class="indicator-value">{value}</div>
                <div class="indicator-tag" style="background-color:{color};">{text}</div>
            </div>
            """

        with c1:
            cond = "good" if latest['K'] > latest['D'] else "bad"
            st.markdown(indicator_box("KD 指標", f"{latest['K']:.1f}", cond, "黃金交叉 🟢", "死亡交叉 🔴"), unsafe_allow_html=True)
        with c2:
            cond = "bad" if latest['RSI'] > 70 else "good" if latest['RSI'] < 30 else "neutral"
            st.markdown(indicator_box("RSI 強弱", f"{latest['RSI']:.1f}", cond, "超賣反彈 🟢", "超買警戒 🔴"), unsafe_allow_html=True)
        with c3:
            cond = "good" if latest['MACD'] > latest['Signal'] else "bad"
            st.markdown(indicator_box("MACD", f"{latest['MACD']:.2f}", cond, "多方控盤 🟢", "空方控盤 🔴"), unsafe_allow_html=True)
        with c4:
            cond = "good" if latest['Close'] > latest['MA20'] else "bad"
            st.markdown(indicator_box("月線乖離", f"{(latest['Close']-latest['MA20']):.1f}", cond, "站上月線 🟢", "跌破月線 🔴"), unsafe_allow_html=True)

        # 法人圖表
        if inst_df is not None and not inst_df.empty:
            st.subheader("🏛️ 法人籌碼 (近60日)")
            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資', marker_color='#2980b9'))
            fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信', marker_color='#8e44ad'))
            fig_inst.update_layout(barmode='group', template="plotly_white", height=300, xaxis=dict(autorange="reversed"), font=dict(color='black'))
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            st.info(f"⚠️ 無法取得法人資料 (FinMind/Yahoo 皆無數據，可能是非台股或資料源暫時異常)")

except Exception as e:
    st.error(f"發生錯誤: {e}")
