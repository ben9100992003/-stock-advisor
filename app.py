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
st.set_page_config(
    page_title="武吉拉 Wujila", 
    page_icon="🦖", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS 樣式 ---
def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except Exception as e:
        st.warning(f"無法載入背景圖片: {e}")
    return ""

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    if bin_str:
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.3);
            pointer-events: none;
            z-index: 0;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)

# 嘗試載入背景圖片（如果不存在也不會報錯）
set_png_as_page_bg('/images/Gemini.jpg')

st.markdown("""
    <style>
    /* 全局設定 */
    .stApp { 
        color: #000000; 
        font-family: "Microsoft JhengHei", "PingFang TC", "Helvetica Neue", sans-serif; 
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 白色卡片容器 */
    .white-card {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        position: relative;
        z-index: 1;
    }
    
    .white-card * {
        color: #000000 !important;
    }

    /* 搜尋框 */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #FFD700 !important;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
        padding: 10px;
    }
    
    .stTextInput label {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000;
        font-weight: bold;
        font-size: 1.2rem;
    }

    /* 股票標題區 */
    .stock-header { 
        display: flex; 
        justify-content: space-between; 
        align-items: baseline; 
        border-bottom: 2px solid #f0f0f0; 
        padding-bottom: 10px; 
        margin-bottom: 15px; 
    }
    
    .stock-title { 
        font-size: 1.8rem !important; 
        font-weight: 900 !important; 
        margin: 0; 
        color: #000 !important;
    }
    
    .stock-id { 
        font-size: 1.1rem !important; 
        color: #666 !important; 
        font-weight: normal; 
    }
    
    .price-big { 
        font-size: 3.5rem !important; 
        font-weight: 800 !important; 
        line-height: 1.2; 
        margin: 10px 0;
    }
    
    /* 統計數據網格 */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px 20px;
        border-top: 1px solid #f0f0f0;
        padding-top: 15px;
        margin-top: 15px;
    }
    
    .stat-row { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }
    
    .stat-lbl { 
        color: #666 !important; 
        font-size: 0.95rem !important; 
    }
    
    .stat-val { 
        color: #000 !important; 
        font-weight: bold !important; 
        font-size: 1.1rem !important; 
    }

    /* Radio 按鈕橫向滾動 */
    div[data-testid="stHorizontalBlock"] {
        overflow-x: auto !important;
        overflow-y: hidden !important;
        white-space: nowrap !important;
        -webkit-overflow-scrolling: touch;
        padding: 5px 0;
    }
    
    div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {
        height: 6px;
    }
    
    div[data-testid="stHorizontalBlock"]::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    div[data-testid="stHorizontalBlock"]::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }

    /* Radio 選項樣式 */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 10px !important;
        background-color: #f8f9fa !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    
    div[role="radiogroup"] label {
        flex: 0 0 auto !important;
        min-width: 60px !important;
        text-align: center !important;
        padding: 8px 16px !important;
        border-radius: 20px !important;
        background-color: #ffffff !important;
        border: 2px solid #e0e0e0 !important;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    div[role="radiogroup"] label:hover {
        border-color: #FFD700 !important;
        transform: translateY(-2px);
    }
    
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #000000 !important;
        border-color: #000000 !important;
    }
    
    div[role="radiogroup"] label[data-checked="true"] p {
        color: #ffffff !important;
    }
    
    div[role="radiogroup"] label p {
        color: #333 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
    }

    /* 圖表容器 */
    .chart-box {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #e0e0e0;
    }

    /* 主標題 */
    h1 { 
        text-shadow: 3px 3px 8px #000; 
        color: white !important; 
        margin-bottom: 20px; 
        text-align: center; 
        font-weight: 900;
        font-size: 3rem !important;
    }
    
    /* 隱藏 Streamlit 預設元素 */
    [data-testid="stMetric"] { display: none; }
    
    /* Spinner 樣式 */
    .stSpinner > div {
        border-top-color: #FFD700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 資料處理函數 ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", 
    "2603.TW": "長榮", "2609.TW": "陽明", "3231.TW": "緯創", 
    "2303.TW": "聯電", "2881.TW": "富邦金", "2882.TW": "國泰金",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微"
}

@st.cache_data(ttl=300, show_spinner=False)
def resolve_ticker(user_input):
    """解析股票代號"""
    try:
        user_input = user_input.strip().upper()
        
        # 如果是純數字，嘗試台股
        if user_input.isdigit():
            # 優先嘗試上市 (.TW)
            ticker_tw = f"{user_input}.TW"
            try:
                stock = yf.Ticker(ticker_tw)
                hist = stock.history(period="1d")
                if not hist.empty:
                    name = stock.info.get('longName', STOCK_NAMES.get(ticker_tw, ticker_tw))
                    return ticker_tw, name
            except:
                pass
            
            # 再嘗試上櫃 (.TWO)
            ticker_two = f"{user_input}.TWO"
            try:
                stock = yf.Ticker(ticker_two)
                hist = stock.history(period="1d")
                if not hist.empty:
                    name = stock.info.get('longName', STOCK_NAMES.get(ticker_two, ticker_two))
                    return ticker_two, name
            except:
                pass
        else:
            # 美股或其他市場
            try:
                stock = yf.Ticker(user_input)
                hist = stock.history(period="1d")
                if not hist.empty:
                    name = stock.info.get('longName', STOCK_NAMES.get(user_input, user_input))
                    return user_input, name
            except:
                pass
        
        return None, None
    except Exception as e:
        st.error(f"解析代號時發生錯誤: {e}")
        return None, None

def calculate_indicators(df):
    """計算技術指標"""
    try:
        # 移動平均線
        df['MA5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        df['MA10'] = df['Close'].rolling(window=10, min_periods=1).mean()
        df['MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        
        # KD 指標
        low_min = df['Low'].rolling(window=9, min_periods=1).min()
        high_max = df['High'].rolling(window=9, min_periods=1).max()
        
        # 避免除以零
        denominator = high_max - low_min
        denominator = denominator.replace(0, np.nan)
        
        df['RSV'] = 100 * (df['Close'] - low_min) / denominator
        df['RSV'] = df['RSV'].fillna(50)  # 填充 NaN 值
        
        df['K'] = df['RSV'].ewm(com=2, adjust=False).mean()
        df['D'] = df['K'].ewm(com=2, adjust=False).mean()
        
        return df
    except Exception as e:
        st.error(f"計算指標時發生錯誤: {e}")
        return df

def generate_report_html(name, ticker, latest):
    """生成分析報告"""
    try:
        price = latest['Close']
        ma20 = latest.get('MA20', price)
        k = latest.get('K', 50)
        d = latest.get('D', 50)
        
        trend = "多頭" if price > ma20 else "空頭"
        kd_stat = "黃金交叉" if k > d else "死亡交叉"
        suggestion = "偏多操作，可考慮逢低買進" if (price > ma20 and k > d) else "保守觀望，等待明確訊號"
        
        return f"""
        <div class="white-card">
            <h3 style="border-bottom:2px solid #FFD700; padding-bottom:8px; margin-bottom:15px; font-size:1.4rem; font-weight:bold; color:#000 !important;">📊 技術分析報告</h3>
            <p style="margin:10px 0; line-height:1.8; color:#000 !important;"><b>趨勢判斷：</b>{trend}格局 (股價相對月線位置)</p>
            <p style="margin:10px 0; line-height:1.8; color:#000 !important;"><b>KD 指標：</b>K值 {k:.1f} / D值 {d:.1f}，呈現 <b>{kd_stat}</b></p>
            <p style="margin:10px 0; line-height:1.8; color:#000 !important;"><b>操作建議：</b>{suggestion}</p>
            <p style="margin-top:15px; padding-top:10px; border-top:1px solid #f0f0f0; font-size:0.85rem; color:#999 !important;">
                ⚠️ 本報告僅供參考，投資有風險，請謹慎評估
            </p>
        </div>
        """
    except Exception as e:
        return f'<div class="white-card"><p style="color:#000 !important;">無法生成報告: {e}</p></div>'

# --- 4. 主程式介面 ---

st.markdown("<h1>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 初始化 session state
if 'target_input' not in st.session_state:
    st.session_state.target_input = "2330"

# 搜尋框
target_input = st.text_input(
    "🔍 輸入股票代號", 
    value=st.session_state.target_input,
    placeholder="例如: 2330, 2454, NVDA, AAPL",
    help="台股請輸入4位數代號，美股請輸入英文代號"
)

if target_input:
    st.session_state.target_input = target_input
    
    with st.spinner("🔍 搜尋股票資料中..."):
        target, name = resolve_ticker(target_input)
        
        if not target:
            st.error("❌ 找不到此股票代號，請確認輸入是否正確")
            st.info("💡 提示：台股請輸入4位數代號（如：2330），美股請輸入英文代號（如：AAPL）")
            st.stop()
else:
    target, name = "2330.TW", "台積電"

try:
    # 獲取股票資料
    stock = yf.Ticker(target)
    
    # 獲取即時報價資料
    with st.spinner("📊 載入報價資料..."):
        df_fast = stock.history(period="5d")
        
        if df_fast.empty:
            st.error("❌ 無法獲取股票資料，請稍後再試")
            st.stop()
        
        latest_fast = df_fast.iloc[-1]
        
        # 計算漲跌
        if len(df_fast) >= 2:
            prev = df_fast['Close'].iloc[-2]
        else:
            prev = latest_fast['Close']
        
        price = latest_fast['Close']
        chg = price - prev
        pct = (chg / prev) * 100 if prev != 0 else 0
        
        # 顏色設定（紅漲綠跌）
        color = "#e53935" if chg >= 0 else "#43a047"
        arrow = "▲" if chg >= 0 else "▼"
        
        # 報價卡片
        st.markdown(f"""
        <div class="white-card">
            <div class="stock-header">
                <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
            </div>
            <div style="display:flex; align-items:baseline; gap:15px; margin-bottom:20px;">
                <div class="price-big" style="color:{color}">{price:.2f}</div>
                <div style="color:{color}; font-weight:bold; font-size:1.3rem;">
                    {arrow} {abs(chg):.2f} ({abs(pct):.2f}%)
                </div>
            </div>
            <div class="stats-grid">
                <div class="stat-row">
                    <span class="stat-lbl">最高</span>
                    <span class="stat-val" style="color:#e53935">{latest_fast['High']:.2f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-lbl">最低</span>
                    <span class="stat-val" style="color:#43a047">{latest_fast['Low']:.2f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-lbl">昨收</span>
                    <span class="stat-val">{prev:.2f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-lbl">開盤</span>
                    <span class="stat-val">{latest_fast['Open']:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 週期選單
    st.markdown('<div class="white-card" style="padding:15px;">', unsafe_allow_html=True)
    
    period_map = {
        "1分": "1m",
        "5分": "5m", 
        "15分": "15m",
        "30分": "30m",
        "60分": "60m",
        "日線": "1d",
        "週線": "1wk",
        "月線": "1mo"
    }
    
    period_label = st.radio(
        "選擇時間週期",
        list(period_map.keys()),
        horizontal=True,
        label_visibility="collapsed",
        index=5  # 預設選擇「日線」
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 獲取歷史資料
    interval = period_map[period_label]
    
    # 根據週期設定資料範圍
    if interval in ["1m", "5m"]:
        data_period = "5d"
    elif interval in ["15m", "30m", "60m"]:
        data_period = "60d"
    elif interval == "1d":
        data_period = "2y"
    elif interval == "1wk":
        data_period = "5y"
    else:  # 1mo
        data_period = "10y"
    
    with st.spinner(f"📈 載入 {period_label} K線資料..."):
        df = stock.history(period=data_period, interval=interval)
        
        if df.empty:
            st.warning(f"⚠️ 此週期（{period_label}）暫無資料")
            st.stop()
        
        # 計算技術指標
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        # K線圖
        st.markdown('<div class="white-card chart-box">', unsafe_allow_html=True)
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2],
            vertical_spacing=0.02,
            subplot_titles=("", "", "")
        )
        
        # 1. K線圖 + 均線
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="K線",
                increasing_line_color='#e53935',
                decreasing_line_color='#43a047',
                increasing_fillcolor='#e53935',
                decreasing_fillcolor='#43a047'
            ),
            row=1, col=1
        )
        
        # 均線
        ma_configs = [
            ('MA5', '#2962ff', '5日線'),
            ('MA10', '#aa00ff', '10日線'),
            ('MA20', '#ff6d00', '20日線')
        ]
        
        for ma, color, label in ma_configs:
            if ma in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[ma],
                        line=dict(color=color, width=1.5),
                        name=label
                    ),
                    row=1, col=1
                )
        
        # 2. 成交量
        colors = ['#e53935' if row['Close'] >= row['Open'] else '#43a047' 
                  for _, row in df.iterrows()]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                marker_color=colors,
                name='成交量',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 3. KD 指標
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['K'],
                line=dict(color='#2962ff', width=1.5),
                name='K值'
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['D'],
                line=dict(color='#ff6d00', width=1.5),
                name='D值'
            ),
            row=3, col=1
        )
        
        # 添加 KD 超買超賣線
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        
        # 設定顯示範圍（最近 60 根 K 棒）
        if len(df) > 60:
            fig.update_xaxes(range=[df.index[-60], df.index[-1]], row=1, col=1)
        
        # 圖表樣式
        fig.update_layout(
            height=700,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x unified',
            dragmode='pan',
            xaxis_rangeslider_visible=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 十字線
        for row_num in [1, 2, 3]:
            fig.update_xaxes(
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                spikedash='dot',
                spikecolor="#999",
                spikethickness=1,
                row=row_num,
                col=1
            )
            fig.update_yaxes(
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                spikedash='dot',
                spikecolor="#999",
                spikethickness=1,
                row=row_num,
                col=1
            )
        
        # 網格線
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
        
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'scrollZoom': True,
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            }
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 分析報告
        st.markdown(generate_report_html(name, target, latest), unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ 發生錯誤: {str(e)}")
    st.info("💡 請嘗試重新整理頁面或更換股票代號")
    
    # 顯示詳細錯誤訊息（開發時使用）
    with st.expander("🔧 詳細錯誤資訊"):
        st.code(str(e))
