import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
import time
import threading
from datetime import datetime
import os

# ==========================================
# CUSTOM CSS FOR PROFESSIONAL TRADING TERMINAL
# ==========================================
st.markdown("""
<style>
    /* Dark trading terminal theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        color: #e0e6ed;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
    }
    
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2.5rem !important;
        margin: 0 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #3b82f6;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #3b82f6 !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
    }
    
    /* Success/Warning/Info boxes */
    .stSuccess {
        background: linear-gradient(135deg, #064e3b 0%, #10b981 100%) !important;
        border: 2px solid #10b981 !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #78350f 0%, #f59e0b 100%) !important;
        border: 2px solid #f59e0b !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        border: 2px solid #3b82f6 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 2px solid #3b82f6;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #3b82f6 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6) !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        background: #1e293b !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATA FETCHING MODULE
# ==========================================
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        return int(data['data'][0]['value']), data['data'][0]['value_classification']
    except Exception as e:
        print(f"Fear & Greed API Error: {e}")
        return 50, "Neutral"

def get_btc_dominance():
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['data']['market_cap_percentage']['btc'])
    except Exception as e:
        print(f"BTC Dominance API Error: {e}")
        return 50.0

def get_bybit_tickers():
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['retCode'] == 0:
            return {item['symbol']: item for item in data['result']['list']}
        return {}
    except Exception as e:
        print(f"Bybit Tickers API Error: {e}")
        return {}

def get_klines(symbol, interval="60", limit="100"):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['retCode'] == 0:
            df = pd.DataFrame(data['result']['list'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df = df.astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Klines API Error for {symbol}: {e}")
        return pd.DataFrame()

# ==========================================
# 2. TECHNICAL ANALYSIS MODULE
# ==========================================
def calculate_ta(df):
    if df.empty or len(df) < 50:
        return None
    
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def evaluate_signal(df, symbol, btc_dom, fg_index):
    if df is None or len(df) < 50:
        return None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    reasoning = []
    score = 0
    
    # Trend Analysis
    if last['EMA_20'] > last['EMA_50'] and prev['EMA_20'] <= prev['EMA_50']:
        score += 2
        reasoning.append("Bullish EMA crossover")
    elif last['EMA_20'] < last['EMA_50'] and prev['EMA_20'] >= prev['EMA_50']:
        score -= 2
        reasoning.append("Bearish EMA crossover")
        
    # RSI
    if last['RSI'] < 30:
        score += 1
        reasoning.append("RSI oversold")
    elif last['RSI'] > 70:
        score -= 1
        reasoning.append("RSI overbought")
        
    # MACD
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 1
        reasoning.append("Bullish MACD crossover")
    elif last['MACD'] < last['Signal'] and prev['MACD'] >= prev['Signal']:
        score -= 1
        reasoning.append("Bearish MACD crossover")
        
    # Volume Spike
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    if last['volume'] > avg_vol * 2.5:
        reasoning.append("Volume spike (Whale Activity)")
        score += 1 if score > 0 else -1
        
    # Market Context
    if fg_index < 25 and score > 0:
        score += 1
        reasoning.append("Extreme fear contrarian long")
    elif fg_index > 75 and score < 0:
        score += 1
        reasoning.append("Extreme greed contrarian short")
        
    if btc_dom > 54 and score > 0:
        reasoning.append("High BTC dominance supports long")
    elif btc_dom < 40 and score > 0 and symbol != "BTCUSDT":
        score -= 1
        reasoning.append("Low BTC dominance altcoin risk")
        
    signal = "NEUTRAL"
    if score >= 3:
        signal = "LONG"
    elif score <= -3:
        signal = "SHORT"
        
    return {
        "symbol": symbol,
        "signal": signal,
        "score": score,
        "price": last['close'],
        "rsi": round(last['RSI'], 2),
        "reasoning": "; ".join(reasoning)
    }

# ==========================================
# 3. DATABASE MODULE
# ==========================================
DB_NAME = "paper_trading.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symbol TEXT, side TEXT, entry_price REAL, 
                  stop_loss REAL, take_profit REAL, amount REAL,
                  leverage INTEGER, reasoning TEXT, status TEXT,
                  exit_price REAL, pnl REAL, entry_time TEXT, exit_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scan_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symbol TEXT, signal TEXT, score INTEGER, price REAL,
                  rsi REAL, reasoning TEXT, scan_time TEXT)''')
    conn.commit()
    conn.close()

def log_trade(symbol, side, entry_price, stop_loss, take_profit, amount, leverage, reasoning):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    entry_time = datetime.now().isoformat()
    c.execute('''INSERT INTO trades (symbol, side, entry_price, stop_loss, take_profit, amount, leverage, reasoning, status, entry_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (symbol, side, entry_price, stop_loss, take_profit, amount, leverage, reasoning, "OPEN", entry_time))
    conn.commit()
    conn.close()

def update_trade(trade_id, exit_price, pnl, status="CLOSED"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    exit_time = datetime.now().isoformat()
    c.execute('''UPDATE trades SET exit_price=?, pnl=?, status=?, exit_time=? WHERE id=?''',
              (exit_price, pnl, status, exit_time, trade_id))
    conn.commit()
    conn.close()

def get_trades():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY entry_time DESC", conn)
    conn.close()
    return df

def save_scan_result(symbol, signal, score, price, rsi, reasoning):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    scan_time = datetime.now().isoformat()
    c.execute('''INSERT INTO scan_results (symbol, signal, score, price, rsi, reasoning, scan_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (symbol, signal, score, price, rsi, reasoning, scan_time))
    conn.commit()
    conn.close()

def get_latest_scan_results():
    conn = sqlite3.connect(DB_NAME)
    # Get the most recent scan for each symbol
    df = pd.read_sql_query("""
        SELECT * FROM scan_results 
        WHERE scan_time = (SELECT MAX(scan_time) FROM scan_results)
        ORDER BY score DESC
    """, conn)
    conn.close()
    return df

def check_open_positions(current_prices):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, symbol, side, entry_price, stop_loss, take_profit, amount, leverage FROM trades WHERE status = 'OPEN'")
    open_trades = c.fetchall()
    conn.close()
    
    for trade in open_trades:
        trade_id, symbol, side, entry_price, sl, tp, amount, leverage = trade
        current_price = current_prices.get(symbol, entry_price)
        
        if side == "LONG":
            if current_price <= sl or current_price >= tp:
                pnl = amount * ((current_price - entry_price) / entry_price) * leverage
                update_trade(trade_id, current_price, pnl, "CLOSED")
        elif side == "SHORT":
            if current_price >= sl or current_price <= tp:
                pnl = amount * ((entry_price - current_price) / entry_price) * leverage
                update_trade(trade_id, current_price, pnl, "CLOSED")

# ==========================================
# 4. BACKGROUND SCANNER & TRADER
# ==========================================
def run_full_scan():
    """Runs a complete scan of all Bybit pairs and logs results"""
    print(f"[{datetime.now()}] Starting full market scan...")
    
    tickers = get_bybit_tickers()
    fg, fg_class = get_fear_and_greed()
    btc_dom = get_btc_dominance()
    
    # Get all USDT pairs
    all_symbols = [k for k in tickers.keys() if k.endswith('USDT')]
    
    print(f"Scanning {len(all_symbols)} Bybit pairs...")
    
    # Clear previous scan results
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM scan_results")
    conn.commit()
    conn.close()
    
    scan_count = 0
    for symbol in all_symbols:
        df = get_klines(symbol, interval="60", limit="100")
        if not df.empty:
            df_ta = calculate_ta(df)
            signal_data = evaluate_signal(df_ta, symbol, btc_dom, fg)
            if signal_data and signal_data['signal'] != "NEUTRAL":
                save_scan_result(
                    signal_data['symbol'],
                    signal_data['signal'],
                    signal_data['score'],
                    signal_data['price'],
                    signal_data['rsi'],
                    signal_data['reasoning']
                )
                scan_count += 1
    
    print(f"[{datetime.now()}] Scan complete. Found {scan_count} signals.")
    return scan_count

def background_scanner(interval_minutes=5):
    """Runs the scanner every X minutes in the background"""
    while True:
        try:
            run_full_scan()
        except Exception as e:
            print(f"Background scanner error: {e}")
        time.sleep(interval_minutes * 60)

def start_background_scanner():
    """Start the background scanner thread if not already running"""
    if 'scanner_thread' not in st.session_state or not st.session_state.scanner_thread.is_alive():
        st.session_state.scanner_thread = threading.Thread(target=background_scanner, args=(5,), daemon=True)
        st.session_state.scanner_thread.start()
        print("Background scanner started")

# ==========================================
# 5. ADAPTIVE LEARNING MODULE
# ==========================================
def generate_adaptive_report():
    df = get_trades()
    if df.empty or len(df) < 5:
        return "📊 **Not enough data**: Need at least 5 closed trades to generate an adaptive report."
    
    closed_df = df[df['status'] == 'CLOSED']
    if closed_df.empty:
        return "📊 **No closed trades yet** to analyze."
    
    win_rate = len(closed_df[closed_df['pnl'] > 0]) / len(closed_df) * 100
    avg_win = closed_df[closed_df['pnl'] > 0]['pnl'].mean() if len(closed_df[closed_df['pnl'] > 0]) > 0 else 0
    avg_loss = closed_df[closed_df['pnl'] < 0]['pnl'].mean() if len(closed_df[closed_df['pnl'] < 0]) > 0 else 0
    net_pnl = closed_df['pnl'].sum()
    
    if len(closed_df) > 1:
        first_trade_date = pd.to_datetime(closed_df['entry_time'].iloc[-1])
        last_trade_date = pd.to_datetime(closed_df['entry_time'].iloc[0])
        days_elapsed = max((last_trade_date - first_trade_date).days, 1)
        daily_growth_pct = (net_pnl / 10000) / days_elapsed * 100 
    else:
        daily_growth_pct = 0.0

    flaws = []
    if win_rate < 80:
        flaws.append(f"⚠️ Win rate is {win_rate:.1f}% (Target: 80%+). Consider tightening entry criteria.")
    if avg_loss < 0 and abs(avg_loss) > (avg_win * 0.8):
        flaws.append("⚠️ Average loss is dangerously close to average win. Tighten Stop-Loss.")
    
    worst_symbol = closed_df.groupby('symbol')['pnl'].sum().idxmin()
    worst_pnl = closed_df.groupby('symbol')['pnl'].sum().min()
    if worst_pnl < -50:
        flaws.append(f"⚠️ Symbol **{worst_symbol}** showing consistent losses (${worst_pnl:.2f}).")

    report = f"""
    ### 🧠 Adaptive Performance Report
    - **Total Closed Trades**: {len(closed_df)}
    - **Win Rate**: {win_rate:.2f}% *(Goal: 80%+)*
    - **Average Win**: ${avg_win:.2f} | **Average Loss**: ${avg_loss:.2f}
    - **Net PnL**: ${net_pnl:.2f}
    - **Estimated Daily Growth**: {daily_growth_pct:.2f}% *(Goal: 1%)*
    
    ### 🔍 Identified Flaws:
    {chr(10).join(flaws) if flaws else '✅ No major flaws detected.'}
    """
    return report

# ==========================================
# 6. STREAMLIT APP UI
# ==========================================
st.set_page_config(page_title="Vibe Trading Pro", layout="wide", page_icon="🚀")

# Initialize
init_db()
start_background_scanner()

# Session State
if 'scanner_enabled' not in st.session_state:
    st.session_state.scanner_enabled = True
if 'auto_trader_enabled' not in st.session_state:
    st.session_state.auto_trader_enabled = False
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 10000.0
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

# Header
st.markdown('<div class="main-header"><h1>🚀 Vibe Trading Pro</h1><p style="color: #cbd5e1; font-size: 1.1rem; margin-top: 0.5rem;">Adaptive Crypto Scanner & Paper Trader | Scanning ALL Bybit Pairs</p></div>', unsafe_allow_html=True)

# Live Price Feed
col1, col2, col3, col4, col5, col6 = st.columns(6)

try:
    tickers = get_bybit_tickers()
    fg, fg_class = get_fear_and_greed()
    btc_dom = get_btc_dominance()
    
    btc_price = float(tickers.get('BTCUSDT', {}).get('lastPrice', 0))
    eth_price = float(tickers.get('ETHUSDT', {}).get('lastPrice', 0))
    xrp_price = float(tickers.get('XRPUSDT', {}).get('lastPrice', 0))
    sol_price = float(tickers.get('SOLUSDT', {}).get('lastPrice', 0))
    
    col1.metric("BTC", f"${btc_price:,.2f}" if btc_price > 0 else "N/A")
    col2.metric("ETH", f"${eth_price:,.2f}" if eth_price > 0 else "N/A")
    col3.metric("XRP", f"${xrp_price:,.4f}" if xrp_price > 0 else "N/A")
    col4.metric("SOL", f"${sol_price:,.2f}" if sol_price > 0 else "N/A")
    col5.metric("Fear & Greed", f"{fg} ({fg_class})")
    col6.metric("BTC Dominance", f"{btc_dom:.2f}%")
except Exception as e:
    st.error(f"Error fetching live data: {e}")

st.markdown("---")

# Sidebar Controls
st.sidebar.header("⚙️ Control Panel")
st.session_state.scanner_enabled = st.sidebar.toggle("🔍 Auto Scanner (Every 5 min)", value=st.session_state.scanner_enabled)
st.session_state.auto_trader_enabled = st.sidebar.toggle("🤖 Auto Paper Trader", value=st.session_state.auto_trader_enabled)

st.sidebar.markdown("### Account Settings")
st.session_state.account_balance = st.sidebar.number_input("Starting Balance (USD)", value=st.session_state.account_balance, step=1000.0)
leverage = st.sidebar.selectbox("Leverage", [1, 3, 5, 10, 20], index=3)
risk_per_trade = st.sidebar.slider("Risk per Trade (%)", 1, 5, 2)

if st.sidebar.button("🔄 Manual Scan Now"):
    with st.spinner("Running manual scan of all Bybit pairs..."):
        signals_found = run_full_scan()
        st.session_state.last_scan_time = datetime.now()
        st.success(f"✅ Scan complete! Found {signals_found} trade signals.")
        st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Live Scanner", "📊 Paper Trading", "🧠 Adaptive Reports"])

with tab1:
    st.header("Live Market Scanner")
    
    if st.session_state.last_scan_time:
        st.info(f"🕐 Last scan: {st.session_state.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')} | Next auto-scan in ~5 minutes")
    
    scan_df = get_latest_scan_results()
    
    if not scan_df.empty:
        st.subheader(f"✅ {len(scan_df)} Trade Opportunities Found")
        
        # Display LONG signals
        long_signals = scan_df[scan_df['signal'] == 'LONG']
        if not long_signals.empty:
            st.markdown("### 🟢 LONG Signals")
            st.dataframe(long_signals, use_container_width=True)
        
        # Display SHORT signals
        short_signals = scan_df[scan_df['signal'] == 'SHORT']
        if not short_signals.empty:
            st.markdown("### 🔴 SHORT Signals")
            st.dataframe(short_signals, use_container_width=True)
    else:
        st.info("📡 No signals found yet. The scanner runs automatically every 5 minutes, or click 'Manual Scan Now' in the sidebar.")

with tab2:
    st.header("Paper Trading Dashboard")
    
    if st.session_state.auto_trader_enabled:
        st.success("🟢 Auto Trader ACTIVE")
        tickers = get_bybit_tickers()
        current_prices = {k: float(v['lastPrice']) for k, v in tickers.items()}
        check_open_positions(current_prices)
    else:
        st.warning("🔴 Auto Trader OFF")

    st.subheader("Open Positions")
    trades_df = get_trades()
    open_positions = trades_df[trades_df['status'] == 'OPEN']
    if not open_positions.empty:
        st.dataframe(open_positions, use_container_width=True)
    else:
        st.info("No open positions.")
        
    st.subheader("Trade History")
    st.dataframe(trades_df, use_container_width=True)
    
    csv = trades_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Trade Log (CSV)", csv, "trade_log.csv", "text/csv")

with tab3:
    st.header("Adaptive Reasoning & Strategy Improvement")
    
    report = generate_adaptive_report()
    st.markdown(report)
    
    st.subheader("System Status")
    st.markdown(f"""
    - **Background Scanner**: {'🟢 Running' if 'scanner_thread' in st.session_state and st.session_state.scanner_thread.is_alive() else '🔴 Stopped'}
    - **Scanning Interval**: Every 5 minutes
    - **Total Bybit Pairs**: {len([k for k in get_bybit_tickers().keys() if k.endswith('USDT')])}
    - **Database**: {DB_NAME}
    """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b;'>Built for continuous 24/7 operation | All data from Bybit, CoinGecko, Alternative.me</p>", unsafe_allow_html=True)
