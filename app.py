import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="T4F Spot Gold Scanner", page_icon="🎯", layout="centered")

st.title("🎯 T4F Spot Gold Scanner")
st.write("Uses Spot Gold (XAUUSD) to match MT5 prices.")

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
    # CHANGED TO SPOT GOLD (XAUUSD)
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    
    if df.empty:
        # Fallback to Futures if Spot fails
        df = yf.download("GC=F", period="2d", interval="15m", progress=False)
        
    if df.empty:
        return {"status": "ERROR", "msg": "Could not fetch data."}
        
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    levels_down = [recent_high - (i * step_high) for i in range(1, 5)]
    levels_up = [recent_low + (i * step_low) for i in range(1, 5)]
    
    return {
        "status": "ACTIVE",
        "current_price": current_price,
        "levels_down": levels_down,
        "levels_up": levels_up
    }

# --- UI ---
st.info("⏰ **Execution Window:** 14:45 - 15:08 (Nigeria Time). Set your limits during this time.")

if st.button("🚀 Scan Spot Gold", use_container_width=True):
    with st.spinner("Calculating 369 Levels on Spot Gold..."):
        result = get_setup()
        
    if result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        st.write(f"**Current Live Spot Price:** ${result['current_price']:.2f}")
        st.divider()
        
        st.subheader("📉 Sell Limit Orders (Bearish Levels)")
        for i, level in enumerate(result['levels_down']):
            entry = level
            sl = entry + 7.00
            tp = entry - 21.00
            st.error(f"**Sell Limit {i+1}:** Entry: {entry:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            
        st.divider()
        
        st.subheader("📈 Buy Limit Orders (Bullish Levels)")
        for i, level in enumerate(result['levels_up']):
            entry = level
            sl = entry - 7.00
            tp = entry + 21.00
            st.success(f"**Buy Limit {i+1}:** Entry: {entry:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            
        st.warning("⚠️ **Rule:** Do not place limits if the MT5 price has already passed the level. Cancel all pending limits at 15:08.")
