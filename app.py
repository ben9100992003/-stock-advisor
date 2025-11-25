import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# --- 1. 頁面設定 (必須在第一行) ---
st.set_page_config(page_title="智富羅盤 Pro", page_icon="💎", layout="wide")

# --- 2. 專業級 CSS 樣式 (讓它看起來像 App) ---
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
    .metric-label {
        color: #aaa;
        font-size: 0.8rem;
    }
    .metric-value {
        color: #fff;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    /* 建議卡片 */
    .recommendation-box {
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        border-left: 6px solid;
    }
    
    /* 分隔線 */
    hr { margin: 20px 0; border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料抓取與計算函式 ---

@st.cache_data(ttl=300) # 快取 5 分鐘，避免重複抓取
def get_institutional_data(ticker):
    """
    抓取台灣三大法人買賣超 (使用 FinMind)
    """
    if ".TW" not in ticker:
        return None # 美股暫不抓取法人
    
    try:
        stock_id = ticker.replace(".TW", "")
        dl = DataLoader()
        # 抓取最近 10 天數據
        df = dl.taiwan_stock_institutional_investors(
            stock_id=stock_id, 
            start_date=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
        )
        if not df.empty:
            # 取得最新一天的資料並加總 (因為 FinMind 分開列出 buy/sell)
            latest_date = df['date'].max()
            today_df = df[df['date'] == latest_date]
            
            # 整理三大法人
            data = {
                'date': latest_date,
                'foreign': today_df[today_df['name'].str.contains('外資')]['buy'].sum() - today_df[today_df['name'].str.contains('外資')]['sell'].sum(),
                'trust': today_df[today_df['name'].str.contains('投信')]['buy'].sum() - today_df[today_df['name'].str.contains('投信')]['sell'].sum(),
                'dealer': today_df[today_df['name'].str.contains('自營')]['buy'].sum() - today_df[today_df['name'].str.contains('自營')]['sell'].sum(),
            }
            # 單位換算成「張」
            data['foreign'] = int(data['foreign'] / 1000)
            data['trust'] = int(data['trust'] / 1000)
            data['dealer'] = int(data['dealer'] / 1000)
            return data
    except:
        return None
    return None

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 抓取 6 個月資料以計算長均線
        df = stock.history(period="6mo")
        
        if df.empty: return None, None, None

        # 計算均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean() # 月線
        df['MA60'] = df['Close'].rolling(window=60).mean() # 季線
        
        # 計算 KD
        df['9_High'] = df['High'].rolling(9).max()
        df['9_Low'] = df['Low'].rolling(9).min()
        df['RSV'] = 100 * (df['Close'] - df['9_Low']) / (df['9_High'] - df['9_Low'])
        df['K'] = df['RSV'].ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        
        latest = df.iloc[-1]
        
        # 抓取法人資料
        inst_data = get_institutional_data(ticker)
        
        return latest, stock.info, df, inst_data
    except Exception as e:
        st.error(f"錯誤: {e}")
        return None, None, None, None

# --- 4. 主程式介面 ---

# 側邊欄
with st.sidebar:
    st.header("🔍 股票代號")
    ticker_input = st.text_input("輸入代號", value="2330.TW")
    
    st.markdown("### 快速選股")
    if st.button("台積電 (2330.TW)"): ticker_input = "2330.TW"
    if st.button("長榮 (2603.TW)"): ticker_input = "2603.TW"
    if st.button("聯發科 (2454.TW)"): ticker_input = "2454.TW"
    if st.button("NVIDIA (NVDA)"): ticker_input = "NVDA"
    
    st.markdown("---")
    st.caption("資料來源: Yahoo Finance, FinMind")

# 執行分析
latest, info, history_df, inst_data = analyze_stock(ticker_input)

if latest is not None:
    # --- 標題區 ---
    st.title(f"{info.get('longName', ticker_input)}")
    current_price = latest['Close']
    change = current_price - history_df['Close'].iloc[-2]
    pct_change = (change / history_df['Close'].iloc[-2]) * 100
    
    # 顏色判斷
    color_css = "color: #ff4b4b;" if change >= 0 else "color: #00c853;" # 台股紅漲綠跌
    
    st.markdown(f"""
        <div style="font-size: 3rem; font-weight: bold; {color_css}">
            {current_price:.2f} 
            <span style="font-size: 1.5rem;">
                {change:+.2f} ({pct_change:+.2f}%)
            </span>
        </div>
    """, unsafe_allow_html=True)

    # --- 分析邏輯 ---
    score = 0
    reasons = []
    
    # 1. 均線邏輯
    if current_price > latest['MA20']:
        score += 30
        reasons.append("📈 股價站上月線 (多頭支撐)")
    else:
        reasons.append("📉 股價跌破月線 (短線轉弱)")
        
    if current_price > latest['MA60']:
        score += 20
        reasons.append("💪 股價站上季線 (長線保護)")

    # 2. KD 邏輯
    if latest['K'] > latest['D']:
        score += 20
        reasons.append("⚡ KD 黃金交叉向上")
    else:
        reasons.append("💤 KD 死亡交叉修正")
        
    # 3. 法人邏輯 (如果有資料)
    if inst_data:
        total_buy = inst_data['foreign'] + inst_data['trust']
        if total_buy > 0:
            score += 20
            reasons.append("💰 外資投信合計買超")
        else:
            reasons.append("💸 法人合計賣超調節")
    elif ".TW" in ticker_input:
        reasons.append("⚠️ 暫無今日法人數據 (盤後更新)")

    # --- 顯示 AI 建議卡片 ---
    bg_color = "rgba(40, 167, 69, 0.15)" if score >= 60 else "rgba(220, 53, 69, 0.15)"
    border_color = "#28a745" if score >= 60 else "#dc3545"
    rec_text = "強力買進" if score >= 80 else "偏多操作" if score >= 60 else "觀望整理"
    
    st.markdown(f"""
    <div class="recommendation-box" style="background-color: {bg_color}; border-color: {border_color};">
        <h2 style="margin:0; color: {border_color};">🤖 AI 綜合評價：{rec_text} (分數: {score})</h2>
        <hr style="opacity: 0.2; margin: 10px 0;">
        <ul style="font-size: 1.1rem; line-height: 1.8;">
            {''.join([f'<li>{r}</li>' for r in reasons])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- 互動式 K 線圖 (Plotly) ---
    st.subheader("📊 技術分析圖表")
    
    # 建立圖表
    fig = go.Figure()
    
    # K線
    fig.add_trace(go.Candlestick(
        x=history_df.index,
        open=history_df['Open'],
        high=history_df['High'],
        low=history_df['Low'],
        close=history_df['Close'],
        name='K線'
    ))
    
    # 均線
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA5'], line=dict(color='orange', width=1), name='MA5'))
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA20'], line=dict(color='cyan', width=1), name='MA20'))
    fig.add_trace(go.Scatter(x=history_df.index, y=history_df['MA60'], line=dict(color='purple', width=1), name='MA60'))

    # 設定圖表樣式 (黑底)
    fig.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 數據儀表板 (Tab 佈局) ---
    tab1, tab2 = st.tabs(["📉 技術指標", "🏛️ 法人籌碼"])
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("K值 (9日)", f"{latest['K']:.1f}")
        c2.metric("D值 (9日)", f"{latest['D']:.1f}")
        c3.metric("MA5", f"{latest['MA5']:.1f}")
        c4.metric("MA20", f"{latest['MA20']:.1f}")
        
    with tab2:
        if inst_data:
            c1, c2, c3 = st.columns(3)
            
            def color_val(val):
                return "normal" if val > 0 else "inverse"
                
            c1.metric("外資", f"{inst_data['foreign']:,} 張", delta=inst_data['foreign'], delta_color=color_val(inst_data['foreign']))
            c2.metric("投信", f"{inst_data['trust']:,} 張", delta=inst_data['trust'], delta_color=color_val(inst_data['trust']))
            c3.metric("自營商", f"{inst_data['dealer']:,} 張", delta=inst_data['dealer'], delta_color=color_val(inst_data['dealer']))
            
            st.caption(f"資料日期: {inst_data['date']} (盤後更新)")
        else:
            if ".TW" in ticker_input:
                st.info("尚無法人資料，可能今日尚未結算或連線逾時。")
            else:
                st.info("美股暫不提供即時法人籌碼分析。")

else:
    st.error("找不到該股票資料，請檢查代號是否正確。")
