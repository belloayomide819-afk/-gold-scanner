import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="T4F Terminal", page_icon="◈", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
    
    /* Global Base */
    .stApp { background-color: #050505; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Top Ticker Bar */
    .ticker-bar {
        background-color: #0A0A0A; border-bottom: 1px solid #1F1F1F;
        padding: 12px 20px; display: flex; justify-content: space-between;
        align-items: center; font-size: 12px; font-weight: 600; color: #A1A1AA;
        margin-top: -60px; margin-bottom: 25px;
    }
    .ticker-green { color: #22C55E; }
    .ticker-red { color: #EF4444; }
    
    /* Dashboard Metrics */
    .metric-card {
        background-color: #0A0A0A; border: 1px solid #1F1F1F;
        border-radius: 12px; padding: 20px; text-align: center;
    }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; margin: 0; }
    .metric-label { font-size: 11px; color: #71717A; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 8px; font-weight: 600;}
    
    /* Action Button */
    .stButton > button {
        background: #FAFAFA; color: #050505; 
        border: none; border-radius: 8px; padding: 15px 30px; 
        font-weight: 700; font-size: 15px; transition: all 0.2s; 
        width: 100%; margin-top: 10px; letter-spacing: 1px;
    }
    .stButton > button:hover { background: #D4D4D8; color: #050505; }
    
    /* Signal Card */
    .signal-card { 
        background-color: #0A0A0A; border: 1px solid #1F1F1F; 
        border-radius: 12px; padding: 25px; margin-top: 20px; 
    }
    .trade-badge-sell { background: #270C0C; color: #EF4444; border: 1px solid #7F1D1D; padding: 6px 16px; border-radius: 6px; font-weight: 700; font-size: 13px; letter-spacing: 1px;}
    .trade-badge-buy { background: #0A1F13; color: #22C55E; border: 1px solid #14532D; padding: 6px 16px; border-radius: 6px; font-weight: 700; font-size: 13px; letter-spacing: 1px;}
    
    /* Data Rows */
    .data-row { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #1F1F1F; }
    .data-label { color: #71717A; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;}
    .data-value { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; }
    
    /* Account Boxes */
    .account-box { background: #111111; border: 1px solid #1F1F1F; border-radius: 8px; padding: 16px; margin-top: 12px; }
    .std-box { border-left: 2px solid #22C55E; }
    .cent-box { border-left: 2px solid #EAB308; }
    
    /* Waiting State */
    .wait-container {
        background-color: #0A0A0A; border: 1px dashed #27272A;
        border-radius: 12px; padding: 40px 20px; text-align: center; margin-top: 20px;
    }
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
    
    if in_w1 or in_w2:
        session_text = "SESSION OPEN"
        session_class = "ticker-green"
    else:
        session_text = "MARKET CLOSED"
        session_class = "ticker-red"
        
    return {"now": now.strftime('%H:%M'), "active": in_w1 or in_w2, "session_text": session_text, "session_class": session_class}

def get_live_price():
    try:
        df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        if df.empty: df = yf.download("GC=F", period="1d", interval="1m", progress=False)
        if df.empty: return 0.0
        return float(df['Close'].iloc[-1].item())
    except:
        return 0.0

def get_trap_signal():
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
        "buy_entry": buy_level,
        "swing_high": recent_high,
        "swing_low": recent_low
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

# --- TOP TICKER BAR ---
time_status = check_time()
live_price = get_live_price()

st.markdown(f"""
<div class='ticker-bar'>
    <div>XAUUSD <span class='ticker-green'>● LIVE</span></div>
    <div class='{time_status["session_class"]}'>{time_status["session_text"]}</div>
    <div>{time_status['now']} WAT</div>
</div>
""", unsafe_allow_html=True)

# --- DASHBOARD STATS ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;'>Account Performance</h4>", unsafe_allow_html=True)

wins = sum(1 for t in st.session_state.history if "Win" in t["Status"])
losses = sum(1 for t in st.session_state.history if "Loss" in t["Status"])
net_usd = (wins * 21) - (losses * 7) 
net_ngn = net_usd * 1500
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

st.markdown(f"""
<div style='display: flex; gap: 12px; margin-bottom: 25px;'>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FAFAFA;'>${net_usd}</p><p class='metric-label'>Net Profit</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FAFAFA;'>₦{net_ngn:,.0f}</p><p class='metric-label'>Naira Value</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FAFAFA;'>{win_rate:.0f}%</p><p class='metric-label'>Win Rate</p></div>
</div>
""", unsafe_allow_html=True)

# --- MAIN LOGIC ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;'>Terminal Engine</h4>", unsafe_allow_html=True)

if st.button("INITIATE SCAN", use_container_width=True):
    if not time_status['active']:
        st.markdown(f"""
        <div style='background-color: #270C0C; border: 1px solid #7F1D1D; border-radius: 8px; padding: 16px; margin-top: 15px;'>
            <p style='color: #EF4444; font-weight: 700; font-size: 14px; margin: 0;'>EXECUTION LOCKED</p>
            <p style='color: #A1A1AA; font-size: 13px; margin: 5px 0 0 0;'>Current time: {time_status['now']}. Please wait for the London (08:03) or NY (14:45) session.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        placeholder = st.empty()
        signal_found = False
        start_time = datetime.now()
        
        while time_status['active'] and not signal_found:
            elapsed = (datetime.now() - start_time).seconds / 60
            if elapsed > 10: 
                with placeholder.container(): 
                    st.markdown("""
                    <div class='wait-container'>
                        <h3 style='color: #A1A1AA; margin: 0;'>SESSION ENDED</h3>
                        <p style='color: #71717A; font-size: 13px; margin-top: 8px;'>No valid setups found in this window.</p>
                    </div>
                    """, unsafe_allow_html=True)
                break
                
            with placeholder.container():
                signal = get_trap_signal()
                
                if signal:
                    if signal['bias'] == "SELL":
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            entry = signal['sell_entry']
                            
                            # Trap Dynamic SL
                            dynamic_sl = signal['swing_high'] + 1.50 
                            sl_dist = dynamic_sl - entry
                            std_tp = entry - (sl_dist * 3)
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 1px;'>XAUUSD</h2>
                                        <p style='color: #71717A; margin: 2px 0 0 0; font-size: 12px; letter-spacing: 1px;'>TRAP & LIMIT</p>
                                    </div>
                                    <div class='trade-badge-sell'>SELL LIMIT</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #1F1F1F;'>
                                    <span class='data-label'>Entry Limit</span>
                                    <span class='data-value' style='color: #FAFAFA;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{dynamic_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #22C55E;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>Standard Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>0.01 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 13px; color: #A1A1AA;'>SL: <b style='color:#FAFAFA;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FAFAFA;'>{std_tp:.2f}</b></p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>Cent Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>1.00 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 13px; color: #A1A1AA;'>SL: <b style='color:#FAFAFA;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FAFAFA;'>{std_tp:.2f}</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{dynamic_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})
                            
                    elif signal['bias'] == "BUY":
                        if abs(signal['price'] - signal['buy_entry']) <= 5.0 and get_1m_confirmation("BUY"):
                            signal_found = True
                            entry = signal['buy_entry']
                            
                            # Trap Dynamic SL
                            dynamic_sl = signal['swing_low'] - 1.50
                            sl_dist = entry - dynamic_sl
                            std_tp = entry + (sl_dist * 3)
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 1px;'>XAUUSD</h2>
                                        <p style='color: #71717A; margin: 2px 0 0 0; font-size: 12px; letter-spacing: 1px;'>TRAP & LIMIT</p>
                                    </div>
                                    <div class='trade-badge-buy'>BUY LIMIT</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #1F1F1F;'>
                                    <span class='data-label'>Entry Limit</span>
                                    <span class='data-value' style='color: #FAFAFA;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{dynamic_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #22C55E;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>Standard Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>0.01 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 13px; color: #A1A1AA;'>SL: <b style='color:#FAFAFA;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FAFAFA;'>{std_tp:.2f}</b></p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FAFAFA; font-weight: 600; font-size: 13px;'>Cent Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>1.00 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 13px; color: #A1A1AA;'>SL: <b style='color:#FAFAFA;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FAFAFA;'>{std_tp:.2f}</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{dynamic_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='wait-container'>
                        <h3 style='color: #22C55E; margin: 0; font-size: 16px; letter-spacing: 2px;'>SCANNING MARKET</h3>
                        <p style='font-family: "JetBrains Mono", monospace; font-size: 36px; font-weight: 700; color: #FAFAFA; margin: 15px 0;'>{signal['price']:.2f}</p>
                        <p style='color: #71717A; font-size: 13px; letter-spacing: 1px;'>Awaiting institutional trap sequence.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3)

# --- HISTORY TABLE ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 30px;'>Execution History</h4>", unsafe_allow_html=True)

if len(st.session_state.history) == 0:
    st.markdown("""
    <div style='border: 1px dashed #27272A; border-radius: 8px; padding: 20px; text-align: center;'>
        <p style='color: #71717A; font-size: 13px; margin: 0; letter-spacing: 1px;'>NO SIGNALS GENERATED</p>
    </div>
    """, unsafe_allow_html=True)
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    if st.button("CLEAR LOGS"):
        st.session_state.history = []
        st.rerun()
