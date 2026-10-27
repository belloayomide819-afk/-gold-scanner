import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Set up the page to look good on a mobile phone
st.set_page_config(page_title="XAUUSD Prop Scanner", page_icon="🎯", layout="centered")

st.title("🎯 XAUUSD Prop Firm Scanner")
st.write("Strategy: Liquidity Sweep + Fixed $7 SL / $20 TP")

# Sidebar for Manual Timeframes
st.sidebar.header("Manual Settings")
manual_tf = st.sidebar.selectbox("Select Timeframe", ["15m", "1h"])

def get_signal(timeframe):
    # Map timeframe for Yahoo Finance
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
    
    # Find Liquidity (Recent Swings)
    recent_low = df['Low'].rolling(window=20).min().iloc[-1]
    recent_high = df['High'].rolling(window=20).max().iloc[-1]
    
    latest = df.iloc[-1]
    current_price = float(latest['Close'].item())
    rsi = float(latest['RSI'].item())
    ema50 = float(latest['EMA50'].item())
    ema200 = float(latest['EMA200'].item())
    recent_low_val = float(recent_low.item())
    recent_high_val = float(recent_high.item())
    
    # Logic
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # PROP FIRM SETTINGS: 
    # We calculate the distance based on a standard lot (0.01 lots = $0.10 per pip)
    # For Gold: 1 point = $0.10 on 0.01 lot.
    # $7 SL = 70 points ($7.00 price move) on 0.01 lot
    # $20 TP = 200 points ($20.00 price move) on 0.01 lot
    sl_distance = 7.00 
    tp_distance = 20.00
    
    # Buy Edge (Price near support, uptrend, RSI low)
    if current_price <= (recent_low_val + 2.0) and ema50 > ema200 and rsi < 45:
        signal = "BUY"
        entry = current_price
        sl = entry - sl_distance
        tp = entry + tp_distance
        reason = f"Price at Liquidity Support, Trend is UP. Fixed Risk $7, Reward $20."
        
    # Sell Edge (Price near resistance, downtrend, RSI high)
    elif current_price >= (recent_high_val - 2.0) and ema50 < ema200 and rsi > 55:
        signal = "SELL"
        entry = current_price
        sl = entry + sl_distance
        tp = entry - tp_distance
        reason = f"Price at Liquidity Resistance, Trend is DOWN. Fixed Risk $7, Reward $20."
        
    else:
        reason = "Price is in the middle of the range. No clear Edge."

    return {
        "price": current_price,
        "low": recent_low_val,
        "high": recent_high_val,
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
    with st.spinner(f"Scanning XAUUSD {selected_tf} for Prop Setup..."):
        result = get_signal(selected_tf)
        
    if result:
        st.subheader(f"Results for {selected_tf}")
        st.write(f"Current Live Price: ${result['price']:.2f}")
        st.write(f"Liquidity Support: ${result['low']:.2f} | Resistance: ${result['high']:.2f}")
        
        if result['signal'] == "BUY":
            st.success("🔥 **BUY SIGNAL DETECTED (PROP)**")
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f} (Risking $7)")
            st.write(f"**Take Profit:** {result['tp']:.2f} (Targeting $20)")
            st.info(f"**Why?** {result['reason']}")
            
        elif result['signal'] == "SELL":
            st.error("🔥 **SELL SIGNAL DETECTED (PROP)**")
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f} (Risking $7)")
            st.write(f"**Take Profit:** {result['tp']:.2f} (Targeting $20)")
            st.info(f"**Why?** {result['reason']}")
            
        else:
            st.warning("⏳ **NO SIGNAL - WAIT**")
            st.write(f"**Reason:** {result['reason']}")
    else:
        st.error("Could not fetch data. Please try again.")
