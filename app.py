import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="T4F Sniper Limits", page_icon="🎯", layout="centered")

st.title("🎯 T4F Sniper Limits")
st.write("Math + Trend Filtered Limit Orders")

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
        return {"status": "LOCKED", "msg": f"Window closed at 15:08. Cancel pending limits."}

    # Fetch 15M Data
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty:
         df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty:
        return {"status": "ERROR", "msg": "Could not fetch data."}
        
    # Calculate 50 EMA for Trend Filter
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    ema50 = float(df['EMA50'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    # Calculate Level 1 for both
    sell_entry = recent_high - step_high
    buy_entry = recent_low + step_low
    
    # --- THE NO RUBBISH FILTER ---
    # Only allow Sell if price is below EMA50. Only allow Buy if price is above EMA50.
    
    show_sell = False
    show_buy = False
    
    if current_price < ema50:
        show_sell = True
    if current_price > ema50:
        show_buy = True
        
    return {
        "status": "ACTIVE",
        "price": current_price,
        "sell_entry": sell_entry,
        "buy_entry": buy_entry,
        "show_sell": show_sell,
        "show_buy": show_buy,
        "ema50": ema50
    }

# --- UI ---
st.info("⏰ **Window:** 14:45 - 15:08. Place these as **Limit Orders** on MT5.")

if st.button("🎯 Get Sniper Limits", use_container_width=True):
    with st.spinner("Calculating..."):
        result = get_setup()
        
    if result["status"] == "LOCKED":
        st.error(f"🚫 **LOCKED**\n\n{result['msg']}")
    elif result["status"] == "ERROR":
        st.error(result["msg"])
    else:
        st.write(f"**App Live Price:** ${result['price']:.2f}")
        st.write(f"**Trend (50 EMA):** ${result['ema50']:.2f}")
        st.divider()
        
        # Show Sell Limit only if Trend is Bearish
        if result['show_sell']:
            sell_sl = result['sell_entry'] + 7.00
            sell_tp = result['sell_entry'] - 21.00
            st.error(f"### 📉 SELL LIMIT\n"
                     f"**Entry:** {result['sell_entry']:.2f}\n\n"
                     f"**SL:** {sell_sl:.2f}\n\n"
                     f"**TP:** {sell_tp:.2f}")
        else:
            st.info("📉 No Sell Limit (Trend is Bullish)")
                     
        st.divider()
        
        # Show Buy Limit only if Trend is Bullish
        if result['show_buy']:
            buy_sl = result['buy_entry'] - 7.00
            buy_tp = result['buy_entry'] + 21.00
            st.success(f"### 📈 BUY LIMIT\n"
                       f"**Entry:** {result['buy_entry']:.2f}\n\n"
                       f"**SL:** {buy_sl:.2f}\n\n"
                       f"**TP:** {buy_tp:.2f}")
        else:
            st.info("📈 No Buy Limit (Trend is Bearish)")
            
        st.warning("⚠️ **Check MT5:** If MT5 price has already passed the level, DO NOT place that limit. Cancel any untriggered limits at 15:08.")
