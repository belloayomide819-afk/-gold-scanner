import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Page Config
st.set_page_config(page_title="Apex Twin Engine", page_icon="⚡", layout="wide")

# Premium CSS Design
st.markdown("""
<style>
    /* Global Background */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
        padding: 20px; border-radius: 15px; border-left: 5px solid #00FFAA;
        margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0, 255, 170, 0.1);
    }
    
    /* Time Windows */
    .window-open { color: #00FFAA; font-weight: bold; font-size: 18px; }
    .window-locked { color: #FF4B4B; font-weight: bold; font-size: 18px; }
    
    /* Trade Cards */
    .sell-card {
        background: linear-gradient(135deg, #FF4B4B 0%, #B22222 100%);
        padding: 25px; border-radius: 15px; text-align: center; color: white;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4); border: 2px solid #FF4B4B;
    }
    .buy-card {
        background: linear-gradient(135deg, #00FFAA 0%, #008B5E 100%);
        padding: 25px; border-radius: 15px; text-align: center; color: black;
        box-shadow: 0 4px 15px rgba(0, 255, 170, 0.4); border: 2px solid #00FFAA;
    }
    
    /* Wait Card */
    .wait-card {
        background-color: #1E1E1E; padding: 30px; border-radius: 15px; 
        border: 2px solid #FFA500; text-align: center;
        box-shadow: 0 4px 15px rgba(255, 165, 0, 0.2);
    }
    
    /* Dashboard Stats */
    .stat-box {
        background-color: #1E1E1E; padding: 15px; border-radius: 10px; 
        text-align: center; border: 1px solid #333;
    }
    .stat-value { font-size: 24px; font-weight: bold; margin: 0; }
    .stat-label { font-size: 14px; color: #888; margin: 0; }
    
    /* Big Fonts */
    .big-font { font-size: 45px !important; font-weight: 900; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Apex Twin Engine")
st.markdown("**T4F 369 Math** + **H1 Trendlines** + **1M Confirmation**")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- LOGIC FUNCTIONS ---
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
    
    if in_w1 or in_w2: next_scan = (now + timedelta(minutes=3)).strftime('%H:%M')
    elif current_time < w1_start: next_scan = "08:03"
    elif current_time < w2_start: next_scan = "14:45"
    else: next_scan = "08:03 (Tomorrow)"
    
    return {"now": now.strftime('%H:%M'), "active": in_w1 or in_w2, "next_scan": next_scan, "in_w1": in_w1, "in_w2": in_w2}

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

    if len(recent_lows) == 2:
        idx1, idx2 = df.index.get_loc(recent_lows.index[0]), df.index.get_loc(recent_lows.index[1])
        price1, price2 = float(recent_lows.iloc[0]), float(recent_lows.iloc[1])
        slope = (price2 - price1) / (idx2 - idx1)
        projected = price1 + slope * (current_idx - idx1)
        if abs(current_price - projected) <= 5.0: return "BUY"

    if len(recent_highs) == 2:
        idx1, idx2 = df.index.get_loc(recent_highs.index[0]), df.index.get_loc(recent_highs.index[1])
        price1, price2 = float(recent_highs.iloc[0]), float(recent_highs.iloc[1])
        slope = (price2 - price1) / (idx2 - idx1)
        projected = price1 + slope * (current_idx - idx1)
        if abs(current_price - projected) <= 5.0: return "SELL"
        
    return "NEUTRAL"

def get_1m_confirmation(direction):
    df = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
    if df.empty: df = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if df.empty: return False
    
    last_c = df.iloc[-1]
    prev_c = df.iloc[-2]
    
    if direction == "SELL" and last_c['Close'] < prev_c['Open']: return True
    if direction == "BUY" and last_c['Close'] > prev_c['Open']: return True
    return False

def get_t4f_signal():
    df = yf.download("XAUUSD=X", period="2d", interval="15m", progress=False)
    if df.empty: df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if df.empty: return None
        
    recent_high = float(df['High'].rolling(window=20).max().iloc[-1].item())
    recent_low = float(df['Low'].rolling(window=20).min().iloc[-1].item())
    current_price = float(df['Close'].iloc[-1].item())
    
    return {"price": current_price, "sell_entry": recent_high - get_digital_root(recent_high), "buy_entry": recent_low + get_digital_root(recent_low)}

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

# --- DASHBOARD UI ---
time_status = check_time()

# Calculate Stats
wins = sum(1 for t in st.session_state.history if "Win" in t["Status"])
losses = sum(1 for t in st.session_state.history if "Loss" in t["Status"])
pending = sum(1 for t in st.session_state.history if "Pending" in t["Status"] or "Active" in t["Status"])
net_usd = (wins * 21) - (losses * 7)
net_ngn = net_usd * 1500
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

# Top Header Card
st.markdown(f"""
<div class='header-card'>
    <h2 style='margin: 0; color: #FFFFFF;'>NairaTrader Instant Account</h2>
    <p style='margin: 5px 0 15px 0; color: #888;'>Target: ₦20,000 | Risk per trade: $7</p>
    <div style='display: flex; gap: 20px;'>
        <div class='stat-box' style='flex: 1;'>
            <p class='stat-value' style='color: #00FFAA;'>${net_usd}</p>
            <p class='stat-label'>Net Profit (USD)</p>
        </div>
        <div class='stat-box' style='flex: 1;'>
            <p class='stat-value' style='color: #00FFAA;'>₦{net_ngn:,.0f}</p>
            <p class='stat-label'>Net Profit (NGN)</p>
        </div>
        <div class='stat-box' style='flex: 1;'>
            <p class='stat-value' style='color: #FFFFFF;'>{win_rate:.0f}%</p>
            <p class='stat-label'>Win Rate</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Scenario Logic
if losses >= 3:
    st.error("🛑 **SCENARIO C PROTECTION ACTIVATED.** You hit 3 losses. The app is locked to protect your account. Come back next week.")
    st.stop()
elif wins >= 4:
    st.success(f"🚀 **SCENARIO B (MONSTER WEEK) UNLOCKED!** You are at +${net_usd}. You are crushing it.")
elif wins >= 2 and losses <= 2:
    st.info(f"✅ **SCENARIO A (STANDARD WEEK).** You are at +${net_usd}. Keep following the rules.")
elif losses >= 2:
    st.warning(f"⚠️ **SCENARIO C (CHOPPY WEEK).** You are at ${net_usd}. Be careful. Do not take any more losses.")
else:
    st.write(f"⏳ **IN PROGRESS** | Net: ${net_usd} | Wins: {wins} | Losses: {losses}")

st.divider()

# Window Status
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<p style='color: #888;'>Current Time</p><p style='font-size: 24px; font-weight: bold;'>{time_status['now']}</p>", unsafe_allow_html=True)
with col2:
    status = "🟢 OPEN" if time_status['in_w1'] else "🔴 CLOSED"
    color = "#00FFAA" if time_status['in_w1'] else "#FF4B4B"
    st.markdown(f"<p style='color: #888;'>London Window (08:03)</p><p style='font-size: 24px; font-weight: bold; color: {color};'>{status}</p>", unsafe_allow_html=True)
with col3:
    status = "🟢 OPEN" if time_status['in_w2'] else "🔴 CLOSED"
    color = "#00FFAA" if time_status['in_w2'] else "#FF4B4B"
    st.markdown(f"<p style='color: #888;'>NY Window (14:45)</p><p style='font-size: 24px; font-weight: bold; color: {color};'>{status}</p>", unsafe_allow_html=True)

st.divider()

# --- SCAN LOGIC ---
if st.button("⚡ SCAN CONFLUENCE ENGINE", use_container_width=True):
    with st.spinner("Scanning Market Structure..."):
        
        trend_bias = get_trendline_bias()
        t4f = get_t4f_signal()
        
        if not t4f:
            st.error("Data error.")
        else:
            update_history(t4f['price'])
            
            if trend_bias == "SELL" and time_status['active']:
                if get_1m_confirmation("SELL"):
                    entry = t4f['sell_entry']
                    st.markdown(f"""
                    <div class='sell-card'>
                        <h1>🔴 EXECUTE SELL</h1>
                        <p class='big-font'>{entry:.2f}</p>
                        <p>Stop Loss: <b>{entry+7:.2f}</b> | Take Profit: <b>{entry-21:.2f}</b></p>
                        <p style='font-size: 14px; margin-top: 10px;'>✅ Trendline Bearish<br>✅ T4F Level Hit<br>✅ 1M Momentum Confirmed</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    exists = any(d['Type'] == 'SELL' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                    if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "SELL", "Entry": f"{entry:.2f}", "SL": f"{entry+7:.2f}", "TP": f"{entry-21:.2f}", "Status": "Pending"})
                else:
                    st.markdown(f"<div class='wait-card'><h2 style='color: #FFA500;'>⏳ 1M NOT CONFIRMED</h2><p>Setup found, but 1M momentum is weak.</p><p>👉 <b>Scan again at {time_status['next_scan']}</b></p></div>", unsafe_allow_html=True)

            elif trend_bias == "BUY" and time_status['active']:
                if get_1m_confirmation("BUY"):
                    entry = t4f['buy_entry']
                    st.markdown(f"""
                    <div class='buy-card'>
                        <h1>🟢 EXECUTE BUY</h1>
                        <p class='big-font'>{entry:.2f}</p>
                        <p>Stop Loss: <b>{entry-7:.2f}</b> | Take Profit: <b>{entry+21:.2f}</b></p>
                        <p style='font-size: 14px; margin-top: 10px; color: black;'>✅ Trendline Bullish<br>✅ T4F Level Hit<br>✅ 1M Momentum Confirmed</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    exists = any(d['Type'] == 'BUY' and d['Entry'] == f"{entry:.2f}" and d['Status'] == 'Pending' for d in st.session_state.history)
                    if not exists: st.session_state.history.append({"Time": time_status['now'], "Type": "BUY", "Entry": f"{entry:.2f}", "SL": f"{entry-7:.2f}", "TP": f"{entry+21:.2f}", "Status": "Pending"})
                else:
                    st.markdown(f"<div class='wait-card'><h2 style='color: #FFA500;'>⏳ 1M NOT CONFIRMED</h2><p>Setup found, but 1M momentum is weak.</p><p>👉 <b>Scan again at {time_status['next_scan']}</b></p></div>", unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class='wait-card'>
                    <h2 style='color: #FFA500;'>⏳ NO CONFLUENCE YET</h2>
                    <p>Trendline: {trend_bias} | T4F Window: {'OPEN' if time_status['active'] else 'LOCKED'}</p>
                    <p>👉 <b>Scan again at {time_status['next_scan']}</b></p>
                </div>
                """, unsafe_allow_html=True)

# --- HISTORY TABLE ---
st.divider()
st.markdown("### 📜 Trade History")
if len(st.session_state.history) == 0:
    st.markdown("<p style='color: #888;'>No trades taken yet. Press scan during a window.</p>", unsafe_allow_html=True)
else:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True)
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
