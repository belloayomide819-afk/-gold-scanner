import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="Gold AI Analysis", page_icon="🪙", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Base Dark/Gold Theme */
    .stApp { background-color: #0A0A0A; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top Ticker */
    .live-ticker {
        background-color: #121212; border: 1px solid #333; border-radius: 12px;
        padding: 15px 20px; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 20px;
    }
    
    /* Card Style */
    .epic-card {
        background-color: #121212; border: 1px solid #2A2A2A;
        border-radius: 16px; padding: 20px; margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    /* Gold Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #F2C94C 0%, #F2994A 100%);
        color: #000000; font-weight: 800; font-size: 16px;
        border: none; border-radius: 12px; padding: 15px;
        transition: all 0.3s; width: 100%;
    }
    .stButton > button:hover { opacity: 0.9; color: #000; }
    
    /* Signal Grids */
    .signal-grid {
        display: flex; gap: 10px; margin-top: 15px;
    }
    .grid-box {
        flex: 1; background: #1A1A1A; border-radius: 10px; padding: 10px; text-align: center;
        border: 1px solid #333;
    }
    .grid-label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px;}
    .grid-val { font-size: 18px; font-weight: 800; margin-top: 5px; font-family: monospace;}

    /* Buy / Sell Colors */
    .c-buy { color: #00E676; }
    .c-sell { color: #FF1744; }
    .c-gold { color: #F2C94C; }
</style>
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

# --- UI ---
time_status = check_time()

# Top Ticker
st.markdown(f"""
<div class='live-ticker'>
    <div style='display: flex; align-items: center; gap: 10px;'>
        <span style='font-size: 24px;'>🪙</span>
        <div>
            <div style='font-size: 12px; color: #888;'>LIVE PRICE</div>
            <div style='font-size: 20px; font-weight: 800; color: #F2C94C;'>XAUUSD</div>
        </div>
    </div>
    <div style='text-align: right;'>
        <div style='font-size: 24px; font-weight: 800;'>4055.51</div>
        <div style='font-size: 12px; color: #00E676;'>↗ spread 0.08</div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("⚡ START AUTO-WATCH", use_container_width=True):
    if not time_status['active']:
        st.error(f"🔒 Market is Locked. Current Time: {time_status['now']}. Please come back at 08:03 or 14:45.")
    else:
        placeholder = st.empty()
        signal_found = False
        start_time = datetime.now()
        
        while time_status['active'] and not signal_found:
            elapsed = (datetime.now() - start_time).seconds / 60
            if elapsed > 10: 
                with placeholder.container():
                    st.warning("⏳ **Session Ended.** No valid setup found in this window. Wait for the next session.")
                break
                
            with placeholder.container():
                signal = get_369_signal()
                
                if signal:
                    if signal['bias'] == "SELL":
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            entry = signal['sell_entry']
                            
                            std_sl = entry + 7.00
                            std_tp = entry - 21.00
                            cent_sl = entry + 1.00
                            cent_tp = entry - 10.00
                            
                            st.markdown(f"""
                            <div class='epic-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 24px;'>XAUUSD</h2>
                                        <p style='margin: 0; color: #888;'>T4F 369 Math</p>
                                    </div>
                                    <div style='background: #FF1744; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold;'>SELL</div>
                                </div>
                                
                                <div class='signal-grid'>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Entry</div>
                                        <div class='grid-val'>{entry:.2f}</div>
                                    </div>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Stop Loss</div>
                                        <div class='grid-val c-sell'>{std_sl:.2f}</div>
                                    </div>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Target</div>
                                        <div class='grid-val c-buy'>{std_tp:.2f}</div>
                                    </div>
                                </div>
                                
                                <div style='margin-top: 20px; background: #1A1A1A; padding: 15px; border-radius: 12px;'>
                                    <p style='margin: 0; color: #00E676; font-weight: bold;'>Standard (NairaTrader)</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #ccc;'>Lot Size: 0.01 | SL: {std_sl:.2f} | TP: {std_tp:.2f}</p>
                                </div>
                                <div style='margin-top: 10px; background: #1A1A1A; padding: 15px; border-radius: 12px;'>
                                    <p style='margin: 0; color: #F2C94C; font-weight: bold;'>Cent Account</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #ccc;'>Lot Size: 1.00 | SL: {cent_sl:.2f} (100c) | TP: {cent_tp:.2f} (1000c)</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})
                            
                    elif signal['bias'] == "BUY":
                        if abs(signal['price'] - signal['buy_entry']) <= 5.0 and get_1m_confirmation("BUY"):
                            signal_found = True
                            entry = signal['buy_entry']
                            
                            std_sl = entry - 7.00
                            std_tp = entry + 21.00
                            cent_sl = entry - 1.00
                            cent_tp = entry + 10.00
                            
                            st.markdown(f"""
                            <div class='epic-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 24px;'>XAUUSD</h2>
                                        <p style='margin: 0; color: #888;'>T4F 369 Math</p>
                                    </div>
                                    <div style='background: #00E676; color: black; padding: 8px 16px; border-radius: 8px; font-weight: bold;'>BUY</div>
                                </div>
                                
                                <div class='signal-grid'>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Entry</div>
                                        <div class='grid-val'>{entry:.2f}</div>
                                    </div>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Stop Loss</div>
                                        <div class='grid-val c-sell'>{std_sl:.2f}</div>
                                    </div>
                                    <div class='grid-box'>
                                        <div class='grid-label'>Target</div>
                                        <div class='grid-val c-buy'>{std_tp:.2f}</div>
                                    </div>
                                </div>
                                
                                <div style='margin-top: 20px; background: #1A1A1A; padding: 15px; border-radius: 12px;'>
                                    <p style='margin: 0; color: #00E676; font-weight: bold;'>Standard (NairaTrader)</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #ccc;'>Lot Size: 0.01 | SL: {std_sl:.2f} | TP: {std_tp:.2f}</p>
                                </div>
                                <div style='margin-top: 10px; background: #1A1A1A; padding: 15px; border-radius: 12px;'>
                                    <p style='margin: 0; color: #F2C94C; font-weight: bold;'>Cent Account</p>
                                    <p style='margin: 5px 0 0 0; font-size: 14px; color: #ccc;'>Lot Size: 1.00 | SL: {cent_sl:.2f} (100c) | TP: {cent_tp:.2f} (1000c)</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='epic-card' style='text-align: center; border-style: dashed;'>
                        <h3 style='color: #F2C94C;'>WATCHING MARKET...</h3>
                        <p style='font-size: 32px; font-weight: 800; margin: 10px 0;'>${signal['price']:.2f}</p>
                        <p style='color: #888; font-size: 14px;'>Scanning every 3 seconds. Auto-stops when session ends.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3)
