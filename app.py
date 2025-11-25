import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 加入防呆機制：嘗試匯入 FinMind ---
try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    print("警告: 無法匯入 FinMind，將暫停法人數據功能。")
except Exception as e:
    FINMIND_AVAILABLE = False
    print(f"警告: FinMind 載入發生錯誤: {e}")

# --- 1. 頁面設定 (必須在第一行) ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide")

# --- 2. 專業級 CSS 樣式 ---
st.markdown("""
    <style>
    /* 全局背景與字體 */
    .stApp {
        background-image: url('uploaded:image_d78e10.png-c6800a35-e7d2-451a-a124-fd5f3dd563fc');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #ffffff;
    }
    
    /* 隱藏預設選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 卡片樣式 - 使用半透明背景 */
    .metric-card {
        background-color: rgba(30, 30, 30, 0.8);
        border: 1px solid rgba(51, 51, 51, 0.8);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* 建議卡片 - 使用半透明背景 */
    .recommendation-box {
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        border-left: 6px solid;
        background-color: rgba(28, 28, 28, 0.8);
    }
    
    /* 分析報告文字區域 - 使用半透明背景 */
    .analysis-text {
        font-size: 1.1rem;
        line-height: 1.8;
        color: #ffffff !important; /* 強制白色 */
        background-color: rgba(38, 39, 48, 0.8);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(68, 68, 68, 0.8);
    }

    /* 強制 Tab 標籤與說明文字為白色 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: bold;
    }
    .stMarkdown p, .stCaption {
        color: #e0e0e0 !important;
    }

    /* 分隔線 */
    hr { margin: 20px 0; border-color: rgba(51, 51, 51, 0.8); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 輔助資料與函式 ---

# 熱門交易股清單
TOP_STOCKS = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2603.TW": "長榮",
    "2609.TW": "陽明",
    "3231.TW": "緯創",
    "2454.TW": "聯發科",
    "NVDA": "NVIDIA (輝達)",
    "TSLA": "Tesla (特斯拉)",
    "AAPL": "Apple (蘋果)",
    "AMD": "AMD (超微)"
}

@st.cache_data(ttl=300)
def get_institutional_data(ticker):
    """抓取台灣三大法人買賣超 (修正 0 資料問題)"""
    if not FINMIND_AVAILABLE: return None
    if ".TW" not in ticker: return None 
    
    try:
        stock_id = ticker.replace(".TW", "")
        dl = DataLoader()
        # 抓取最近 30 天數據，確保能回溯
        df = dl.taiwan_stock_institutional_investors(
            stock_id=stock_id, 
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )
        
        if df.empty: return None

        # 將日期排序，從最新開始找
        dates = df['date'].unique()
        dates.sort()
        dates = dates[::-1] # 反轉，最新在最前

        # 迴圈尋找有數據的最近一天
        for target_date in dates:
            today_df = df[df['date'] == target_date]
            
            # 計算買賣超
            f_buy = today_df[today_df['name'].str.contains('外資')]['buy'].sum() - today_df[today_df['name'].str.contains('外資')]['sell'].sum()
            t_buy = today_df[today_df['name'].str.contains('投信')]['buy'].sum() - today_df[today_df['name'].str.contains('投信')]['sell'].sum()
            d_buy = today_df[today_df['name'].str.contains('自營')]['buy'].sum() - today_df[today_df['name'].str.contains('自營')]['sell'].sum()
            
            # 如果這一天所有法人數據都是 0，可能是有問題或休市，繼續找前一天
            if f_buy == 0 and t_buy == 0 and d_buy == 0:
                continue
            
            # 找到有意義的數據了
            data = {
                'date': target_date,
                'foreign': int(f_buy / 1000),
                'trust': int(t_buy / 1000),
                'dealer': int(d_buy / 1000),
            }
            return data
            
        return None # 真的都沒資料
    except:
        return None

def calculate_technical_indicators(df):
    """計算技術指標"""
    # 均線
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # KD
    df['9_High'] = df['High'].rolling(9).max()
    df['9_Low'] = df['Low'].rolling(9).min()
    df['RSV'] = 100 * (df['Close'] - df['9_Low']) / (df['9_High'] - df['9_Low'])
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # RSI (14日)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def generate_analysis_report(ticker, latest, inst_data, history_df):
    """生成詳細的文字分析報告"""
    price = latest['Close']
    vol = latest['Volume']
    report = []
    
    # 1. 價量分析
    report.append(f"【價量概況】：收盤價 {price:.2f}，成交量 {int(vol/1000):,} 張。")
    recent_high = history_df['High'].tail(20).max()
    recent_low = history_df['Low'].tail(20).min()
    report.append(f"近20日區間：高點 {recent_high:.2f} / 低點 {recent_low:.2f}。")

    # 2. 籌碼分析 (詳細列出)
    if inst_data:
        f_buy = inst_data['foreign']
        t_buy = inst_data['trust']
        d_buy = inst_data['dealer']
        total = f_buy + t_buy + d_buy
        
        inst_text = f"外資 {'買超' if f_buy>0 else '賣超'} {abs(f_buy):,} 張，" \
                    f"投信 {'買超' if t_buy>0 else '賣超'} {abs(t_buy):,} 張，" \
                    f"自營 {'買超' if d_buy>0 else '賣超'} {abs(d_buy):,} 張。"
        report.append(f"【法人動向】：{inst_text} (合計 {total:,} 張 / 資料日期: {inst_data['date']})")
    else:
        report.append("【法人動向】：暫無資料 (僅台股提供，或資料源連線中)。")

    # 3. 技術指標 (KD/均線)
    ma_trend = "多頭排列 (站上月線)" if price > latest['MA20'] else "空頭修正 (跌破月線)"
    kd_val = f"K({latest['K']:.1f}) / D({latest['D']:.1f})"
    kd_sig = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
    report.append(f"【技術指標】：均線呈{ma_trend}。KD指標為 {kd_val}，呈現{kd_sig}。")

    # 4. 進出場建議 (簡單邏輯)
    support = latest['MA20'] if price > latest['MA20'] else recent_low
    resistance = recent_high if price > latest['MA20'] else latest['MA20']
    
    if price > latest['MA20'] and latest['K'] > latest['D']:
        strategy = f"偏多操作。建議防守支撐 {support:.2f}，目標前高 {recent_high:.2f}。"
    elif price < latest['MA20'] and latest['K'] < latest['D']:
        strategy = f"偏空觀望。上方壓力 {resistance:.2f}，需等待止跌訊號。"
    else:
        strategy = f"區間震盪。建議在 {support:.2f} ~ {resistance:.2f} 區間來回操作。"
        
    report.append(f"【操作建議】：{strategy}")
    
    return "\n\n".join(report)

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty: return None, None, None, None, None

        df = calculate_technical_indicators(df)
        latest = df.iloc[-1]
        inst_data = get_institutional_data(ticker)
        
        name = TOP_STOCKS.get(ticker, stock.info.get('longName', ticker))
        
        report_text = generate_analysis_report(ticker, latest, inst_data, df)
        
        return latest, name, df, inst_data, report_text
    except Exception as e:
        st.error(f"錯誤: {e}")
        return None, None, None, None, None

# --- 4. 主程式介面 ---

# 側邊欄
with st.sidebar:
    st.header("🦖 武吉拉選股")
    selected_hot_stock = st.selectbox(
        "🔥 市場熱門交易 Top 10",
        options=list(TOP_STOCKS.keys()),
        format_func=lambda x: f"{x} - {TOP_STOCKS[x]}"
    )
    st.markdown("---")
    ticker_input = st.text_input("或輸入代號查詢", value="")
    
    target_ticker = ticker_input.upper() if ticker_input else selected_hot_stock
    if target_ticker.isdigit() and len(target_ticker) == 4:
        target_ticker += ".TW"
        
    st.caption("資料來源: Yahoo Finance, FinMind")
    
    # Yahoo 連結按鈕 (側邊欄)
    yahoo_url = f"https://tw.stock.yahoo.com/quote/{target_ticker}"
    st.link_button(f"🔗 前往 Yahoo 股市 ({target_ticker})", yahoo_url, use_container_width=True)

# 執行分析
latest, stock_name, history_df, inst_data, report_text = analyze_stock(target_ticker)

if latest is not None:
    # --- 標題區 ---
    col_title, col_link = st.columns([3, 1])
    with col_title:
        st.title(f"{stock_name} ({target_ticker})")
    with col_link:
        # Yahoo 連結按鈕 (標題旁)
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("前往 Yahoo 詳細資料 ↗", f"https://tw.stock.yahoo.com/quote/{target_ticker}")

    current_price = latest['Close']
    change = current_price - history_df['Close'].iloc[-2]
    pct_change = (change / history_df['Close'].iloc[-2]) * 100
    color_css = "color: #ff4b4b;" if change >= 0 else "color: #00c853;" 
    
    st.markdown(f"""
        <div style="font-size: 3rem; font-weight: bold; {color_css}">
            {current_price:.2f} 
            <span style="font-size: 1.5rem;">
                {change:+.2f} ({pct_change:+.2f}%)
            </span>
        </div>
    """, unsafe_allow_html=True)

    # --- 深度分析報告區塊 ---
    st.subheader("📝 武吉拉投資筆記")
    st.markdown(f"""
    <div class="analysis-text">
        {report_text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    # --- 互動式 K 線圖 (含成交量) ---
    st.subheader("📊 技術分析圖表")
    
    # 建立子圖 (上: K線, 下: 成交量)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # K線圖
    fig.add_trace(go.Candlestick(
        x=history_df.index.strftime('%Y-%m-%d'), # 轉字串以移除休市日空隙
        open=history_df['Open'], high=history_df['High'],
        low=history_df['Low'], close=history_df['Close'],
        name='K線'
    ), row=1, col=1)
    
    # 均線
    fig.add_trace(go.Scatter(x=history_df.index.strftime('%Y-%m-%d'), y=history_df['MA5'], line=dict(color='orange', width=1), name='MA5'), row=1, col=1)
    fig.add_trace(go.Scatter(x=history_df.index.strftime('%Y-%m-%d'), y=history_df['MA20'], line=dict(color='cyan', width=1), name='MA20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=history_df.index.strftime('%Y-%m-%d'), y=history_df['MA60'], line=dict(color='purple', width=1), name='MA60'), row=1, col=1)

    # 成交量圖
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in history_df.iterrows()]
    fig.add_trace(go.Bar(
        x=history_df.index.strftime('%Y-%m-%d'), 
        y=history_df['Volume'],
        marker_color=colors,
        name='成交量'
    ), row=2, col=1)

    # 設定圖表樣式
    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_rangeslider_visible=False, # 隱藏下方滑桿，改用滑鼠拖曳
        dragmode='pan', # 預設為拖曳模式
        hovermode='x unified' # 統一顯示資訊
    )
    
    # 修復 X 軸顯示
    fig.update_xaxes(type='category', tickangle=-45, nticks=20) # 使用類別軸避免日期空隙

    st.plotly_chart(fig, use_container_width=True)

    # --- 數據儀表板 ---
    tab1, tab2 = st.tabs(["📉 詳細指標", "🏛️ 法人籌碼"])
    
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("RSI (14)", f"{latest['RSI']:.1f}")
        c2.metric("K值 (9)", f"{latest['K']:.1f}")
        c3.metric("D值 (9)", f"{latest['D']:.1f}")
        c4.metric("MA20", f"{latest['MA20']:.1f}")
        c5.metric("MACD", f"{latest['MACD']:.2f}")

    with tab2:
        if inst_data:
            c1, c2, c3 = st.columns(3)
            def color_val(val): return "normal" if val > 0 else "inverse"
            c1.metric("外資", f"{inst_data['foreign']:,} 張", delta=inst_data['foreign'], delta_color=color_val(inst_data['foreign']))
            c2.metric("投信", f"{inst_data['trust']:,} 張", delta=inst_data['trust'], delta_color=color_val(inst_data['trust']))
            c3.metric("自營商", f"{inst_data['dealer']:,} 張", delta=inst_data['dealer'], delta_color=color_val(inst_data['dealer']))
            st.caption(f"資料日期: {inst_data['date']}")
        else:
            if ".TW" in target_ticker:
                if not FINMIND_AVAILABLE: st.warning("⚠️ 系統模組維護中")
                else: st.info("尚無今日法人資料 (通常於下午 3-4 點後更新)")
            else:
                st.info("美股暫不提供即時法人籌碼分析")

else:
    st.error("找不到該股票資料，請檢查代號是否正確。")
