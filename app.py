import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* 隱藏預設選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 卡片樣式 */
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* 建議卡片 */
    .recommendation-box {
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        border-left: 6px solid;
    }
    
    /* 分析報告文字 */
    .analysis-text {
        font-size: 1.1rem;
        line-height: 1.8;
        color: #e0e0e0;
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #444;
    }

    /* 分隔線 */
    hr { margin: 20px 0; border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 輔助資料與函式 ---

# 熱門交易股清單 (模擬 Top 10)
TOP_STOCKS = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2603.TW": "長榮",
    "2609.TW": "陽明",
    "3231.TW": "緯創",
    "NVDA": "NVIDIA (輝達)",
    "TSLA": "Tesla (特斯拉)",
    "AAPL": "Apple (蘋果)",
    "AMD": "AMD (超微)",
    "PLTR": "Palantir"
}

@st.cache_data(ttl=300)
def get_institutional_data(ticker):
    """抓取台灣三大法人買賣超"""
    if not FINMIND_AVAILABLE: return None
    if ".TW" not in ticker: return None 
    
    try:
        stock_id = ticker.replace(".TW", "")
        dl = DataLoader()
        df = dl.taiwan_stock_institutional_investors(
            stock_id=stock_id, 
            start_date=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
        )
        if not df.empty:
            latest_date = df['date'].max()
            today_df = df[df['date'] == latest_date]
            data = {
                'date': latest_date,
                'foreign': today_df[today_df['name'].str.contains('外資')]['buy'].sum() - today_df[today_df['name'].str.contains('外資')]['sell'].sum(),
                'trust': today_df[today_df['name'].str.contains('投信')]['buy'].sum() - today_df[today_df['name'].str.contains('投信')]['sell'].sum(),
                'dealer': today_df[today_df['name'].str.contains('自營')]['buy'].sum() - today_df[today_df['name'].str.contains('自營')]['sell'].sum(),
            }
            # 換算成張
            for k in ['foreign', 'trust', 'dealer']:
                data[k] = int(data[k] / 1000)
            return data
    except:
        return None
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

def generate_analysis_report(ticker, latest, inst_data):
    """生成詳細的文字分析報告"""
    price = latest['Close']
    report = []
    
    # 1. 均線形態分析
    ma_trend = ""
    if price > latest['MA5'] and price > latest['MA20'] and price > latest['MA60']:
        ma_trend = "呈現多頭排列，股價站穩所有均線之上，短中長期趨勢皆強勢。"
    elif price < latest['MA5'] and price < latest['MA20']:
        ma_trend = "呈現空頭排列，股價受制於短中期均線反壓，趨勢偏弱。"
    elif price > latest['MA20']:
        ma_trend = "站穩月線之上，中期趨勢有支撐，但需留意短線波動。"
    else:
        ma_trend = "跌破月線，中期趨勢轉弱，需觀察季線支撐。"
    report.append(f"【趨勢分析】：目前股價 {price:.2f}，{ma_trend}")

    # 2. KD 與 RSI 分析
    kd_status = "黃金交叉向上" if latest['K'] > latest['D'] else "死亡交叉向下"
    rsi_status = ""
    if latest['RSI'] > 70: rsi_status = "RSI 進入過熱區(>70)，留意追高風險。"
    elif latest['RSI'] < 30: rsi_status = "RSI 進入超賣區(<30)，醞釀反彈機會。"
    else: rsi_status = f"RSI 指標為 {latest['RSI']:.1f}，處於中性區間。"
    
    report.append(f"【動能指標】：KD 指標呈現{kd_status}，{rsi_status}")

    # 3. 籌碼分析 (僅台股)
    if inst_data:
        total = inst_data['foreign'] + inst_data['trust'] + inst_data['dealer']
        if total > 0:
            report.append(f"【籌碼動向】：三大法人今日合計買超 {total:,} 張，資金動能偏多。")
        else:
            report.append(f"【籌碼動向】：三大法人今日合計賣超 {abs(total):,} 張，籌碼面有調節壓力。")
    
    # 4. 總結
    if price > latest['MA20'] and latest['K'] > latest['D']:
        advice = "建議偏多操作，設好停損順勢而為。"
    elif price < latest['MA20'] and latest['K'] < latest['D']:
        advice = "建議保守觀望，等待止跌訊號。"
    else:
        advice = "建議區間操作，觀察均線支撐與壓力。"
        
    report.append(f"【武吉拉觀點】：{advice}")
    
    return "\n\n".join(report)

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty: return None, None, None, None, None

        df = calculate_technical_indicators(df)
        latest = df.iloc[-1]
        inst_data = get_institutional_data(ticker)
        
        # 嘗試獲取中文名稱
        name = TOP_STOCKS.get(ticker, stock.info.get('longName', ticker))
        
        # 生成報告
        report_text = generate_analysis_report(ticker, latest, inst_data)
        
        return latest, name, df, inst_data, report_text
    except Exception as e:
        st.error(f"錯誤: {e}")
        return None, None, None, None, None

# --- 4. 主程式介面 ---

# 側邊欄
with st.sidebar:
    st.header("🦖 武吉拉選股")
    
    # 熱門股選單
    selected_hot_stock = st.selectbox(
        "🔥 市場熱門交易 Top 10",
        options=list(TOP_STOCKS.keys()),
        format_func=lambda x: f"{x} - {TOP_STOCKS[x]}"
    )
    
    # 手動輸入框 (優先權高於選單)
    st.markdown("---")
    ticker_input = st.text_input("或輸入代號查詢", value="")
    
    # 邏輯：如果有輸入代號就用輸入的，否則用選單的
    target_ticker = ticker_input.upper() if ticker_input else selected_hot_stock
    
    # 智慧代號處理：如果是 4 位數字，自動加 .TW
    if target_ticker.isdigit() and len(target_ticker) == 4:
        target_ticker += ".TW"
        
    st.caption("資料來源: Yahoo Finance, FinMind")

# 執行分析
latest, stock_name, history_df, inst_data, report_text = analyze_stock(target_ticker)

if latest is not None:
    # --- 標題區 ---
    st.title(f"{stock_name} ({target_ticker})")
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

    # --- 互動式 K 線圖 ---
    st.subheader("📊 技術分析圖表")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=history_df.index,
        open=history_df['Open'], high=history_df['High'],
        low=history_df['Low'], close=history_df['Close'],
        name='K線'
    ))
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA5'], line=dict(color='orange', width=1), name='MA5'))
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA20'], line=dict(color='cyan', width=1), name='MA20'))
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA60'], line=dict(color='purple', width=1), name='MA60'))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
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
