import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date
import math
import time
import altair as alt
from scipy.stats import norm

st.set_page_config(page_title="Forward Factor Pro", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 CUSTOM CSS: INSTITUTIONAL UI OVERHAUL
# ==========================================
st.markdown("""
    <style>
    /* Global Theme & Background */
    .stApp { 
        background-color: #0A0D14 !important; 
        color: #E2E8F0 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Default Clutter */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography Overhauls */
    h1 { color: #FFFFFF !important; font-weight: 800 !important; letter-spacing: -1px; }
    h2, h3 { color: #F8FAFC !important; font-weight: 600 !important; }
    p, span, label { color: #94A3B8 !important; }
    
    /* 🎛️ Hyper-Intuitive Input Boxes */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #121621 !important;
        border: 1px solid #2A3143 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    
    /* Input Focus Glow */
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #FF4B00 !important;
        box-shadow: 0 0 0 3px rgba(255, 75, 0, 0.25), inset 0 2px 4px rgba(0,0,0,0.2) !important;
        outline: none !important;
    }

    /* Primary Action Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #FF4B00 0%, #D43F00 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        padding: 12px 24px !important;
        width: 100%;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 15px rgba(255, 75, 0, 0.3) !important;
    }
    .stButton>button:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 6px 20px rgba(255, 75, 0, 0.4) !important;
        background: linear-gradient(135deg, #FF5B1A 0%, #E64400 100%) !important;
    }

    /* 📊 Metric Cards (Glassmorphism) */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #141925 0%, #0D1017 100%);
        border: 1px solid #2A3143;
        border-radius: 12px;
        padding: 20px 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: #FF4B00;
    }
    div[data-testid="stMetricValue"] { 
        color: #FFFFFF !important; 
        font-size: 2rem !important; 
        font-weight: 700 !important;
    }
    div[data-testid="stMetricDelta"] { font-weight: 600 !important; }

    /* 📁 Custom Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
        border-bottom: 2px solid #1E2433;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #121621;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        color: #94A3B8;
        border: 1px solid #2A3143;
        border-bottom: none;
        transition: all 0.2s ease;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
        background-color: #1A202F;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B00 !important;
        color: #FFFFFF !important;
        border-color: #FF4B00 !important;
        box-shadow: 0 -4px 15px rgba(255, 75, 0, 0.2);
    }

    /* Signal Cards */
    .signal-card-green {
        background: linear-gradient(135deg, #062615 0%, #0A1410 100%);
        border: 1px solid #10B981;
        border-left: 6px solid #10B981;
        border-radius: 10px; padding: 25px; color: white; margin-top: 15px;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.15);
    }
    .signal-card-neutral {
        background: linear-gradient(145deg, #141925 0%, #0D1017 100%);
        border: 1px solid #2A3143;
        border-left: 6px solid #475569;
        border-radius: 10px; padding: 25px; margin-top: 15px;
    }
    
    /* Native Container Styling for Double Calendar */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2A3143 !important;
        background-color: #121621 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2A3143;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CORE QUANTITATIVE FUNCTIONS
# ==========================================
def get_dte(expiration_date_str):
    exp_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    today = date.today()
    return (exp_date - today).days

def format_nice_date(date_str):
    if date_str == "N/A": return date_str
    dt_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return f"{dt_obj.day} {dt_obj.strftime('%B %Y')}"

def safe_num(val, default=0.0):
    try: return default if pd.isna(val) else float(val)
    except: return default

def safe_int(val, default=0):
    try: return default if pd.isna(val) else int(val)
    except: return default

def calc_delta(S, K, T_days, r, sigma, opt_type='call'):
    T = T_days / 365.0
    if T <= 0 or sigma <= 0: return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return norm.cdf(d1) if opt_type == 'call' else norm.cdf(d1) - 1.0

def fetch_volatility_regime(ticker_symbol):
    try:
        tkr = yf.Ticker(ticker_symbol)
        df = tkr.history(period="1y")
        if df.empty or len(df) < 30: return None
        df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
        df['HV30'] = df['Log_Ret'].rolling(window=21).std() * math.sqrt(252) * 100
        hv_series = df['HV30'].dropna()
        if hv_series.empty: return None
        current_hv = hv_series.iloc[-1]
        min_hv, max_hv = hv_series.min(), hv_series.max()
        if max_hv == min_hv: return None
        return {'current_hv': current_hv, 'hv_rank': ((current_hv - min_hv) / (max_hv - min_hv)) * 100}
    except: return None

def fetch_next_earnings(tkr_obj):
    future_dates = []
    today = date.today()
    
    try:
        cal = tkr_obj.calendar
        if isinstance(cal, dict) and 'Earnings Date' in cal:
            for d in cal['Earnings Date']:
                if pd.notna(d):
                    dt = pd.to_datetime(d).tz_localize(None).date()
                    if dt >= today: future_dates.append(dt)
        elif isinstance(cal, pd.DataFrame) and 'Earnings Date' in cal.index:
            val = cal.loc['Earnings Date'].values[0]
            if pd.notna(val):
                dt = pd.to_datetime(val).tz_localize(None).date()
                if dt >= today: future_dates.append(dt)
    except: pass

    if not future_dates:
        try:
            edf = tkr_obj.get_earnings_dates(limit=10)
            if edf is not None and not edf.empty:
                for d in edf.index:
                    if pd.notna(d):
                        dt = pd.to_datetime(d).tz_localize(None).date()
                        if dt >= today: future_dates.append(dt)
        except: pass
        
    if future_dates:
        return min(future_dates)
    return None

def fetch_ticker_data(ticker, target_front, target_back):
    tkr = yf.Ticker(ticker)
    try: current_price = tkr.fast_info['lastPrice']
    except:
        try: current_price = tkr.history(period="1d", interval="1m")['Close'].iloc[-1]
        except: return None

    next_earnings = fetch_next_earnings(tkr)
        
    options_dates = tkr.options
    if not options_dates: return None
    dates_with_dte = [{'date': d, 'dte': get_dte(d)} for d in options_dates if get_dte(d) > 0]
    
    if len(dates_with_dte) < 2: return None
    front_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_front))
    back_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_back))
    
    if front_exp['date'] == back_exp['date']:
        dates_with_dte.remove(front_exp)
        if dates_with_dte: back_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_back))
        else: return None
    if back_exp['dte'] <= front_exp['dte']: return None

    def get_atm_data(exp_date, current_price):
        try:
            chain = tkr.option_chain(exp_date).calls
            if chain.empty: return 0.0, 0.0, 0.0, 0.0, 0
            chain['distance'] = abs(chain['strike'] - current_price)
            atm = chain.loc[chain['distance'].idxmin()]
            return safe_num(atm['impliedVolatility']), safe_num(atm['strike']), safe_num(atm.get('bid')), safe_num(atm.get('ask')), safe_int(atm.get('openInterest'))
        except: return 0.0, 0.0, 0.0, 0.0, 0

    f_iv, f_strike, f_bid, f_ask, f_oi = get_atm_data(front_exp['date'], current_price)
    b_iv, b_strike, b_bid, b_ask, b_oi = get_atm_data(back_exp['date'], current_price)
    if f_iv == 0.0 or b_iv == 0.0: return None

    return {
        'price': current_price, 'next_earnings': next_earnings,
        'f_dte': front_exp['dte'], 'f_date': front_exp['date'], 'f_iv': f_iv, 'f_strike': f_strike, 'f_bid': f_bid, 'f_ask': f_ask, 'f_oi': f_oi,
        'b_dte': back_exp['dte'], 'b_date': back_exp['date'], 'b_iv': b_iv, 'b_strike': b_strike, 'b_bid': b_bid, 'b_ask': b_ask, 'b_oi': b_oi
    }

def fetch_term_structure(ticker_symbol, current_price):
    tkr = yf.Ticker(ticker_symbol)
    ts_data = []
    
    for exp_date in tkr.options:
        dte = get_dte(exp_date)
        
        # Hard limit to save heavy API calls and compute time
        if dte > 400:
            continue
            
        if dte > 0:
            try:
                calls = tkr.option_chain(exp_date).calls
                if not calls.empty:
                    calls['distance'] = abs(calls['strike'] - current_price)
                    iv = calls.loc[calls['distance'].idxmin()]['impliedVolatility']
                    if iv > 0: ts_data.append({'DTE': dte, 'Expiration': format_nice_date(exp_date), 'IV (%)': round(iv * 100, 2)})
            except: continue
    return pd.DataFrame(ts_data)

def calculate_ff(f_iv_dec, b_iv_dec, f_dte, b_dte):
    t1, t2 = f_dte / 365.0, b_dte / 365.0
    v1, v2 = f_iv_dec ** 2, b_iv_dec ** 2
    try: f_var = ((v2 * t2) - (v1 * t1)) / (t2 - t1)
    except: return np.nan, np.nan
    if f_var < 0: return np.nan, np.nan
    f_vol = math.sqrt(f_var)
    ff = (f_iv_dec - f_vol) / f_vol if f_vol > 0 else 0
    return f_vol, ff

def fetch_double_calendar_data(ticker, target_front, target_back):
    tkr = yf.Ticker(ticker)
    try: current_price = tkr.fast_info['lastPrice']
    except:
        try: current_price = tkr.history(period="1d", interval="1m")['Close'].iloc[-1]
        except: return None

    r_rate = 0.045
    try:
        irx = yf.Ticker("^IRX")
        r_rate = irx.fast_info['lastPrice'] / 100.0
    except: pass

    options_dates = tkr.options
    if not options_dates: return None
    dates_with_dte = [{'date': d, 'dte': get_dte(d)} for d in options_dates if get_dte(d) > 0]
    if len(dates_with_dte) < 2: return None

    front_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_front))
    back_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_back))

    if front_exp['date'] == back_exp['date']:
        dates_with_dte.remove(front_exp)
        if dates_with_dte: back_exp = min(dates_with_dte, key=lambda x: abs(x['dte'] - target_back))
        else: return None
    if back_exp['dte'] <= front_exp['dte']: return None
    f_dte, b_dte = front_exp['dte'], back_exp['dte']

    try:
        f_chain = tkr.option_chain(front_exp['date'])
        f_calls, f_puts = f_chain.calls, f_chain.puts
        if f_calls.empty or f_puts.empty: return None

        f_calls['Delta'] = f_calls.apply(lambda r: calc_delta(current_price, r['strike'], f_dte, r_rate, r['impliedVolatility'], 'call'), axis=1)
        f_calls['Delta_Dist'] = abs(f_calls['Delta'] - 0.35)
        best_call = f_calls.loc[f_calls['Delta_Dist'].idxmin()]
        call_strike = best_call['strike']

        f_puts['Delta'] = f_puts.apply(lambda r: calc_delta(current_price, r['strike'], f_dte, r_rate, r['impliedVolatility'], 'put'), axis=1)
        f_puts['Delta_Dist'] = abs(f_puts['Delta'] - (-0.35))
        best_put = f_puts.loc[f_puts['Delta_Dist'].idxmin()]
        put_strike = best_put['strike']

        b_chain = tkr.option_chain(back_exp['date'])
        b_calls, b_puts = b_chain.calls, b_chain.puts
        
        b_call_match = b_calls[b_calls['strike'] == call_strike]
        b_put_match = b_puts[b_puts['strike'] == put_strike]
        
        if b_call_match.empty or b_put_match.empty: return None
        b_call, b_put = b_call_match.iloc[0], b_put_match.iloc[0]

        return {
            'price': current_price, 'r_rate': r_rate,
            'f_dte': f_dte, 'f_date': front_exp['date'], 'b_dte': b_dte, 'b_date': back_exp['date'],
            'call_strike': call_strike, 'call_delta': best_call['Delta'],
            'f_c_iv': safe_num(best_call['impliedVolatility']), 'f_c_bid': safe_num(best_call.get('bid')), 'f_c_ask': safe_num(best_call.get('ask')), 'f_c_oi': safe_int(best_call.get('openInterest')),
            'b_c_iv': safe_num(b_call['impliedVolatility']), 'b_c_bid': safe_num(b_call.get('bid')), 'b_c_ask': safe_num(b_call.get('ask')), 'b_c_oi': safe_int(b_call.get('openInterest')),
            'put_strike': put_strike, 'put_delta': best_put['Delta'],
            'f_p_iv': safe_num(best_put['impliedVolatility']), 'f_p_bid': safe_num(best_put.get('bid')), 'f_p_ask': safe_num(best_put.get('ask')), 'f_p_oi': safe_int(best_put.get('openInterest')),
            'b_p_iv': safe_num(b_put['impliedVolatility']), 'b_p_bid': safe_num(b_put.get('bid')), 'b_p_ask': safe_num(b_put.get('ask')), 'b_p_oi': safe_int(b_put.get('openInterest')),
        }
    except Exception: return None

# ==========================================
# SESSION STATE INIT (Data Syncing)
# ==========================================
if 't1_fdte' not in st.session_state: st.session_state.t1_fdte = 30
if 't1_bdte' not in st.session_state: st.session_state.t1_bdte = 60
if 't1_fiv' not in st.session_state: st.session_state.t1_fiv = 45.0
if 't1_biv' not in st.session_state: st.session_state.t1_biv = 35.0
if 't1_fetched' not in st.session_state: st.session_state.t1_fetched = False

if 'dc_p_f_iv' not in st.session_state: st.session_state.dc_p_f_iv = 45.0
if 'dc_p_b_iv' not in st.session_state: st.session_state.dc_p_b_iv = 35.0
if 'dc_c_f_iv' not in st.session_state: st.session_state.dc_c_f_iv = 45.0
if 'dc_c_b_iv' not in st.session_state: st.session_state.dc_c_b_iv = 35.0
if 'dc_fetched' not in st.session_state: st.session_state.dc_fetched = False

# ==========================================
# HEADER & NAVIGATION
# ==========================================
st.markdown("<h1 style='color: #FF4B00 !important; font-size: 2.5rem; margin-bottom: 5px;'>Forward Factor Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; margin-bottom: 30px;'>Quantitative Intelligence & Options Term Structure Analytics.</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Forward Factor Calculator", "📊 Watchlist Screener", "🦇 35-Delta Double Calendar"])

# ------------------------------------------
# TAB 1: FORWARD FACTOR CALCULATOR (Deep Dive)
# ------------------------------------------
with tab1:
    st.write("### ")
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.2])
    tick = col1.text_input("Underlying Asset", value="SPY", key="t1_tick").upper()
    tf = col2.number_input("Target Front DTE", value=30, key="t1_tf")
    tb = col3.number_input("Target Back DTE", value=60, key="t1_tb")
    
    with col4:
        st.write("") 
        st.write("")
        if st.button("Execute Data Pipeline", key="t1_btn"):
            with st.spinner("Executing"):
                d = fetch_ticker_data(tick, tf, tb)
                regime = fetch_volatility_regime(tick)
                if d:
                    st.session_state.t1_data = d
                    st.session_state.ts_df = fetch_term_structure(tick, d['price'])
                    st.session_state.regime = regime
                    st.session_state.t1_fdte = int(d['f_dte'])
                    st.session_state.t1_bdte = int(d['b_dte'])
                    st.session_state.t1_fiv = float(d['f_iv'] * 100)
                    st.session_state.t1_biv = float(d['b_iv'] * 100)
                    st.session_state.t1_fetched = True
                else: 
                    st.error("Data pipeline failed. Ticker may be invalid or options chain is empty.")

    if st.session_state.t1_fetched:
        d = st.session_state.t1_data
        st.write("---")
        
        # 📏 Height-Synced Metric Cards (Using Ghost Deltas)
        colA, colB, colC = st.columns([1, 2, 2])
        colA.metric(f"Spot Price ({tick})", f"${d['price']:.2f}", delta=" ", delta_color="off")
        
        if st.session_state.regime and not np.isnan(st.session_state.regime['current_hv']):
            vrp = (d['f_iv']*100) - st.session_state.regime['current_hv']
            colB.metric("HV30 (Realized Volatility)", f"{st.session_state.regime['current_hv']:.2f}%", f"Risk Premium: {vrp:.2f}%", delta_color="inverse" if vrp < 0 else "normal")
            colC.metric("Regime Risk (HV Rank)", f"{st.session_state.regime['hv_rank']:.0f} Percentile", delta=" ", delta_color="off")
        else:
            colB.metric("HV30 (Realized Volatility)", "N/A", delta=" ", delta_color="off")
            colC.metric("Regime Risk", "N/A", delta=" ", delta_color="off")
            
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### Front Period (T1)")
            st.markdown(f"<p style='margin-bottom: 5px;'>Expiry: <strong style='color: white;'>{format_nice_date(d['f_date'])}</strong> | Strike: <strong style='color: white;'>${d['f_strike']}</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top: 0px;'>Bid/Ask: ${d['f_bid']:.2f}-${d['f_ask']:.2f} | OI: {d['f_oi']}</p>", unsafe_allow_html=True)
            f_dte_input = st.number_input("Front DTE", step=1, key="t1_fdte")
            f_iv_input = st.number_input("Front Implied Volatility (%)", step=0.1, format="%.2f", key="t1_fiv")
            
        with col2:
            st.markdown(f"### Back Period (T2)")
            st.markdown(f"<p style='margin-bottom: 5px;'>Expiry: <strong style='color: white;'>{format_nice_date(d['b_date'])}</strong> | Strike: <strong style='color: white;'>${d['b_strike']}</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top: 0px;'>Bid/Ask: ${d['b_bid']:.2f}-${d['b_ask']:.2f} | OI: {d['b_oi']}</p>", unsafe_allow_html=True)
            b_dte_input = st.number_input("Back DTE", step=1, key="t1_bdte")
            b_iv_input = st.number_input("Back Implied Volatility (%)", step=0.1, format="%.2f", key="t1_biv")
            
        fv, ff = calculate_ff(f_iv_input/100.0, b_iv_input/100.0, f_dte_input, b_dte_input)
        
        if np.isnan(ff):
            st.markdown("<div class='signal-card-neutral'><h3>⚠️ Term Structure Inverted</h3><p>Unable to compute forward variance accurately.</p></div>", unsafe_allow_html=True)
        elif ff > 0.20:
            st.markdown(f"""
                <div class='signal-card-green'>
                    <h3 style='color: #10B981 !important; margin-bottom: 5px;'>🟢 Tactical Setup Identified</h3>
                    <h1 style='color: white !important; font-size: 3rem; margin: 0px;'>{ff*100:.2f}% <span style='font-size: 1rem; color: #94A3B8; font-weight: 400;'>Forward Factor</span></h1>
                    <p style='color: #A7F3D0; margin-top: 10px; font-weight: 600;'>Implied Forward Volatility is {fv*100:.2f}%.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='signal-card-neutral'>
                    <h3 style='color: #94A3B8 !important; margin-bottom: 5px;'>⚪ Standard Curve (Contango)</h3>
                    <h1 style='color: white !important; font-size: 2.5rem; margin: 0px;'>{ff*100:.2f}% <span style='font-size: 1rem; color: #94A3B8; font-weight: 400;'>Forward Factor</span></h1>
                    <p style='color: #94A3B8; margin-top: 10px;'>No actionable backwardation detected. Implied Fwd Vol: {fv*100:.2f}%.</p>
                </div>
            """, unsafe_allow_html=True)

        st.write("---")
        st.markdown("### 📅 Earnings Catalyst Risk")
        if d['next_earnings'] and d['next_earnings'] != "N/A":
            b_date_obj = datetime.strptime(d['b_date'], '%Y-%m-%d').date()
            formatted_earnings = format_nice_date(d['next_earnings'].strftime('%Y-%m-%d'))
            
            if date.today() <= d['next_earnings'] <= b_date_obj:
                st.markdown(f"""
                    <div style='background-color:#1A0F14; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #EF4444; border-top: 1px solid #2A3143; border-right: 1px solid #2A3143; border-bottom: 1px solid #2A3143;'>
                        <p style='color:#FCA5A5 !important; margin:0;'><strong>⚠️ RISK DETECTED:</strong> Earnings scheduled for <strong>{formatted_earnings}</strong> (Falls before your Back Expiration).</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:#062615; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #10B981; border-top: 1px solid #2A3143; border-right: 1px solid #2A3143; border-bottom: 1px solid #2A3143;'>
                        <p style='color:#A7F3D0 !important; margin:0;'><strong>✅ CLEAR:</strong> Next earnings on <strong>{formatted_earnings}</strong> (Falls AFTER your Back Expiration).</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background-color:#121621; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #475569; border-top: 1px solid #2A3143; border-right: 1px solid #2A3143; border-bottom: 1px solid #2A3143;'>
                    <p style='color:#94A3B8 !important; margin:0;'><strong>ℹ️ INFO:</strong> No upcoming earnings date found for this asset.</p>
                </div>
            """, unsafe_allow_html=True)
            
        if not st.session_state.ts_df.empty:
            st.write("---")
            st.markdown("### 📉 Volatility Term Structure")
            chart = alt.Chart(st.session_state.ts_df).mark_line(
                point=alt.OverlayMarkDef(color="#FF4B00", size=120, opacity=1, filled=True), 
                color="#334155", 
                strokeWidth=2
            ).encode(
                x=alt.X('DTE:Q', title='Days to Expiry (DTE)', scale=alt.Scale(zero=False), axis=alt.Axis(grid=False, labelColor="#94A3B8", titleColor="#94A3B8")),
                y=alt.Y('IV (%):Q', title='Implied Volatility (%)', scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="#1E293B", labelColor="#94A3B8", titleColor="#94A3B8")), 
                tooltip=['Expiration:N', 'DTE:Q', 'IV (%):Q']
            ).properties(height=350).configure_view(strokeWidth=0).interactive()
            st.altair_chart(chart, use_container_width=True)

# ------------------------------------------
# TAB 2: WATCHLIST SCREENER
# ------------------------------------------
with tab2:
    st.write("### ")
    if 'wl_df' not in st.session_state: st.session_state.wl_df = pd.DataFrame()

    col_wl1, col_wl2, col_wl3, col_wl4 = st.columns([2, 1, 1, 1])
    with col_wl1: watchlist_input = st.text_input("Asset Watchlist:", value="SPY, QQQ, IWM, AAPL, MSFT, TSLA, NVDA, NKE")
    with col_wl2: scan_front = st.number_input("Target Front", value=30, key="scan_f")
    with col_wl3: scan_back = st.number_input("Target Back", value=60, key="scan_b")
    
    with col_wl4:
        st.write("")
        st.write("")
        if st.button("Run Screener", type="primary"):
            tickers = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]
            if len(tickers) > 0:
                results = []
                bar = st.progress(0)
                for i, tick in enumerate(tickers):
                    time.sleep(0.5) 
                    data = fetch_ticker_data(tick, scan_front, scan_back)
                    regime = fetch_volatility_regime(tick)
                    if data:
                        f_mid = (data['f_bid'] + data['f_ask']) / 2
                        b_mid = (data['b_bid'] + data['b_ask']) / 2
                        f_spread_pct = ((data['f_ask'] - data['f_bid']) / f_mid * 100) if f_mid > 0 else 100.0
                        b_spread_pct = ((data['b_ask'] - data['b_bid']) / b_mid * 100) if b_mid > 0 else 100.0
                        
                        pass_liq = (data['f_oi'] >= st.session_state.min_oi and data['b_oi'] >= st.session_state.min_oi and f_spread_pct <= st.session_state.max_spread and b_spread_pct <= st.session_state.max_spread)
                        
                        if not (st.session_state.hide_illiquid and not pass_liq):
                            results.append({
                                "Asset": tick,
                                "Status": "🟢 Liquid" if pass_liq else "🔴 Illiquid",
                                "Price": f"${data['price']:.2f}",
                                "Front DTE": data['f_dte'], "Back DTE": data['b_dte'],
                                "Front IV (%)": float(data['f_iv'] * 100), "Back IV (%)": float(data['b_iv'] * 100),
                                "HV Rank": regime['hv_rank'] if regime else np.nan
                            })
                    bar.progress((i + 1) / len(tickers))
                bar.empty()
                if results: st.session_state.wl_df = pd.DataFrame(results)
                else: st.session_state.wl_df = pd.DataFrame()

    st.write("##### Liquidity Engine Constraints")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1.5])
    with f_col1: 
        st.session_state.min_oi = st.number_input("Minimum Open Interest:", value=500, step=100)
    with f_col2: 
        st.session_state.max_spread = st.number_input("Max Bid/Ask Spread (%):", value=15.0, step=1.0)
    with f_col3:
        st.write("")
        st.write("")
        st.session_state.hide_illiquid = st.toggle("Filter Illiquid Signals", value=True)

    if not st.session_state.wl_df.empty:
        st.write("---")
        st.markdown("### 🎛️ Interactive Intelligence Feed")
        st.caption("Double-click any IV cell to override parameters. The leaderboard will auto-sort.")
        edited_df = st.data_editor(st.session_state.wl_df, hide_index=True, use_container_width=True)
        
        def recalculate_row(row):
            fv, ff = calculate_ff(row['Front IV (%)'] / 100.0, row['Back IV (%)'] / 100.0, row['Front DTE'], row['Back DTE'])
            return pd.Series([fv * 100, ff * 100])

        calc_df = edited_df.copy()
        calc_df[['Fwd Vol (%)', 'FF (%)']] = calc_df.apply(recalculate_row, axis=1)
        calc_df = calc_df.sort_values(by="FF (%)", ascending=False).reset_index(drop=True)
        
        def highlight_ff(val):
            try:
                val_float = float(val)
                if val_float > 0: 
                    return 'color: #10B981; font-weight: bold;'
                elif val_float < 0: 
                    return 'color: #EF4444; font-weight: bold;'
                return 'color: #94A3B8;'
            except: return ''

        styled_df = calc_df.style.map(highlight_ff, subset=['FF (%)']).format({
            'Front IV (%)': "{:.2f}%", 'Back IV (%)': "{:.2f}%", 'HV Rank': "{:.0f}", 
            'Fwd Vol (%)': "{:.2f}%", 'FF (%)': "{:.2f}%"
        })
        
        st.write("### ")
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 3: 35-DELTA DOUBLE CALENDAR
# ------------------------------------------
with tab3:
    st.write("### ")
    col_dc1, col_dc2, col_dc3, col_dcb = st.columns([1.5, 1, 1, 1.2])
    with col_dc1: dc_tick = st.text_input("Asset", value="SPY", key="dc_tick_in").upper()
    with col_dc2: dc_front = st.number_input("Target Front", value=30, key="dc_front_in")
    with col_dc3: dc_back = st.number_input("Target Back", value=60, key="dc_back_in")
    with col_dcb:
        st.write(""); st.write("")
        if st.button("Calculate B-S Skew", type="primary", key="dc_btn"):
            with st.spinner(f"Running Black-Scholes engine..."):
                dc_data = fetch_double_calendar_data(dc_tick, dc_front, dc_back)
                if dc_data: 
                    st.session_state.dc_data = dc_data
                    st.session_state.dc_p_f_iv = float(dc_data['f_p_iv'] * 100)
                    st.session_state.dc_p_b_iv = float(dc_data['b_p_iv'] * 100)
                    st.session_state.dc_c_f_iv = float(dc_data['f_c_iv'] * 100)
                    st.session_state.dc_c_b_iv = float(dc_data['b_c_iv'] * 100)
                    st.session_state.dc_fetched = True
                else: 
                    st.error("Failed to map exact strikes across expirations.")

    if st.session_state.dc_fetched:
        dc = st.session_state.dc_data
        st.write("---")
        
        m_col1, m_col2, m_col3 = st.columns([1, 1, 2])
        m_col1.metric(f"Market Price ({dc_tick})", f"${dc['price']:.2f}", delta=" ", delta_color="off")
        m_col2.metric(f"Treasury Yield", f"{dc['r_rate']*100:.2f}%", delta="Risk-Free Base", delta_color="off")
        m_col3.write("") 
        
        st.write("---")
        col_put, col_call = st.columns(2)
        
        with col_put:
            with st.container():
                st.markdown(f"### 🔻 Put Wing (-35 Delta)")
                st.markdown(f"<h4 style='color: #E2E8F0; margin-top: -10px; margin-bottom: 20px;'>Matched Strike: <span style='color: #FF4B00; font-size: 1.4rem;'>${dc['put_strike']}</span></h4>", unsafe_allow_html=True)
                p_f_iv = st.number_input("Front Put IV (%)", step=0.1, key="dc_p_f_iv")
                p_b_iv = st.number_input("Back Put IV (%)", step=0.1, key="dc_p_b_iv")
                
                st.write("---")
                p_fv, p_ff = calculate_ff(p_f_iv/100, p_b_iv/100, dc['f_dte'], dc['b_dte'])
                
                if np.isnan(p_ff): 
                    st.error("Inverted Term Structure")
                elif p_ff > 0.2: 
                    st.markdown(f"<div class='signal-card-green' style='margin-top:0;'><h3 style='color:#10B981 !important; margin:0;'>Put FF: {p_ff*100:.2f}% 🟢</h3></div>", unsafe_allow_html=True)
                else: 
                    st.markdown(f"<div class='signal-card-neutral' style='margin-top:0;'><h3 style='color:#94A3B8 !important; margin:0;'>Put FF: {p_ff*100:.2f}%</h3></div>", unsafe_allow_html=True)

        with col_call:
            with st.container():
                st.markdown(f"### 🚀 Call Wing (35 Delta)")
                st.markdown(f"<h4 style='color: #E2E8F0; margin-top: -10px; margin-bottom: 20px;'>Matched Strike: <span style='color: #FF4B00; font-size: 1.4rem;'>${dc['call_strike']}</span></h4>", unsafe_allow_html=True)
                c_f_iv = st.number_input("Front Call IV (%)", step=0.1, key="dc_c_f_iv")
                c_b_iv = st.number_input("Back Call IV (%)", step=0.1, key="dc_c_b_iv")
                
                st.write("---")
                c_fv, c_ff = calculate_ff(c_f_iv/100, c_b_iv/100, dc['f_dte'], dc['b_dte'])
                
                if np.isnan(c_ff): 
                    st.error("Inverted Term Structure")
                elif c_ff > 0.2: 
                    st.markdown(f"<div class='signal-card-green' style='margin-top:0;'><h3 style='color:#10B981 !important; margin:0;'>Call FF: {c_ff*100:.2f}% 🟢</h3></div>", unsafe_allow_html=True)
                else: 
                    st.markdown(f"<div class='signal-card-neutral' style='margin-top:0;'><h3 style='color:#94A3B8 !important; margin:0;'>Call FF: {c_ff*100:.2f}%</h3></div>", unsafe_allow_html=True)
