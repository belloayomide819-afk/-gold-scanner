import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Set up the page to look good on a mobile phone
st.set_page_config(page_title="XAUUSD Edge Scanner", page_icon="🎯", layout="centered")

st.title("🎯 XAUUSD Edge Scanner")
st.write("Liquidity Sweep & Trend Bounce Strategy")

# Sidebar for Manual Timeframes
st.sidebar.header("Manual Settings")
manual_tf = st.sidebar.selectbox("Select Timeframe", ["15m", "1h"])

def get_signal(timeframe):
    # Map timeframe for Yahoo Finance (GC=F is Gold Futures, highly accurate)
    interval = "15m" if timeframe == "15m" else "1h"
    
    # Fetch Data
    df = yf.download("GC=F", period="5d", interval=interval, progress=False)
    
    if df.empty:
        return None
        
    # Calculate Indicators
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    # Find Liquidity (Recent Swings)
    recent_low = df['Low'].rolling(window=20).min().iloc[-1]
    recent_high = df['High'].rolling(window=20).max().iloc[-1]
    
    latest = df.iloc[-1]
    current_price = float(latest['Close'])
    rsi = float(latest['RSI'])
    ema50 = float(latest['EMA50'])
    ema200 = float(latest['EMA200'])
    atr = float(latest['ATR'])
    
    # Logic
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # Buy Edge
    if current_price <= (recent_low + (atr * 0.5)) and ema50 > ema200 and rsi < 45:
        signal = "BUY"
        entry = current_price
        sl = entry - (atr * 1.5)
        tp = entry + (atr * 3.0)
        reason = "Price at Liquidity Support, Trend is UP (EMA50>200), RSI is low."
        
    # Sell Edge
    elif current_price >= (recent_high - (atr * 0.5)) and ema50 < ema200 and rsi > 55:
        signal = "SELL"
        entry = current_price
        sl = entry + (atr * 1.5)
        tp = entry - (atr * 3.0)
        reason = "Price at Liquidity Resistance, Trend is DOWN (EMA50<200), RSI is high."
        
    else:
        reason = "Price is in the middle of the range. No clear Edge."

    return {
        "price": current_price,
        "low": recent_low,
        "high": recent_high,
        "rsi": rsi,
        "signal": signal,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "reason": reason
    }

# --- UI LAYOUT ---
col1, col2, col3 = st.columns(3)

with col1:
    scalp_btn = st.button("⚡ Scalp (15m)", use_container_width=True)
with col2:
    intra_btn = st.button("☀️ Intraday (1H)", use_container_width=True)
with col3:
    manual_btn = st.button("⚙️ Manual", use_container_width=True)

selected_tf = None
if scalp_btn: selected_tf = "15m"
elif intra_btn: selected_tf = "1h"
elif manual_btn: selected_tf = manual_tf

if selected_tf:
    with st.spinner(f"Scanning XAUUSD {selected_tf} for Liquidity..."):
        result = get_signal(selected_tf)
        
    if result:
        st.subheader(f"Results for {selected_tf}")
        st.write(f"**Current Live Price:** ${result['price']:.2f}")
        st.write(f"**Liquidity Support:** ${result['low']:.2f} | **Resistance:** ${result['high']:.2f}")
        
        if result['signal'] == "BUY":
            st.success("🔥 **BUY SIGNAL DETECTED**")
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f}")
            st.write(f"**Take Profit:** {result['tp']:.2f}")
            st.info(f"**Why?** {result['reason']}")
            
        elif result['signal'] == "SELL":
            st.error("🔥 **SELL SIGNAL DETECTED**")
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f}")
            st.write(f"**Take Profit:** {result['tp']:.2f}")
            st.info(f"**Why?** {result['reason']}")
            
        else:
            st.warning("⏳ **NO SIGNAL - WAIT**")
            st.write(f"**Reason:** {result['reason']}")
    else:
        st.error("Could not fetch data. Please try again.")
