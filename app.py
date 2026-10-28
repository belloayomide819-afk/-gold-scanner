import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

# Page Config
st.set_page_config(page_title="T4F Gold Terminal", page_icon="⚜️", layout="wide")

# Custom Premium CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
    
    /* Global Base */
    .stApp { background-color: #000000; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Top Ticker Bar */
    .ticker-bar {
        background-color: #0A0A0A; border-bottom: 1px solid #1F1F1F;
        padding: 15px 20px; display: flex; justify-content: space-between;
        align-items: center; font-size: 13px; font-weight: 600; color: #A1A1AA;
        margin-top: -60px; margin-bottom: 30px;
    }
    .status-open { color: #10B981; }
    .status-closed { color: #EF4444; }
    
    /* Logo */
    .logo-container { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: 1px;}
    .logo-icon { color: #F59E0B; font-size: 22px; }
    
    /* Dashboard Cards */
    .metric-card {
        background-color: #0A0A0A; border: 1px solid #1F1F1F;
        border-radius: 12px; padding: 20px; text-align: center;
    }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700; margin: 0; }
    .metric-label { font-size: 11px; color: #71717A; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 8px; font-weight: 600;}
    
    /* Primary Button */
    .stButton > button {
        background: #FFFFFF; color: #000000; 
        border: none; border-radius: 8px; padding: 16px 30px; 
        font-weight: 800; font-size: 16px; transition: all 0.2s; 
        width: 100%; margin-top: 10px; letter-spacing: 1px;
    }
    .stButton > button:hover { background: #D4D4D8; color: #000000; }
    
    /* Signal Card */
    .signal-card { 
        background-color: #0A0A0A; border: 1px solid #1F1F1F; 
        border-radius: 16px; padding: 30px; margin-top: 25px; 
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    .badge-sell { background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 8px 20px; border-radius: 8px; font-weight: 800; font-size: 14px; letter-spacing: 1px;}
    .badge-buy { background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); padding: 8px 20px; border-radius: 8px; font-weight: 800; font-size: 14px; letter-spacing: 1px;}
    
    /* Data Rows */
    .data-row { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #1F1F1F; }
    .data-label { color: #71717A; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;}
    .data-value { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; }
    
    /* Execution Boxes */
    .exec-box { background: #111111; border: 1px solid #1F1F1F; border-radius: 8px; padding: 16px; margin-top: 15px; }
    .std-box { border-left: 3px solid #10B981; }
    .cent-box { border-left: 3px solid #F59E0B; }
    
    /* Waiting State */
    .wait-container {
        background-color: #0A0A0A; border: 1px dashed #27272A;
        border-radius: 12px; padding: 50px 20px; text-align: center; margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'is_scanning' not in st.session_state:
    st.session_state.is_scanning = False

def play_sound():
    sound_html = """
    <audio autoplay>
        <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

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
        session_class = "status-open"
    else:
        session_text = "MARKET CLOSED"
        session_class = "status-closed"
        
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
    df_15m = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df_15m.empty: df_15m = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df_15m.empty: return None
        
    df_1h = yf.download("XAUUSD=X", period="5d", interval="1h", progress=False)
    if df_1h.empty: df_1h = yf.download("GC=F", period="5d", interval="1h", progress=False)
    
    df_1h['EMA50'] = df_1h['Close'].ewm(span=50, adjust=False).mean()
    current_1h_close = float(df_1h['Close'].iloc[-1].item())
    current_1h_ema = float(df_1h['EMA50'].iloc[-1].item())
    
    phase3_open = float(df_15m['Open'].iloc[-1].item()) 
    current_price = float(df_15m['Close'].iloc[-1].item())
    
    recent_high = float(df_15m['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df_15m['Low'].rolling(window=20).min().iloc[-1].item())
    
    sell_level = recent_high - get_digital_root(recent_high)
    buy_level = recent_low + get_digital_root(recent_low)
    
    bias = "SELL" if current_price > phase3_open else "BUY"
    
    is_macro_bullish = current_1h_close > current_1h_ema
    is_macro_bearish = current_1h_close < current_1h_ema
    
    return {
        "price": current_price, 
        "bias": bias,
        "sell_entry": sell_level, 
        "buy_entry": buy_level,
        "swing_high": recent_high,
        "swing_low": recent_low,
        "macro_bull": is_macro_bullish,
        "macro_bear": is_macro_bearish
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

def update_history(live_price):
    for trade in st.session_state.history:
        if trade["Status"] == "PENDING":
            entry = float(trade["Entry"])
            sl = float(trade["SL"])
            tp = float(trade["TP"])
            
            # Check if pending order was triggered
            if trade["Type"] == "SELL" and live_price >= entry: trade["Status"] = "ACTIVE"
            elif trade["Type"] == "BUY" and live_price <= entry: trade["Status"] = "ACTIVE"
                
        elif trade["Status"] == "ACTIVE":
            entry = float(trade["Entry"])
            sl = float(trade["SL"])
            tp = float(trade["TP"])
            
            # Check if TP or SL hit
            if trade["Type"] == "SELL":
                if live_price >= sl: trade["Status"] = "❌ LOSS"
                elif live_price <= tp: trade["Status"] = "✅ WIN"
            elif trade["Type"] == "BUY":
                if live_price <= sl: trade["Status"] = "❌ LOSS"
                elif live_price >= tp: trade["Status"] = "✅ WIN"

# --- TOP TICKER BAR ---
time_status = check_time()
live_price = get_live_price()
update_history(live_price)

st.markdown(f"""
<div class='ticker-bar'>
    <div class='logo-container'>
        <span class='logo-icon'>⚜️</span> T4F TERMINAL
    </div>
    <div class='{time_status["session_class"]}'>{time_status["session_text"]}</div>
    <div style='color: #FFF;'>XAUUSD <span class='{time_status["session_class"]}'>{live_price:.2f}</span></div>
</div>
""", unsafe_allow_html=True)

# --- PERFORMANCE DASHBOARD ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 15px;'>Account Performance</h4>", unsafe_allow_html=True)

wins = sum(1 for t in st.session_state.history if "WIN" in t["Status"])
losses = sum(1 for t in st.session_state.history if "LOSS" in t["Status"])
total_trades = wins + losses

# Calculate Profit based on actual TP/SL distances recorded
net_usd = 0
for t in st.session_state.history:
    if t["Status"] == "✅ WIN":
        # Approximate profit in USD for 0.01 lot Standard
        dist = abs(float(t["TP"]) - float(t["Entry"]))
        net_usd += (dist * 1) # $1 per point for 0.01 lot
    elif t["Status"] == "❌ LOSS":
        dist = abs(float(t["SL"]) - float(t["Entry"]))
        net_usd -= (dist * 1)

net_ngn = net_usd * 1500
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

st.markdown(f"""
<div style='display: flex; gap: 12px; margin-bottom: 30px;'>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FFFFFF;'>${net_usd:.2f}</p><p class='metric-label'>Net Profit</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FFFFFF;'>₦{net_ngn:,.0f}</p><p class='metric-label'>Naira Value</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FFFFFF;'>{win_rate:.0f}%</p><p class='metric-label'>Win Rate</p></div>
    <div class='metric-card' style='flex: 1;'><p class='metric-value' style='color: #FFFFFF;'>{total_trades}</p><p class='metric-label'>Total Trades</p></div>
</div>
""", unsafe_allow_html=True)

# --- TERMINAL ENGINE ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 15px;'>Terminal Engine</h4>", unsafe_allow_html=True)

if st.button("SCAN MARKET", use_container_width=True, disabled=st.session_state.is_scanning):
    if not time_status['active']:
        st.markdown(f"""
        <div style='background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 8px; padding: 20px; margin-top: 15px;'>
            <p style='color: #EF4444; font-weight: 800; font-size: 15px; margin: 0; letter-spacing: 1px;'>EXECUTION LOCKED</p>
            <p style='color: #A1A1AA; font-size: 13px; margin: 8px 0 0 0;'>Current time: {time_status['now']}. Please wait for the London (08:03) or NY (14:45) session.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.session_state.is_scanning = True
        placeholder = st.empty()
        signal_found = False
        start_time = datetime.now()
        
        while time_status['active'] and not signal_found:
            elapsed = (datetime.now() - start_time).seconds / 60
            if elapsed > 10: 
                with placeholder.container(): 
                    st.markdown("""
                    <div class='wait-container'>
                        <h3 style='color: #A1A1AA; margin: 0; letter-spacing: 1px;'>SESSION ENDED</h3>
                        <p style='color: #71717A; font-size: 13px; margin-top: 8px;'>No valid setups found. Wait for the next session.</p>
                    </div>
                    """, unsafe_allow_html=True)
                break
                
            with placeholder.container():
                signal = get_trap_signal()
                
                if signal:
                    if signal['bias'] == "SELL" and signal['macro_bear']:
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            play_sound()
                            
                            entry = signal['sell_entry']
                            dynamic_sl = signal['swing_high'] + 1.50 
                            sl_dist = dynamic_sl - entry
                            std_tp = entry - (sl_dist * 3)
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;'>XAUUSD</h2>
                                        <p style='color: #71717A; margin: 4px 0 0 0; font-size: 13px; letter-spacing: 1px;'>T4F TRAP & LIMIT</p>
                                    </div>
                                    <div class='badge-sell'>SELL LIMIT</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #1F1F1F;'>
                                    <span class='data-label'>Entry Limit</span>
                                    <span class='data-value' style='color: #FFFFFF;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{dynamic_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #10B981;'>{std_tp:.2f}</span>
                                </div>
                                <div class='data-row' style='border-bottom: none;'>
                                    <span class='data-label'>Risk : Reward</span>
                                    <span class='data-value' style='color: #F59E0B; font-size: 16px;'>1 : 3</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='exec-box std-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FFFFFF; font-weight: 700; font-size: 14px;'>Standard Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>0.01 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 14px; color: #A1A1AA;'>SL: <b style='color:#FFF;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FFF;'>{std_tp:.2f}</b></p>
                                    </div>
                                    
                                    <div class='exec-box cent-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FFFFFF; font-weight: 700; font-size: 14px;'>Cent Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>1.00 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 14px; color: #A1A1AA;'>SL: <b style='color:#FFF;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FFF;'>{std_tp:.2f}</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'PENDING' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{dynamic_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "PENDING"})
                            
                    elif signal['bias'] == "BUY" and signal['macro_bull']:
                        if abs(signal['price'] - signal['buy_entry']) <= 5.0 and get_1m_confirmation("BUY"):
                            signal_found = True
                            play_sound()
                            
                            entry = signal['buy_entry']
                            dynamic_sl = signal['swing_low'] - 1.50
                            sl_dist = entry - dynamic_sl
                            std_tp = entry + (sl_dist * 3)
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;'>
                                    <div>
                                        <h2 style='margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;'>XAUUSD</h2>
                                        <p style='color: #71717A; margin: 4px 0 0 0; font-size: 13px; letter-spacing: 1px;'>T4F TRAP & LIMIT</p>
                                    </div>
                                    <div class='badge-buy'>BUY LIMIT</div>
                                </div>
                                
                                <div class='data-row' style='border-top: 1px solid #1F1F1F;'>
                                    <span class='data-label'>Entry Limit</span>
                                    <span class='data-value' style='color: #FFFFFF;'>{entry:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Stop Loss</span>
                                    <span class='data-value' style='color: #EF4444;'>{dynamic_sl:.2f}</span>
                                </div>
                                <div class='data-row'>
                                    <span class='data-label'>Take Profit</span>
                                    <span class='data-value' style='color: #10B981;'>{std_tp:.2f}</span>
                                </div>
                                <div class='data-row' style='border-bottom: none;'>
                                    <span class='data-label'>Risk : Reward</span>
                                    <span class='data-value' style='color: #F59E0B; font-size: 16px;'>1 : 3</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='exec-box std-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FFFFFF; font-weight: 700; font-size: 14px;'>Standard Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>0.01 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 14px; color: #A1A1AA;'>SL: <b style='color:#FFF;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FFF;'>{std_tp:.2f}</b></p>
                                    </div>
                                    
                                    <div class='exec-box cent-box'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                            <span style='color: #FFFFFF; font-weight: 700; font-size: 14px;'>Cent Account</span>
                                            <span style='color: #71717A; font-weight: 600; font-size: 12px;'>1.00 LOTS</span>
                                        </div>
                                        <p style='margin: 0; font-size: 14px; color: #A1A1AA;'>SL: <b style='color:#FFF;'>{dynamic_sl:.2f}</b> | TP: <b style='color:#FFF;'>{std_tp:.2f}</b></p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'PENDING' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{dynamic_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "PENDING"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='wait-container'>
                        <h3 style='color: #F59E0B; margin: 0; font-size: 16px; letter-spacing: 2px;'>SCANNING MARKET</h3>
                        <p style='font-family: "JetBrains Mono", monospace; font-size: 42px; font-weight: 700; color: #FFFFFF; margin: 15px 0;'>{signal['price']:.2f}</p>
                        <p style='color: #71717A; font-size: 13px; letter-spacing: 1px;'>Awaiting 1H macro alignment & 1M confirmation...</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not signal_found:
                time.sleep(3)
        
        st.session_state.is_scanning = False
        st.rerun()

# --- EXECUTION HISTORY ---
st.markdown("<h4 style='color: #71717A; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 40px; margin-bottom: 15px;'>Execution History</h4>", unsafe_allow_html=True)

if len(st.session_state.history) == 0:
    st.markdown("""
    <div style='border: 1px dashed #27272A; border-radius: 8px; padding: 40px; text-align: center;'>
        <p style='color: #71717A; font-size: 14px; margin: 0; letter-spacing: 1px;'>NO SIGNALS GENERATED YET</p>
        <p style='color: #52525B; font-size: 12px; margin: 8px 0 0 0;'>Scans will appear here once a valid setup is found.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Format the history for display
    display_data = []
    for t in reversed(st.session_state.history):
        display_data.append({
            "Time": t["Time"],
            "Type": t["Type"],
            "Entry": t["Entry"],
            "SL": t["SL"],
            "TP": t["TP"],
            "Status": t["Status"]
        })
    df_history = pd.DataFrame(display_data)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    
    if st.button("CLEAR HISTORY", use_container_width=True):
        st.session_state.history = []
        st.rerun()
