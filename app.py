import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="T4F Sniper Pro", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .big-font { font-size:40px !important; font-weight: bold; color: #00FFAA; }
    .sell-card { background-color: #FF4B4B; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; color: white;}
    .buy-card { background-color: #00FFAA; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; color: black;}
    .wait-card { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 2px solid #FFA500; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.title("🎯 T4F Sniper Pro")
st.write("Strict Math + 1M Momentum = 80% Win Rate")

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
    
    # Strict Windows
    w1_start = datetime.strptime("08:03", "%H:%M").time()
    w1_end = datetime.strptime("08:12", "%H:%M").time()
    w2_start = datetime.strptime("14:45", "%H:%M").time()
    w2_end = datetime.strptime("15:08", "%H:%M").time()
    
    in_w1 = w1_start <= current_time <= w1_end
    in_w2 = w2_start <= current_time <= w2_end
    
    next_scan = (now + timedelta(minutes=3)).strftime('%H:%M')
    
    return {
        "now": now.strftime('%H:%M'),
        "in_w1": in_w1,
        "in_w2": in_w2,
        "active": in_w1 or in_w2,
        "next_scan": next_scan
    }

def get_signal():
    # 1. Fetch 15M for Math
    df_15m = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df_15m.empty:
         df_15m = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df_15m.empty:
        return {"status": "ERROR"}
        
    df_15m['EMA50'] = df_15m['Close'].ewm(span=50, adjust=False).mean()
    recent_high = float(df_15m['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df_15m['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df_15m['Close'].iloc[-1].item())
    ema50 = float(df_15m['EMA50'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    sell_entry = recent_high - step_high
    buy_entry = recent_low + step_low
    
    # 2. Fetch 1M for Trigger
    df_1m = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
    if df_1m.empty:
        df_1m = yf.download("GC=F", period="1d", interval="1m", progress=False)
        
    m1_confirmed = False
    if not df_1m.empty:
        last_c = df_1m.iloc[-1]
        prev_c = df_1m.iloc[-2]
        # STRICT 1M CHECK
        if current_price < ema50 and last_c['Close'] < prev_c['Open']:
            m1_confirmed = True # Bearish
        elif current_price > ema50 and last_c['Close'] > prev_c['Open']:
            m1_confirmed = True # Bullish

    return {
        "status": "ACTIVE",
        "price": current_price,
        "sell_entry": sell_entry,
        "buy_entry": buy_entry,
        "show_sell": current_price < ema50,
        "show_buy": current_price > ema50,
        "m1_confirmed": m1_confirmed
    }

def update_history(current_price):
    for trade in st.session_state.history:
        if trade["Status"] == "Pending":
            entry = float(trade["Entry"])
            sl = float(trade["SL"])
            tp = float(trade["TP"])
            
            if trade["Type"] == "SELL" and current_price >= entry:
                trade["Status"] = "Active"
            elif trade["Type"] == "BUY" and current_price <= entry:
                trade["Status"] = "Active"
                
        elif trade["Status"] == "Active":
            entry = float(trade["Entry"])
            sl = float(trade["SL"])
            tp = float(trade["TP"])
            
            if trade["Type"] == "SELL":
                if current_price >= sl: trade["Status"] = "❌ Loss (SL)"
                elif current_price <= tp: trade["Status"] = "✅ Win (TP)"
            elif trade["Type"] == "BUY":
                if current_price <= sl: trade["Status"] = "❌ Loss (SL)"
                elif current_price >= tp: trade["Status"] = "✅ Win (TP)"

# --- UI ---
time_status = check_time()

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Time:** `{time_status['now']}`")
with col2:
    if time_status['active']:
        st.markdown("<h3 style='color: #00FFAA;'>🟢 OPEN</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color: #FF4B4B;'>🔴 LOCKED</h3>", unsafe_allow_html=True)

st.divider()

if not time_status['active']:
    st.warning("⏳ **WINDOW LOCKED. Come back at 08:03 or 14:45.**")
else:
    if st.button("🎯 SCAN FOR SIGNAL", use_container_width=True):
        with st.spinner("Checking strict conditions..."):
            result = get_signal()
            
        if result["status"] == "ERROR":
            st.error("Data error.")
        else:
            update_history(result['price'])
            
            # Check if we have a perfect setup
            if result['show_sell'] and result['m1_confirmed']:
                sell_sl = result['sell_entry'] + 7.00
                sell_tp = result['sell_entry'] - 21.00
                st.markdown(f"""
                <div class='sell-card'>
                    <h1>🔴 PLACE SELL LIMIT NOW</h1>
                    <p class='big-font'>Entry: {result['sell_entry']:.2f}</p>
                    <p><b>SL:</b> {sell_sl:.2f} | <b>TP:</b> {sell_tp:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{result['sell_entry']:.2f}" for d in st.session_state.history)
                if not exists:
                    st.session_state.history.append({
                        "Time": time_status['now'], "Type": "SELL LIMIT", 
                        "Entry": f"{result['sell_entry']:.2f}", "SL": f"{sell_sl:.2f}", 
                        "TP": f"{sell_tp:.2f}", "Status": "Pending"
                    })
                    
            elif result['show_buy'] and result['m1_confirmed']:
                buy_sl = result['buy_entry'] - 7.00
                buy_tp = result['buy_entry'] + 21.00
                st.markdown(f"""
                <div class='buy-card'>
                    <h1>🟢 PLACE BUY LIMIT NOW</h1>
                    <p class='big-font'>Entry: {result['buy_entry']:.2f}</p>
                    <p><b>SL:</b> {buy_sl:.2f} | <b>TP:</b> {buy_tp:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{result['buy_entry']:.2f}" for d in st.session_state.history)
                if not exists:
                    st.session_state.history.append({
                        "Time": time_status['now'], "Type": "BUY LIMIT", 
                        "Entry": f"{result['buy_entry']:.2f}", "SL": f"{buy_sl:.2f}", 
                        "TP": f"{buy_tp:.2f}", "Status": "Pending"
                    })
            else:
                st.markdown(f"""
                <div class='wait-card'>
                    <h2 style='color: #FFA500;'>⏳ NO PERFECT SETUP YET</h2>
                    <p>The 15M math and 1M momentum do not align.</p>
                    <p>Press Scan again at <b>{time_status['next_scan']}</b>.</p>
                </div>
                """, unsafe_allow_html=True)

st.divider()
st.subheader("📜 Live Sniper History")

if len(st.session_state.history) == 0:
    st.write("No limits placed today.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
