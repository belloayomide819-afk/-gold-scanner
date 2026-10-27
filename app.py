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
    df = pd.DataFrame()
    
    # Try Spot Gold first, if it fails, try Gold Futures
    try:
        df = yf.download("XAUUSD=X", period="5d", interval="15m", progress=False)
        if df.empty:
            raise ValueError("Empty data")
    except:
        try:
            df = yf.download("GC=F", period="5d", interval="15m", progress=False)
            if df.empty:
                raise ValueError("Empty data")
        except:
            return None 
    
    # 1. Time Filter (Rule 5)
    lagos_tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(lagos_tz)
    current_hour = now.hour
    
    if current_hour < 9 or current_hour >= 12:
        return {"status": "TIME_LOCKED", "message": f"Current time is {now.strftime('%H:%M')}. You can only scan between 09:00 and 12:00 Nigeria Time."}

    # 2. Calculate Asian Box
    asian_box = df.tail(28)
    box_high = float(asian_box['High'].max().item())
    box_low = float(asian_box['Low'].min().item())
    box_range = box_high - box_low
    
    # Use the open of the most recent candle for a more accurate recent price
    current_price = float(df['Open'].iloc[-1].item())
    
    signal = "WAIT"
    reason = ""
    
    # Rule 3 & 4 Logic
    broke_up = df['High'].iloc[-10:].max().item() > box_high
    broke_down = df['Low'].iloc[-10:].min().item() < box_low
    
    if broke_up and broke_down and current_price < box_low:
        if abs(current_price - box_low) < (box_range * 0.3): # Widened slightly for lag
            signal = "SELL (Retest)"
            reason = f"Fakeout above {box_high:.2f}, then broke down. Price is retesting the Box Low."
            
    elif broke_down and broke_up and current_price > box_high:
        if abs(current_price - box_high) < (box_range * 0.3): # Widened slightly for lag
            signal = "BUY (Retest)"
            reason = f"Fakeout below {box_low:.2f}, then broke up. Price is retesting the Box High."
            
    else:
        reason = f"No clear setup. Box High: {box_high:.2f}, Box Low: {box_low:.2f}. Waiting for fakeout and retest."

    return {
        "status": "ACTIVE",
        "price": current_price,
        "high": box_high,
        "low": box_low,
        "signal": signal,
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
            st.write(f"**App Price (Delayed):** ${result['price']:.2f}")
            st.divider()
            
            if "BUY" in result['signal'] or "SELL" in result['signal']:
                if "BUY" in result['signal']:
                    st.success(f"🔥 **{result['signal']} DETECTED**")
                else:
                    st.error(f"🔥 **{result['signal']} DETECTED**")
                
                st.info(f"**Why?** {result['reason']}")
                
                st.error("🚨 **ACTION REQUIRED** 🚨")
                st.write("1. Open your MT5 App immediately.")
                st.write("2. Look at your broker's exact live price.")
                st.write("3. Enter the trade on MT5.")
                st.write("4. Set your Stop Loss to **$7 away** from your entry.")
                st.write("5. Set your Take Profit to **$20 away** from your entry.")
                
            else:
                st.warning("⏳ **NO SIGNAL - WAIT**")
                st.write(f"**Reason:** {result['reason']}")
    else:
        st.error("Both data sources failed. Please try again in 1 minute.")
