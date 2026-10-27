import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="T4F 369 Monster", page_icon="👾", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .header-card { background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%); padding: 20px; border-radius: 15px; border-left: 5px solid #00FFAA; margin-bottom: 25px; }
    .sell-card { background: linear-gradient(135deg, #FF4B4B 0%, #B22222 100%); padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4); }
    .buy-card { background: linear-gradient(135deg, #00FFAA 0%, #008B5E 100%); padding: 25px; border-radius: 15px; text-align: center; color: black; box-shadow: 0 4px 15px rgba(0, 255, 170, 0.4); }
    .wait-card { background-color: #1E1E1E; padding: 30px; border-radius: 15px; border: 2px solid #FFA500; text-align: center; }
    .stat-box { background-color: #1E1E1E; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    .stat-value { font-size: 24px; font-weight: bold; margin: 0; }
    .big-font { font-size: 45px !important; font-weight: 900; margin: 10px 0; }
    .lot-box { background-color: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; margin-top: 15px; border: 1px solid rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)

st.title("👾 T4F 369 Monster")
st.markdown("**Twin Engine** | **Standard ($7/$21)** | **Cent (100c/1000c)**")

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
    
    return {"now": now.strftime('%H:%M'), "active": in_w1 or in_w2, "in_w1": in_w1, "in_w2": in_w2}

def get_369_signal():
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty: df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty: return None
        
    phase3_open = float(df['Open'].iloc[-1].item()) 
    current_price = float(df['Close'].iloc[-1].item())
    
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    
    sell_level = recent_high - get_digital_root(recent_high)
    buy_level = recent_low + get_digital_root(recent_low)
    
    bias = "SELL" if current_price > phase3_open else "BUY"
    
    return {
        "price": current_price, 
        "bias": bias,
        "sell_entry": sell_level, 
        "buy_entry": buy_level
    }

def get_1m_confirmation(direction):
    df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
    if df.empty: df = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if df.empty: return False
    
    last_c = df.iloc[-1]
    prev_c = df.iloc[-2]
    
    if direction == "SELL" and last_c['Close'] < prev_c['Open']: return True
    if direction == "BUY" and last_c['Close'] > prev_c['Open']: return True
    return False

def update_history(current_price):
    for trade in st.session_state.history:
        if trade["Status"] == "Pending":
            entry = float(trade["Entry"])
            if trade["Type"] == "SELL" and current_price >= entry: trade["Status"] = "Active"
            elif trade["Type"] == "BUY" and current_price <= entry: trade["Status"] = "Active"
        elif trade["Status"] == "Active":
            entry = float(trade["Entry"]); sl = float(trade["SL"]); tp = float(trade["TP"])
            if trade["Type"] == "SELL":
                if current_price >= sl: trade["Status"] = "❌ Loss"
                elif current_price <= tp: trade["Status"] = "✅ Win"
            elif trade["Type"] == "BUY":
                if current_price <= sl: trade["Status"] = "❌ Loss"
                elif current_price >= tp: trade["Status"] = "✅ Win"

# --- UI ---
time_status = check_time()

wins = sum(1 for t in st.session_state.history if "Win" in t["Status"])
losses = sum(1 for t in st.session_state.history if "Loss" in t["Status"])
net_usd = (wins * 21) - (losses * 7)
net_ngn = net_usd * 1500
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

st.markdown(f"""
<div class='header-card'>
    <h2 style='margin: 0; color: #FFFFFF;'>T4F 369 Monster Dashboard</h2>
    <div style='display: flex; gap: 20px; margin-top: 15px;'>
        <div class='stat-box' style='flex: 1;'><p class='stat-value' style='color: #00FFAA;'>${net_usd}</p><p style='font-size: 12px; color: #888;'>USD</p></div>
        <div class='stat-box' style='flex: 1;'><p class='stat-value' style='color: #00FFAA;'>₦{net_ngn:,.0f}</p><p style='font-size: 12px; color: #888;'>NGN</p></div>
        <div class='stat-box' style='flex: 1;'><p class='stat-value' style='color: #FFFFFF;'>{win_rate:.0f}%</p><p style='font-size: 12px; color: #888;'>Win Rate</p></div>
    </div>
</div>
""", unsafe_allow_html=True)

if losses >= 3:
    st.error("🛑 **SCENARIO C PROTECTION ACTIVATED.** You hit 3 losses. App locked to protect your Prop Firm account.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<p style='color: #888;'>Current Time</p><p style='font-size: 24px; font-weight: bold;'>{time_status['now']}</p>", unsafe_allow_html=True)
with col2: 
    status = "🟢 OPEN" if time_status['in_w1'] else "🔴 CLOSED"
    color = "#00FFAA" if time_status['in_w1'] else "#FF4B4B"
    st.markdown(f"<p style='color: #888;'>London (08:03)</p><p style='font-size: 24px; font-weight: bold; color: {color};'>{status}</p>", unsafe_allow_html=True)
with col3:
    status = "🟢 OPEN" if time_status['in_w2'] else "🔴 CLOSED"
    color = "#00FFAA" if time_status['in_w2'] else "#FF4B4B"
    st.markdown(f"<p style='color: #888;'>NY (14:45)</p><p style='font-size: 24px; font-weight: bold; color: {color};'>{status}</p>", unsafe_allow_html=True)

st.divider()

# --- AUTO WATCH MODE ---
if st.button("⚡ START AUTO-WATCH", use_container_width=True):
    if not time_status['active']:
        st.error(f"🚫 Market is locked. Please come back at 08:03 or 14:45.")
    else:
        placeholder = st.empty()
        signal_found = False
        
        while time_status['active'] and not signal_found:
            with placeholder.container():
                st.info("🔄 Watching market... Do not close this window. Scanning every 3 seconds.")
                
                signal = get_369_signal()
                if signal:
                    update_history(signal['price'])
                    
                    if signal['bias'] == "SELL":
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            entry = signal['sell_entry']
                            
                            # Standard Math (NairaTrader)
                            std_sl, std_tp = entry + 7.00, entry - 21.00
                            
                            # Cent Math (100c SL = $1, 1000c TP = $10)
                            cent_sl, cent_tp = entry + 1.00, entry - 10.00
                            
                            st.markdown(f"""
                            <div class='sell-card'>
                                <h1>🔴 EXECUTE SELL</h1>
                                <p class='big-font'>{entry:.2f}</p>
                                <div style='display: flex; gap: 10px; margin-top: 15px;'>
                                    <div class='lot-box' style='flex: 1;'>
                                        <h4>Standard (NairaTrader)</h4>
                                        <p><b>SL:</b> {std_sl:.2f} ($7)</p>
                                        <p><b>TP:</b> {std_tp:.2f} ($21)</p>
                                        <p style='color: #FFD700;'><b>Lot Size: 0.01</b></p>
                                    </div>
                                    <div class='lot-box' style='flex: 1;'>
                                        <h4>Cent Account</h4>
                                        <p><b>SL:</b> {cent_sl:.2f} (100c)</p>
                                        <p><b>TP:</b> {cent_tp:.2f} (1000c)</p>
                                        <p style='color: #FFD700;'><b>Lot Size: 0.01</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{cent_sl:.2f}", "TP": f"{cent_tp:.2f}", "Status": "Pending"})

                    elif signal['bias'] == "BUY":
                        if abs(signal['price'] - signal['buy_entry']) <= 5.0 and get_1m_confirmation("BUY"):
                            signal_found = True
                            entry = signal['buy_entry']
                            
                            std_sl, std_tp = entry - 7.00, entry + 21.00
                            cent_sl, cent_tp = entry - 1.00, entry + 10.00
                            
                            st.markdown(f"""
                            <div class='buy-card'>
                                <h1>🟢 EXECUTE BUY</h1>
                                <p class='big-font'>{entry:.2f}</p>
                                <div style='display: flex; gap: 10px; margin-top: 15px;'>
                                    <div class='lot-box' style='flex: 1;'>
                                        <h4>Standard (NairaTrader)</h4>
                                        <p><b>SL:</b> {std_sl:.2f} ($7)</p>
                                        <p><b>TP:</b> {std_tp:.2f} ($21)</p>
                                        <p style='color: #000;'><b>Lot Size: 0.01</b></p>
                                    </div>
                                    <div class='lot-box' style='flex: 1;'>
                                        <h4>Cent Account</h4>
                                        <p><b>SL:</b> {cent_sl:.2f} (100c)</p>
                                        <p><b>TP:</b> {cent_tp:.2f} (1000c)</p>
                                        <p style='color: #000;'><b>Lot Size: 0.01</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{cent_sl:.2f}", "TP": f"{cent_tp:.2f}", "Status": "Pending"})

                    if not signal_found:
                        st.markdown(f"<div class='wait-card'><h2 style='color: #FFA500;'>⏳ WAITING...</h2><p>Price: {signal['price']:.2f} | Bias: {signal['bias']}</p><p>Waiting for 369 Location and 1M Confirmation.</p></div>", unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3) # Scan every 3 seconds

st.divider()
st.subheader("📜 Trade History")
if len(st.session_state.history) == 0:
    st.write("No trades taken yet.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
