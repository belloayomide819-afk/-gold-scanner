import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="T4F Signal Journal", page_icon="📓", layout="centered")

st.title("📓 T4F Signal Journal")
st.write("Auto-Signals + Trade History")

# Initialize history in memory
if 'history' not in st.session_state:
    st.session_state.history = []

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
    
    # T4F Window (14:45 - 15:08)
    start_time = datetime.strptime("14:45", "%H:%M").time()
    end_time = datetime.strptime("15:08", "%H:%M").time()
    
    if current_time < start_time:
        return {"status": "LOCKED", "msg": f"Window opens at 14:45. Current: {now.strftime('%H:%M')}."}
    elif current_time > end_time:
        return {"status": "LOCKED", "msg": f"Window closed at 15:08. Done for today."}

    # Fetch Data
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty:
         df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty:
        return {"status": "ERROR", "msg": "Could not fetch data."}
        
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    ema50 = float(df['EMA50'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    levels_down = [recent_high - (i * step_high) for i in range(1, 5)]
    levels_up = [recent_low + (i * step_low) for i in range(1, 5)]
    
    signal = "WAIT"
    entry, sl, tp, reason = 0, 0, 0, ""
    
    # Sell Setup
    for i, level in enumerate(levels_down):
        if abs(current_price - level) <= 3.0 and current_price < ema50:
            signal = "SELL"
            entry = current_price
            sl = entry + 7.00
            tp = entry - 21.00
            reason = f"Tapped Level {i+1} (${level:.2f}) below 50EMA"
            break
            
    # Buy Setup
    if signal == "WAIT":
        for i, level in enumerate(levels_up):
            if abs(current_price - level) <= 3.0 and current_price > ema50:
                signal = "BUY"
                entry = current_price
                sl = entry - 7.00
                tp = entry + 21.00
                reason = f"Tapped Level {i+1} (${level:.2f}) above 50EMA"
                break

    if signal == "WAIT":
        reason = "Price not at 369 level or EMA trend mismatch."

    return {
        "status": "ACTIVE",
        "price": current_price,
        "signal": signal,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "reason": reason,
        "time": now.strftime('%H:%M')
    }

# --- UI ---
st.info("⏰ **Window:** 14:45 - 15:08 (Nigeria Time).")

if st.button("🚀 Scan for Signal", use_container_width=True):
    with st.spinner("Calculating..."):
        result = get_signal()
        
    if result["status"] == "LOCKED":
        st.error(f"🚫 **LOCKED**\n\n{result['msg']}")
    elif result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        if result["signal"] in ["BUY", "SELL"]:
            # Add to History if not already added
            new_trade = {
                "Time": result["time"],
                "Type": result["signal"],
                "Entry": f"${result['entry']:.2f}",
                "SL": f"${result['sl']:.2f}",
                "TP": f"${result['tp']:.2f}",
                "Current": f"${result['price']:.2f}"
            }
            
            # Check if this signal is already in history (to avoid duplicates)
            is_duplicate = False
            for trade in st.session_state.history:
                if trade["Entry"] == new_trade["Entry"]:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                st.session_state.history.append(new_trade)
            
            # Show Signal
            if result["signal"] == "BUY":
                st.success(f"🔥 **BUY SIGNAL @ {result['time']}**")
            else:
                st.error(f"🔥 **SELL SIGNAL @ {result['time']}**")
                
            st.write(f"**Entry:** {result['entry']:.2f}")
            st.write(f"**Stop Loss:** {result['sl']:.2f} (Risk $7)")
            st.write(f"**Take Profit:** {result['tp']:.2f} (Reward $21)")
            st.info(f"**Why?** {result['reason']}")
            st.warning("👉 Open MT5, place the trade immediately.")
            
        else:
            st.warning("⏳ **NO SIGNAL YET**")
            st.write(f"**Reason:** {result['reason']}")

# --- HISTORY SECTION ---
st.divider()
st.subheader("📜 Today's Signal History")
if len(st.session_state.history) == 0:
    st.write("No signals generated yet today.")
else:
    # Display as a clean table
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
