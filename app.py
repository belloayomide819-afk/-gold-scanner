import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="T4F Auto-Setup", page_icon="🎯", layout="centered")

st.title("🎯 T4F Auto-Setup (1:3 RR)")
st.write("Press Scan. Get Entry, SL, and TP. No chart watching.")

def get_digital_root(price):
    integer_part = int(price)
    digit_sum = sum(int(digit) for digit in str(integer_part))
    while digit_sum > 9:
        digit_sum = sum(int(digit) for digit in str(digit_sum))
    if digit_sum in [1, 4, 7]: return 12
    elif digit_sum in [2, 5, 8]: return 15
    elif digit_sum in [3, 6, 9]: return 18
    return 12

def get_setup():
    # Fetch 15M Data for Levels
    df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty:
        return {"status": "ERROR", "msg": "Could not fetch data. Try again."}
        
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    levels_down = [recent_high - (i * step_high) for i in range(1, 5)]
    levels_up = [recent_low + (i * step_low) for i in range(1, 5)]
    
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # Check for Setup (Within 4.0 points of a level)
    for i, level in enumerate(levels_down):
        if abs(current_price - level) <= 4.0:
            signal = "SELL"
            entry = current_price
            sl = entry + 7.00
            tp = entry - 21.00 # 1:3 RR
            reason = f"Price tapped Bearish Level {i+1} (${level:.2f})"
            break
            
    if signal == "WAIT":
        for i, level in enumerate(levels_up):
            if abs(current_price - level) <= 4.0:
                signal = "BUY"
                entry = current_price
                sl = entry - 7.00
                tp = entry + 21.00 # 1:3 RR
                reason = f"Price tapped Bullish Level {i+1} (${level:.2f})"
                break

    if signal == "WAIT":
        reason = "Price is in the middle of the range. Waiting for a 369 Level tap."

    return {
        "status": "ACTIVE",
        "price": current_price,
        "signal": signal,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "reason": reason,
        "levels_down": levels_down,
        "levels_up": levels_up
    }

# --- UI ---
st.info("⏰ **Best Time to Scan:** 14:45 - 15:08 (Nigeria Time)")

if st.button("🚀 Scan for Setup", use_container_width=True):
    with st.spinner("Calculating 369 Levels..."):
        result = get_setup()
        
    if result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        st.write(f"**Current Live Price:** ${result['price']:.2f}")
        st.divider()
        
        if result["signal"] == "BUY":
            st.success("🔥 **BUY SETUP (1:3 RR)**")
            st.write(f"**Entry:** ${result['entry']:.2f}")
            st.write(f"**Stop Loss:** ${result['sl']:.2f} (Risk $7)")
            st.write(f"**Take Profit:** ${result['tp']:.2f} (Reward $21)")
            st.info(f"**Why?** {result['reason']}")
            st.warning("👉 Open MT5, place a BUY order immediately.")
            
        elif result["signal"] == "SELL":
            st.error("🔥 **SELL SETUP (1:3 RR)**")
            st.write(f"**Entry:** ${result['entry']:.2f}")
            st.write(f"**Stop Loss:** ${result['sl']:.2f} (Risk $7)")
            st.write(f"**Take Profit:** ${result['tp']:.2f} (Reward $21)")
            st.info(f"**Why?** {result['reason']}")
            st.warning("👉 Open MT5, place a SELL order immediately.")
            
        else:
            st.warning("⏳ **NO SETUP YET**")
            st.write(f"**Reason:** {result['reason']}")
            
        st.divider()
        st.write("### 369 Levels to Watch:")
        st.write(f"Sell Targets: {', '.join([f'${x:.2f}' for x in result['levels_down']])}")
        st.write(f"Buy Targets: {', '.join([f'${x:.2f}' for x in result['levels_up']])}")
