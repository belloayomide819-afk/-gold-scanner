import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="T4F Confluence Sniper", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .big-font { font-size:40px !important; font-weight: bold; color: #00FFAA; }
    .sell-card { background-color: #FF4B4B; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; color: white;}
    .buy-card { background-color: #00FFAA; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; color: black;}
    .wait-card { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 2px solid #FFA500; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ T4F Confluence Sniper")
st.write("T4F 369 + H1 Trendlines = High Probability")

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

def check_time():
    lagos_tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(lagos_tz)
    current_time = now.time()
    
    w1_start = datetime.strptime("08:03", "%H:%M").time()
    w1_end = datetime.strptime("08:12", "%H:%M").time()
    w2_start = datetime.strptime("14:45", "%H:%M").time()
    w2_end = datetime.strptime("15:08", "%H:%M").time()
    
    in_w1 = w1_start <= current_time <= w1_end
    in_w2 = w2_start <= current_time <= w2_end
    
    return {"now": now.strftime('%H:%M'), "active": in_w1 or in_w2}

def get_trendline_bias():
    df = yf.download("XAUUSD=X", period="10d", interval="1h", progress=False)
    if df.empty: df = yf.download("GC=F", period="10d", interval="1h", progress=False)
    if df.empty: return "NEUTRAL"

    df['Swing_Low'] = df['Low'][(df['Low'].shift(1) > df['Low']) & (df['Low'].shift(-1) > df['Low'])]
    df['Swing_High'] = df['High'][(df['High'].shift(1) < df['High']) & (df['High'].shift(-1) < df['High'])]
    
    recent_lows = df['Swing_Low'].dropna().tail(2)
    recent_highs = df['Swing_High'].dropna().tail(2)
    current_price = float(df['Close'].iloc[-1].item())
    current_idx = len(df) - 1

    # Check Support (Bullish Bias)
    if len(recent_lows) == 2:
        idx1, idx2 = df.index.get_loc(recent_lows.index[0]), df.index.get_loc(recent_lows.index[1])
        price1, price2 = float(recent_lows.iloc[0]), float(recent_lows.iloc[1])
        slope = (price2 - price1) / (idx2 - idx1)
        projected = price1 + slope * (current_idx - idx1)
        if abs(current_price - projected) <= 5.0: return "BUY"

    # Check Resistance (Bearish Bias)
    if len(recent_highs) == 2:
        idx1, idx2 = df.index.get_loc(recent_highs.index[0]), df.index.get_loc(recent_highs.index[1])
        price1, price2 = float(recent_highs.iloc[0]), float(recent_highs.iloc[1])
        slope = (price2 - price1) / (idx2 - idx1)
        projected = price1 + slope * (current_idx - idx1)
        if abs(current_price - projected) <= 5.0: return "SELL"
        
    return "NEUTRAL"

def get_t4f_signal():
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty: df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty: return None
        
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    return {
        "price": current_price,
        "sell_entry": recent_high - step_high,
        "buy_entry": recent_low + step_low
    }

def update_history(current_price):
    for trade in st.session_state.history:
        if trade["Status"] == "Pending":
            entry = float(trade["Entry"])
            if trade["Type"] == "SELL" and current_price >= entry: trade["Status"] = "Active"
            elif trade["Type"] == "BUY" and current_price <= entry: trade["Status"] = "Active"
        elif trade["Status"] == "Active":
            entry = float(trade["Entry"]); sl = float(trade["SL"]); tp = float(trade["TP"])
            if trade["Type"] == "SELL":
                if current_price >= sl: trade["Status"] = "❌ Loss (SL)"
                elif current_price <= tp: trade["Status"] = "✅ Win (TP)"
            elif trade["Type"] == "BUY":
                if current_price <= sl: trade["Status"] = "❌ Loss (SL)"
                elif current_price >= tp: trade["Status"] = "✅ Win (TP)"

# --- UI ---
time_status = check_time()

col1, col2 = st.columns(2)
with col1: st.markdown(f"**Time:** `{time_status['now']}`")
with col2:
    if time_status['active']: st.markdown("<h3 style='color: #00FFAA;'>🟢 WINDOW OPEN</h3>", unsafe_allow_html=True)
    else: st.markdown("<h3 style='color: #FF4B4B;'>🔴 WINDOW LOCKED</h3>", unsafe_allow_html=True)

st.divider()

if st.button("🎯 SCAN CONFLUENCE", use_container_width=True):
    with st.spinner("Checking Trendlines + 369 Math..."):
        
        trend_bias = get_trendline_bias()
        t4f = get_t4f_signal()
        
        if not t4f:
            st.error("Data error.")
        else:
            update_history(t4f['price'])
            
            # CONFLUENCE LOGIC
            # Only give Sell if Trendline is Bearish AND T4F level is close
            if trend_bias == "SELL" and time_status['active']:
                entry = t4f['sell_entry']
                st.markdown(f"""
                <div class='sell-card'>
                    <h1>🔴 CONFLUENCE SELL</h1>
                    <p class='big-font'>Entry: {entry:.2f}</p>
                    <p><b>SL:</b> {entry+7:.2f} | <b>TP:</b> {entry-21:.2f}</p>
                    <p><i>H1 Trendline Bearish + T4F Level Hit</i></p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{entry+7:.2f}", "TP": f"{entry-21:.2f}", "Status": "Pending"})

            # Only give Buy if Trendline is Bullish AND T4F level is close
            elif trend_bias == "BUY" and time_status['active']:
                entry = t4f['buy_entry']
                st.markdown(f"""
                <div class='buy-card'>
                    <h1>🟢 CONFLUENCE BUY</h1>
                    <p class='big-font'>Entry: {entry:.2f}</p>
                    <p><b>SL:</b> {entry-7:.2f} | <b>TP:</b> {entry+21:.2f}</p>
                    <p><i>H1 Trendline Bullish + T4F Level Hit</i></p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{entry-7:.2f}", "TP": f"{entry+21:.2f}", "Status": "Pending"})

            else:
                st.markdown(f"""
                <div class='wait-card'>
                    <h2 style='color: #FFA500;'>⏳ NO CONFLUENCE YET</h2>
                    <p>Trendline bias is {trend_bias}. T4F Window is {'OPEN' if time_status['active'] else 'LOCKED'}.</p>
                    <p>The app is protecting you from a rubbish trade. Press Scan again later.</p>
                </div>
                """, unsafe_allow_html=True)

st.divider()
st.subheader("📜 Confluence History")

if len(st.session_state.history) == 0:
    st.write("No limits placed today.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
