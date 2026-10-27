import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="T4F Pro Scanner", page_icon="⏱️", layout="centered")

st.title("⏱️ T4F Pro Scanner")
st.write("Time-Locked + 1M Rejection Filter")

def get_digital_root(price):
    integer_part = int(price)
    digit_sum = sum(int(digit) for digit in str(integer_part))
    while digit_sum > 9:
        digit_sum = sum(int(digit) for digit in str(digit_sum))
    if digit_sum in [1, 4, 7]: return 12
    elif digit_sum in [2, 5, 8]: return 15
    elif digit_sum in [3, 6, 9]: return 18
    return 12

def get_signal():
    lagos_tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(lagos_tz)
    current_time = now.time()
    
    # Display the time window prominently
    st.info(f"🕒 **Current Time:** {now.strftime('%H:%M')} (Nigeria Time)\n\n"
            f"🎯 **SCAN WINDOW:** 15:52 to 17:02 only.\n\n"
            f"*(If you press scan outside this time, it will lock.)*")
    
    # Phase 9 Window
    start_time = datetime.strptime("15:52", "%H:%M").time()
    end_time = datetime.strptime("17:02", "%H:%M").time()
    
    if current_time < start_time:
        return {"status": "LOCKED", "msg": "Phase 9 has not started yet. Come back at 15:52."}
    elif current_time > end_time:
        return {"status": "LOCKED", "msg": "Phase 9 is over for today. Do not trade."}

    # Fetch 15M Data
    df_15m = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df_15m.empty:
        return {"status": "ERROR", "msg": "Could not fetch data."}
        
    recent_high = float(df_15m['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df_15m['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df_15m['Close'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    levels_down = [recent_high - (i * step_high) for i in range(1, 5)]
    levels_up = [recent_low + (i * step_low) for i in range(1, 5)]
    
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    level_hit = ""
    direction = ""

    # Check if at a level (within 4.0 points)
    for i, level in enumerate(levels_down):
        if abs(current_price - level) <= 4.0:
            level_hit = f"Bearish Level {i+1} (${level:.2f})"
            direction = "SELL"
            break
            
    if direction == "":
        for i, level in enumerate(levels_up):
            if abs(current_price - level) <= 4.0:
                level_hit = f"Bullish Level {i+1} (${level:.2f})"
                direction = "BUY"
                break

    if direction == "":
        return {"status": "ACTIVE", "price": current_price, "signal": "WAIT", "reason": "Price is in the middle. No edge."}

    # If at a level, check 1M Momentum for Rejection
    df_1m = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if df_1m.empty:
         return {"status": "ERROR", "msg": "Could not fetch 1M data."}
         
    last_candle = df_1m.iloc[-1]
    prev_candle = df_1m.iloc[-2]
    
    # Simple rejection check
    if direction == "SELL":
        # For a sell, we want the last 1M candle to be red (Close < Open)
        if last_candle['Close'] < last_candle['Open']:
            signal = "SELL"
            entry = current_price
            sl = entry + 7.00
            tp = entry - 20.00
            reason = f"{level_hit} hit + 1M Bearish Momentum."
        else:
            reason = f"{level_hit} hit, but 1M candle is green. Wait for rejection."
            
    elif direction == "BUY":
        # For a buy, we want the last 1M candle to be green (Close > Open)
        if last_candle['Close'] > last_candle['Open']:
            signal = "BUY"
            entry = current_price
            sl = entry - 7.00
            tp = entry + 20.00
            reason = f"{level_hit} hit + 1M Bullish Momentum."
        else:
            reason = f"{level_hit} hit, but 1M candle is red. Wait for rejection."

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

if st.button("🚀 Scan Market", use_container_width=True):
    with st.spinner("Analyzing 369 Levels & 1M Momentum..."):
        result = get_signal()
        
    if result["status"] == "LOCKED":
        st.error(f"🚫 **LOCKED**\n\n{result['msg']}")
    elif result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        st.write(f"**Current Live Price:** ${result['price']:.2f}")
        st.divider()
        
        if result["signal"] == "BUY":
            st.success("🔥 **BUY SIGNAL CONFIRMED**")
            st.write(f"**Entry:** ${result['entry']:.2f}")
            st.write(f"**Stop Loss:** ${result['sl']:.2f} (Risk $7)")
            st.write(f"**Take Profit:** ${result['tp']:.2f} (Target $20)")
            st.info(f"**Why?** {result['reason']}")
            
        elif result["signal"] == "SELL":
            st.error("🔥 **SELL SIGNAL CONFIRMED**")
            st.write(f"**Entry:** ${result['entry']:.2f}")
            st.write(f"**Stop Loss:** ${result['sl']:.2f} (Risk $7)")
            st.write(f"**Take Profit:** ${result['tp']:.2f} (Target $20)")
            st.info(f"**Why?** {result['reason']}")
            
        else:
            st.warning("⏳ **WAITING FOR CONFIRMATION**")
            st.write(f"**Reason:** {result['reason']}")
            
        st.divider()
        st.write("### 369 Levels to Watch:")
        st.write(f"Resistance: {', '.join([f'${x:.2f}' for x in result['levels_down']])}")
        st.write(f"Support: {', '.join([f'${x:.2f}' for x in result['levels_up']])}")
