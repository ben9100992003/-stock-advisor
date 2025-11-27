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
import xml.etree.ElementTree as ET 

# --- 0. 設定與金鑰 ---
FINMIND_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yNiAxMDo1MzoxOCIsInVzZXJfaWQiOiJiZW45MTAwOTkiLCJpcCI6IjM5LjEwLjEuMzgifQ.osRPdmmg6jV5UcHuiu2bYetrgvcTtBC4VN4zG0Ct5Ng"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="武吉拉 Wujila", page_icon="🦖", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS 樣式 ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def set_png_as_page_bg(png_file):
    if not os.path.exists(png_file): return
    bin_str = get_base64_of_bin_file(png_file)
    if not bin_str: return
    
    page_bg_img = """
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{0}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """.format(bin_str)
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 載入哥吉拉背景
set_png_as_page_bg('Gemini_Generated_Image_enh52venh52venh5.png') 

st.markdown("""
    <style>
    /* 強制文字黑色 (白底黑字核心) */
    .stApp { color: #000; font-family: "Microsoft JhengHei", sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 卡片通用設定 */
    .quote-card, .content-card, .kd-card, .market-summary-box, .chart-container {
        background-color: rgba(255, 255, 255, 0.98) !important;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* 確保所有卡片內的元素都是黑色 */
    .quote-card *, .content-card *, .kd-card *, .market-summary-box *, .chart-container * {
        color: #000 !important;
        text-shadow: none !important;
    }
    
    /* 報價卡片排版 */
    .quote-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .stock-title { font-size: 1.8rem !important; font-weight: 900 !important; margin: 0; line-height: 1.2;}
    .price-big { font-size: 4rem !important; font-weight: 800 !important; line-height: 1; letter-spacing: -1px;}
    .price-change { font-size: 1.4rem !important; font-weight: 700 !important; }
    .stats-grid {
        display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 30px;
        border-top: 1px solid #eee; padding-top: 12px;
    }

    /* 週期按鈕列 (關鍵：橫向滑動) */
    .stRadio > div {
        display: flex; flex-direction: row; gap: 5px;
        background-color: #f0f0f0; padding: 6px; border-radius: 20px;
        width: 100%; overflow-x: scroll; /* 啟用橫向滑動 */
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #eee;
    }
    .stRadio div[role="radiogroup"] > label {
        flex-shrink: 0; /* 強制不換行 */
        min-width: 50px; text-align: center; padding: 8px 0; border-radius: 15px;
        background-color: transparent;
    }
    .stRadio div[role="radiogroup"] > label p { color: #555 !important; font-weight: bold; font-size: 0.9rem; }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] { background-color: #333 !important; }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p { color: #fff !important; }

    /* K 線圖容器 */
    .chart-container { padding: 0 !important; overflow: hidden; }
    .js-plotly-plot .plotly .main-svg { background: white !important; border-radius: 12px; }
    
    /* 搜尋框 */
    .stTextInput label { color: #ffffff !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 數據與分析邏輯 (保持完整性) ---

STOCK_NAMES = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "4903.TWO": "聯光通", "8110.TW": "華東", "6187.TWO": "萬潤", "3131.TWO": "弘塑",
    "NVDA": "輝達", "TSLA": "特斯拉", "AAPL": "蘋果", "AMD": "超微", "PLTR": "Palantir",
    "MSFT": "微軟", "GOOGL": "谷歌", "AMZN": "亞馬遜", "META": "Meta", "TSM": "台積電 ADR"
}

@st.cache_data(ttl=3600)
def resolve_ticker(user_input):
    user_input = user_input.strip().upper()
    if user_input.isdigit():
        ticker_tw = f"{user_input}.TW"
        try:
            s = yf.Ticker(ticker_tw)
            if not s.history(period="1d").empty: return ticker_tw, s.info.get('longName', ticker_tw)
        except: pass
        ticker_two = f"{user_input}.TWO"
        try:
            s = yf.Ticker(ticker_two)
            if not s.history(period="1d").empty: return ticker_two, s.info.get('longName', ticker_two)
        except: pass
        return None, None
    else:
        try:
            s = yf.Ticker(user_input)
            if not s.history(period="1d").empty: return user_input, s.info.get('longName', user_input)
        except: pass
        return None, None

@st.cache_data(ttl=300)
def get_institutional_data_finmind(ticker):
    if ".TW" not in ticker and ".TWO" not in ticker: return None
    stock_id = ticker.split(".")[0]
    dl = DataLoader(token=FINMIND_API_TOKEN)
    try:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if df.empty: return None
        
        def normalize_name(n):
            if '外資' in n or 'Foreign' in n: return 'Foreign'
            if '投信' in n or 'Trust' in n: return 'Trust'
            if '自營' in n or 'Dealer' in n: return 'Dealer'
            return 'Other'
        df['norm_name'] = df['name'].apply(normalize_name)
        df['net'] = df['buy'] - df['sell']
        pivot_df = df.pivot_table(index='date', columns='norm_name', values='net', aggfunc='sum').fillna(0)
        for col in ['Foreign', 'Trust', 'Dealer']:
            if col not in pivot_df.columns: pivot_df[col] = 0
        pivot_df = (pivot_df / 1000).astype(int)
        pivot_df = pivot_df.reset_index()
        pivot_df = pivot_df.rename(columns={'date': 'Date'})
        pivot_df['Date'] = pd.to_datetime(pivot_df['Date']).dt.strftime('%Y/%m/%d')
        return pivot_df
    except Exception as e: return None

@st.cache_data(ttl=300)
def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['MA240'] = df['Close'].rolling(240).mean()
    df['VOL_MA5'] = df['Volume'].rolling(5).mean()
    low_min = df['Low'].rolling(9).min()
    high_max = df['High'].rolling(9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def generate_narrative_report(name, ticker, latest, inst_df, df, info):
    price = latest['Close']
    ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
    k, d = latest['K'], latest['D']
    
    # 1. 技術面
    tech_trend = "盤整"
    tech_desc = ""
    if price > ma5 and ma5 > ma10 and ma10 > ma20:
        tech_trend = "多頭排列"
        tech_desc = "均線結構良好，顯示股價處於健康的上漲趨勢中。"
    elif price > ma20: tech_trend = "站上月線"; tech_desc = "中期趨勢偏多，唯短線可能震盪。"
    else: tech_trend = "跌破月線"; tech_desc = "短線轉弱，需觀察季線支撐。"
    kd_status = "黃金交叉" if k > d else "死亡交叉"
    kd_desc = f"KD 指標 ({k:.1f}/{d:.1f}) 呈現 <b>{kd_status}</b>。"
    
    # 2. 籌碼面
    inst_table_html = "<tr><td colspan='4'>暫無資料</td></tr>"
    inst_desc = "暫無法人數據。"
    if inst_df is not None and not inst_df.empty:
        last = inst_df.iloc[-1]
        f_val, t_val, d_val = last['Foreign'], last['Trust'], last['Dealer']
        total = f_val + t_val + d_val
        inst_desc = f"法人單日合計 <b>{'買超' if total>0 else '賣超'} {abs(total):,} 張</b>。"
        inst_table_html = f"""
        <tr>
            <td>{last['Date']}</td>
            <td>{f_val:,}</td><td>{t_val:,}</td><td>{d_val:,}</td>
            <td><b>{total:,}</b></td>
        </tr>
        """
        
    # 3. 建議
    support = ma10 if price > ma10 else ma20
    if price > ma20 and k > d: action = "偏多操作"; entry = f"拉回至 5 日線 {ma5:.2f} 附近不破可佈局。"; exit_pt = f"跌破月線 {ma20:.2f} 嚴設停損。"
    else: action = "保守觀望"; entry = f"等待站回月線 {ma20:.2f} 再考慮進場。"; exit_pt = f"反彈至月線 {ma20:.2f} 遇壓可減碼。"

    return f"""
    <div class="content-card">
        <h3>📊 {name} ({ticker}) 綜合分析報告</h3>
        
        <h4>1. 技術指標分析</h4>
        <table class="analysis-table">
            <tr><td><b>收盤價</b></td><td>{price:.2f}</td><td><b>MA5</b></td><td>{ma5:.2f}</td></tr>
            <tr><td><b>MA20</b></td><td>{ma20:.2f}</td><td><b>KD</b></td><td>{k:.1f}/{d:.1f}</td></tr>
            <tr><td colspan="4"><b>趨勢判讀：</b>{tech_trend}。{tech_desc} {kd_desc}</td></tr>
        </table>
        
        <h4>2. 三大法人籌碼分析</h4>
        <table class="analysis-table">
            <thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營</th><th>合計</th></tr></thead>
            <tbody>{inst_table_html}</tbody>
        </table>
        <p><b>籌碼解讀：</b>{inst_desc}</p>
        
        <h4>3. 💡 進出場價格建議 ({action})</h4>
        <ul>
            <li><b>🟢 進場參考：</b>{entry}</li>
            <li><b>🔴 出場參考：</b>{exit_pt}</li>
        </ul>
    </div>
    """

# --- 5. UI 介面 ---
if 'ticker_input' not in st.session_state: st.session_state.ticker_input = "2330"
if 'target' not in st.session_state: st.session_state.target = "2330.TW"
if 'name' not in st.session_state: st.session_state.name = "台積電"
if 'current_period' not in st.session_state: st.session_state.current_period = "日"


st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 8px #000; margin-bottom: 20px;'>🦖 武吉拉 Wujila</h1>", unsafe_allow_html=True)

# 搜尋與熱門股 (卡片 A)
col_search, col_hot = st.columns([3, 1])
with col_search:
    target_input = st.text_input("🔍 搜尋代號/名稱 (如: 4903, 2330, NVDA)", value=st.session_state.ticker_input, key='main_input')
if target_input != st.session_state.ticker_input: st.session_state.ticker_input = target_input; st.session_state.update_trigger = True

with col_hot:
    if st.button("🔄 更新", use_container_width=True): st.session_state.update_trigger = True

if 'update_trigger' in st.session_state and st.session_state.update_trigger:
    with st.spinner("正在搜尋資料..."):
        resolved_ticker, resolved_name = resolve_ticker(st.session_state.ticker_input)
        if resolved_ticker:
            st.session_state.target = resolved_ticker
            st.session_state.name = resolved_name
        else:
            st.error(f"❌ 找不到股票代號：{st.session_state.ticker_input}。")
            st.session_state.target = None
    st.session_state.update_trigger = False

target = st.session_state.target
name = st.session_state.name

# K線週期設定 (卡片 C)
period_map = {"1分": "1m", "5分": "5m", "10分": "5m", "30分": "30m", "60分": "60m", "日": "1d", "週": "1wk", "月": "1mo"}
period_labels = list(period_map.keys())

st.markdown('<div class="chart-period-card">', unsafe_allow_html=True)
selected_period = st.radio("週期", period_labels, index=period_labels.index(st.session_state.current_period), horizontal=True, key='period_radio', label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.current_period != selected_period: st.session_state.current_period = selected_period

# --- 主內容執行 ---
if target:
    try:
        # 1. 抓取數據
        stock = yf.Ticker(target)
        info = stock.info
        
        interval = period_map[st.session_state.current_period]
        data_period = "2y" if interval in ["1d", "1wk", "1mo"] else "5d"
        df = stock.history(period=data_period, interval=interval)
        
        if df.empty: st.error("無歷史數據。")
        else:
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # 2. 頂部報價卡片 (卡片 B)
            prev_close = df['Close'].iloc[-2]
            price = latest['Close']
            change = price - prev_close
            pct = (change / prev_close) * 100
            color = "#e53935" if change >= 0 else "#43a047"
            arrow = "▲" if change >= 0 else "▼"
            
            st.markdown(f"""
            <div class="quote-card">
                <div class="quote-header">
                    <div class="stock-title">{name} <span class="stock-id">({target})</span></div>
                </div>
                <div class="price-container">
                    <div class="price-big" style="color:{color};">{price:.2f}</div>
                    <div class="price-change" style="color:{color};"> {arrow} {abs(change):.2f} ({abs(pct):.2f}%)</div>
                </div>
                <div class="stats-grid">
                    <div class="stat-row"><span class="stat-label">最高</span><span class="stat-val" style="color:#e53935;">{latest['High']:.2f}</span></div>
                    <div class="stat-row"><span class="stat-label">最低</span><span class="stat-val" style="color:#43a047;">{latest['Low']:.2f}</span></div>
                    <div class="stat-row"><span class="stat-label">昨收</span><span class="stat-val">{prev_close:.2f}</span></div>
                    <div class="stat-row"><span class="stat-label">開盤</span><span class="stat-val">{latest['Open']:.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 3. K 線圖與分析
            tab1, tab2, tab3, tab4 = st.tabs(["📈 K 線", "📝 分析", "🏛️ 籌碼", "📰 新聞"])
            
            with tab1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # K 線圖
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#e53935', decreasing_line_color='#43a047'), row=1, col=1)
                for ma, c in [('MA5','#1f77b4'), ('MA10','#9467bd'), ('MA20','#ff7f0e')]:
                    if ma in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=c, width=1), name=ma), row=1, col=1)
                
                colors_vol = ['#e53935' if r['Open'] < r['Close'] else '#43a047' for i, r in df.iterrows()]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='成交量'), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['K'], line=dict(color='#1f77b4', width=1.5), name='K9'), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['D'], line=dict(color='#ff7f0e', width=1.5), name='D9'), row=3, col=1)

                # 設定預設顯示範圍：最近 45 根 (放大)
                if len(df) > 45:
                    fig.update_xaxes(range=[df.index[-45], df.index[-1]], row=1, col=1)
                    
                fig.update_layout(
                    template="plotly_white", height=650, margin=dict(l=15, r=15, t=10, b=10), legend=dict(orientation="h", y=1.01, x=0),
                    dragmode='pan', hovermode='x unified', xaxis=dict(rangeslider_visible=False), yaxis=dict(fixedrange=True)
                )
                for row in [1, 2, 3]: # 十字線
                    fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="grey", spikethickness=1, rangeslider_visible=False, row=row, col=1)
                    fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=True, spikedash='dash', spikecolor="grey", spikethickness=1, row=row, col=1)
                    
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
                
                # KD 卡片 (卡片 D)
                kd_color = "#e53935" if latest['K'] > latest['D'] else "#26a69a"
                kd_text = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
                st.markdown(f"""<div class="kd-card" style="border-left: 6px solid {kd_color};"><div class="kd-title">KD 指標 (9,3,3)</div><div style="text-align:right;"><div class="kd-val">{latest['K']:.1f} / {latest['D']:.1f}</div><div class="kd-tag" style="background-color:{kd_color};">{kd_text}</div></div></div>""", unsafe_allow_html=True)

            with tab2:
                inst_df = get_institutional_data_finmind(target)
                st.markdown(generate_narrative_report(name, target, latest, inst_df, df, info), unsafe_allow_html=True)

            with tab3:
                inst_df = get_institutional_data_finmind(target)
                if inst_df is not None and not inst_df.empty:
                    st.markdown(f"<div class='content-card'><h3>🏛️ 三大法人買賣超 (近30日)</h3></div>", unsafe_allow_html=True)
                    # (圖表代碼省略，與 K 線圖類似)
                    st.dataframe(inst_df.sort_values('Date', ascending=False).head(10), use_container_width=True)
                else: st.info("無法人籌碼資料")

            with tab4:
                st.markdown("<div class='content-card'><h3>📰 個股相關新聞</h3></div>", unsafe_allow_html=True)
                news_list = get_google_news(target)
                for news in news_list:
                    st.markdown(f"<div class='news-item'><a href='{news['link']}' target='_blank'>{news['title']}</a><div class='news-meta'>{news['pubDate']} | {news['source']}</div></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"無法取得資料，請確認代號是否正確。錯誤：{e}")

