import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="T4F Signal Pro", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* Base Theme */
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', -apple-system, sans-serif; }
    
    /* Top Header */
    .top-header { 
        background: linear-gradient(90deg, #111 0%, #1A1A1A 100%); 
        padding: 15px 20px; border-radius: 12px; border: 1px solid #333;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;
    }
    .logo-text { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; }
    
    /* Dashboard Stats */
    .stat-box { 
        background: #111; border: 1px solid #222; border-radius: 12px; 
        padding: 15px; text-align: center;
    }
    .stat-val { font-size: 22px; font-weight: bold; margin: 0; }
    .stat-label { font-size: 12px; color: #666; margin: 5px 0 0 0; }
    
    /* Signal Card */
    .signal-card { 
        background: #0F0F0F; border-radius: 16px; padding: 25px; 
        border: 1px solid #2A2A2A; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        margin-bottom: 20px;
    }
    
    /* BUY/SELL Badges */
    .badge-buy { background: #00E676; color: #000; padding: 8px 20px; border-radius: 8px; font-weight: 900; font-size: 18px; }
    .badge-sell { background: #FF1744; color: #fff; padding: 8px 20px; border-radius: 8px; font-weight: 900; font-size: 18px; }
    
    /* Price Levels */
    .price-row { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #222; }
    .price-label { font-size: 14px; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}
    .price-val { font-size: 24px; font-weight: 900; }
    
    /* Account Tabs */
    .account-box { background: #161616; border-radius: 10px; padding: 15px; margin-top: 15px; border: 1px solid #222; }
    .std-box { border-left: 4px solid #00E676; }
    .cent-box { border-left: 4px solid #FFD700; }
    
    /* Waiting State */
    .wait-container { 
        background: #0F0F0F; border-radius: 16px; padding: 40px 20px; 
        border: 1px dashed #444; text-align: center; margin-top: 20px;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class='top-header'>
    <div style='display: flex; align-items: center; gap: 10px;'>
        <span style='font-size: 24px;'>⚡</span>
        <span class='logo-text'>T4F Signal Pro</span>
    </div>
    <div style='color: #00E676; font-size: 12px; font-weight: bold; background: rgba(0,230,118,0.1); padding: 5px 10px; border-radius: 20px;'>
        ● LIVE
    </div>
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

# --- DASHBOARD STATS ---
wins = sum(1 for t in st.session_state.history if "Win" in t["Status"])
losses = sum(1 for t in st.session_state.history if "Loss" in t["Status"])
net_usd = (wins * 21) - (losses * 7)
net_ngn = net_usd * 1500
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

st.markdown(f"""
<div style='display: flex; gap: 10px; margin-bottom: 25px;'>
    <div class='stat-box' style='flex: 1;'><p class='stat-val' style='color: #00E676;'>${net_usd}</p><p class='stat-label'>NET PROFIT</p></div>
    <div class='stat-box' style='flex: 1;'><p class='stat-val' style='color: #00E676;'>₦{net_ngn:,.0f}</p><p class='stat-label'>NAIRA</p></div>
    <div class='stat-box' style='flex: 1;'><p class='stat-val' style='color: #FFF;'>{win_rate:.0f}%</p><p class='stat-label'>WIN RATE</p></div>
</div>
""", unsafe_allow_html=True)

# --- MAIN APP LOGIC ---
time_status = check_time()

if st.button("⚡ START AUTO-WATCH", use_container_width=True, type="primary"):
    if not time_status['active']:
        st.error(f"🔒 **MARKET LOCKED.** Current Time: {time_status['now']}. Please come back at 08:03 or 14:45.")
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
                        <h2 style='color: #FFA500;'>⏳ WINDOW CLOSED</h2>
                        <p style='color: #888;'>No valid setup found in this session.</p>
                        <p style='font-weight: bold; margin-top: 20px;'>Wait for the next window.</p>
                    </div>
                    """, unsafe_allow_html=True)
                break
                
            with placeholder.container():
                signal = get_369_signal()
                
                if signal:
                    if signal['bias'] == "SELL":
                        if abs(signal['price'] - signal['sell_entry']) <= 5.0 and get_1m_confirmation("SELL"):
                            signal_found = True
                            entry = signal['sell_entry']
                            
                            # Standard Math (NairaTrader)
                            std_sl = entry + 7.00
                            std_tp = entry - 21.00
                            
                            # Cent Math (100c SL, 1000c TP)
                            cent_sl = entry + 1.00
                            cent_tp = entry - 10.00
                            
                            st.markdown(f"""
                            <div class='signal-card'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
                                    <div>
                                        <h1 style='margin: 0; font-size: 28px; font-weight: 900;'>XAUUSD</h1>
                                        <p style='color: #888; margin: 0; font-size: 14px;'>T4F 369 Code • M15</p>
                                    </div>
                                    <div class='badge-sell'>↘ SELL</div>
                                </div>
                                
                                <div class='price-row' style='border-top: 1px solid #222;'>
                                    <span class='price-label'>Entry Price</span>
                                    <span class='price-val' style='color: #FFF;'>{entry:.2f}</span>
                                </div>
                                <div class='price-row'>
                                    <span class='price-label'>Stop Loss</span>
                                    <span class='price-val' style='color: #FF1744;'>{std_sl:.2f}</span>
                                </div>
                                <div class='price-row'>
                                    <span class='price-label'>Take Profit (Final)</span>
                                    <span class='price-val' style='color: #00E676;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #00E676; font-weight: bold;'>NairaTrader (Standard)</span>
                                            <span style='color: #FFF; font-weight: bold; font-size: 14px;'>Lot Size: 0.01</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 14px;'>SL: <b>{std_sl:.2f}</b> ($7) | TP: <b>{std_tp:.2f}</b> ($21)</p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #FFD700; font-weight: bold;'>Cent Account</span>
                                            <span style='color: #FFF; font-weight: bold; font-size: 14px;'>Lot Size: 1.00</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 14px;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp:.2f}</b> (1000c)</p>
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
                                        <h1 style='margin: 0; font-size: 28px; font-weight: 900;'>XAUUSD</h1>
                                        <p style='color: #888; margin: 0; font-size: 14px;'>T4F 369 Code • M15</p>
                                    </div>
                                    <div class='badge-buy'>↗ BUY</div>
                                </div>
                                
                                <div class='price-row' style='border-top: 1px solid #222;'>
                                    <span class='price-label'>Entry Price</span>
                                    <span class='price-val' style='color: #FFF;'>{entry:.2f}</span>
                                </div>
                                <div class='price-row'>
                                    <span class='price-label'>Stop Loss</span>
                                    <span class='price-val' style='color: #FF1744;'>{std_sl:.2f}</span>
                                </div>
                                <div class='price-row'>
                                    <span class='price-label'>Take Profit (Final)</span>
                                    <span class='price-val' style='color: #00E676;'>{std_tp:.2f}</span>
                                </div>
                                
                                <div style='margin-top: 25px;'>
                                    <div class='account-box std-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #00E676; font-weight: bold;'>NairaTrader (Standard)</span>
                                            <span style='color: #FFF; font-weight: bold; font-size: 14px;'>Lot Size: 0.01</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 14px;'>SL: <b>{std_sl:.2f}</b> ($7) | TP: <b>{std_tp:.2f}</b> ($21)</p>
                                    </div>
                                    
                                    <div class='account-box cent-box'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #FFD700; font-weight: bold;'>Cent Account</span>
                                            <span style='color: #FFF; font-weight: bold; font-size: 14px;'>Lot Size: 1.00</span>
                                        </div>
                                        <p style='margin: 8px 0 0 0; font-size: 14px;'>SL: <b>{cent_sl:.2f}</b> (100c) | TP: <b>{cent_tp:.2f}</b> (1000c)</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                            if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{std_sl:.2f}", "TP": f"{std_tp:.2f}", "Status": "Pending"})

                if not signal_found:
                    st.markdown(f"""
                    <div class='wait-container'>
                        <h2 style='color: #00E676;'>⏳ WATCHING MARKET...</h2>
                        <p style='font-size: 32px; font-weight: 900; margin: 15px 0;'>${signal['price']:.2f}</p>
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
