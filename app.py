import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="T4F Sniper + History", page_icon="🎯", layout="centered")

st.title("🎯 T4F Sniper + History")
st.write("Exact Math. No Rubbish. Full History.")

# Initialize History
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

def get_setup():
    lagos_tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(lagos_tz)
    current_time = now.time()
    
    # Window Check (14:45 - 15:08)
    start_time = datetime.strptime("14:45", "%H:%M").time()
    end_time = datetime.strptime("15:08", "%H:%M").time()
    
    if current_time < start_time:
        return {"status": "LOCKED", "msg": f"Wait until 14:45. Current: {now.strftime('%H:%M')}."}
    elif current_time > end_time:
        return {"status": "LOCKED", "msg": f"Window closed at 15:08. Cancel limits."}

    # Fetch 15M Data
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
    
    sell_entry = recent_high - step_high
    buy_entry = recent_low + step_low
    
    # Trend Filter
    show_sell = current_price < ema50
    show_buy = current_price > ema50
        
    return {
        "status": "ACTIVE",
        "price": current_price,
        "sell_entry": sell_entry,
        "buy_entry": buy_entry,
        "show_sell": show_sell,
        "show_buy": show_buy,
        "ema50": ema50,
        "time": now.strftime('%H:%M')
    }

# --- UI ---
st.info("⏰ **Window:** 14:45 - 15:08. Place these as **Limit Orders** on MT5.")

if st.button("🎯 Scan for Setup", use_container_width=True):
    with st.spinner("Calculating..."):
        result = get_setup()
        
    if result["status"] == "LOCKED":
        st.error(f"🚫 **LOCKED**\n\n{result['msg']}")
    elif result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        st.write(f"**App Live Price:** ${result['price']:.2f} | **50 EMA:** ${result['ema50']:.2f}")
        st.divider()
        
        # SELL SETUP
        if result['show_sell']:
            sell_sl = result['sell_entry'] + 7.00
            sell_tp = result['sell_entry'] - 21.00
            st.error(f"### 📉 SELL LIMIT\n"
                     f"**Entry:** {result['sell_entry']:.2f} | **SL:** {sell_sl:.2f} | **TP:** {sell_tp:.2f}")
            
            # Save to history
            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{result['sell_entry']:.2f}" for d in st.session_state.history)
            if not exists:
                st.session_state.history.append({
                    "Time": result['time'], "Type": "SELL", 
                    "Entry": f"{result['sell_entry']:.2f}", 
                    "SL": f"{sell_sl:.2f}", "TP": f"{sell_tp:.2f}", "Status": "Pending"
                })
        else:
            st.info("📉 No Sell Limit (Trend is Bullish - Filtered out)")

        st.divider()
        
        # BUY SETUP
        if result['show_buy']:
            buy_sl = result['buy_entry'] - 7.00
            buy_tp = result['buy_entry'] + 21.00
            st.success(f"### 📈 BUY LIMIT\n"
                       f"**Entry:** {result['buy_entry']:.2f} | **SL:** {buy_sl:.2f} | **TP:** {buy_tp:.2f}")
            
            # Save to history
            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{result['buy_entry']:.2f}" for d in st.session_state.history)
            if not exists:
                st.session_state.history.append({
                    "Time": result['time'], "Type": "BUY", 
                    "Entry": f"{result['buy_entry']:.2f}", 
                    "SL": f"{buy_sl:.2f}", "TP": f"{buy_tp:.2f}", "Status": "Pending"
                })
        else:
            st.info("📈 No Buy Limit (Trend is Bearish - Filtered out)")

# --- HISTORY & CHECKER ---
st.divider()
st.subheader("📜 Trade History & Checker")

if len(st.session_state.history) == 0:
    st.write("No setups generated yet today.")
else:
    # Auto-checker for past trades
    df_check = yf.download("XAUUSD=X", period="1d", interval="15m", progress=False)
    if not df_check.empty:
        for trade in st.session_state.history:
            if trade["Status"] == "Pending":
                entry = float(trade["Entry"])
                sl = float(trade["SL"])
                tp = float(trade["TP"])
                
                # Check recent highs/lows
                recent_high = df_check['High'].tail(10).max()
                recent_low = df_check['Low'].tail(10).min()
                
                if trade["Type"] == "SELL":
                    if recent_high >= entry: # Entry Triggered
                        if recent_low <= tp: trade["Status"] = "✅ WIN (TP Hit)"
                        elif recent_high >= sl: trade["Status"] = "❌ LOSS (SL Hit)"
                        else: trade["Status"] = "⏳ Active"
                elif trade["Type"] == "BUY":
                    if recent_low <= entry: # Entry Triggered
                        if recent_high >= tp: trade["Status"] = "✅ WIN (TP Hit)"
                        elif recent_low <= sl: trade["Status"] = "❌ LOSS (SL Hit)"
                        else: trade["Status"] = "⏳ Active"

    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
