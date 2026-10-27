import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# Set up the page
st.set_page_config(page_title="London Breakout Scanner", page_icon="🇬🇧", layout="centered")

st.title("🇬🇧 London Breakout Scanner (Gold)")
st.write("Strategy: Asian Range Fakeout + Retest")

def get_signal():
    # Use Spot Gold to match MT5 closer
    ticker = "XAUUSD=X"
    interval = "15m"
    
    df = yf.download(ticker, period="5d", interval=interval, progress=False)
    
    if df.empty:
        return None
        
    # 1. Time Filter (Rule 5)
    # Get current time in Lagos/Nigeria (WAT)
    lagos_tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(lagos_tz)
    current_hour = now.hour
    
    # Only allow trading between 9:00 AM and 12:00 PM
    if current_hour < 9 or current_hour >= 12:
        return {"status": "TIME_LOCKED", "message": f"Current time is {now.strftime('%H:%M')}. You can only scan between 09:00 and 12:00 Nigeria Time."}

    # 2. Calculate Asian Box (Rule 1: 28 candles = 7 hours)
    asian_box = df.tail(28)
    box_high = float(asian_box['High'].max().item())
    box_low = float(asian_box['Low'].min().item())
    box_range = box_high - box_low
    
    latest = df.iloc[-1]
    current_price = float(latest['Close'].item())
    
    # Prop Firm Settings
    sl_distance = 7.00
    tp_distance = 20.00
    
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # 3. Rule 3 & 4 Logic
    broke_up = df['High'].iloc[-10:].max().item() > box_high
    broke_down = df['Low'].iloc[-10:].min().item() < box_low
    
    if broke_up and broke_down and current_price < box_low:
        if abs(current_price - box_low) < (box_range * 0.2):
            signal = "SELL (Retest)"
            entry = current_price
            sl = entry + sl_distance
            tp = entry - tp_distance
            reason = f"Fakeout above {box_high:.2f}, then broke down. Retesting box low for Short."
            
    elif broke_down and broke_up and current_price > box_high:
        if abs(current_price - box_high) < (box_range * 0.2):
            signal = "BUY (Retest)"
            entry = current_price
            sl = entry - sl_distance
            tp = entry + tp_distance
            reason = f"Fakeout below {box_low:.2f}, then broke up. Retesting box high for Long."
            
    else:
        reason = f"No clear setup. Box High: {box_high:.2f}, Box Low: {box_low:.2f}. Waiting for fakeout and retest."

    return {
        "status": "ACTIVE",
        "price": current_price,
        "high": box_high,
        "low": box_low,
        "signal": signal,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "reason": reason
    }

# --- UI LAYOUT ---
st.info("⏰ **Rule 5:** App will ONLY work between 09:00 - 12:00 Nigeria Time (08:00 - 11:00 UK Time).")

if st.button("🇬🇧 Scan London Breakout", use_container_width=True):
    with st.spinner("Scanning Asian Range..."):
        result = get_signal()
        
    if result:
        if result["status"] == "TIME_LOCKED":
            st.error(f"🚫 **MARKET LOCKED** \n\n{result['message']}")
        else:
            st.subheader("Asian Session Box (00:00 - 07:00 UK)")
            st.write(f"**Box High:** ${result['high']:.2f}")
            st.write(f"**Box Low:** ${result['low']:.2f}")
            st.write(f"**Current Live Price:** ${result['price']:.2f}")
            st.divider()
            
            if "BUY" in result['signal']:
                st.success(f"🔥 **{result['signal']} DETECTED**")
                st.write(f"**Entry:** {result['entry']:.2f}")
                st.write(f"**Stop Loss:** {result['sl']:.2f} (Risking $7)")
                st.write(f"**Take Profit:** {result['tp']:.2f} (Targeting $20)")
                st.info(f"**Why?** {result['reason']}")
                st.warning("👉 Go to MT5 NOW and place the trade using YOUR broker's current price.")
                
            elif "SELL" in result['signal']:
                st.error(f"🔥 **{result['signal']} DETECTED**")
                st.write(f"**Entry:** {result['entry']:.2f}")
                st.write(f"**Stop Loss:** {result['sl']:.2f} (Risking $7)")
                st.write(f"**Take Profit:** {result['tp']:.2f} (Targeting $20)")
                st.info(f"**Why?** {result['reason']}")
                st.warning("👉 Go to MT5 NOW and place the trade using YOUR broker's current price.")
                
            else:
                st.warning("⏳ **NO SIGNAL - WAIT**")
                st.write(f"**Reason:** {result['reason']}")
    else:
        st.error("Could not fetch data. Please try again.")
