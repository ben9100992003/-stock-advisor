import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import os
import requests
from FinMind.data import DataLoader
import xml.etree.ElementTree as ET 

# --- 0. 設定與金鑰 ---
# 設定頁面資訊 (必須是第一行 Streamlit 指令)
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. Session State (自選股管理) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["2330.TW", "NVDA", "2317.TW"] # 預設自選股

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "2330.TW"

def add_to_watchlist():
    ticker = st.session_state.current_ticker
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
        st.toast(f"✅ 已將 {ticker} 加入自選股！")

def remove_from_watchlist(ticker_to_remove):
    if ticker_to_remove in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker_to_remove)
        st.toast(f"🗑️ 已移除 {ticker_to_remove}")

# --- 2. CSS 樣式 (視覺核心修復) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_png_as_page_bg(png_file):
    # 預設深色背景，避免圖片載入失敗時全白刺眼
    if not os.path.exists(png_file): 
        st.markdown('<style>.stApp {background-color: #1a1a1a;}</style>', unsafe_allow_html=True)
        return
        
    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str: return
    
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 設定背景圖
set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png')

st.markdown("""
    <style>
    /* --- 1. 全局強制黑字 --- */
    .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, span, li, div {
        text-shadow: none !important;
    }
    
    /* 除了主標題外，所有內容文字強制黑色 */
    .stMarkdown p, .stMarkdown li, .stMarkdown span, .stDataFrame, .stTable {
        color: #000000 !important;
    }
    
    /* --- 2. 卡片系統 --- */
    .content-card, .quote-card, .kd-card, .market-summary-box {
        background-color: #ffffff !important;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: 1px solid #e0e0e0;
    }

    /* --- 3. 橫向滑動週期選單 (手機優化) --- */
    [data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 8px;
        padding-bottom: 5px;
        -webkit-overflow-scrolling: touch;
    }
    [data-testid="stRadio"] label {
        background-color: #f0f0f0 !important;
        color: #333 !important;
        border: 1px solid #ccc;
        border-radius: 20px;
        padding: 6px 14px !important;
        min-width: 50px;
        text-align: center;
        margin-right: 0 !important;
        white-space: nowrap;
        cursor: pointer;
    }
    [data-testid="stRadio"] label[data-checked="true"] {
        background-color: #222 !important;
        border-color: #FFD700 !important;
    }
    [data-testid="stRadio"] label[data-checked="true"] p {
        color: #FFD700 !important;
    }
    [data-testid="stRadio"] label p {
        font-weight: bold !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
    }

    /* --- 4. 輸入框與按鈕 --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 10px;
        font-weight: bold;
    }
    .stTextInput label, .stSelectbox label {
        color: #ffffff !important;
        font-weight: bold;
        text-shadow: 1px 1px 2px #000;
    }
    button[kind="secondary"] {
        background-color: #fff !important;
        color: #000 !important;
        border: 1px solid #ccc !important;
    }

    /* --- 5. 圖表修復 --- */
    /* 強制 Plotly 背景為白，避免透明 */
    .js-plotly-plot .plotly .main-svg {
        background: #ffffff !important;
        border-radius: 8px;
    }
    
    /* --- 6. 其他細節 --- */
    .price-big { font-size: 3rem !important; font-weight: 800; line-height: 1; margin: 10px 0; }
    .stock-title { font-size: 1.4rem; font-weight: 900; color: #000; }
    .stock-id { font-size: 1rem; color: #666 !important; }
    h1 { color: #FFFFFF !important; text-shadow: 2px 2px 4px #000; font-weight: 900; text-align: center; }
    
    /* Tab 標籤 */
    .stTabs [aria-selected="true"] {
        background-color: #fff !important;
        border-radius: 20px;
    }
    .stTabs [aria-selected="true"] p { color: #000 !important; }
    .stTabs [aria-selected="false"] p { color: #fff !important; opacity: 0.9; }
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心功能函式 ---

@st.cache_data(ttl=300)
def resolve_ticker_and_info(user_input):
    """
    智慧搜尋：
    1. 輸入數字 -> 嘗試 .TW (上市) -> 失敗嘗試 .TWO (上櫃)
    2. 輸入英文 -> 嘗試美股
    回傳: (ticker, info_dict) 或 (None, None)
    """
    user_input = user_input.strip().upper()
    
    # 狀況 A: 純數字 (假設是台股)
    if user_input.isdigit():
        # 1. 嘗試上市
        ticker_tw = f"{user_input}.TW"
        try:
            stock = yf.Ticker(ticker_tw)
            hist = stock.history(period="1d")
            if not hist.empty:
                return ticker_tw, stock.info
        except: pass
        
        # 2. 嘗試上櫃
        ticker_two = f"{user_input}.TWO"
        try:
            stock = yf.Ticker(ticker_two)
            hist = stock.history(period="1d")
            if not hist.empty:
                return ticker_two, stock.info
        except: pass
        
        return None, None

    # 狀況 B: 英文/混雜 (假設是美股或已帶後綴)
    else:
        # 如果使用者自己打了 .TW 或 .TWO，直接用
        if ".TW" in user_input or ".TWO" in user_input:
            target = user_input
        else:
            target = user_input # 假設美股

        try:
            stock = yf.Ticker(target)
            hist = stock.history(period="1d")
            if not hist.empty:
                return target, stock.info
        except: pass
        
        return None, None

@st.cache_data(ttl=300)
def get_institutional_data(ticker):
    """取得法人資料 (FinMind 優先，Yahoo 備援)"""
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split(".")[0]
    
    # 1. FinMind
    try:
        dl = DataLoader(token=FINMIND_API_TOKEN)
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if not df.empty:
            def normalize_name(n):
                if '外資' in n or 'Foreign' in n: return 'Foreign'
                if '投信' in n or 'Trust' in n: return 'Trust'
                if '自營' in n or 'Dealer' in n: return 'Dealer'
                return 'Other'
            df['norm_name'] = df['name'].apply(normalize_name)
            df['net'] = df['buy'] - df['sell']
            pivot = df.pivot_table(index='date', columns='norm_name', values='net', aggfunc='sum').fillna(0)
            pivot = (pivot / 1000).astype(int) # 轉張數
            pivot = pivot.reset_index().rename(columns={'date': 'Date'})
            pivot['Date'] = pd.to_datetime(pivot['Date']).dt.strftime('%Y/%m/%d')
            return pivot.sort_values('Date', ascending=False)
    except: pass
    
    # 2. Yahoo (備援)
    try:
        url = f"https://tw.stock.yahoo.com/quote/{ticker}/institutional-trading"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        dfs = pd.read_html(r.text)
        target_df = dfs[0] # 通常是第一個
        # 簡單處理欄位
        target_df.columns = [str(c) for c in target_df.columns]
        # 尋找關鍵字
        cols = target_df.columns
        date_col = next((c for c in cols if '日期' in c), None)
        foreign_col = next((c for c in cols if '外資' in c), None)
        trust_col = next((c for c in cols if '投信' in c), None)
        dealer_col = next((c for c in cols if '自營' in c), None)
        
        if date_col and foreign_col:
            res = pd.DataFrame()
            res['Date'] = target_df[date_col]
            
            def clean_num(x):
                if isinstance(x, str):
                    return int(x.replace(',','').replace('+',''))
                return x
            
            res['Foreign'] = target_df[foreign_col].apply(clean_num)
            res['Trust'] = target_df[trust_col].apply(clean_num) if trust_col else 0
            res['Dealer'] = target_df[dealer_col].apply(clean_num) if dealer_col else 0
            # 日期處理
            res['Date'] = res['Date'].apply(lambda x: f"{datetime.now().year}/{x}" if len(str(x)) <= 5 else x)
            return res.head(30)
    except: pass
    
    return None

def calculate_indicators(df):
    if len(df) < 20: return df
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    # KD
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def generate_report(name, ticker, latest, df, info):
    price = latest['Close']
    ma5, ma20 = latest.get('MA5', price), latest.get('MA20', price)
    k, d = latest.get('K', 50), latest.get('D', 50)
    
    # 判斷
    tech_trend = "偏多" if price > ma20 else "偏空"
    kd_sig = "黃金交叉 (看漲)" if k > d else "死亡交叉 (看跌)"
    
    # 建議
    if price > ma20 and k > d:
        action = "🟢 偏多操作"
        entry = f"拉回 5日線 {ma5:.1f} 不破可進場"
    elif price < ma20 and k < d:
        action = "🔴 保守觀望"
        entry = f"需站回月線 {ma20:.1f} 再觀察"
    else:
        action = "🟡 區間震盪"
        entry = "箱型操作，低買高賣"

    summary = info.get('longBusinessSummary', '暫無資料')[:100] + "..."
    
    return f"""
    <div class="content-card">
        <h3>📊 {name} 分析報告</h3>
        <p><b>{info.get('sector', '產業')}</b>：{summary}</p>
        <hr>
        <h4>技術面分析</h4>
        <ul>
            <li><b>趨勢：</b>股價 {tech_trend} (收盤 {price:.2f})</li>
            <li><b>KD指標：</b>K={k:.1f}, D={d:.1f} -> <b>{kd_sig}</b></li>
        </ul>
        <h4>💡 操作建議：{action}</h4>
        <p>{entry}</p>
    </div>
    """

def analyze_index(symbol, name):
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="5d")
        if h.empty: return None
        last = h.iloc[-1]
        prev = h.iloc[-2]
        chg = last['Close'] - prev['Close']
        color = "#e53935" if chg > 0 else "#43a047"
        return f"<span style='color:{color}; font-weight:bold;'>{last['Close']:.0f} ({chg:+.0f})</span>"
    except: return "N/A"

# --- 4. UI 主流程 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 頂部控制列 (兩欄：左邊搜尋，右邊自選)
col_search, col_watch = st.columns([2, 1])

with col_search:
    # 搜尋框
    search_query = st.text_input("🔍 搜尋股票 (輸入代號如 2330 或 NVDA)", value="")
    if st.button("搜尋 Go"):
        if search_query:
            resolved_ticker, resolved_info = resolve_ticker_and_info(search_query)
            if resolved_ticker:
                st.session_state.current_ticker = resolved_ticker
                # st.session_state.current_info = resolved_info # 避免存太大物件
            else:
                st.error(f"❌ 找不到股票：{search_query}，請確認代號。")

with col_watch:
    # 自選股下拉選單
    selected_watch = st.selectbox("⭐ 我的自選股", ["(請選擇)"] + st.session_state.watchlist)
    if selected_watch != "(請選擇)":
        st.session_state.current_ticker = selected_watch

# --- 5. 顯示股票內容 ---

target = st.session_state.current_ticker

if target:
    try:
        stock = yf.Ticker(target)
        # 抓取基本資料
        info = stock.info
        name = info.get('longName', target)
        if 'TW' in target and 'longName' in info: name = info['longName'] # 修正台股名稱
        
        # 抓取股價 (預設日線)
        df = stock.history(period="1y") # 抓長一點計算均線
        
        if df.empty:
            st.warning("⚠️ 無法取得股價資料，可能代號有誤或暫停交易。")
        else:
            # 報價卡片
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change = latest['Close'] - prev['Close']
            pct = (change / prev['Close']) * 100
            color = "#e53935" if change >= 0 else "#43a047"
            arrow = "▲" if change >= 0 else "▼"
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div class="quote-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="stock-title">{name} <span class="stock-id">{target}</span></div>
                            <div class="price-big" style="color:{color};">{latest['Close']:.2f}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.5rem; font-weight:bold; color:{color};">
                                {arrow} {abs(change):.2f} ({abs(pct):.2f}%)
                            </div>
                            <div style="font-size:0.9rem; color:#666;">量: {int(latest['Volume']/1000):,} K</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                # 加入自選股按鈕
                if st.button("❤️ 加入\n自選"):
                    add_to_watchlist()
                # 移除按鈕 (只有在列表中才顯示)
                if target in st.session_state.watchlist:
                    if st.button("🗑️ 移除"):
                        remove_from_watchlist(target)

            # 分頁
            tab1, tab2, tab3 = st.tabs(["📈 K線圖", "📝 分析報告", "🏛️ 籌碼"])
            
            with tab1:
                # 週期選擇 (橫向)
                st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
                period = st.radio("週期", ["1分", "5分", "30分", "60分", "日", "週", "月"], horizontal=True, label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 根據週期抓資料
                p_map = {"1分":"1m", "5分":"5m", "30分":"30m", "60分":"60m", "日":"1d", "週":"1wk", "月":"1mo"}
                interval = p_map[period]
                
                # 調整抓取長度
                fetch_period = "2y"
                if interval in ["1m", "5m"]: fetch_period = "5d"
                elif interval in ["30m", "60m"]: fetch_period = "1mo"
                
                with st.spinner("繪製圖表中..."):
                    df_chart = stock.history(period=fetch_period, interval=interval)
                    if df_chart.empty:
                        st.error("此週期無資料")
                    else:
                        # 計算指標
                        df_chart = calculate_indicators(df_chart)
                        
                        # --- Plotly 繪圖 (修復空白問題) ---
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                        
                        # K線
                        fig.add_trace(go.Candlestick(
                            x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
                            name="K線", increasing_line_color='#e53935', decreasing_line_color='#43a047'
                        ), row=1, col=1)
                        
                        # 均線
                        if 'MA5' in df_chart.columns:
                            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='blue', width=1), name='MA5'), row=1, col=1)
                        if 'MA20' in df_chart.columns:
                            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
                            
                        # KD
                        if 'K' in df_chart.columns:
                            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['K'], line=dict(color='#e53935', width=1), name='K'), row=2, col=1)
                            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['D'], line=dict(color='#43a047', width=1), name='D'), row=2, col=1)

                        # 設定顯示範圍 (最近 60 根)
                        if len(df_chart) > 60:
                            fig.update_xaxes(range=[df_chart.index[-60], df_chart.index[-1]], row=1, col=1)

                        # 佈局設定 (關鍵修復：強制背景色)
                        fig.update_layout(
                            height=500,
                            margin=dict(l=10, r=40, t=10, b=10),
                            paper_bgcolor='rgba(255,255,255,1)', # 卡片背景
                            plot_bgcolor='rgba(255,255,255,1)',  # 圖表背景
                            showlegend=False,
                            xaxis_rangeslider_visible=False,
                            dragmode='pan',
                            hovermode='x unified'
                        )
                        # Y軸格式
                        fig.update_yaxes(showgrid=True, gridcolor='#eee', row=1, col=1)
                        fig.update_yaxes(showgrid=True, gridcolor='#eee', row=2, col=1)
                        fig.update_xaxes(showgrid=True, gridcolor='#eee', row=2, col=1)

                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

            with tab2:
                # 分析報告
                df_daily = calculate_indicators(df) # 確保用日線分析
                st.markdown(generate_report(name, target, df_daily.iloc[-1], df_daily, info), unsafe_allow_html=True)
            
            with tab3:
                # 籌碼 (僅台股)
                inst_data = get_institutional_data(target)
                if inst_data is not None:
                    st.markdown("<div class='content-card'><h3>🏛️ 三大法人 (近30日)</h3></div>", unsafe_allow_html=True)
                    st.dataframe(inst_data.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("此股票無法人籌碼資料或為美股。")

    except Exception as e:
        st.error(f"發生錯誤：{e}")

# 大盤 (Footer)
st.markdown("---")
c1, c2 = st.columns(2)
with c1: st.markdown(f"🇹🇼 加權指數: {analyze_index('^TWII', '台股')}", unsafe_allow_html=True)
with c2: st.markdown(f"🇺🇸 那斯達克: {analyze_index('^IXIC', '美股')}", unsafe_allow_html=True)


