import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set up the page
st.set_page_config(page_title="London Breakout Scanner", page_icon="🇬🇧", layout="centered")

st.title("🇬🇧 London Breakout Scanner (Gold)")
st.write("Strategy: Asian Range Fakeout + Retest")

def get_signal(timeframe):
    # We only use 15m for this strategy (Rule 1: 7-hour Asian session = 28 candles)
    interval = "15m"
    
    df = yf.download("GC=F", period="5d", interval=interval, progress=False)
    
    if df.empty:
        return None
        
    # Get the most recent 28 candles (approx 7 hours: Midnight to 7am UK)
    # This defines the Asian Box (Rule 1)
    asian_box = df.tail(28)
    box_high = float(asian_box['High'].max().item())
    box_low = float(asian_box['Low'].min().item())
    box_range = box_high - box_low
    
    latest = df.iloc[-1]
    current_price = float(latest['Close'].item())
    
    # Prop Firm Settings
    sl_distance = 7.00 # $7 Loss
    tp_distance = 20.00 # $20 Profit
    
    # Logic Variables
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # Rule 2: Only Trade London Break (We check if the price has left the box)
    # We look at the last few candles to see if a fakeout (Rule 3) and retest (Rule 4) happened.
    
    # Check if price broke UP (Fakeout high)
    broke_up = df['High'].iloc[-10:].max().item() > box_high
    # Check if price broke DOWN (Fakeout low)
    broke_down = df['Low'].iloc[-10:].min().item() < box_low
    
    # Scenario 1: Price faked out UP, then broke DOWN (SELL setup)
    if broke_up and broke_down and current_price < box_low:
        # Rule 4: Wait for retest. If price is coming back UP to the box_low...
        if abs(current_price - box_low) < (box_range * 0.2): # Price is close to the box edge
            signal = "SELL (Retest)"
            entry = current_price
            sl = entry + sl_distance
            tp = entry - tp_distance
            reason = f"Fakeout above {box_high:.2f}, then broke down. Retesting box low for Short."
            
    # Scenario 2: Price faked out DOWN, then broke UP (BUY setup)
    elif broke_down and broke_up and current_price > box_high:
        # Rule 4: Wait for retest. If price is coming back DOWN to the box_high...
        if abs(current_price - box_high) < (box_range * 0.2):
            signal = "BUY (Retest)"
            entry = current_price
            sl = entry - sl_distance
            tp = entry + tp_distance
            reason = f"Fakeout below {box_low:.2f}, then broke up. Retesting box high for Long."
            
    else:
        reason = f"No clear setup. Box High: {box_high:.2f}, Box Low: {box_low:.2f}. Waiting for fakeout and retest."

    return {
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
st.info("⏰ **Rule 5:** Only trade between 08:00 - 11:00 UK Time (09:00 - 12:00 Nigeria Time).")

if st.button("🇬🇧 Scan London Breakout", use_container_width=True):
    with st.spinner("Scanning Asian Range for Fakeout..."):
        result = get_signal("15m")
        
    if result:
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
            
        elif "SELL" in result['signal']:
            st.error(f"🔥 **{result['signal']} DETECTED**")
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f} (Risking $7)")
            st.write(f"**Take Profit:** {result['tp']:.2f} (Targeting $20)")
            st.info(f"**Why?** {result['reason']}")
            
        else:
            st.warning("⏳ **NO SIGNAL - WAIT**")
            st.write(f"**Reason:** {result['reason']}")
    else:
        st.error("Could not fetch data.")
