import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="T4F Epic Sniper", page_icon="🚀", layout="wide")

# Custom CSS for a Neon/Prop Firm look
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
        color: #00FFAA;
    }
    .sell-card {
        background-color: rgba(255, 75, 75, 0.1);
        border-left: 5px solid #FF4B4B;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .buy-card {
        background-color: rgba(0, 255, 170, 0.1);
        border-left: 5px solid #00FFAA;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .locked-card {
        background-color: rgba(255, 165, 0, 0.1);
        border-left: 5px solid orange;
        padding: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 T4F Epic Sniper")
st.write("Protected Prop Firm Execution. Exact Math. Limit Orders Only.")

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
    
    return {
        "now": now.strftime('%H:%M'),
        "in_w1": in_w1,
        "in_w2": in_w2,
        "active": in_w1 or in_w2
    }

def get_setup():
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty:
         df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty:
        return {"status": "ERROR", "msg": "Data server offline. Try again."}
        
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    ema50 = float(df['EMA50'].iloc[-1].item())
    
    step_high = get_digital_root(recent_high)
    step_low = get_digital_root(recent_low)
    
    sell_entry = recent_high - step_high
    buy_entry = recent_low + step_low
    
    show_sell = current_price < ema50
    show_buy = current_price > ema50
        
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
time_status = check_time()

# Header Dashboard
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Current Time:** `{time_status['now']}` (Nigeria Time)")
with col2:
    if time_status['active']:
        st.markdown("<h3 style='color: #00FFAA;'>🟢 WINDOW IS OPEN</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color: #FF4B4B;'>🔴 WINDOW LOCKED</h3>", unsafe_allow_html=True)

st.markdown(f"""
<div style='display: flex; gap: 20px;'>
    <div style='flex: 1; padding: 10px; background: #1E1E1E; border-radius: 5px;'>
        <b>London Window:</b> 08:03 - 08:12 {'(OPEN 🟢)' if time_status['in_w1'] else '(CLOSED 🔴)'}
    </div>
    <div style='flex: 1; padding: 10px; background: #1E1E1E; border-radius: 5px;'>
        <b>New York Window:</b> 14:45 - 15:08 {'(OPEN 🟢)' if time_status['in_w2'] else '(CLOSED 🔴)'}
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

if not time_status['active']:
    st.markdown("""
    <div class='locked-card'>
        <h3>⏳ SCANNER LOCKED</h3>
        <p>You are outside the T4F Execution Window. Do not trade. Come back at the next window.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    if st.button("🎯 SCAN FOR SNIPER SETUP", use_container_width=True):
        with st.spinner("Calculating 369 Math..."):
            result = get_setup()
            
        if result["status"] == "ERROR":
            st.error(result["msg"])
        else:
            st.markdown(f"### Live Price: `${result['price']:.2f}` | 50 EMA: `${result['ema50']:.2f}`")
            
            # SELL CARD
            if result['show_sell']:
                sell_sl = result['sell_entry'] + 7.00
                sell_tp = result['sell_entry'] - 21.00
                st.markdown(f"""
                <div class='sell-card'>
                    <h2 style='color: #FF4B4B;'>📉 PLACE SELL LIMIT</h2>
                    <p><b>Entry Price:</b> <span class='big-font'>{result['sell_entry']:.2f}</span></p>
                    <p><b>Stop Loss:</b> {sell_sl:.2f} (Risk $7)</p>
                    <p><b>Take Profit:</b> {sell_tp:.2f} (Reward $21)</p>
                    <p>👉 <i>Open MT5, select Pending Order -> Sell Limit, and enter these exact numbers.</i></p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{result['sell_entry']:.2f}" for d in st.session_state.history)
                if not exists:
                    st.session_state.history.append({
                        "Time": time_status['now'], "Type": "SELL LIMIT", 
                        "Entry": f"{result['sell_entry']:.2f}", 
                        "SL": f"{sell_sl:.2f}", "TP": f"{sell_tp:.2f}", "Status": "Pending"
                    })
            else:
                st.info("📉 Sell Setup Filtered Out (Trend is Bullish)")

            # BUY CARD
            if result['show_buy']:
                buy_sl = result['buy_entry'] - 7.00
                buy_tp = result['buy_entry'] + 21.00
                st.markdown(f"""
                <div class='buy-card'>
                    <h2 style='color: #00FFAA;'>📈 PLACE BUY LIMIT</h2>
                    <p><b>Entry Price:</b> <span class='big-font'>{result['buy_entry']:.2f}</span></p>
                    <p><b>Stop Loss:</b> {buy_sl:.2f} (Risk $7)</p>
                    <p><b>Take Profit:</b> {buy_tp:.2f} (Reward $21)</p>
                    <p>👉 <i>Open MT5, select Pending Order -> Buy Limit, and enter these exact numbers.</i></p>
                </div>
                """, unsafe_allow_html=True)
                
                exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{result['buy_entry']:.2f}" for d in st.session_state.history)
                if not exists:
                    st.session_state.history.append({
                        "Time": time_status['now'], "Type": "BUY LIMIT", 
                        "Entry": f"{result['buy_entry']:.2f}", 
                        "SL": f"{buy_sl:.2f}", "TP": f"{buy_tp:.2f}", "Status": "Pending"
                    })
            else:
                st.info("📈 Buy Setup Filtered Out (Trend is Bearish)")

# --- HISTORY ---
st.divider()
st.subheader("📜 Sniper History")

if len(st.session_state.history) == 0:
    st.write("No limits placed today.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
