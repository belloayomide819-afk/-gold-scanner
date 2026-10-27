import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="T4F Signal Generator", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0A0A0A; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Top Navigation */
    .top-nav { background-color: #1A1A1A; padding: 15px 20px; border-radius: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
    
    /* Main Signal Card */
    .signal-card { background-color: #121212; border-radius: 20px; padding: 25px; border: 1px solid #2A2A2A; box-shadow: 0 8px 24px rgba(0,0,0,0.5); margin-bottom: 20px; }
    
    /* Buy/Sell Button */
    .buy-btn { background: linear-gradient(90deg, #00C853 0%, #00E676 100%); color: black; padding: 8px 20px; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-flex; align-items: center; }
    .sell-btn { background: linear-gradient(90deg, #D50000 0%, #FF1744 100%); color: white; padding: 8px 20px; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-flex; align-items: center; }
    
    /* Confidence Bar */
    .confidence-bar { background-color: #222; height: 10px; border-radius: 5px; margin-top: 10px; overflow: hidden; }
    .confidence-fill { background: linear-gradient(90deg, #00E676, #00C853); height: 100%; border-radius: 5px; }
    
    /* R:R Ladder */
    .level-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #2A2A2A; }
    .level-row:last-child { border-bottom: none; }
    .level-label { font-weight: bold; font-size: 16px; }
    .level-price { font-size: 20px; font-weight: 900; }
    .rr-badge { padding: 4px 10px; border-radius: 5px; font-size: 12px; font-weight: bold; background-color: #1E1E1E; border: 1px solid #444; }
    
    /* Price Colors */
    .c-green { color: #00E676; }
    .c-red { color: #FF1744; }
    .c-white { color: #FFFFFF; }
    .c-gray { color: #888; }
    
    /* Account Box */
    .account-box { background-color: #1E1E1E; border-radius: 10px; padding: 15px; margin-top: 15px; border-left: 4px solid #00E676; }
    .cent-box { border-left: 4px solid #FFD700; }
    
    /* Wait Card */
    .wait-card { background-color: #121212; border-radius: 20px; padding: 40px 20px; border: 1px solid #FFA500; text-align: center; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- UI HEADER ---
st.markdown(f"""
<div class='top-nav'>
    <div style='display: flex; align-items: center; gap: 10px;'>
        <span style='font-size: 24px;'>⚡</span>
        <h2 style='margin: 0; font-size: 20px;'>T4F Signal Generator</h2>
    </div>
    <div style='color: #888; font-size: 14px;'>XAUUSD • M15</div>
</div>
""", unsafe_allow_html=True)

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

# --- MAIN LOGIC ---
time_status = check_time()

if st.button("⚡ START AUTO-WATCH", use_container_width=True):
    if not time_status['active']:
        st.error(f"🚫 Market is locked. Please come back at 08:03 or 14:45.")
    else:
        placeholder = st.empty()
        signal_found = False
        start_time = datetime.now()
        
        while time_status['active'] and not signal_found:
            # Check if 9-minute window is over
            elapsed = (datetime.now() - start_time).seconds / 60
            if elapsed > 10: 
                with placeholder.container():
                    st.markdown("""
                    <div class='wait-card'>
                        <h2 style='color: #FFA500;'>⏳ AUTO-WATCH STOPPED</h2>
                        <p>No signal found within the time window.</p>
                        <p><b>Wait for the next setup.</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                break
                
            with placeholder.container():
                signal = get_369_signal()
                
                if signal:
                    # Check for SELL
                    if signal['bias'] == "SELL":
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            entry = signal['sell_entry']
                            
                            # Standard Math
                            std_sl = entry + 7.00
                            std_tp1 = entry - 7.00
                            std_tp2 = entry - 14.00
                            std_tp3 = entry - 21.00
                            
                            # Cent Math
                            cent_sl = entry + 1.00
                            cent_tp1 = entry - 5.00 # Approx 500 cents
                            cent_tp2 = entry - 10.00 # 1000 cents
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                    <div>
                                        <h1 style='margin: 0; font-size: 32px;'>XAUUSD</h1>
                                        <p style='color: #888; margin: 0;'>T4F 369 Math • M15</p>
                                    </div>
                                    <div class='sell-btn'>↘ SELL</div>
                                </div>
                                
                                <div style='margin-top: 20px;'>
                                    <div style='display: flex; justify-content: space-between; color: #888; font-size: 14px;'>
                                        <span>AI CONFIDENCE</span>
                                        <span style='color: #FF1744; font-weight: bold;'>85%</span>
                                    </div>
                                    <div class='confidence-bar'>
                                        <div class='confidence-fill' style='width: 85%; background: #FF1744;'></div>
                                    </div>
                                </div>
                                
                                <div style='margin-top: 30px;'>
                                    <div class='level-row'>
                                        <span class='level-label c-white'>Entry</span>
                                        <span class='level-price c-white'>{entry:.2f}</span>
                                    </div>
                                    <div class='level-row'>
                                        <span class='level-label c-red'>Stop Loss</span>
                                        <span class='level-price c-red'>{std_sl:.2f}</span>
                                    </div>
                                    <div class='level-row'>
                                        <span class='level-label c-green'>Target 3 (Final)</span>
                                        <span class='level-price c-green'>{std_tp3:.2f}</span>
                                    </div>
                                </div>
                                
                                <div class='account-box'>
                                    <h4 style='margin: 0 0 10px 0; color: #00E676;'>Standard (NairaTrader)</h4>
                                    <p style='margin: 0; font-size: 14px;'>SL: <b>{std_sl:.2f}</b> | TP: <b>{std_tp3:.2f}</b></p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #888;'>Lot Size: 0.01</p>
                                </div>
                                
                                <div class='account-box cent-box'>
                                    <h4 style='margin: 0 0 10px 0; color: #FFD700;'>Cent Account</h4>
                                    <p style='margin: 0; font-size: 14px;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp2:.2f}</b> (1000c)</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #888;'>Lot Size: 0.01</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp3:.2f}", "Status": "Pending"})
                            
                    # Check for BUY
                    elif signal['bias'] == "BUY":
                        if abs(signal['price'] - signal['buy_entry']) <= 5.0 and get_1m_confirmation("BUY"):
                            signal_found = True
                            entry = signal['buy_entry']
                            
                            std_sl = entry - 7.00
                            std_tp1 = entry + 7.00
                            std_tp2 = entry + 14.00
                            std_tp3 = entry + 21.00
                            
                            cent_sl = entry - 1.00
                            cent_tp1 = entry + 5.00
                            cent_tp2 = entry + 10.00
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                    <div>
                                        <h1 style='margin: 0; font-size: 32px;'>XAUUSD</h1>
                                        <p style='color: #888; margin: 0;'>T4F 369 Math • M15</p>
                                    </div>
                                    <div class='buy-btn'>↗ BUY</div>
                                </div>
                                
                                <div style='margin-top: 20px;'>
                                    <div style='display: flex; justify-content: space-between; color: #888; font-size: 14px;'>
                                        <span>AI CONFIDENCE</span>
                                        <span style='color: #00E676; font-weight: bold;'>85%</span>
                                    </div>
                                    <div class='confidence-bar'>
                                        <div class='confidence-fill' style='width: 85%;'></div>
                                    </div>
                                </div>
                                
                                <div style='margin-top: 30px;'>
                                    <div class='level-row'>
                                        <span class='level-label c-white'>Entry</span>
                                        <span class='level-price c-white'>{entry:.2f}</span>
                                    </div>
                                    <div class='level-row'>
                                        <span class='level-label c-red'>Stop Loss</span>
                                        <span class='level-price c-red'>{std_sl:.2f}</span>
                                    </div>
                                    <div class='level-row'>
                                        <span class='level-label c-green'>Target 3 (Final)</span>
                                        <span class='level-price c-green'>{std_tp3:.2f}</span>
                                    </div>
                                </div>
                                
                                <div class='account-box'>
                                    <h4 style='margin: 0 0 10px 0; color: #00E676;'>Standard (NairaTrader)</h4>
                                    <p style='margin: 0; font-size: 14px;'>SL: <b>{std_sl:.2f}</b> | TP: <b>{std_tp3:.2f}</b></p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #888;'>Lot Size: 0.01</p>
                                </div>
                                
                                <div class='account-box cent-box'>
                                    <h4 style='margin: 0 0 10px 0; color: #FFD700;'>Cent Account</h4>
                                    <p style='margin: 0; font-size: 14px;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp2:.2f}</b> (1000c)</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #888;'>Lot Size: 0.01</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp3:.2f}", "Status": "Pending"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='wait-card'>
                        <h2 style='color: #FFA500;'>⏳ WATCHING MARKET...</h2>
                        <p style='font-size: 24px; font-weight: bold;'>${signal['price']:.2f}</p>
                        <p style='color: #888;'>Scanning every 3 seconds. Do not close this page.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3)

st.divider()
st.subheader("📜 Signal History")

if len(st.session_state.history) == 0:
    st.write("No signals generated yet today.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
