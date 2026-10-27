import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="T4F Terminal", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
    .stApp { background-color: #09090B; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .metric-card {
        background-color: #18181B; border: 1px solid #27272A;
        border-radius: 12px; padding: 20px; text-align: center;
    }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 700; margin: 0; }
    .metric-label { font-size: 11px; color: #A1A1AA; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
    
    .stButton > button {
        background: linear-gradient(90deg, #F2C94C 0%, #F2994A 100%);
        color: #000000; font-weight: 800; font-size: 16px;
        border: none; border-radius: 12px; padding: 15px;
        transition: all 0.3s; width: 100%; margin-top: 10px;
    }
    .stButton > button:hover { opacity: 0.9; color: #000; }
    
    .live-ticker {
        background-color: #121212; border: 1px solid #333; border-radius: 12px;
        padding: 15px 20px; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 20px;
    }
    
    .signal-card { background-color: #18181B; border: 1px solid #27272A; border-radius: 16px; padding: 25px; margin-top: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .trade-badge-sell { background: #7F1D1D; color: #FCA5A5; padding: 6px 16px; border-radius: 8px; font-weight: 700; font-size: 14px; }
    .trade-badge-buy { background: #14532D; color: #86EFAC; padding: 6px 16px; border-radius: 8px; font-weight: 700; font-size: 14px; }
    
    .data-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #27272A; }
    .data-label { color: #A1A1AA; font-size: 14px; font-weight: 500; }
    .data-value { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; }
    
    .account-box { background: #09090B; border: 1px solid #27272A; border-radius: 10px; padding: 15px; margin-top: 15px; }
    .std-box { border-left: 3px solid #22C55E; }
    .cent-box { border-left: 3px solid #EAB308; }
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

def get_live_price():
    df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
    if df.empty: 
        df = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if df.empty: return 0.0
    return float(df['Close'].iloc[-1].item())

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

# --- LIVE PRICE SECTION ---
st.markdown("### 📡 Live Market")
col1, col2 = st.columns([2, 1])

live_price = get_live_price()

with col1:
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
            <div style='font-size: 24px; font-weight: 800;'>{live_price:.2f}</div>
            <div style='font-size: 12px; color: #00E676;'>↗ spread 0.08</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("🔄 Refresh Price"):
        st.rerun()

# --- DASHBOARD STATS ---
st.markdown("### 📊 Performance")
wins = sum(1 for t in st.session_state.history if "Win" in t["Status"])
losses = sum(1 for t in st.session_state.history if "Loss" in t["Status"])
net_usd = (wins * 21) - (losses * 7)
net_ngn = net_usd * 1500
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

st.markdown(f"""
<div style='display: flex; gap: 12px; margin-bottom: 20px;'>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #22C55E;'>${net_usd}</p><p class='metric-label'>Net Profit</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #22C55E;'>₦{net_ngn:,.0f}</p><p class='metric-label'>Naira Value</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FAFAFA;'>{win_rate:.0f}%</p><p class='metric-label'>Win Rate</p></div>
</div>
""", unsafe_allow_html=True)

# --- MAIN LOGIC ---
st.markdown("### ⚡ Trading Engine")
time_status = check_time()

if st.button("START AUTO-WATCH", use_container_width=True):
    if not time_status['active']:
        st.error(f"🔒 **Market Locked.** Current time: {time_status['now']}. Please wait for the London or NY session (08:03 or 14:45).")
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
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
                                    <div>
                                        <h1 style='margin: 0; font-size: 24px; font-weight: 800; font-family: "JetBrains Mono", monospace;'>XAUUSD</h1>
                                        <p style='color: #A1A1AA; margin: 0; font-size: 13px;'>T4F 369 • M15</p>
                                    </div>
                                    <div class='trade-badge-sell'>SELL</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #27272A;'>
                                    <span class='data-label'>Entry Price</span>
                                    <span class='data-value' style='color: #FAFAFA;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{std_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #22C55E;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #22C55E; font-weight: 600; font-size: 13px;'>NairaTrader (Standard)</span>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>0.01 Lots</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 13px; color: #A1A1AA;'>SL: <b>{std_sl:.2f}</b> ($7) | TP: <b>{std_tp:.2f}</b> ($21)</p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #EAB308; font-weight: 600; font-size: 13px;'>Cent Account</span>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>1.00 Lots</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 13px; color: #A1A1AA;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp:.2f}</b> (1000c)</p>
                                    </div>
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
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
                                    <div>
                                        <h1 style='margin: 0; font-size: 24px; font-weight: 800; font-family: "JetBrains Mono", monospace;'>XAUUSD</h1>
                                        <p style='color: #A1A1AA; margin: 0; font-size: 13px;'>T4F 369 • M15</p>
                                    </div>
                                    <div class='trade-badge-buy'>BUY</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #27272A;'>
                                    <span class='data-label'>Entry Price</span>
                                    <span class='data-value' style='color: #FAFAFA;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{std_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #22C55E;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #22C55E; font-weight: 600; font-size: 13px;'>NairaTrader (Standard)</span>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>0.01 Lots</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 13px; color: #A1A1AA;'>SL: <b>{std_sl:.2f}</b> ($7) | TP: <b>{std_tp:.2f}</b> ($21)</p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #EAB308; font-weight: 600; font-size: 13px;'>Cent Account</span>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>1.00 Lots</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 13px; color: #A1A1AA;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp:.2f}</b> (1000c)</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='signal-card' style='text-align: center; border-style: dashed;'>
                        <h3 style='color: #22C55E;'>WATCHING MARKET...</h3>
                        <p style='font-size: 32px; font-weight: 800; margin: 10px 0; font-family: monospace;'>${signal['price']:.2f}</p>
                        <p style='color: #A1A1AA; font-size: 14px;'>Scanning every 3 seconds. Auto-stops when session ends.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3)

# --- HISTORY TABLE ---
st.markdown("### 📜 Trade History")
if len(st.session_state.history) == 0:
    st.info("No signals generated today.")
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
