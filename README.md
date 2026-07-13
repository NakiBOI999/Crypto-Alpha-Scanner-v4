# 🚀 Vibe Trading Pro: Adaptive Crypto Scanner & Paper Trader

A professional, 24/7 autonomous crypto trading system that scans **ALL Bybit pairs**, paper trades with 10x leverage, and adapts to market conditions.

## ✨ Key Features

### 🔄 Continuous Background Scanning
- **Runs 24/7** even when you're not using the app
- Scans **ALL Bybit USDT perpetual pairs** (no limits)
- Auto-scans every **5 minutes**
- Manual "Scan Now" button for immediate triggers

### 📊 Live Market Data
- Real-time prices: BTC, ETH, XRP, SOL
- Fear & Greed Index (1-100)
- Bitcoin Market Dominance
- All data from free public APIs (no keys required)

### 🤖 Paper Trading Engine
- Simulates 10x leverage trades
- Automatic Stop-Loss and Take-Profit execution
- Logs every trade with detailed reasoning
- Tracks win rate, PnL, and daily growth

### 🧠 Adaptive Learning
- Analyzes closed trades to identify flaws
- Suggests strategy improvements
- Prevents strategy decay over time
- Tracks worst-performing symbols

### 🎨 Professional Design
- Dark trading terminal theme
- Custom CSS for modern UI
- Color-coded signals (GREEN = LONG, RED = SHORT)
- Responsive layout for all devices

## 🚀 Deployment

### Streamlit Community Cloud (Recommended)
1. Push this code to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Click "New app" and select your repository
4. Main file path: `app.py`
5. Click "Deploy"

Your app will run 24/7 in the cloud!

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
