import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import io
import json
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import plotly.io as pio

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="نظام تحليل مراقبي الحفريات - مكة المكرمة",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
# Luxury Government Report Palette:
#   Background:   #080C14  (deep navy black)
#   Surface:      #0D1321  (dark navy)
#   Card:         #101A2E  (midnight blue)
#   Border:       #1C2E4A  (steel blue border)
#   Accent Gold:  #C9A84C  (muted gold — authority)
#   Accent Blue:  #2E6FD8  (royal blue — primary)
#   Accent Teal:  #0F7B6C  (deep teal — positive)
#   Accent Red:   #A03030  (deep crimson — alert)
#   Text Primary: #E6EAF2  (cool white)
#   Text Muted:   #6B7A9A  (slate grey)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');

    /* ── Reset & Base ── */
    * { font-family: 'Cairo', sans-serif !important; box-sizing: border-box; }

    .main, .stApp {
        background: #080C14 !important;
        color: #E6EAF2;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0D1321; }
    ::-webkit-scrollbar-thumb { background: #1C2E4A; border-radius: 4px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060A12 0%, #0A1020 60%, #080C18 100%) !important;
        border-left: 1px solid #1C2E4A !important;
    }
    [data-testid="stSidebar"] hr { border-color: #1C2E4A !important; opacity: 0.6; }

    /* ── Radio nav ── */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 4px !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: transparent !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        transition: background 0.2s !important;
        color: #8A9BBF !important;
        font-size: 13px !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(46,111,216,0.12) !important;
        color: #C9A84C !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(90deg,rgba(46,111,216,0.18),rgba(201,168,76,0.10)) !important;
        color: #C9A84C !important;
        border-left: 3px solid #C9A84C !important;
    }

    /* ── Header Banner ── */
    .header-banner {
        background: linear-gradient(135deg, #0A1428 0%, #0F1E3A 40%, #091220 100%);
        border: 1px solid #1C2E4A;
        border-top: 3px solid #C9A84C;
        border-radius: 14px;
        padding: 22px 36px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(201,168,76,0.15);
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-banner::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 240px; height: 100%;
        background: radial-gradient(ellipse at right center, rgba(201,168,76,0.07) 0%, transparent 70%);
        pointer-events: none;
    }
    .header-title {
        font-size: 24px;
        font-weight: 900;
        color: #E6EAF2;
        margin: 0;
        direction: rtl;
        letter-spacing: 0.3px;
    }
    .header-subtitle {
        font-size: 13px;
        color: #6B7A9A;
        margin-top: 5px;
        direction: rtl;
        letter-spacing: 0.5px;
    }
    .header-date-badge {
        background: rgba(201,168,76,0.12);
        border: 1px solid rgba(201,168,76,0.3);
        border-radius: 8px;
        padding: 6px 16px;
        color: #C9A84C;
        font-size: 12px;
        font-weight: 600;
        white-space: nowrap;
        letter-spacing: 0.5px;
    }

    /* ── Section Title ── */
    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #C9A84C;
        border-bottom: 1px solid #1C2E4A;
        padding-bottom: 10px;
        margin: 28px 0 18px 0;
        direction: rtl;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 0.3px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #1C2E4A, transparent);
        display: block;
    }

    /* ── Metric Cards ── */
    div[data-testid="metric-container"] {
        background: linear-gradient(160deg, #0D1828 0%, #101A2E 100%);
        border: 1px solid #1C2E4A;
        border-top: 2px solid #2E6FD8;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(46,111,216,0.2);
    }
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #6B7A9A !important;
        font-size: 12px !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #E6EAF2 !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #14305C, #1D4A8C);
        color: #D4E4FF;
        border: 1px solid #2A4E80;
        border-radius: 8px;
        padding: 9px 22px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.25s;
        letter-spacing: 0.3px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4A8C, #2E6FD8);
        border-color: #3A6FAA;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(46,111,216,0.35);
        color: #ffffff;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8A5A10, #C9A84C);
        border-color: #C9A84C;
        color: #080C14;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #C9A84C, #E8C870);
        box-shadow: 0 6px 16px rgba(201,168,76,0.35);
    }

    /* ── Inputs ── */
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
        color: #8A9BBF !important;
        font-size: 13px !important;
        direction: rtl;
    }
    .stSelectbox > div > div, .stTextInput > div > div > input {
        background: #0D1321 !important;
        border-color: #1C2E4A !important;
        color: #E6EAF2 !important;
        border-radius: 8px !important;
    }

    /* ── Success / Warning boxes ── */
    .success-box {
        background: linear-gradient(135deg, #07201A, #0A2E24);
        border: 1px solid #0F5A48;
        border-right: 3px solid #15876A;
        border-radius: 10px;
        padding: 12px 18px;
        direction: rtl;
        color: #4DC4A8;
        margin: 10px 0;
        font-size: 13px;
    }
    .warning-box {
        background: linear-gradient(135deg, #1C1408, #28200C);
        border: 1px solid #4A3A10;
        border-right: 3px solid #C9A84C;
        border-radius: 10px;
        padding: 12px 18px;
        direction: rtl;
        color: #C9A84C;
        margin: 10px 0;
        font-size: 13px;
    }

    /* ── Dataframe ── */
    .stDataFrame, [data-testid="stDataFrame"] {
        border: 1px solid #1C2E4A !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    .stDataFrame thead tr th {
        background: #0D1828 !important;
        color: #C9A84C !important;
        border-bottom: 1px solid #1C2E4A !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }
    .stDataFrame tbody tr td {
        background: #0A1020 !important;
        color: #CBD5E8 !important;
        border-bottom: 1px solid #0F1A2E !important;
        font-size: 13px !important;
    }
    .stDataFrame tbody tr:hover td {
        background: rgba(46,111,216,0.06) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #0D1321 !important;
        border-radius: 10px 10px 0 0 !important;
        border-bottom: 1px solid #1C2E4A !important;
        gap: 2px !important;
        padding: 4px 8px 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #6B7A9A !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 10px 20px !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #C9A84C !important;
        background: rgba(201,168,76,0.06) !important;
    }
    .stTabs [aria-selected="true"] {
        color: #C9A84C !important;
        border-bottom: 2px solid #C9A84C !important;
        background: rgba(201,168,76,0.08) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: #0A1020 !important;
        border: 1px solid #1C2E4A !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 20px !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: #0D1828 !important;
        border: 1px solid #1C2E4A !important;
        border-radius: 10px !important;
        color: #8A9BBF !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderContent {
        background: #0A1020 !important;
        border: 1px solid #1C2E4A !important;
        border-top: none !important;
    }

    /* ── Spinners & alerts ── */
    .stAlert {
        background: #0D1321 !important;
        border-radius: 10px !important;
        border-left: 3px solid #2E6FD8 !important;
    }

    /* ── Top / Bottom badges (legacy) ── */
    .top-badge {
        background: linear-gradient(135deg, #07201A, #0A2E24);
        border: 1px solid #0F5A48;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 6px 0;
        direction: rtl;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .bottom-badge {
        background: linear-gradient(135deg, #1C0808, #2E0F0F);
        border: 1px solid #6A1A1A;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 6px 0;
        direction: rtl;
    }
    .rank-number { font-size: 20px; font-weight: 700; color: #C9A84C; min-width: 30px; }

    .kpi-card {
        background: linear-gradient(160deg, #0D1828, #101A2E);
        border: 1px solid #1C2E4A;
        border-top: 2px solid #2E6FD8;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-value { font-size: 30px; font-weight: 700; color: #E6EAF2; }
    .kpi-label { font-size: 12px; color: #6B7A9A; margin-top: 4px; direction: rtl; }

    .rtl-text { direction: rtl; text-align: right; }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: #0D1321 !important;
        border: 1px dashed #1C2E4A !important;
        border-radius: 10px !important;
    }

    /* ── Info / Warning ── */
    .stInfo { background: #0A1828 !important; border-color: #2E6FD8 !important; }
    .stWarning { background: #1C1408 !important; border-color: #C9A84C !important; }
    .stSuccess { background: #07201A !important; border-color: #15876A !important; }
    .stError { background: #1C0808 !important; border-color: #A03030 !important; }

    /* ── Login page ── */
    .login-container {
        max-width: 420px;
        margin: 80px auto;
        background: linear-gradient(160deg, #0D1828, #101A2E);
        border: 1px solid #1C2E4A;
        border-top: 3px solid #C9A84C;
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 12px 48px rgba(0,0,0,0.7);
    }
</style>
""", unsafe_allow_html=True)

# ─── Database Setup ─────────────────────────────────────────────────────────────
DB_PATH = "excavation_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'viewer'
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS external_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_name TEXT NOT NULL,
        task_description TEXT NOT NULL,
        task_count INTEGER DEFAULT 1,
        task_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS performance_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_name TEXT NOT NULL,
        justification TEXT NOT NULL,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS uploaded_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT,
        data_json TEXT,
        upload_date TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS saved_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_name TEXT NOT NULL,
        report_type TEXT NOT NULL,
        report_ext  TEXT NOT NULL,
        report_mime TEXT NOT NULL,
        report_data BLOB NOT NULL,
        created_by  TEXT DEFAULT 'admin',
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # Default admin user
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", admin_hash, "admin"))
    
    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return row[1]
    return None

# ─── Data Parsing Functions ──────────────────────────────────────────────────────
def parse_xlsx_manually(file_bytes):
    """
    Parse xlsx using zipfile + cell references (e.g. A1, B2) so that
    sparse/merged cells land in the correct column position.
    Fixes column-shift bugs that occur when some cells are empty/skipped.
    """
    import re as _re_px
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

            # ── Shared strings ──
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for si in ss_tree.findall('ns:si', ns):
                    t_el = si.find('ns:t', ns)
                    if t_el is not None:
                        shared_strings.append(t_el.text or '')
                    else:
                        texts = [r.find('ns:t', ns) for r in si.findall('ns:r', ns)]
                        shared_strings.append(''.join(t.text or '' for t in texts if t is not None))

            # ── Find first sheet ──
            ws_name = None
            for f in sorted(z.namelist()):
                if f.startswith('xl/worksheets/sheet') and f.endswith('.xml'):
                    ws_name = f
                    break
            if not ws_name:
                return None

            ws_tree = ET.fromstring(z.read(ws_name))

            def _col_letter_to_idx(s):
                """'A'→0, 'B'→1, 'AA'→26 …"""
                n = 0
                for ch in s.upper():
                    n = n * 26 + (ord(ch) - 64)
                return n - 1

            rows_data = []
            for row_el in ws_tree.findall('.//ns:row', ns):
                row_dict = {}
                for c in row_el.findall('ns:c', ns):
                    ref = c.get('r', '')
                    m = _re_px.match(r'([A-Z]+)', ref)
                    if not m:
                        continue
                    col_idx = _col_letter_to_idx(m.group(1))
                    t = c.get('t', '')
                    v = c.find('ns:v', ns)
                    if v is None:
                        val = None
                    elif t == 's':
                        try:
                            val = shared_strings[int(v.text)]
                        except Exception:
                            val = v.text
                    else:
                        try:
                            fv = float(v.text)
                            val = int(fv) if fv == int(fv) else fv
                        except Exception:
                            val = v.text
                    row_dict[col_idx] = val

                if row_dict:
                    mx = max(row_dict.keys())
                    rows_data.append([row_dict.get(i) for i in range(mx + 1)])

            if not rows_data:
                return None

            headers   = rows_data[0]
            data_rows = rows_data[1:]

            max_len = max((len(r) for r in [headers] + data_rows), default=len(headers))
            headers = (list(headers) + [None] * max_len)[:max_len]
            normalized = [(list(r) + [None] * max_len)[:max_len] for r in data_rows]

            df = pd.DataFrame(normalized, columns=headers)
            df = df.dropna(how='all')
            return df

    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        return None

def load_analytics_from_saved_report(report_id):
    """
    Load a saved HTML report from DB and reconstruct a minimal analytics dict.
    Handles column name variations between HTML report and expected dict keys.
    """
    import re as _re_rpt
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT report_data, report_type FROM saved_reports WHERE id=?",
            (report_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        raw_bytes, rtype = bytes(row[0]), row[1]
        if rtype != 'HTML':
            return None
        html = raw_bytes.decode('utf-8', errors='replace')

        def _parse_html_table(html_str, section_keyword):
            idx = html_str.find(section_keyword)
            if idx == -1:
                return None
            tbl_start = html_str.find('<table', idx)
            if tbl_start == -1:
                return None
            tbl_end = html_str.find('</table>', tbl_start)
            if tbl_end == -1:
                return None
            tbl_html = html_str[tbl_start: tbl_end + 8]
            headers = _re_rpt.findall(r'<th[^>]*>(.*?)</th>', tbl_html, _re_rpt.S)
            headers = [_re_rpt.sub(r'<[^>]+>', '', h).strip() for h in headers]
            rows = []
            for tr in _re_rpt.findall(r'<tr[^>]*>(.*?)</tr>', tbl_html, _re_rpt.S):
                cells = _re_rpt.findall(r'<td[^>]*>(.*?)</td>', tr, _re_rpt.S)
                cells = [_re_rpt.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if cells and len(cells) == len(headers):
                    rows.append(cells)
            if not headers or not rows:
                return None
            return pd.DataFrame(rows, columns=headers)

        def _to_num(series):
            return pd.to_numeric(
                series.astype(str).str.replace('%', '').str.replace(',', '').str.strip(),
                errors='coerce'
            ).fillna(0)

        analytics = {}

        # ── جدول الأداء الكامل ──
        perf_df = None
        for kw in ['جدول الأداء الكامل', 'أداء المراقبين', 'اسم المراقب']:
            perf_df = _parse_html_table(html, kw)
            if perf_df is not None and 'اسم المراقب' in perf_df.columns:
                break

        if perf_df is not None and 'اسم المراقب' in perf_df.columns:
            num_cols = ['عدد الزيارات','عدد البلاغات','إجمالي المخالفات',
                        'مخالفات مقبولة','مخالفات مرفوضة','درجة الأداء',
                        'نسبة الأداء الكلية %','نسبة قبول المخالفات %','نسبة رفض المخالفات %']
            for col in num_cols:
                if col in perf_df.columns:
                    perf_df[col] = _to_num(perf_df[col])
            analytics['unified'] = perf_df

            if 'عدد الزيارات' in perf_df.columns:
                analytics['visits'] = perf_df[['اسم المراقب','عدد الزيارات']].copy()
            if 'عدد البلاغات' in perf_df.columns:
                analytics['reports'] = perf_df[['اسم المراقب','عدد البلاغات']].copy()
            if 'إجمالي المخالفات' in perf_df.columns:
                vcols = [c for c in ['اسم المراقب','إجمالي المخالفات',
                                     'مخالفات مقبولة','مخالفات مرفوضة'] if c in perf_df.columns]
                analytics['violations'] = perf_df[vcols].copy()

        # ── جدول البلديات ──
        muni_df = None
        for kw in ['إجمالي الزيارات والبلاغات لكل بلدية', 'البلديات', 'البلدي']:
            muni_df = _parse_html_table(html, kw)
            if muni_df is not None and 'البلدية' in muni_df.columns:
                break

        if muni_df is not None and 'البلدية' in muni_df.columns:
            # توحيد اسم عمود الزيارات — قد يكون "الزيارات" أو "إجمالي الزيارات"
            col_rename = {}
            for c in muni_df.columns:
                if c == 'الزيارات' or (c and 'زيار' in c and c != 'إجمالي الزيارات'):
                    col_rename[c] = 'إجمالي الزيارات'
                elif c == 'البلاغات' or (c and 'بلاغ' in c and c != 'عدد البلاغات'):
                    col_rename[c] = 'عدد البلاغات'
            if col_rename:
                muni_df = muni_df.rename(columns=col_rename)

            for col in ['إجمالي الزيارات','عدد البلاغات','نسبة الزيارات %','نسبة البلاغات %']:
                if col in muni_df.columns:
                    muni_df[col] = _to_num(muni_df[col])

            # تأكد من وجود العمودين المطلوبين دائماً
            if 'إجمالي الزيارات' not in muni_df.columns:
                muni_df['إجمالي الزيارات'] = 0
            if 'عدد البلاغات' not in muni_df.columns:
                muni_df['عدد البلاغات'] = 0

            analytics['municipality'] = muni_df

        # ── بنود اللائحة ──
        art_df = None
        for kw in ['بنود اللائحة', 'اللائحة الأكثر', 'اللائحة']:
            art_df = _parse_html_table(html, kw)
            if art_df is not None and len(art_df.columns) >= 2:
                break
        if art_df is not None and len(art_df.columns) >= 2:
            art_df.columns = ['رقم البند', 'التكرار'] + list(art_df.columns[2:])
            art_df['التكرار'] = pd.to_numeric(
                art_df['التكرار'].astype(str).str.replace(',',''), errors='coerce'
            ).fillna(0).astype(int)
            analytics['top_articles'] = art_df

        return analytics if analytics else None

    except Exception as e:
        return None


def parse_visits_file(file_bytes):
    """
    Parse visits Excel file using raw data columns:
      - اسم المراقب        → monitor name (text, not ID)
      - البلدية             → municipality
      - تاريخ انهاء الزيارة → count of completed visits per row

    Returns: (visits_df, visits_raw_df)
      visits_df     — اسم المراقب | عدد الزيارات   (one row per monitor)
      visits_raw_df — full raw df with البلدية column for municipality breakdown
    """
    import re as _re

    def _read_sheet(z, sheet_path, shared_strings):
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        def col_to_idx(s):
            n = 0
            for ch in s: n = n * 26 + (ord(ch.upper()) - 64)
            return n - 1

        rows_data = []
        for row_el in ET.fromstring(z.read(sheet_path)).findall('.//ns:row', ns):
            rd = {}
            for c in row_el.findall('ns:c', ns):
                m = _re.match(r'([A-Z]+)', c.get('r', ''))
                if not m: continue
                ci = col_to_idx(m.group(1))
                t, v = c.get('t', ''), c.find('ns:v', ns)
                if v is None:
                    val = None
                elif t == 's':
                    try: val = shared_strings[int(v.text)]
                    except: val = v.text
                else:
                    try:
                        fv = float(v.text)
                        val = int(fv) if fv == int(fv) else fv
                    except: val = v.text
                rd[ci] = val
            if rd:
                mx = max(rd.keys())
                rows_data.append([rd.get(i) for i in range(mx + 1)])
        if not rows_data:
            return None
        headers = rows_data[0]
        mx = max(len(r) for r in rows_data)
        norm = [(r + [None] * mx)[:mx] for r in rows_data[1:]]
        extra = [f'_col{i}' for i in range(mx - len(headers))]
        cols = (headers + extra)[:mx]
        return pd.DataFrame(norm, columns=cols).dropna(how='all')

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            # ── Shared strings ──
            ns_ss = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('ns:si', ns_ss):
                    t_el = si.find('ns:t', ns_ss)
                    if t_el is not None:
                        shared_strings.append(t_el.text or '')
                    else:
                        txts = [r.find('ns:t', ns_ss) for r in si.findall('ns:r', ns_ss)]
                        shared_strings.append(''.join(t.text or '' for t in txts if t is not None))

            # ── Find first sheet that has the 3 required columns ──
            sheets = sorted(
                [s for s in z.namelist() if s.startswith('xl/worksheets/sheet') and s.endswith('.xml')],
                key=lambda x: int(_re.search(r'sheet(\d+)', x).group(1))
            )

            raw_df = None
            for sh in sheets:
                df_try = _read_sheet(z, sh, shared_strings)
                if df_try is None: continue
                if ('اسم المراقب' in df_try.columns and
                    'البلدية' in df_try.columns and
                    'تاريخ انهاء الزيارة' in df_try.columns):
                    raw_df = df_try
                    break

            if raw_df is None:
                return pd.DataFrame(columns=['اسم المراقب', 'عدد الزيارات']), None

            # ── Clean: keep only rows with valid monitor name & completion date ──
            raw_df = raw_df[raw_df['اسم المراقب'].notna()].copy()
            raw_df = raw_df[raw_df['تاريخ انهاء الزيارة'].notna()].copy()
            raw_df['اسم المراقب'] = raw_df['اسم المراقب'].astype(str).str.strip()
            raw_df['البلدية']      = raw_df['البلدية'].astype(str).str.strip()

            # ── visits_df: count of completed visits per monitor ──
            visits_df = (
                raw_df.groupby('اسم المراقب')['تاريخ انهاء الزيارة']
                .count()
                .reset_index()
            )
            visits_df.columns = ['اسم المراقب', 'عدد الزيارات']
            visits_df = visits_df.sort_values('عدد الزيارات', ascending=False).reset_index(drop=True)

            return visits_df, raw_df

    except Exception as e:
        return pd.DataFrame(columns=['اسم المراقب', 'عدد الزيارات']), None

def parse_reports_file(file_bytes):
    """Parse the full reports file"""
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except:
        df = parse_xlsx_manually(file_bytes)
    if df is None:
        return None
    return df

def parse_violations_file(file_bytes):
    """
    Parse violations file — uses cell-reference based parser so columns
    land in correct positions even when cells are sparse/skipped.
    """
    df = parse_xlsx_manually(file_bytes)
    if df is None:
        return None

    # ── Strip all column names ──
    df.columns = [str(c).strip() if c is not None else c for c in df.columns]

    # ── Detect اسم المراقب column (could be named differently) ──
    monitor_col = next(
        (c for c in df.columns if c and 'مراقب' in str(c) and 'هوية' not in str(c) and 'رقم' not in str(c)),
        next((c for c in df.columns if c and 'موظف' in str(c) and 'هوية' not in str(c)), None)
    )
    if monitor_col and monitor_col != 'اسم المراقب':
        df = df.rename(columns={monitor_col: 'اسم المراقب'})

    # ── Detect article column — exact match first, then fuzzy ──
    article_col_exact = 'رقم بند اللائحة'
    if article_col_exact not in df.columns:
        # Try fuzzy
        article_col_exact = next(
            (c for c in df.columns if c and 'بند' in str(c) and 'لائحة' in str(c)),
            next((c for c in df.columns if c and 'بند' in str(c)), None)
        )
        if article_col_exact and article_col_exact != 'رقم بند اللائحة':
            df = df.rename(columns={article_col_exact: 'رقم بند اللائحة'})

    return df

def compute_analytics(visits_df, reports_df, violations_df, external_tasks_df=None, notes_df=None, visits_raw_df=None):
    """Merge all data sources into unified monitor performance dataframe"""
    import re as _re_ca

    def _valid_name(s):
        """True only for genuine Arabic monitor names"""
        s = str(s).strip()
        if not s or s in ('nan', 'None', ''):
            return False
        if _re_ca.match(r'^\d', s):  # starts with digit → date / number
            return False
        return len(_re_ca.findall(r'[\u0600-\u06FF]', s)) >= 2

    results = {}

    # 1. Visits per monitor
    if visits_df is not None:
        _vd = visits_df[visits_df['اسم المراقب'].apply(lambda x: _valid_name(str(x)))].copy()
        visits_summary = _vd.groupby('اسم المراقب')['عدد الزيارات'].sum().reset_index()
        results['visits'] = visits_summary

    # 2. Reports per monitor — try both اسم الموظف and اسم المراقب
    if reports_df is not None:
        _rep_name_col = None
        if 'اسم الموظف' in reports_df.columns:
            _rep_name_col = 'اسم الموظف'
        elif 'اسم المراقب' in reports_df.columns:
            _rep_name_col = 'اسم المراقب'
        if _rep_name_col:
            _rd = reports_df[reports_df[_rep_name_col].apply(lambda x: _valid_name(str(x)))].copy()
            reports_summary = _rd.groupby(_rep_name_col).size().reset_index()
            reports_summary.columns = ['اسم المراقب', 'عدد البلاغات']
            results['reports'] = reports_summary

    # 3. Violations analysis
    if violations_df is not None and 'اسم المراقب' in violations_df.columns:
        # Clean: keep only valid monitor names
        violations_df = violations_df[violations_df['اسم المراقب'].apply(lambda x: _valid_name(str(x)))].copy()
        violations_df['اسم المراقب'] = violations_df['اسم المراقب'].astype(str).str.strip()

        viol_total = violations_df.groupby('اسم المراقب').size().reset_index()
        viol_total.columns = ['اسم المراقب', 'إجمالي المخالفات']

        if 'حالة الاعتماد' in violations_df.columns:
            # ── Normalize values: strip whitespace, handle all known variants ──
            viol_status = violations_df['حالة الاعتماد'].astype(str).str.strip()

            # مقبولة: مقبولة / معتمدة / مقبول / approved / قبول
            approved_mask = viol_status.str.contains(
                r'مقبول|معتمد|قبول|approved', case=False, na=False
            )
            # مرفوضة: مرفوضة / مرفوض / rejected / رفض
            rejected_mask = viol_status.str.contains(
                r'مرفوض|رفض|rejected', case=False, na=False
            )

            approved = violations_df[approved_mask]
            rejected = violations_df[rejected_mask]

            approved_cnt = approved.groupby('اسم المراقب').size().reset_index()
            approved_cnt.columns = ['اسم المراقب', 'مخالفات مقبولة']

            rejected_cnt = rejected.groupby('اسم المراقب').size().reset_index()
            rejected_cnt.columns = ['اسم المراقب', 'مخالفات مرفوضة']

            viol_total = viol_total.merge(approved_cnt, on='اسم المراقب', how='left')
            viol_total = viol_total.merge(rejected_cnt, on='اسم المراقب', how='left')
            viol_total['مخالفات مقبولة']  = viol_total['مخالفات مقبولة'].fillna(0).astype(int)
            viol_total['مخالفات مرفوضة'] = viol_total['مخالفات مرفوضة'].fillna(0).astype(int)

            # ── Debug: store unique status values for reference ──
            results['_violation_status_unique'] = sorted(viol_status.unique().tolist())
        else:
            # No حالة الاعتماد column — treat all as pending
            viol_total['مخالفات مقبولة']  = 0
            viol_total['مخالفات مرفوضة'] = 0

        results['violations'] = viol_total

        # ── Top article violations (overall) ──
        # بعد parse_violations_file العمود دائماً باسم 'رقم بند اللائحة'
        article_col = 'رقم بند اللائحة' if 'رقم بند اللائحة' in violations_df.columns else next(
            (c for c in violations_df.columns
             if c and ('بند' in str(c) or 'مادة' in str(c))),
            None
        )
        if article_col:
            top_article = violations_df[article_col].dropna().astype(str).str.strip()
            top_article = top_article[top_article != ''].value_counts().reset_index()
            top_article.columns = ['رقم البند', 'التكرار']
            results['top_articles'] = top_article
            results['_article_col'] = article_col

            # ── Top article per monitor ──
            mon_art = (
                violations_df[['اسم المراقب', article_col]]
                .dropna()
                .copy()
            )
            mon_art[article_col] = mon_art[article_col].astype(str).str.strip()
            mon_art = mon_art[mon_art[article_col] != '']

            # Most frequent article per monitor
            def _top_art(grp):
                vc = grp[article_col].value_counts()
                if vc.empty:
                    return pd.Series({'أكثر_بند': '—', 'عدد_تكرار_البند': 0})
                return pd.Series({'أكثر_بند': str(vc.index[0]), 'عدد_تكرار_البند': int(vc.iloc[0])})

            mon_art_summary = mon_art.groupby('اسم المراقب').apply(_top_art).reset_index()
            results['monitor_top_articles'] = mon_art_summary
    
    # 4. Municipality data — DIRECT from visits raw data (most accurate)
    muni_built = False

    # Priority 1: visits_raw_df from sheet3 (البلدية + اسم المراقب exact)
    if visits_raw_df is not None and 'البلدية' in visits_raw_df.columns and 'اسم المراقب' in visits_raw_df.columns:
        # إجمالي الزيارات الفعلية لكل بلدية
        muni_v = visits_raw_df.groupby('البلدية').size().reset_index(name='إجمالي الزيارات')
        # إجمالي الزيارات لكل مراقب لكل بلدية
        muni_mon = visits_raw_df.groupby(['البلدية', 'اسم المراقب']).size().reset_index(name='زيارات_في_البلدية')
        results['municipality_visits'] = muni_v
        results['municipality_monitor'] = muni_mon
        muni = muni_v.copy()
        muni_built = True

    # Priority 2: reports_df has البلدية
    if reports_df is not None and 'البلدية' in reports_df.columns:
        rep_muni = reports_df.groupby('البلدية').size().reset_index(name='عدد البلاغات')
        if muni_built:
            muni = muni.merge(rep_muni, on='البلدية', how='outer').fillna(0)
            muni['إجمالي الزيارات'] = muni['إجمالي الزيارات'].astype(int)
            muni['عدد البلاغات'] = muni['عدد البلاغات'].astype(int)
        else:
            muni = rep_muni.copy()
            # Estimate visits from reports using monitor link
            monitor_col = next((c for c in ['اسم الموظف', 'اسم المراقب', 'الموظف'] if c in reports_df.columns), None)
            if monitor_col and visits_df is not None and 'اسم المراقب' in visits_df.columns:
                visits_map = dict(zip(visits_df['اسم المراقب'].astype(str).str.strip(),
                                      pd.to_numeric(visits_df['عدد الزيارات'], errors='coerce').fillna(0).astype(int)))
                mon_total = reports_df.groupby(monitor_col).size().to_dict()
                mon_muni  = reports_df.groupby([monitor_col, 'البلدية']).size().reset_index()
                mon_muni.columns = ['المراقب', 'البلدية', 'بلاغات']
                rows_est = []
                for _, r in mon_muni.iterrows():
                    m = str(r['المراقب']).strip()
                    total_m = mon_total.get(m, 1)
                    visits_m = visits_map.get(m, 0)
                    rows_est.append({'البلدية': r['البلدية'],
                                     'زيارات_مقدرة': round(visits_m * r['بلاغات'] / total_m)})
                if rows_est:
                    est = pd.DataFrame(rows_est).groupby('البلدية')['زيارات_مقدرة'].sum().reset_index()
                    est.columns = ['البلدية', 'إجمالي الزيارات']
                    muni = muni.merge(est, on='البلدية', how='left').fillna(0)
                    muni['إجمالي الزيارات'] = muni['إجمالي الزيارات'].astype(int)
            muni_built = True

    if muni_built:
        # Add percentage columns
        total_v_muni = muni['إجمالي الزيارات'].sum() if 'إجمالي الزيارات' in muni.columns else 0
        if total_v_muni > 0:
            muni['نسبة الزيارات %'] = (muni['إجمالي الزيارات'] / total_v_muni * 100).round(1)
        if 'عدد البلاغات' in muni.columns:
            total_r_muni = muni['عدد البلاغات'].sum()
            if total_r_muni > 0:
                muni['نسبة البلاغات %'] = (muni['عدد البلاغات'] / total_r_muni * 100).round(1)
        results['municipality'] = muni.sort_values('إجمالي الزيارات', ascending=False).reset_index(drop=True)
    
    # 5. Merge all into unified monitor table
    import re as _re_u

    def _is_real_monitor_name(s):
        """Return True only for genuine Arabic/text names — reject dates, timestamps, numbers"""
        s = str(s).strip()
        if not s or s in ('nan', 'None', ''):
            return False
        # Reject if starts with digits (date / number pattern)
        if _re_u.match(r'^\d', s):
            return False
        # Must have at least 2 Arabic characters
        arabic_chars = len(_re_u.findall(r'[\u0600-\u06FF]', s))
        return arabic_chars >= 2

    all_monitors = set()
    for key in ['visits', 'reports', 'violations']:
        if key in results:
            df_key = results[key]
            col = 'اسم المراقب'
            if col in df_key.columns:
                all_monitors.update(
                    n for n in df_key[col].dropna().tolist()
                    if _is_real_monitor_name(n)
                )
    
    if all_monitors:
        unified = pd.DataFrame({'اسم المراقب': list(all_monitors)})
        
        if 'visits' in results:
            unified = unified.merge(results['visits'], on='اسم المراقب', how='left')
        if 'reports' in results:
            unified = unified.merge(results['reports'], on='اسم المراقب', how='left')
        if 'violations' in results:
            unified = unified.merge(results['violations'], on='اسم المراقب', how='left')

        # Merge top article per monitor
        if 'monitor_top_articles' in results:
            unified = unified.merge(results['monitor_top_articles'], on='اسم المراقب', how='left')
            unified['أكثر_بند']          = unified['أكثر_بند'].fillna('—')
            unified['عدد_تكرار_البند']   = unified['عدد_تكرار_البند'].fillna(0).astype(int)
        
        # Fill NaN
        num_cols = ['عدد الزيارات', 'عدد البلاغات', 'إجمالي المخالفات', 'مخالفات مقبولة', 'مخالفات مرفوضة']
        for col in num_cols:
            if col in unified.columns:
                unified[col] = unified[col].fillna(0).astype(int)
        
        # Add external tasks
        if external_tasks_df is not None and not external_tasks_df.empty:
            ext = external_tasks_df.groupby('monitor_name')['task_count'].sum().reset_index()
            ext.columns = ['اسم المراقب', 'مهام خارجية']
            unified = unified.merge(ext, on='اسم المراقب', how='left')
            unified['مهام خارجية'] = unified['مهام خارجية'].fillna(0).astype(int)
        else:
            unified['مهام خارجية'] = 0
        
        # Performance justification adjustments
        adj = {}
        if notes_df is not None and not notes_df.empty:
            for _, row in notes_df.iterrows():
                adj[row['monitor_name']] = row['justification']
        unified['تبرير الأداء'] = unified['اسم المراقب'].map(adj).fillna('')
        
        # KPI Score calculation (weighted)
        unified['درجة الأداء'] = (
            unified.get('عدد الزيارات', pd.Series(0, index=unified.index)) * 0.45 +
            unified.get('عدد البلاغات', pd.Series(0, index=unified.index)) * 0.25 +
            unified.get('مخالفات مقبولة', pd.Series(0, index=unified.index)) * 0.20 +
            unified.get('مهام خارجية', pd.Series(0, index=unified.index)) * 0.10
        ).round(1)
        
        # Adjust score for justifications
        for idx, row in unified.iterrows():
            if row['تبرير الأداء'] in ['إجازة', 'مسح ميداني']:
                unified.at[idx, 'درجة الأداء'] = unified.at[idx, 'درجة الأداء'] * 1.15
        
        unified = unified.sort_values('درجة الأداء', ascending=False).reset_index(drop=True)
        unified['الترتيب'] = range(1, len(unified) + 1)
        
        # ── Percentage / relative KPIs ──
        # نسبة الزيارات: نسبة أداء مقارنةً بأعلى مراقب (0–100)
        if 'عدد الزيارات' in unified.columns:
            max_v = unified['عدد الزيارات'].max()
            unified['نسبة الزيارات %'] = (
                unified['عدد الزيارات'] / max_v * 100
            ).round(1) if max_v > 0 else 0.0
        
        # نسبة البلاغات: نسبة أداء مقارنةً بأعلى مراقب (0–100)
        if 'عدد البلاغات' in unified.columns:
            max_r = unified['عدد البلاغات'].max()
            unified['نسبة البلاغات %'] = (
                unified['عدد البلاغات'] / max_r * 100
            ).round(1) if max_r > 0 else 0.0
        
        # نسبة قبول المخالفات لكل مراقب (من مخالفاته هو)
        if 'مخالفات مقبولة' in unified.columns and 'إجمالي المخالفات' in unified.columns:
            unified['نسبة قبول المخالفات %'] = (
                unified['مخالفات مقبولة'] / unified['إجمالي المخالفات'].replace(0, np.nan) * 100
            ).round(1).fillna(0.0)
        
        # نسبة رفض المخالفات
        if 'مخالفات مرفوضة' in unified.columns and 'إجمالي المخالفات' in unified.columns:
            unified['نسبة رفض المخالفات %'] = (
                unified['مخالفات مرفوضة'] / unified['إجمالي المخالفات'].replace(0, np.nan) * 100
            ).round(1).fillna(0.0)
        
        # نسبة الأداء الكلية (0–100) مقارنةً بأعلى درجة أداء
        max_score = unified['درجة الأداء'].max()
        unified['نسبة الأداء الكلية %'] = (
            unified['درجة الأداء'] / max_score * 100
        ).round(1) if max_score > 0 else 0.0
        
        results['unified'] = unified
    
    return results

# ─── Login Page ─────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stAppViewBlockContainer"] { padding-top: 2rem !important; }
    
    /* Style the login column like a card */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stTextInput"]) {
        background: linear-gradient(145deg, #1a2035, #1f2b45);
        border: 1px solid #2d4a6e;
        border-radius: 20px;
        padding: 28px 32px !important;
        box-shadow: 0 12px 48px rgba(0,0,0,0.6);
    }
    
    .login-logo-wrap {
        text-align: center;
        padding: 32px 0 24px 0;
    }
    .login-logo-circle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 88px; height: 88px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1e3a5f, #2d5986);
        border: 2px solid #3a6fa8;
        font-size: 44px;
        box-shadow: 0 0 32px rgba(77,184,255,0.3);
        margin-bottom: 16px;
    }
    .login-main-title {
        font-size: 28px; font-weight: 700;
        color: #4db8ff; direction: rtl; text-align: center;
        text-shadow: 0 0 20px rgba(77,184,255,0.3);
        margin: 8px 0 4px 0;
    }
    .login-sub { color: #8a9bb5; font-size:13px; text-align:center; direction:rtl; margin-bottom:8px; }
    .login-card-header {
        color: #c8ddf5; text-align:center; font-size:16px;
        font-weight:600; direction:rtl; margin-bottom:16px;
        padding-bottom: 12px; border-bottom: 1px solid #2d4a6e;
    }
    .login-hint-txt { color:#3d5a78; text-align:center; font-size:11px; direction:rtl; margin-top:12px; }
    .login-footer-txt { margin-top:24px; text-align:center; color:#2d4a6e; font-size:11px; letter-spacing:1px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo + title
    st.markdown("""
    <div class="login-logo-wrap">
        <div class="login-logo-circle">🏗️</div>
        <div class="login-main-title">نظام تحليل مراقبي الحفريات</div>
        <div class="login-sub">أمانة العاصمة المقدسة  •  مكة المكرمة</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Login card using columns (no wrapping div to avoid rectangle)
    _, col_mid, _ = st.columns([1, 1.6, 1])
    with col_mid:
        st.markdown('<div class="login-card-header">🔐 تسجيل الدخول</div>', unsafe_allow_html=True)
        username = st.text_input("اسم المستخدم", key="login_user", placeholder="أدخل اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password", key="login_pass", placeholder="أدخل كلمة المرور")
        
        if st.button("→  دخول", use_container_width=True, type="primary"):
            role = verify_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown('<div class="login-hint-txt">المستخدم الافتراضي: admin &nbsp;|&nbsp; كلمة المرور: admin123</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-footer-txt">✦ By: Rakan_Alharbi ✦</div>', unsafe_allow_html=True)

# ─── PDF Report Generator (HTML → pdfkit with full Arabic support) ──────────────
def _build_report_html(analytics, month="يناير 2026"):
    """Build full HTML report with proper Arabic RTL styling"""
    now_str = datetime.now().strftime('%Y-%m-%d  %H:%M')

    css = """
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
        font-family: 'DejaVu Sans', Arial, 'Segoe UI', sans-serif;
        direction: rtl;
        color: #1a1a2e;
        background: #ffffff;
        font-size: 10.5pt;
        line-height: 1.6;
    }
    .page { padding: 0; }
    .header-banner {
        background: linear-gradient(135deg, #1a3a6e, #0e2248);
        color: white;
        padding: 20px 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }
    .header-title { font-size: 17pt; font-weight: 900; }
    .header-subtitle { font-size: 9.5pt; color: #a8c4e8; margin-top: 4px; }
    .header-meta { text-align: left; color: #a8c4e8; font-size: 8.5pt; line-height: 1.8; }
    .kpi-band { display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; padding: 0 8px; }
    .kpi-card { flex:1; min-width:80px; border-radius:8px; padding:10px 8px; text-align:center; color:white; }
    .kpi-val  { font-size:18pt; font-weight:900; line-height:1.1; }
    .kpi-lbl  { font-size:7.5pt; opacity:0.88; margin-top:2px; }
    .kpi-blue   { background:#1a4080; }
    .kpi-teal   { background:#0e6680; }
    .kpi-green  { background:#1a6640; }
    .kpi-gold   { background:#8a6010; }
    .kpi-dgreen { background:#1a7a40; }
    .kpi-red    { background:#801a1a; }
    .kpi-purple { background:#503080; }
    .sec-title {
        font-size: 11.5pt; font-weight: 700; color: #1a4080;
        border-right: 4px solid #1a4080;
        padding: 4px 10px 4px 0;
        margin: 16px 8px 8px 0;
    }
    table { width:100%; border-collapse:collapse; margin-bottom:12px; font-size:9pt; }
    thead tr th { padding:8px 9px; text-align:center; font-weight:700; color:white; font-size:8.5pt; }
    tbody tr td { padding:6px 9px; text-align:center; border-bottom:1px solid #dde8f4; }
    tbody tr:nth-child(odd)  td { background:#f6f9fd; }
    tbody tr:nth-child(even) td { background:#ffffff; }
    .td-name { text-align:right !important; font-weight:600; padding-right:12px !important; }
    .total-row td { background:#1a4080 !important; color:white !important; font-weight:700 !important; }
    .th-blue   thead tr th { background:#1a4080; }
    .th-green  thead tr th { background:#1a6640; }
    .th-red    thead tr th { background:#801a1a; }
    .th-gold   thead tr th { background:#7a5010; }
    .th-teal   thead tr th { background:#0e6680; }
    .rank-gold   { color:#b8860b; font-weight:900; }
    .rank-silver { color:#666; font-weight:700; }
    .rank-bronze { color:#a05020; font-weight:700; }
    .bar-wrap { background:#e0e8f4; border-radius:3px; height:4px; margin-top:3px; }
    .bar-fill { height:100%; border-radius:3px; }
    .footer {
        margin-top:24px; padding:8px 8px 0 8px;
        border-top:1px solid #c0ccdc;
        text-align:center; color:#888; font-size:7.5pt;
    }
    .page-break { page-break-after:always; margin:0; padding:0; }
    .note-box {
        background:#fff8e0; border:1px solid #e8c050;
        border-radius:5px; padding:6px 12px;
        font-size:8pt; color:#7a5000; margin:0 8px 10px 0;
    }
    .content { padding: 0 8px; }
    """

    def tbl_open(cols_list, color_class):
        ths = ''.join(f'<th>{c}</th>' for c in cols_list)
        return f'<table class="{color_class}"><thead><tr>{ths}</tr></thead><tbody>'

    def safe_int(v):
        try: return int(float(v))
        except: return 0

    def safe_pct(v):
        try: return f"{float(v):.1f}%"
        except: return "—"

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>{css}</style>
</head>
<body>
<div class="page">
<div class="header-banner">
  <div>
    <div class="header-title">&#x1F3D7; تقرير أداء مراقبي الحفريات</div>
    <div class="header-subtitle">أمانة العاصمة المقدسة  •  مكة المكرمة</div>
  </div>
  <div class="header-meta">
    <div>الفترة: {month}</div>
    <div>تاريخ الإنشاء: {now_str}</div>
    <div>إعداد: Rakan_Alharbi</div>
  </div>
</div>
<div class="content">
"""

    if 'unified' not in analytics:
        html += '<p>لا تتوفر بيانات</p></div></div></body></html>'
        return html

    df = analytics['unified']
    total_v   = safe_int(df['عدد الزيارات'].sum())      if 'عدد الزيارات'    in df.columns else 0
    total_r   = safe_int(df['عدد البلاغات'].sum())      if 'عدد البلاغات'    in df.columns else 0
    total_vi  = safe_int(df['إجمالي المخالفات'].sum())  if 'إجمالي المخالفات' in df.columns else 0
    total_app = safe_int(df['مخالفات مقبولة'].sum())    if 'مخالفات مقبولة'  in df.columns else 0
    total_rej = safe_int(df['مخالفات مرفوضة'].sum())    if 'مخالفات مرفوضة'  in df.columns else 0
    acc_rate  = f"{total_app/total_vi*100:.1f}%" if total_vi > 0 else "—"

    html += f"""
<div class="kpi-band">
  <div class="kpi-card kpi-blue">  <div class="kpi-val">{len(df)}</div>         <div class="kpi-lbl">&#x1F465; المراقبون</div></div>
  <div class="kpi-card kpi-teal">  <div class="kpi-val">{total_v:,}</div>       <div class="kpi-lbl">&#x1F4CD; الزيارات</div></div>
  <div class="kpi-card kpi-green"> <div class="kpi-val">{total_r:,}</div>       <div class="kpi-lbl">&#x1F4E2; البلاغات</div></div>
  <div class="kpi-card kpi-gold">  <div class="kpi-val">{total_vi:,}</div>      <div class="kpi-lbl">&#x2696; المخالفات الكلية</div></div>
  <div class="kpi-card kpi-dgreen"><div class="kpi-val">{total_app:,}</div>     <div class="kpi-lbl">&#x2705; مخالفات مقبولة</div></div>
  <div class="kpi-card kpi-red">   <div class="kpi-val">{total_rej:,}</div>     <div class="kpi-lbl">&#x274C; مخالفات مرفوضة</div></div>
  <div class="kpi-card kpi-purple"><div class="kpi-val">{acc_rate}</div>        <div class="kpi-lbl">&#x1F4C8; نسبة القبول</div></div>
</div>
"""

    data_cols = [c for c in ['اسم المراقب','عدد الزيارات','عدد البلاغات',
                               'مخالفات مقبولة','مخالفات مرفوضة',
                               'نسبة قبول المخالفات %','نسبة الأداء الكلية %'] if c in df.columns]
    pct_cols  = [c for c in data_cols if '%' in c]
    hdrs_ar   = {'اسم المراقب':'اسم المراقب','عدد الزيارات':'الزيارات',
                 'عدد البلاغات':'البلاغات','مخالفات مقبولة':'مقبولة',
                 'مخالفات مرفوضة':'مرفوضة','نسبة قبول المخالفات %':'نسبة القبول',
                 'نسبة الأداء الكلية %':'نسبة الأداء'}

    def monitor_rows(df_slice):
        rows = ''
        for i, (_, row) in enumerate(df_slice.iterrows(), 1):
            rc = {1:'rank-gold',2:'rank-silver',3:'rank-bronze'}.get(i,'')
            sym = {1:'&#x1F947;',2:'&#x1F948;',3:'&#x1F949;'}.get(i, f'#{i}')
            cells = f'<td class="{rc}">{sym}</td>'
            for c in data_cols:
                val = row.get(c, 0)
                if c == 'اسم المراقب':
                    cells += f'<td class="td-name">{val}</td>'
                elif c in pct_cols:
                    cells += f'<td>{safe_pct(val)}</td>'
                else:
                    cells += f'<td>{safe_int(val):,}</td>'
            rows += f'<tr>{cells}</tr>'
        return rows

    # TOP 5
    html += '<div class="sec-title">&#x1F3C6; أفضل 5 مراقبين أداءً</div>'
    html += tbl_open(['#'] + [hdrs_ar.get(c,c) for c in data_cols], 'th-green')
    html += monitor_rows(df.head(5))
    html += '</tbody></table>'

    # BOTTOM 5
    html += '<div class="sec-title">&#x1F4C9; أقل 5 مراقبين أداءً</div>'
    html += tbl_open(['#'] + [hdrs_ar.get(c,c) for c in data_cols], 'th-red')
    bottom_df = df.tail(5).reset_index(drop=True)
    for i, (_, row) in enumerate(bottom_df.iterrows(), len(df)-4):
        cells = f'<td>#{i}</td>'
        for c in data_cols:
            val = row.get(c, 0)
            if c == 'اسم المراقب':
                cells += f'<td class="td-name">{val}</td>'
            elif c in pct_cols:
                cells += f'<td>{safe_pct(val)}</td>'
            else:
                cells += f'<td>{safe_int(val):,}</td>'
        html += f'<tr>{cells}</tr>'
    html += '</tbody></table>'

    # ALL MONITORS
    html += '<div class="sec-title">&#x1F4CB; جدول الأداء الكامل لجميع المراقبين</div>'
    html += tbl_open(['#'] + [hdrs_ar.get(c,c) for c in data_cols], 'th-blue')
    for i, (_, row) in enumerate(df.iterrows(), 1):
        cells = f'<td>{i}</td>'
        for c in data_cols:
            val = row.get(c, 0)
            if c == 'اسم المراقب':
                cells += f'<td class="td-name">{val}</td>'
            elif c in pct_cols:
                cells += f'<td>{safe_pct(val)}</td>'
            else:
                cells += f'<td>{safe_int(val):,}</td>'
        html += f'<tr>{cells}</tr>'
    html += '</tbody></table>'

    # PAGE BREAK
    html += '<div class="page-break"></div>'

    # MUNICIPALITY
    if 'municipality' in analytics:
        muni_df   = analytics['municipality'].copy()
        has_v     = 'إجمالي الزيارات' in muni_df.columns and int(muni_df['إجمالي الزيارات'].sum()) > 0
        has_r     = 'عدد البلاغات' in muni_df.columns

        # Safe sort — prefer visits, then reports, then unsorted
        if has_v:
            muni_s = muni_df.sort_values('إجمالي الزيارات', ascending=False)
        elif has_r:
            muni_s = muni_df.sort_values('عدد البلاغات', ascending=False)
        else:
            muni_s = muni_df.copy()

        total_mr  = safe_int(muni_s['عدد البلاغات'].sum()) if has_r else 0
        total_mv  = safe_int(muni_s['إجمالي الزيارات'].sum()) if has_v else 0

        html += '<div class="sec-title">&#x1F3DB; إجمالي الزيارات والبلاغات لكل بلدية</div>'
        if not has_v:
            html += '<div class="note-box">ملاحظة: الزيارات تُقدَّر بنسبة مساهمة كل بلدية من بلاغات المراقب مضروبةً بإجمالي زياراته.</div>'

        html += f"""
<div class="kpi-band">
  <div class="kpi-card kpi-blue"> <div class="kpi-val">{len(muni_s)}</div>      <div class="kpi-lbl">&#x1F3DB; عدد البلديات</div></div>
  <div class="kpi-card kpi-teal"> <div class="kpi-val">{total_mv:,}</div> <div class="kpi-lbl">&#x1F4CD; إجمالي الزيارات</div></div>
  <div class="kpi-card kpi-green"><div class="kpi-val">{total_mr:,}</div> <div class="kpi-lbl">&#x1F4E2; إجمالي البلاغات</div></div>
</div>
"""
        # Table headers depend on what data is available
        if has_v and has_r:
            html += tbl_open(['البلدية','الزيارات','نسبة الزيارات %','البلاغات','نسبة البلاغات %'], 'th-teal')
        elif has_v:
            html += tbl_open(['البلدية','الزيارات','نسبة الزيارات %'], 'th-teal')
        elif has_r:
            html += tbl_open(['البلدية','البلاغات','نسبة البلاغات %'], 'th-teal')
        else:
            html += tbl_open(['البلدية'], 'th-teal')

        for _, row in muni_s.iterrows():
            bname = str(row.get('البلدية', '—'))
            r_val = safe_int(row['عدد البلاغات']) if has_r else 0
            r_pct = f"{r_val/total_mr*100:.1f}%" if (has_r and total_mr > 0) else "0%"
            v_val = safe_int(row.get('إجمالي الزيارات', 0)) if has_v else 0
            v_pct = f"{v_val/total_mv*100:.1f}%" if (has_v and total_mv > 0) else "0%"

            if has_v and has_r:
                html += f'<tr><td class="td-name">{bname}</td><td>{v_val:,}</td><td>{v_pct}</td><td>{r_val:,}</td><td>{r_pct}</td></tr>'
            elif has_v:
                html += f'<tr><td class="td-name">{bname}</td><td>{v_val:,}</td><td>{v_pct}</td></tr>'
            elif has_r:
                html += f'<tr><td class="td-name">{bname}</td><td>{r_val:,}</td><td>{r_pct}</td></tr>'
            else:
                html += f'<tr><td class="td-name">{bname}</td></tr>'

        if has_v and has_r:
            html += f'<tr class="total-row"><td>الإجمالي</td><td>{total_mv:,}</td><td>100%</td><td>{total_mr:,}</td><td>100%</td></tr>'
        elif has_v:
            html += f'<tr class="total-row"><td>الإجمالي</td><td>{total_mv:,}</td><td>100%</td></tr>'
        elif has_r:
            html += f'<tr class="total-row"><td>الإجمالي</td><td>{total_mr:,}</td><td>100%</td></tr>'
        html += '</tbody></table>'

    # VIOLATIONS DETAIL
    if 'violations' in analytics:
        viol_df = analytics['violations'].copy()
        v_cols = [c for c in ['اسم المراقب','إجمالي المخالفات','مخالفات مقبولة',
                               'مخالفات مرفوضة','نسبة قبول المخالفات %'] if c in viol_df.columns]
        v_hdrs = {'اسم المراقب':'المراقب','إجمالي المخالفات':'الكلي',
                  'مخالفات مقبولة':'مقبولة','مخالفات مرفوضة':'مرفوضة',
                  'نسبة قبول المخالفات %':'نسبة القبول'}
        html += '<div class="sec-title">&#x2696; تفاصيل المخالفات لكل مراقب</div>'
        html += tbl_open([v_hdrs.get(c,c) for c in v_cols], 'th-gold')
        for _, row in viol_df.sort_values('إجمالي المخالفات', ascending=False).iterrows():
            cells = ''
            for c in v_cols:
                val = row.get(c, 0)
                if c == 'اسم المراقب':
                    cells += f'<td class="td-name">{val}</td>'
                elif '%' in c:
                    cells += f'<td>{safe_pct(val)}</td>'
                else:
                    cells += f'<td>{safe_int(val):,}</td>'
            html += f'<tr>{cells}</tr>'
        html += '</tbody></table>'

    # TOP ARTICLES
    if 'top_articles' in analytics:
        art_df = analytics['top_articles'].head(15)
        total_art = int(art_df['التكرار'].sum())
        max_art   = int(art_df.iloc[0]['التكرار'])
        html += '<div class="sec-title">&#x1F4D1; بنود اللائحة الأكثر تكراراً</div>'
        html += tbl_open(['رقم البند / نص البند', 'عدد التكرار', 'النسبة %'], 'th-red')
        for _, row in art_df.iterrows():
            bnd = str(row['رقم البند'])
            cnt = int(row['التكرار'])
            pct = f"{cnt/total_art*100:.1f}%"
            bar_w = min(int(cnt/max_art*100), 100)
            bar = f'<div class="bar-wrap"><div class="bar-fill" style="width:{bar_w}%;background:#801a1a;"></div></div>'
            html += f'<tr><td class="td-name">{bnd}</td><td>{cnt:,}{bar}</td><td>{pct}</td></tr>'
        html += '</tbody></table>'

    # FOOTER
    html += f"""
</div>
<div class="footer">
  نظام تحليل أداء مراقبي الحفريات  •  أمانة العاصمة المقدسة  •  إعداد: Rakan_Alharbi  •  {now_str}
</div>
</div></body></html>"""
    return html


def generate_pdf_report(analytics, month="يناير 2026"):
    """Generate PDF from HTML using pdfkit for full Arabic support"""
    html = _build_report_html(analytics, month)
    options = {
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top':    '14mm',
        'margin-bottom': '14mm',
        'margin-right':  '14mm',
        'margin-left':   '14mm',
        'quiet': '',
        'enable-local-file-access': '',
        'no-outline': None,
        'print-media-type': '',
        'disable-smart-shrinking': '',
    }
    try:
        import pdfkit
        pdf_bytes = pdfkit.from_string(html, False, options=options)
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return buf, 'pdf'
    except Exception as e:
        buf = io.BytesIO(html.encode('utf-8'))
        buf.seek(0)
        return buf, 'html'


def get_report_html(analytics, month="يناير 2026"):
    """Return the HTML report string"""
    return _build_report_html(analytics, month)


# ─── Main Dashboard ──────────────────────────────────────────────────────────────
def show_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 12px 12px 12px; text-align:center;">
            <div style="
                display:inline-flex; align-items:center; justify-content:center;
                width:64px; height:64px; border-radius:50%;
                background:linear-gradient(135deg,#0A1428,#14305C);
                border:1px solid rgba(201,168,76,0.4);
                box-shadow:0 0 20px rgba(201,168,76,0.15);
                font-size:28px; margin-bottom:12px;">
                🏗️
            </div>
            <p style="color:#C9A84C; font-weight:700; font-size:14px; margin:0; direction:rtl; letter-spacing:0.5px;">
                نظام مراقبة الحفريات
            </p>
            <p style="color:#3A4A6A; font-size:11px; direction:rtl; margin:4px 0 0 0; letter-spacing:0.5px;">
                أمانة العاصمة المقدسة
            </p>
        </div>
        <div style="height:1px; background:linear-gradient(90deg,transparent,#1C2E4A,transparent); margin:4px 0 12px 0;"></div>
        """, unsafe_allow_html=True)

        page = st.radio("القائمة الرئيسية",
                       ["📤 رفع البيانات", "📊 لوحة الأداء", "📋 تحليل البيانات",
                        "⚙️ إدارة المراقبين", "📄 تصدير التقارير", "👤 إدارة الحسابات"],
                       label_visibility="collapsed")

        st.markdown("<div style='height:1px; background:linear-gradient(90deg,transparent,#1C2E4A,transparent); margin:12px 0;'></div>", unsafe_allow_html=True)

        _uname = st.session_state.get('username', '')
        _role  = st.session_state.get('role', '')
        _role_label = {'admin':'مسؤول كامل','supervisor':'مشرف','manager':'مدير','viewer':'مشاهد'}.get(_role, _role)
        st.markdown(f"""
        <div style="direction:rtl; font-size:12px; padding:8px 12px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                <span style="font-size:18px;">👤</span>
                <div>
                    <div style="color:#CBD5E8; font-weight:600; font-size:13px;">{_uname}</div>
                    <div style="color:#3A4A6A; font-size:11px;">{_role_label}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; padding:12px 0 10px 0;">
            <span style="
                color: #C9A84C;
                font-size: 13px;
                font-weight: 700;
                font-family: 'Cairo', sans-serif;
                letter-spacing: 1px;
                text-shadow: 0 0 8px rgba(201,168,76,0.5);
            ">✦ Developer By : Rakan_Alharbi ✦</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.pop('report_loaded_name', None)
            st.rerun()
    
    # ── Header ──
    now_display = datetime.now().strftime('%d %B %Y')
    st.markdown(f"""
    <div class="header-banner">
        <div>
            <div class="header-title">🏗️ نظام تحليل أداء مراقبي الحفريات</div>
            <div class="header-subtitle">أمانة العاصمة المقدسة  •  مكة المكرمة</div>
        </div>
        <div class="header-date-badge">📅 يناير 2026</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Load stored data from session ──
    analytics = st.session_state.get('analytics', {})
    
    # ── PAGES ──────────────────────────────────────────────────────────────────
    
    # ═══════════════════════════════════════════════
    if "رفع البيانات" in page:
        st.markdown('<div class="section-title">📤 رفع ملفات البيانات</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="warning-box">
            ⚠️ يرجى رفع الملفات الثلاثة للحصول على تحليل شامل. صيغة الملفات المدعومة: xlsx
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<p style="color:#4db8ff;text-align:center;font-weight:600;direction:rtl;">📍 ملف الزيارات</p>', unsafe_allow_html=True)
            visits_file = st.file_uploader("ملف الزيارات", type=['xlsx'], key='visits', label_visibility='collapsed')
            if visits_file:
                st.markdown('<div class="success-box">✅ تم رفع ملف الزيارات</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<p style="color:#4db8ff;text-align:center;font-weight:600;direction:rtl;">📢 ملف البلاغات</p>', unsafe_allow_html=True)
            reports_file = st.file_uploader("ملف البلاغات", type=['xlsx'], key='reports', label_visibility='collapsed')
            if reports_file:
                st.markdown('<div class="success-box">✅ تم رفع ملف البلاغات</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<p style="color:#4db8ff;text-align:center;font-weight:600;direction:rtl;">⚖️ ملف المخالفات</p>', unsafe_allow_html=True)
            violations_file = st.file_uploader("ملف المخالفات", type=['xlsx'], key='violations', label_visibility='collapsed')
            if violations_file:
                st.markdown('<div class="success-box">✅ تم رفع ملف المخالفات</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Count how many files are uploaded
        uploaded_count = sum([1 for f in [visits_file, reports_file, violations_file] if f is not None])
        
        if uploaded_count > 0:
            st.info(f"✅ تم رفع {uploaded_count} ملف — يمكنك المعالجة الآن. (لا يُشترط رفع الملفات الثلاثة)")
        
        if st.button("🔄 معالجة وتحليل البيانات", use_container_width=True, 
                     disabled=(uploaded_count == 0)):
            with st.spinner("جاري تحليل البيانات..."):
                visits_df, reports_df, violations_df = None, None, None
                visits_raw_df = None
                
                if visits_file:
                    result = parse_visits_file(visits_file.read())
                    if isinstance(result, tuple):
                        visits_df, visits_raw_df = result
                    else:
                        visits_df = result
                if reports_file:
                    reports_df = parse_reports_file(reports_file.read())
                if violations_file:
                    violations_df = parse_violations_file(violations_file.read())
                
                # Load external tasks and notes from DB
                conn = sqlite3.connect(DB_PATH)
                ext_tasks = pd.read_sql("SELECT * FROM external_tasks", conn)
                notes = pd.read_sql("SELECT * FROM performance_notes", conn)
                conn.close()
                
                st.session_state['visits_df']     = visits_df
                st.session_state['visits_raw_df'] = visits_raw_df
                st.session_state['reports_df']    = reports_df
                st.session_state['violations_df'] = violations_df
                
                analytics = compute_analytics(visits_df, reports_df, violations_df,
                                              ext_tasks, notes, visits_raw_df)
                st.session_state['analytics'] = analytics
                
                # Save to DB
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM uploaded_data")
                if visits_df is not None:
                    c.execute("INSERT INTO uploaded_data (data_type, data_json) VALUES (?,?)",
                             ('visits', visits_df.to_json(force_ascii=False)))
                if visits_raw_df is not None:
                    c.execute("INSERT INTO uploaded_data (data_type, data_json) VALUES (?,?)",
                             ('visits_raw', visits_raw_df.to_json(force_ascii=False)))
                if reports_df is not None:
                    c.execute("INSERT INTO uploaded_data (data_type, data_json) VALUES (?,?)",
                             ('reports', reports_df.to_json(force_ascii=False)))
                if violations_df is not None:
                    c.execute("INSERT INTO uploaded_data (data_type, data_json) VALUES (?,?)",
                             ('violations', violations_df.to_json(force_ascii=False)))
                conn.commit()
                conn.close()
                
                st.success("✅ تم تحليل البيانات بنجاح!")
                
                # Show summary
                if 'unified' in analytics:
                    df = analytics['unified']
                    c1,c2,c3,c4 = st.columns(4)
                    with c1:
                        st.metric("إجمالي المراقبين", len(df))
                    with c2:
                        v = int(df['عدد الزيارات'].sum()) if 'عدد الزيارات' in df.columns else 0
                        st.metric("إجمالي الزيارات", f"{v:,}")
                    with c3:
                        r = int(df['عدد البلاغات'].sum()) if 'عدد البلاغات' in df.columns else 0
                        st.metric("إجمالي البلاغات", f"{r:,}")
                    with c4:
                        viol = int(df['إجمالي المخالفات'].sum()) if 'إجمالي المخالفات' in df.columns else 0
                        st.metric("إجمالي المخالفات", f"{viol:,}")
        
        # Try loading saved data from DB if no session data
        if not analytics and not (visits_file or reports_file or violations_file):
            conn = sqlite3.connect(DB_PATH)
            saved = pd.read_sql("SELECT * FROM uploaded_data ORDER BY id DESC", conn)
            conn.close()
            
            if not saved.empty:
                st.markdown("""
                <div class="success-box">
                    💾 توجد بيانات محفوظة مسبقاً. يمكنك تحميلها أدناه.
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("📂 تحميل البيانات المحفوظة"):
                    visits_df, reports_df, violations_df, visits_raw_df = None, None, None, None
                    for _, row in saved.iterrows():
                        df_loaded = pd.read_json(io.StringIO(row['data_json']))
                        if row['data_type'] == 'visits':
                            visits_df = df_loaded
                        elif row['data_type'] == 'visits_raw':
                            visits_raw_df = df_loaded
                        elif row['data_type'] == 'reports':
                            reports_df = df_loaded
                        elif row['data_type'] == 'violations':
                            violations_df = df_loaded
                    
                    conn = sqlite3.connect(DB_PATH)
                    ext_tasks = pd.read_sql("SELECT * FROM external_tasks", conn)
                    notes = pd.read_sql("SELECT * FROM performance_notes", conn)
                    conn.close()
                    
                    analytics = compute_analytics(visits_df, reports_df, violations_df,
                                                  ext_tasks, notes, visits_raw_df)
                    st.session_state['analytics']     = analytics
                    st.session_state['visits_df']     = visits_df
                    st.session_state['visits_raw_df'] = visits_raw_df
                    st.session_state['reports_df']    = reports_df
                    st.session_state['violations_df'] = violations_df
                    st.success("✅ تم تحميل البيانات المحفوظة!")
                    st.rerun()
    
    # ═══════════════════════════════════════════════
    elif "لوحة الأداء" in page:
        st.markdown('<div class="section-title">📊 لوحة تحليل الأداء</div>', unsafe_allow_html=True)

        # ── استعراض التقارير المحفوظة — متاح لجميع الأدوار ──
        conn_sv = sqlite3.connect(DB_PATH)
        sv_reps = pd.read_sql(
            "SELECT id, report_name, report_type, report_ext, report_mime, created_at "
            "FROM saved_reports WHERE report_type IN ('PDF','HTML') ORDER BY created_at DESC",
            conn_sv
        )
        conn_sv.close()

        if not sv_reps.empty:
            with st.expander("استعراض تقرير محفوظ 📋", expanded=not bool(analytics)):
                col_sel, col_load, col_dash = st.columns([4, 1, 2])
                with col_sel:
                    rep_options = {
                        f"{r['report_name']}.{r['report_ext']}  —  {r['created_at']}": r['id']
                        for _, r in sv_reps.iterrows()
                    }
                    chosen_label = st.selectbox(
                        "اختر تقريراً لاستعراضه:",
                        list(rep_options.keys()),
                        key='dash_rep_select'
                    )
                    chosen_id = rep_options[chosen_label]

                with col_load:
                    st.markdown("<br>", unsafe_allow_html=True)
                    load_rep = st.button("🔍 عرض", use_container_width=True, key='load_rep_btn')

                with col_dash:
                    st.markdown("<br>", unsafe_allow_html=True)
                    load_to_dash = st.button(
                        "📊 تحميل للوحة والتحليل",
                        use_container_width=True,
                        key='load_rep_to_dash',
                        help="يستخرج بيانات التقرير ويعرضها في لوحة الأداء وتحليل البيانات"
                    )

                # ── تحميل البيانات للوحة ──
                if load_to_dash:
                    with st.spinner("جاري تحميل بيانات التقرير..."):
                        rep_analytics = load_analytics_from_saved_report(chosen_id)
                    if rep_analytics and 'unified' in rep_analytics:
                        st.session_state['analytics']           = rep_analytics
                        st.session_state['report_loaded_name'] = chosen_label
                        st.success(f"✅ تم تحميل بيانات التقرير — يمكنك الآن مشاهدتها في لوحة الأداء وتحليل البيانات")
                        st.rerun()
                    else:
                        st.error("⚠️ تعذّر استخراج البيانات من هذا التقرير. تأكد أنه تقرير HTML صادر من النظام.")

                # ── معاينة HTML ──
                if load_rep:
                    conn_ld = sqlite3.connect(DB_PATH)
                    row_d = conn_ld.execute(
                        "SELECT report_data, report_type, report_name, report_ext, report_mime "
                        "FROM saved_reports WHERE id=?",
                        (chosen_id,)
                    ).fetchone()
                    conn_ld.close()
                    if row_d:
                        raw_data, rtype, rname, rext, rmime = row_d
                        raw_bytes = bytes(raw_data)
                        st.download_button(
                            label=f"⬇️ تحميل {rname}.{rext}",
                            data=raw_bytes,
                            file_name=f"{rname}.{rext}",
                            mime=rmime,
                            use_container_width=True,
                            key='dash_dl_rep'
                        )
                        if rtype == 'HTML':
                            st.markdown("**📋 معاينة مباشرة:**")
                            html_str = raw_bytes.decode('utf-8', errors='replace')
                            components.html(html_str, height=700, scrolling=True)
                        else:
                            st.info("📄 تقرير PDF — اضغط التحميل أعلاه لفتحه في متصفحك.")

        # ── إشعار إذا كانت البيانات محملة من تقرير ──
        if st.session_state.get('report_loaded_name'):
            st.info(f"📂 البيانات المعروضة مستخرجة من التقرير: **{st.session_state['report_loaded_name']}**")

        if not analytics or 'unified' not in analytics:
            st.warning("⚠️ الرجاء رفع البيانات أولاً من صفحة 'رفع البيانات'")
            return
        
        df_all = analytics['unified']

        # ── فلتر المراقب (اختياري) ──
        # Clean names: keep only valid Arabic/text names, exclude timestamps/dates/numbers
        import re as _re_mon
        def _is_valid_name(s):
            s = str(s).strip()
            if not s or s in ('nan', 'None', '—'):
                return False
            # Reject if it looks like a date or timestamp (contains / or : heavily with digits)
            if _re_mon.match(r'^\d+[/\-]\d+[/\-\s]', s):
                return False
            # Reject pure numbers
            if _re_mon.match(r'^\d+\.?\d*$', s):
                return False
            # Keep anything with at least 2 Arabic/Latin characters
            arabic_latin = len(_re_mon.findall(r'[\u0600-\u06FF\u0041-\u007A\u0061-\u007A]', s))
            return arabic_latin >= 2

        valid_names = [n for n in df_all['اسم المراقب'].dropna().astype(str).tolist() if _is_valid_name(n)]
        monitor_names = ['— الكل —'] + sorted(set(valid_names))

        # ── callback لإعادة الفلتر للكل ──
        def _clear_monitor_filter():
            st.session_state['monitor_filter_select'] = '— الكل —'

        filter_col1, filter_col2 = st.columns([3, 1])
        with filter_col1:
            selected_monitor = st.selectbox(
                "🔍 عرض بيانات مراقب محدد (اختياري):",
                options=monitor_names,
                index=monitor_names.index(st.session_state.get('monitor_filter_select', '— الكل —'))
                      if st.session_state.get('monitor_filter_select', '— الكل —') in monitor_names else 0,
                key='monitor_filter_select',
                help="اختر مراقباً لعرض بياناته منفردةً، أو اتركه على «الكل» لعرض الجميع"
            )
        with filter_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if selected_monitor != '— الكل —':
                st.button(
                    "✖ إلغاء الفلتر",
                    use_container_width=True,
                    key='clear_filter',
                    on_click=_clear_monitor_filter
                )

        # تطبيق الفلتر
        is_filtered = selected_monitor != '— الكل —'
        df = df_all[df_all['اسم المراقب'] == selected_monitor].copy() if is_filtered else df_all.copy()

        # بطاقة معلومات المراقب المحدد
        if is_filtered and len(df) > 0:
            mon_row = df.iloc[0]
            mon_visits  = int(mon_row.get('عدد الزيارات', 0))
            mon_reports = int(mon_row.get('عدد البلاغات', 0))
            mon_viol    = int(mon_row.get('إجمالي المخالفات', 0))
            mon_app     = int(mon_row.get('مخالفات مقبولة', 0))
            mon_rej     = int(mon_row.get('مخالفات مرفوضة', 0))
            mon_score   = float(mon_row.get('نسبة الأداء الكلية %', 0))
            mon_rank    = int(mon_row.get('الترتيب', 0)) if 'الترتيب' in mon_row.index else '—'
            mon_just    = str(mon_row.get('تبرير الأداء', '') or '')
            total_monitors = len(df_all)

            score_color = '#C9A84C' if mon_score >= 85 else '#2E6FD8' if mon_score >= 60 else '#A03030'
            just_line = f'<div style="color:#ffd47d;font-size:12px;margin-top:6px;">📝 التبرير: {mon_just}</div>' if mon_just else ''

            monitor_card_html = f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
            .mon-profile {{
                font-family: 'Cairo', sans-serif;
                direction: rtl;
                background: linear-gradient(135deg, #080E1C, #0D1828);
                border: 1px solid #1C2E4A;
                border-top: 2px solid #C9A84C;
                border-radius: 16px;
                padding: 20px 24px;
                margin: 12px 0 16px 0;
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            }}
            .mon-avatar {{
                width: 68px; height: 68px;
                border-radius: 50%;
                background: linear-gradient(135deg, #0A1428, #14305C);
                border: 2px solid rgba(201,168,76,0.4);
                display: flex; align-items: center; justify-content: center;
                font-size: 30px; flex-shrink: 0;
                box-shadow: 0 0 16px rgba(201,168,76,0.1);
            }}
            .mon-info {{ flex: 1; min-width: 200px; }}
            .mon-name {{ font-size: 17px; font-weight: 700; color: #E6EAF2; }}
            .mon-sub  {{ font-size: 12px; color: #3A4A6A; margin-top: 2px; }}
            .mon-stats-row {{ display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap; }}
            .mon-stat {{ text-align: center; }}
            .mon-stat-val {{ font-size: 20px; font-weight: 700; }}
            .mon-stat-lbl {{ font-size: 10px; color: #3A4A6A; margin-top: 2px; }}
            .mon-score-badge {{
                font-size: 32px; font-weight: 700;
                color: {score_color};
                text-align: center; min-width: 100px;
                padding: 10px 18px;
                background: rgba(0,0,0,0.3);
                border-radius: 12px;
                border: 1px solid {score_color}30;
            }}
            .mon-score-lbl {{ font-size: 10px; color: #3A4A6A; text-align: center; margin-top: 4px; letter-spacing:0.3px; }}
            </style>
            <div class="mon-profile">
                <div class="mon-avatar">👤</div>
                <div class="mon-info">
                    <div class="mon-name">{selected_monitor}</div>
                    <div class="mon-sub">الترتيب: #{mon_rank} من أصل {total_monitors} مراقب</div>
                    {just_line}
                    <div class="mon-stats-row">
                        <div class="mon-stat">
                            <div class="mon-stat-val" style="color:#2E6FD8;">{mon_visits:,}</div>
                            <div class="mon-stat-lbl">📍 زيارات</div>
                        </div>
                        <div class="mon-stat">
                            <div class="mon-stat-val" style="color:#15876A;">{mon_reports:,}</div>
                            <div class="mon-stat-lbl">📢 بلاغات</div>
                        </div>
                        <div class="mon-stat">
                            <div class="mon-stat-val" style="color:#6B7A9A;">{mon_viol:,}</div>
                            <div class="mon-stat-lbl">⚖️ مخالفات</div>
                        </div>
                        <div class="mon-stat">
                            <div class="mon-stat-val" style="color:#4DC4A8;">{mon_app:,}</div>
                            <div class="mon-stat-lbl">✅ مقبولة</div>
                        </div>
                        <div class="mon-stat">
                            <div class="mon-stat-val" style="color:#A03030;">{mon_rej:,}</div>
                            <div class="mon-stat-lbl">❌ مرفوضة</div>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="mon-score-badge">{mon_score:.1f}%</div>
                    <div class="mon-score-lbl">نسبة الأداء الكلية</div>
                </div>
            </div>
            """
            components.html(monitor_card_html, height=170, scrolling=False)

        # ── KPI Cards using st.metric (always works) ──
        _muni_count = len(analytics['municipality']) if 'municipality' in analytics else 0
        kpi_cols = st.columns(6)
        kpi_data = [
            ("👥 المراقبون", len(df_all) if not is_filtered else 1, None),
            ("🏛️ البلديات", _muni_count, None),
            ("📍 الزيارات", int(df['عدد الزيارات'].sum()) if 'عدد الزيارات' in df.columns else 0, None),
            ("📢 البلاغات", int(df['عدد البلاغات'].sum()) if 'عدد البلاغات' in df.columns else 0, None),
            ("⚖️ المخالفات الكلية", int(df['إجمالي المخالفات'].sum()) if 'إجمالي المخالفات' in df.columns else 0, None),
            ("✅ المخالفات المقبولة", int(df['مخالفات مقبولة'].sum()) if 'مخالفات مقبولة' in df.columns else 0, None),
        ]
        for i, (label, val, delta) in enumerate(kpi_data):
            with kpi_cols[i]:
                st.metric(label=label, value=f"{val:,}")
        
        # ── Violations detail KPI row ──
        if 'مخالفات مقبولة' in df.columns and 'مخالفات مرفوضة' in df.columns and 'إجمالي المخالفات' in df.columns:
            total_all   = int(df['إجمالي المخالفات'].sum())
            total_app   = int(df['مخالفات مقبولة'].sum())
            total_rej   = int(df['مخالفات مرفوضة'].sum())
            acc_rate    = (total_app / total_all * 100) if total_all > 0 else 0
            rej_rate    = (total_rej / total_all * 100) if total_all > 0 else 0
            
            viol_html = f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
            .vkpi-row {{ display:flex; gap:10px; direction:rtl; font-family:'Cairo',sans-serif; margin:14px 0; }}
            .vkpi-card {{
                flex:1; border-radius:12px; padding:16px 18px; text-align:center;
                border: 1px solid; position:relative; overflow:hidden;
            }}
            .vkpi-card::before {{
                content:''; position:absolute; top:0; left:0; right:0; height:2px;
            }}
            .vkpi-total  {{ background:linear-gradient(160deg,#0D1828,#101A2E); border-color:#1C3060; }}
            .vkpi-total::before {{ background:#2E6FD8; }}
            .vkpi-app    {{ background:linear-gradient(160deg,#071C16,#0A2820); border-color:#0F4A38; }}
            .vkpi-app::before {{ background:#15876A; }}
            .vkpi-rej    {{ background:linear-gradient(160deg,#180808,#220E0E); border-color:#5A1818; }}
            .vkpi-rej::before {{ background:#A03030; }}
            .vkpi-rate-g {{ background:linear-gradient(160deg,#07201A,#0A2C24); border-color:#0F5040; }}
            .vkpi-rate-g::before {{ background:#C9A84C; }}
            .vkpi-rate-r {{ background:linear-gradient(160deg,#180E04,#221408); border-color:#5A3810; }}
            .vkpi-rate-r::before {{ background:#8A5020; }}
            .vkpi-num  {{ font-size:28px; font-weight:700; margin-bottom:3px; line-height:1.1; }}
            .vkpi-lbl  {{ font-size:11px; color:#6B7A9A; letter-spacing:0.3px; }}
            .c-total {{ color:#7AA8E8; }}
            .c-app   {{ color:#4DC4A8; }}
            .c-rej   {{ color:#D06060; }}
            .c-gr    {{ color:#C9A84C; }}
            .c-rr    {{ color:#A07040; }}
            .vkpi-bar {{ width:100%; height:4px; border-radius:2px; background:rgba(255,255,255,0.05); margin-top:10px; overflow:hidden; }}
            .vkpi-bar-fill {{ height:100%; border-radius:2px; }}
            </style>
            <div class="vkpi-row">
                <div class="vkpi-card vkpi-total">
                    <div class="vkpi-num c-total">{total_all:,}</div>
                    <div class="vkpi-lbl">⚖️ إجمالي المخالفات</div>
                    <div class="vkpi-bar"><div class="vkpi-bar-fill" style="width:100%;background:#2E6FD8;"></div></div>
                </div>
                <div class="vkpi-card vkpi-app">
                    <div class="vkpi-num c-app">{total_app:,}</div>
                    <div class="vkpi-lbl">✅ مخالفات مقبولة</div>
                    <div class="vkpi-bar"><div class="vkpi-bar-fill" style="width:{acc_rate:.0f}%;background:#15876A;"></div></div>
                </div>
                <div class="vkpi-card vkpi-rej">
                    <div class="vkpi-num c-rej">{total_rej:,}</div>
                    <div class="vkpi-lbl">❌ مخالفات مرفوضة</div>
                    <div class="vkpi-bar"><div class="vkpi-bar-fill" style="width:{rej_rate:.0f}%;background:#A03030;"></div></div>
                </div>
                <div class="vkpi-card vkpi-rate-g">
                    <div class="vkpi-num c-gr">{acc_rate:.1f}%</div>
                    <div class="vkpi-lbl">📈 نسبة القبول</div>
                    <div class="vkpi-bar"><div class="vkpi-bar-fill" style="width:{acc_rate:.0f}%;background:#C9A84C;"></div></div>
                </div>
                <div class="vkpi-card vkpi-rate-r">
                    <div class="vkpi-num c-rr">{rej_rate:.1f}%</div>
                    <div class="vkpi-lbl">📉 نسبة الرفض</div>
                    <div class="vkpi-bar"><div class="vkpi-bar-fill" style="width:{rej_rate:.0f}%;background:#8A5020;"></div></div>
                </div>
            </div>
            """
            components.html(viol_html, height=110, scrolling=False)

        # ── Municipality Visits Summary ──
        if 'municipality' in analytics:
            st.markdown(
                f'<div class="section-title">🏛️ {"زيارات المراقب حسب البلدية" if is_filtered else "إجمالي الزيارات لكل بلدية"}</div>',
                unsafe_allow_html=True
            )

            # If filtered: use per-monitor-municipality data
            if is_filtered and 'municipality_monitor' in analytics:
                muni_mon_df = analytics['municipality_monitor']
                muni_dash = muni_mon_df[muni_mon_df['اسم المراقب'] == selected_monitor].copy()
                muni_dash = muni_dash.rename(columns={'زيارات_في_البلدية': 'إجمالي الزيارات'})
                muni_dash = muni_dash[['البلدية', 'إجمالي الزيارات']].copy()
            else:
                muni_dash = analytics['municipality'].copy()

            # KPI mini row
            total_muni_v = int(muni_dash['إجمالي الزيارات'].sum()) if 'إجمالي الزيارات' in muni_dash.columns else 0
            num_muni = len(muni_dash)
            avg_muni_v = round(total_muni_v / num_muni, 1) if num_muni > 0 else 0
            
            mn1, mn2, mn3 = st.columns(3)
            mn1.metric("🏛️ عدد البلديات" + (" المُغطّاة" if is_filtered else ""), num_muni)
            mn2.metric("📍 إجمالي الزيارات" + (f" لـ {selected_monitor}" if is_filtered else " للبلديات"), f"{total_muni_v:,}")
            mn3.metric("📊 متوسط الزيارات للبلدية", f"{avg_muni_v:,}")
            
            if 'إجمالي الزيارات' in muni_dash.columns and total_muni_v > 0:
                muni_sorted_d = muni_dash.sort_values('إجمالي الزيارات', ascending=True)
                muni_colors = [
                    '#C9A84C' if v >= muni_sorted_d['إجمالي الزيارات'].max() * 0.85 else
                    '#2E6FD8' if v >= muni_sorted_d['إجمالي الزيارات'].max() * 0.55 else
                    '#1A3A6E' for v in muni_sorted_d['إجمالي الزيارات']
                ]
                fig_muni = go.Figure(go.Bar(
                    y=muni_sorted_d['البلدية'],
                    x=muni_sorted_d['إجمالي الزيارات'],
                    orientation='h',
                    marker=dict(color=muni_colors, line=dict(width=0)),
                    text=[f'{int(v):,}' for v in muni_sorted_d['إجمالي الزيارات']],
                    textposition='outside',
                    textangle=0,
                    textfont=dict(size=11, color='#CBD5E8', family='Cairo'),
                    cliponaxis=False,
                ))
                fig_muni.update_layout(
                    height=max(350, num_muni * 38 + 80),
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(8,12,20,0.97)',
                    font=dict(color='#CBD5E8', size=11, family='Cairo'),
                    margin=dict(l=10, r=90, t=30, b=20),
                    xaxis=dict(gridcolor='#1C2E4A', title='عدد الزيارات', tickfont=dict(color='#6B7A9A')),
                    yaxis=dict(gridcolor='#1C2E4A', tickfont=dict(size=11, family='Cairo', color='#CBD5E8')),
                    title=dict(text='إجمالي الزيارات الميدانية حسب البلدية', font=dict(size=13, color='#C9A84C')),
                )
                st.plotly_chart(fig_muni, use_container_width=True)
            
            # Municipality detail table
            muni_tbl_dash = muni_dash.copy()
            if 'إجمالي الزيارات' in muni_tbl_dash.columns and total_muni_v > 0:
                muni_tbl_dash['نسبة الزيارات %'] = (muni_tbl_dash['إجمالي الزيارات'] / total_muni_v * 100).round(1)
            muni_tbl_dash = muni_tbl_dash.sort_values('إجمالي الزيارات', ascending=False).reset_index(drop=True)
            muni_tbl_dash.index += 1
            st.dataframe(muni_tbl_dash, use_container_width=True)

        st.markdown("---")

        if 'مخالفات مقبولة' in df.columns and 'مخالفات مرفوضة' in df.columns and 'إجمالي المخالفات' in df.columns:
            total_all   = int(df['إجمالي المخالفات'].sum())
            total_app   = int(df['مخالفات مقبولة'].sum())
            total_rej   = int(df['مخالفات مرفوضة'].sum())
            acc_rate    = (total_app / total_all * 100) if total_all > 0 else 0
            rej_rate    = (total_rej / total_all * 100) if total_all > 0 else 0

            # Per-monitor violations breakdown table
            st.markdown('<div class="section-title">📋 مؤشر المخالفات التفصيلي لكل مراقب</div>', unsafe_allow_html=True)
            
            viol_cols = [c for c in ['اسم المراقب','إجمالي المخالفات','مخالفات مقبولة','مخالفات مرفوضة'] if c in df.columns]
            viol_display = df[viol_cols].copy().sort_values('إجمالي المخالفات', ascending=False).reset_index(drop=True)
            viol_display.index += 1
            
            if 'مخالفات مقبولة' in viol_display.columns and 'إجمالي المخالفات' in viol_display.columns:
                viol_display['نسبة القبول %'] = (
                    viol_display['مخالفات مقبولة'] / viol_display['إجمالي المخالفات'].replace(0, np.nan) * 100
                ).round(1).fillna(0)
            
            # Violations stacked bar per monitor
            fig_vb = go.Figure()
            vbd = viol_display.sort_values('إجمالي المخالفات', ascending=True)
            
            if 'مخالفات مقبولة' in vbd.columns:
                fig_vb.add_trace(go.Bar(
                    y=vbd['اسم المراقب'], x=vbd['مخالفات مقبولة'],
                    name='مقبولة', orientation='h',
                    marker_color='#15876A',
                    text=[str(int(v)) if v > 0 else '' for v in vbd['مخالفات مقبولة']],
                    textposition='inside',
                    textangle=0,
                    textfont=dict(size=13, color='#FFFFFF', family='Cairo'),
                    insidetextanchor='middle',
                ))
            if 'مخالفات مرفوضة' in vbd.columns:
                fig_vb.add_trace(go.Bar(
                    y=vbd['اسم المراقب'], x=vbd['مخالفات مرفوضة'],
                    name='مرفوضة', orientation='h',
                    marker_color='#C03030',
                    text=[str(int(v)) if v > 0 else '' for v in vbd['مخالفات مرفوضة']],
                    textposition='inside',
                    textangle=0,
                    textfont=dict(size=13, color='#FFFFFF', family='Cairo'),
                    insidetextanchor='middle',
                ))
            
            fig_vb.update_layout(
                barmode='stack',
                height=max(550, len(vbd) * 38),
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(8,12,20,0.95)',
                font=dict(color='#CBD5E8', size=13, family='Cairo'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                           font=dict(size=14), bgcolor='rgba(0,0,0,0)', bordercolor='#1C2E4A'),
                margin=dict(l=10, r=30, t=50, b=10),
                xaxis=dict(
                    gridcolor='#1C2E4A',
                    title='عدد المخالفات',
                    tickfont=dict(color='#6B7A9A', size=12),
                    range=[0, vbd[['مخالفات مقبولة','مخالفات مرفوضة']].sum(axis=1).max() * 1.15]
                    if 'مخالفات مقبولة' in vbd.columns and 'مخالفات مرفوضة' in vbd.columns else None
                ),
                yaxis=dict(
                    gridcolor='#1C2E4A',
                    tickfont=dict(color='#E6EAF2', size=13, family='Cairo'),
                    automargin=True,
                ),
                title=dict(text='مخالفات مقبولة ومرفوضة لكل مراقب', font=dict(size=15, color='#C9A84C')),
                bargap=0.25,
            )
            st.plotly_chart(fig_vb, use_container_width=True)
            st.dataframe(viol_display, use_container_width=True)
        
        st.markdown("---")
        
        # ── Top 5 / Bottom 5 using st.components for guaranteed HTML rendering ──
        
        col_top, col_bot = st.columns(2)
        
        with col_top:
            st.markdown('<div class="section-title">🏆 أفضل 5 مراقبين أداءً</div>', unsafe_allow_html=True)
            top5 = df.head(5)
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            
            cards_html = """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
            .top-card {
                font-family: 'Cairo', sans-serif;
                background: linear-gradient(135deg,#071C16,#0A2820);
                border: 1px solid #0F4A38;
                border-top: 2px solid #C9A84C;
                border-radius: 12px;
                padding: 14px 18px;
                margin: 8px 0;
                direction: rtl;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            }
            .card-name { font-weight:700; color:#E6EAF2; font-size:14px; }
            .card-stats { color:#4DC4A8; font-size:12px; margin-top:3px; }
            .card-just { color:#C9A84C; font-size:11px; margin-top:2px; }
            .card-medal { text-align:center; font-size:28px; line-height:1.2; }
            .card-score { color:#C9A84C; font-size:14px; font-weight:700; text-align:center; }
            </style>
            """
            
            for i, (_, row) in enumerate(top5.iterrows()):
                name = str(row['اسم المراقب'])
                visits = int(row.get('عدد الزيارات', 0))
                reports = int(row.get('عدد البلاغات', 0))
                viol = int(row.get('مخالفات مقبولة', 0))
                score = float(row.get('درجة الأداء', 0))
                pct   = float(row.get('نسبة الأداء الكلية %', 0))
                app_r = float(row.get('نسبة قبول المخالفات %', 0))
                just = str(row.get('تبرير الأداء', '') or '')
                medal = medals[i] if i < 5 else str(i+1)
                just_line = f'<div class="card-just">📝 {just}</div>' if just else ''
                cards_html += f"""
                <div class="top-card">
                    <div>
                        <div class="card-name">{name}</div>
                        <div class="card-stats">زيارات: {visits} | بلاغات: {reports} | مخالفات مقبولة: {viol}</div>
                        <div class="card-stats" style="color:#C9A84C;">نسبة قبول المخالفات: {app_r:.1f}%</div>
                        {just_line}
                    </div>
                    <div style="text-align:center;min-width:64px;">
                        <div class="card-medal">{medal}</div>
                        <div class="card-score">{pct:.1f}%</div>
                        <div style="color:#3A4A6A;font-size:10px;">من الأعلى أداءً</div>
                    </div>
                </div>"""
            
            components.html(cards_html, height=len(top5)*108 + 40, scrolling=False)
        
        with col_bot:
            st.markdown('<div class="section-title">📉 أقل 5 مراقبين أداءً</div>', unsafe_allow_html=True)
            bottom5 = df.tail(5)
            
            bot_html = """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
            .bot-card {
                font-family: 'Cairo', sans-serif;
                background: linear-gradient(135deg,#180808,#220E0E);
                border: 1px solid #5A1818;
                border-top: 2px solid #A03030;
                border-radius: 12px;
                padding: 14px 18px;
                margin: 8px 0;
                direction: rtl;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            }
            .bot-name { font-weight:700; color:#E6EAF2; font-size:14px; }
            .bot-stats { color:#D06060; font-size:12px; margin-top:3px; }
            .bot-just { color:#C9A84C; font-size:11px; margin-top:2px; }
            .bot-rank { font-size:22px; color:#A03030; text-align:center; }
            .bot-score { color:#D06060; font-size:13px; font-weight:700; text-align:center; }
            </style>
            """
            
            for idx, (_, row) in enumerate(bottom5.iterrows()):
                name = str(row['اسم المراقب'])
                visits = int(row.get('عدد الزيارات', 0))
                reports = int(row.get('عدد البلاغات', 0))
                viol = int(row.get('مخالفات مقبولة', 0))
                score = float(row.get('درجة الأداء', 0))
                pct   = float(row.get('نسبة الأداء الكلية %', 0))
                app_r = float(row.get('نسبة قبول المخالفات %', 0))
                just = str(row.get('تبرير الأداء', '') or '')
                rank = len(df) - len(bottom5) + idx + 1
                just_line = f'<div class="bot-just">📝 {just}</div>' if just else ''
                bot_html += f"""
                <div class="bot-card">
                    <div>
                        <div class="bot-name">{name}</div>
                        <div class="bot-stats">زيارات: {visits} | بلاغات: {reports} | مخالفات مقبولة: {viol}</div>
                        <div class="bot-stats" style="color:#ffd47d;">نسبة قبول المخالفات: {app_r:.1f}%</div>
                        {just_line}
                    </div>
                    <div style="text-align:center;min-width:60px;">
                        <div class="bot-rank">⬇</div>
                        <div class="bot-score">{pct:.1f}%</div>
                        <div style="color:#8a9bb5;font-size:10px;">#{rank}</div>
                    </div>
                </div>"""
            
            components.html(bot_html, height=len(bottom5)*130 + 60, scrolling=False)
        
        st.markdown("---")
        
        # ── مخطط الأداء الشامل — Subplots احترافي ──
        st.markdown('<div class="section-title">📈 مخطط الأداء الشامل</div>', unsafe_allow_html=True)
        
        chart_df = df.sort_values('درجة الأداء', ascending=True).copy()
        names = chart_df['اسم المراقب'].tolist()
        
        # تحديد الأعمدة المتوفرة
        has_visits  = 'عدد الزيارات'    in chart_df.columns
        has_reports = 'عدد البلاغات'    in chart_df.columns
        has_viol    = 'مخالفات مقبولة'  in chart_df.columns and 'مخالفات مرفوضة' in chart_df.columns
        has_score   = 'نسبة الأداء الكلية %' in chart_df.columns
        
        active_cols = [x for x in [has_visits, has_reports, has_viol, has_score] if x]
        n_cols = len(active_cols) if active_cols else 1
        
        subplot_titles = []
        if has_visits:  subplot_titles.append('📍 الزيارات')
        if has_reports: subplot_titles.append('📢 البلاغات')
        if has_viol:    subplot_titles.append('⚖️ المخالفات مقبولة / مرفوضة')
        if has_score:   subplot_titles.append('🎯 نسبة الأداء الكلية %')
        
        row_h = max(28, int(600 / max(len(names), 1)))
        fig_h = max(500, len(names) * row_h + 80)
        
        fig = make_subplots(
            rows=1, cols=n_cols,
            shared_yaxes=True,
            subplot_titles=subplot_titles,
            horizontal_spacing=0.04,
        )
        
        col_idx = 1
        
        # ── الزيارات ──
        if has_visits:
            vals = chart_df['عدد الزيارات']
            max_v = vals.max() if vals.max() > 0 else 1
            colors_v = [
                '#C9A84C' if v >= max_v * 0.85 else
                '#2E6FD8' if v >= max_v * 0.55 else
                '#1A3A6E' for v in vals
            ]
            fig.add_trace(go.Bar(
                x=vals, y=names, orientation='h',
                name='الزيارات',
                marker=dict(color=colors_v, line=dict(width=0)),
                text=[f'{v:,}' for v in vals],
                textposition='outside',
                textfont=dict(size=11, color='#CBD5E8', family='Cairo'),
                cliponaxis=False,
                showlegend=False,
            ), row=1, col=col_idx)
            fig.update_xaxes(showgrid=True, gridcolor='#1C2E4A',
                            tickfont=dict(size=10, color='#6B7A9A'), row=1, col=col_idx)
            col_idx += 1
        
        # ── البلاغات ──
        if has_reports:
            vals = chart_df['عدد البلاغات']
            max_v = vals.max() if vals.max() > 0 else 1
            colors_r = [
                '#C9A84C' if v >= max_v * 0.85 else
                '#15876A' if v >= max_v * 0.55 else
                '#0A4A38' for v in vals
            ]
            fig.add_trace(go.Bar(
                x=vals, y=names, orientation='h',
                name='البلاغات',
                marker=dict(color=colors_r, line=dict(width=0)),
                text=[f'{v:,}' for v in vals],
                textposition='outside',
                textfont=dict(size=11, color='#CBD5E8', family='Cairo'),
                cliponaxis=False,
                showlegend=False,
            ), row=1, col=col_idx)
            fig.update_xaxes(showgrid=True, gridcolor='#1C2E4A',
                            tickfont=dict(size=10, color='#6B7A9A'), row=1, col=col_idx)
            col_idx += 1
        
        # ── المخالفات مقبولة/مرفوضة (stacked) ──
        if has_viol:
            app_vals = chart_df['مخالفات مقبولة']
            rej_vals = chart_df['مخالفات مرفوضة']
            fig.add_trace(go.Bar(
                x=app_vals, y=names, orientation='h',
                name='مقبولة',
                marker=dict(color='#15876A', line=dict(width=0)),
                text=[str(int(v)) if v > 0 else '' for v in app_vals],
                textposition='inside',
                textangle=0,
                textfont=dict(size=11, color='#E6EAF2', family='Cairo'),
                insidetextanchor='middle',
                showlegend=True,
            ), row=1, col=col_idx)
            fig.add_trace(go.Bar(
                x=rej_vals, y=names, orientation='h',
                name='مرفوضة',
                marker=dict(color='#8A2828', line=dict(width=0)),
                text=[str(int(v)) if v > 0 else '' for v in rej_vals],
                textposition='inside',
                textangle=0,
                textfont=dict(size=11, color='#E6EAF2', family='Cairo'),
                insidetextanchor='middle',
                showlegend=True,
            ), row=1, col=col_idx)
            fig.update_xaxes(showgrid=True, gridcolor='#1C2E4A',
                            tickfont=dict(size=10, color='#6B7A9A'), row=1, col=col_idx)
            col_idx += 1
        
        # ── نسبة الأداء الكلية % ──
        if has_score:
            pct_vals = chart_df['نسبة الأداء الكلية %']
            colors_p = [
                '#C9A84C' if v >= 85 else
                '#2E6FD8' if v >= 60 else
                '#8A2828' for v in pct_vals
            ]
            fig.add_trace(go.Bar(
                x=pct_vals, y=names, orientation='h',
                name='نسبة الأداء',
                marker=dict(color=colors_p, line=dict(width=0)),
                text=[f'{v:.1f}%' for v in pct_vals],
                textposition='outside',
                textfont=dict(size=11, color='#CBD5E8', family='Cairo'),
                cliponaxis=False,
                showlegend=False,
            ), row=1, col=col_idx)
            fig.update_xaxes(
                showgrid=True, gridcolor='#1C2E4A',
                ticksuffix='%', range=[0, 115],
                tickfont=dict(size=10, color='#6B7A9A'), row=1, col=col_idx)
        
        # ── اليمين: أسماء المراقبين ──
        fig.update_yaxes(
            tickfont=dict(size=11, family='Cairo', color='#CBD5E8'),
            showgrid=False,
            row=1, col=1
        )
        
        fig.update_layout(
            height=fig_h,
            barmode='stack',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(8,12,20,0.97)',
            font=dict(color='#CBD5E8', size=11, family='Cairo'),
            legend=dict(
                orientation='h', yanchor='bottom', y=1.04,
                xanchor='center', x=0.5,
                font=dict(size=12), bgcolor='rgba(0,0,0,0)',
                bordercolor='#1C2E4A', borderwidth=1,
            ),
            margin=dict(l=20, r=70, t=70, b=20),
        )
        
        # Style subplot titles
        for ann in fig.layout.annotations:
            ann.font = dict(size=13, color='#C9A84C', family='Cairo')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ── مؤشر النسب الكلية لكل مراقب ──
        st.markdown('<div class="section-title">🎯 مؤشر الأداء النسبي لكل مراقب</div>', unsafe_allow_html=True)
        
        pct_df = df.sort_values('نسبة الأداء الكلية %', ascending=False).copy() if 'نسبة الأداء الكلية %' in df.columns else df.sort_values('درجة الأداء', ascending=False).copy()
        
        # Build a grouped bar chart: all % indicators per monitor
        pct_fig = go.Figure()
        
        pct_cols = [
            ('نسبة الأداء الكلية %',      '#2E6FD8', 'نسبة الأداء الكلية'),
            ('نسبة الزيارات %',           '#C9A84C', 'نسبة الزيارات'),
            ('نسبة البلاغات %',           '#15876A', 'نسبة البلاغات'),
            ('نسبة قبول المخالفات %',     '#4DC4A8', 'نسبة قبول المخالفات'),
            ('نسبة رفض المخالفات %',      '#8A2828', 'نسبة رفض المخالفات'),
        ]
        
        for col, color, label in pct_cols:
            if col in pct_df.columns:
                pct_fig.add_trace(go.Bar(
                    x=pct_df['اسم المراقب'],
                    y=pct_df[col],
                    name=label,
                    marker_color=color,
                    text=pct_df[col].apply(lambda v: f"{v:.1f}%"),
                    textposition='inside',
                    textfont=dict(size=12, color='#ffffff', family='Cairo'),
                    insidetextanchor='middle',
                ))
        
        pct_fig.update_layout(
            barmode='group',
            height=480,
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(8,12,20,0.97)',
            font=dict(color='#CBD5E8', size=11, family='Cairo'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                       font=dict(size=11), bgcolor='rgba(0,0,0,0)', bordercolor='#1C2E4A', borderwidth=1),
            margin=dict(l=10, r=20, t=50, b=80),
            xaxis=dict(tickangle=-40, gridcolor='#1C2E4A', tickfont=dict(size=10, color='#6B7A9A')),
            yaxis=dict(gridcolor='#1C2E4A', title='النسبة %', range=[0, 110],
                      ticksuffix='%', tickfont=dict(size=11, color='#6B7A9A')),
            title=dict(text='مقارنة نسب الأداء لجميع المراقبين', font=dict(size=14, color='#C9A84C')),
        )
        # Mean line for overall %
        if 'نسبة الأداء الكلية %' in pct_df.columns:
            mean_pct = pct_df['نسبة الأداء الكلية %'].mean()
            pct_fig.add_hline(y=mean_pct, line_dash='dot', line_color='#C9A84C', line_width=1.5,
                             annotation_text=f'المتوسط: {mean_pct:.1f}%',
                             annotation_position='top left',
                             annotation_font_color='#C9A84C', annotation_font_size=12)
        st.plotly_chart(pct_fig, use_container_width=True)
        
        # ── جدول النسب التفصيلي ──
        st.markdown('<div class="section-title">📋 جدول النسب التفصيلي لكل مراقب</div>', unsafe_allow_html=True)
        
        pct_table_cols = ['الترتيب', 'اسم المراقب',
                          'نسبة الأداء الكلية %', 'نسبة الزيارات %',
                          'نسبة البلاغات %', 'نسبة قبول المخالفات %',
                          'نسبة رفض المخالفات %']
        pct_table_cols = [c for c in pct_table_cols if c in pct_df.columns]
        
        pct_display = pct_df[pct_table_cols].copy()
        
        # Build per-row HTML table with colored progress bars
        tbl_html = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        .pct-table { width:100%; border-collapse:collapse; font-family:'Cairo',sans-serif; direction:rtl; font-size:13px; }
        .pct-table th { background:#0D1828; color:#C9A84C; padding:10px 14px; text-align:center; font-weight:700;
                        border-bottom:2px solid #1C2E4A; font-size:12px; letter-spacing:0.3px; }
        .pct-table td { padding:9px 12px; text-align:center; border-bottom:1px solid #0F1A2E; color:#CBD5E8; }
        .pct-table tr:hover td { background:rgba(46,111,216,0.06); }
        .pct-table tr:nth-child(even) td { background:rgba(13,24,40,0.5); }
        .bar-wrap { background:#08121E; border-radius:3px; height:5px; width:100%; margin-top:5px; overflow:hidden; }
        .bar-fill  { height:100%; border-radius:3px; }
        .rank-gold   { color:#C9A84C; font-weight:700; font-size:16px; }
        .rank-silver { color:#9AA8B8; font-weight:700; }
        .rank-bronze { color:#8A6030; font-weight:700; }
        .rank-other  { color:#3A4A6A; }
        .pct-overall { color:#7AA8E8; font-weight:700; }
        .pct-visits  { color:#C9A84C; }
        .pct-reports { color:#4DC4A8; }
        .pct-app     { color:#15876A; font-weight:600; }
        .pct-rej     { color:#A03030; font-weight:600; }
        </style>
        <table class="pct-table">
        <tr>
            <th>#</th><th>اسم المراقب</th>
            <th>نسبة الأداء الكلية</th>
            <th>نسبة الزيارات</th>
            <th>نسبة البلاغات</th>
            <th>نسبة قبول المخالفات</th>
            <th>نسبة رفض المخالفات</th>
        </tr>
        """
        
        rank_classes = ['rank-gold', 'rank-silver', 'rank-bronze']
        
        def pct_cell(val, color, bar_color):
            bar_w = min(val, 100)
            return f"""<td><span style="color:{color};font-weight:600;">{val:.1f}%</span>
                       <div class="bar-wrap"><div class="bar-fill" style="width:{bar_w}%;background:{bar_color};"></div></div></td>"""
        
        for i, (_, row) in enumerate(pct_df.iterrows()):
            rc = rank_classes[i] if i < 3 else 'rank-other'
            rank_sym = ['🥇','🥈','🥉'][i] if i < 3 else f'#{i+1}'
            name = str(row['اسم المراقب'])
            
            overall = float(row.get('نسبة الأداء الكلية %', 0))
            visits  = float(row.get('نسبة الزيارات %', 0))
            reports = float(row.get('نسبة البلاغات %', 0))
            app_r   = float(row.get('نسبة قبول المخالفات %', 0))
            rej_r   = float(row.get('نسبة رفض المخالفات %', 0))
            
            tbl_html += f"""<tr>
                <td class="{rc}">{rank_sym}</td>
                <td style="text-align:right;font-weight:600;color:#E6EAF2;">{name}</td>
                {pct_cell(overall, '#7AA8E8', '#2E6FD8')}
                {pct_cell(visits,  '#C9A84C', '#8A6020')}
                {pct_cell(reports, '#4DC4A8', '#15876A')}
                {pct_cell(app_r,   '#4DC4A8', '#0F6050')}
                {pct_cell(rej_r,   '#D06060', '#8A2828')}
            </tr>"""
        
        tbl_html += "</table>"
        components.html(tbl_html, height=min(55 * len(pct_df) + 80, 700), scrolling=True)
        
        # ── Violations pie ──
        if 'violations' in analytics:
            viol_df = analytics['violations']
            if 'مخالفات مقبولة' in viol_df.columns and 'مخالفات مرفوضة' in viol_df.columns:
                total_approved = int(viol_df['مخالفات مقبولة'].sum())
                total_rejected = int(viol_df['مخالفات مرفوضة'].sum())
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="section-title">📊 توزيع حالة المخالفات</div>', unsafe_allow_html=True)
                    pie_fig = go.Figure(go.Pie(
                        labels=['مقبولة', 'مرفوضة'],
                        values=[total_approved, total_rejected],
                        hole=0.5,
                        marker=dict(colors=['#15876A', '#8A2828'],
                                   line=dict(color='#080C14', width=2)),
                        textinfo='label+percent+value',
                        textfont=dict(size=12, family='Cairo', color='#E6EAF2'),
                    ))
                    pie_fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=320,
                        margin=dict(l=20, r=20, t=20, b=20),
                        font=dict(color='#e8eaf0', family='Cairo'),
                    )
                    st.plotly_chart(pie_fig, use_container_width=True)
                
                with c2:
                    if 'top_articles' in analytics:
                        st.markdown('<div class="section-title">📑 أكثر بنود اللائحة تكراراً</div>', unsafe_allow_html=True)
                        art = analytics['top_articles'].head(8)
                        art_fig = px.bar(art, x='التكرار', y='رقم البند', orientation='h',
                                        color='التكرار', color_continuous_scale='Blues',
                                        template='plotly_dark',
                                        text='التكرار')
                        art_fig.update_traces(textposition='outside', textfont_size=11)
                        art_fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(15,20,35,0.8)',
                            height=320,
                            margin=dict(l=10, r=60, t=10, b=10),
                            font=dict(color='#e8eaf0', family='Cairo'),
                            showlegend=False,
                            coloraxis_showscale=False,
                        )
                        st.plotly_chart(art_fig, use_container_width=True)
        
        # ── Recommendations ──
        st.markdown("---")
        st.markdown('<div class="section-title">💡 توصيات وتحسينات للمراقبين</div>', unsafe_allow_html=True)
        
        if 'unified' in analytics:
            # ── حساب جميع النسب ──
            avg_pct       = df['نسبة الأداء الكلية %'].mean()      if 'نسبة الأداء الكلية %'     in df.columns else 0
            avg_v_pct     = df['نسبة الزيارات %'].mean()           if 'نسبة الزيارات %'           in df.columns else 0
            avg_r_pct     = df['نسبة البلاغات %'].mean()           if 'نسبة البلاغات %'           in df.columns else 0
            avg_app_pct   = df['نسبة قبول المخالفات %'].mean()     if 'نسبة قبول المخالفات %'    in df.columns else 0
            avg_rej_pct   = df['نسبة رفض المخالفات %'].mean()      if 'نسبة رفض المخالفات %'     in df.columns else 0

            top_performer  = df.iloc[0]  if len(df) > 0 else None
            low_performers = df[df['نسبة الأداء الكلية %'] < avg_pct * 0.7] if 'نسبة الأداء الكلية %' in df.columns else pd.DataFrame()

            # مراقبون بنسبة قبول مخالفات منخفضة
            low_acc = df[df['نسبة قبول المخالفات %'] < 50] if 'نسبة قبول المخالفات %' in df.columns else pd.DataFrame()
            # مراقبون بنسبة زيارات أقل من المتوسط
            low_visits = df[df['نسبة الزيارات %'] < avg_v_pct * 0.6] if 'نسبة الزيارات %' in df.columns else pd.DataFrame()
            # مراقبون متميزون (نسبة أداء > 85%)
            stars = df[df['نسبة الأداء الكلية %'] >= 85] if 'نسبة الأداء الكلية %' in df.columns else pd.DataFrame()

            recs_html = """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
            * { box-sizing: border-box; }
            .rec-wrap {
                font-family: 'Cairo', sans-serif;
                direction: rtl;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
                padding: 4px 0;
            }
            .rec-card {
                border-radius: 14px;
                padding: 18px 20px;
                border: 1px solid;
                position: relative;
                overflow: hidden;
            }
            .rec-card::before {
                content: '';
                position: absolute;
                top: 0; right: 0;
                width: 3px; height: 100%;
            }
            .rec-card::after {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; height: 1px;
            }
            .rc-gold   { background: linear-gradient(160deg,#0E0C04,#1A1608); border-color:#3A2E08; }
            .rc-gold::before   { background: #C9A84C; }
            .rc-gold::after    { background: linear-gradient(90deg,#C9A84C,transparent); }
            .rc-blue   { background: linear-gradient(160deg,#060E1C,#091428); border-color:#142040; }
            .rc-blue::before   { background: #2E6FD8; }
            .rc-blue::after    { background: linear-gradient(90deg,#2E6FD8,transparent); }
            .rc-green  { background: linear-gradient(160deg,#04100C,#071814); border-color:#0A3020; }
            .rc-green::before  { background: #15876A; }
            .rc-green::after   { background: linear-gradient(90deg,#15876A,transparent); }
            .rc-red    { background: linear-gradient(160deg,#0E0404,#180808); border-color:#3A1010; }
            .rc-red::before    { background: #A03030; }
            .rc-red::after     { background: linear-gradient(90deg,#A03030,transparent); }
            .rc-orange { background: linear-gradient(160deg,#0E0800,#1A1008); border-color:#3A2000; }
            .rc-orange::before { background: #8A5020; }
            .rc-orange::after  { background: linear-gradient(90deg,#8A5020,transparent); }
            .rc-purple { background: linear-gradient(160deg,#080614,#0E0C1E); border-color:#201840; }
            .rc-purple::before { background: #5A3A9A; }
            .rc-purple::after  { background: linear-gradient(90deg,#5A3A9A,transparent); }
            .rec-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
            .rec-icon-big { font-size: 20px; }
            .rec-title { font-size: 13px; font-weight: 700; letter-spacing: 0.3px; }
            .rec-body  { font-size: 12px; color: #6B7A9A; line-height: 1.8; }
            .tag {
                display: inline-block; border-radius: 5px;
                padding: 1px 8px; font-size: 11px; font-weight: 700; margin: 0 2px;
            }
            .tag-gold   { background:#1A1200; color:#C9A84C; border:1px solid #3A2E08; }
            .tag-blue   { background:#060E1C; color:#7AA8E8; border:1px solid #142040; }
            .tag-green  { background:#04100C; color:#4DC4A8; border:1px solid #0A3020; }
            .tag-red    { background:#0E0404; color:#D06060; border:1px solid #3A1010; }
            .tag-warn   { background:#0E0800; color:#A07040; border:1px solid #3A2000; }
            .pct-badge { font-size: 22px; font-weight: 700; margin: 6px 0 3px 0; }
            .pct-label { font-size: 10px; color: #3A4A6A; letter-spacing: 0.3px; }
            .mini-bar-wrap { background:#080C14; border-radius:3px; height:4px; margin-top:8px; overflow:hidden; }
            .mini-bar { height:100%; border-radius:3px; }
            .names-list { color:#8A9BBF; font-size:11px; margin-top:6px; }
            </style>
            <div class="rec-wrap">
            """

            # ── بطاقة 1: المراقب الأفضل ──
            if top_performer is not None:
                top_pct    = float(top_performer.get('نسبة الأداء الكلية %', 0))
                top_v_pct  = float(top_performer.get('نسبة الزيارات %', 0))
                top_r_pct  = float(top_performer.get('نسبة البلاغات %', 0))
                top_a_pct  = float(top_performer.get('نسبة قبول المخالفات %', 0))
                top_name   = str(top_performer['اسم المراقب'])
                recs_html += f"""
                <div class="rec-card rc-gold">
                    <div class="rec-head">
                        <span class="rec-icon-big">🏆</span>
                        <span class="rec-title" style="color:#ffd700;">المراقب المتميز</span>
                    </div>
                    <div class="pct-badge" style="color:#ffd700;">{top_pct:.1f}%</div>
                    <div class="pct-label">نسبة الأداء الكلية</div>
                    <div class="mini-bar-wrap"><div class="mini-bar" style="width:{min(top_pct,100):.0f}%;background:#ffd700;"></div></div>
                    <div class="rec-body" style="margin-top:10px;">
                        <span class="tag tag-gold">{top_name}</span> يحقق أعلى أداء.
                        نسبة زياراته <span class="tag tag-blue">{top_v_pct:.1f}%</span>
                        ونسبة بلاغاته <span class="tag tag-green">{top_r_pct:.1f}%</span>
                        ونسبة قبول مخالفاته <span class="tag tag-green">{top_a_pct:.1f}%</span>.
                        يُنصح باستضافته لنقل الخبرات للفريق.
                    </div>
                </div>"""

            # ── بطاقة 2: المراقبون تحت المتوسط ──
            if len(low_performers) > 0:
                lp_names = '، '.join(low_performers['اسم المراقب'].tolist()[:4])
                threshold = avg_pct * 0.7
                recs_html += f"""
                <div class="rec-card rc-red">
                    <div class="rec-head">
                        <span class="rec-icon-big">⚠️</span>
                        <span class="rec-title" style="color:#ff7d7d;">مراقبون يحتاجون متابعة</span>
                    </div>
                    <div class="pct-badge" style="color:#ff7d7d;">{len(low_performers)} مراقب</div>
                    <div class="pct-label">أداؤهم أقل من {threshold:.1f}% (70% من المتوسط)</div>
                    <div class="mini-bar-wrap"><div class="mini-bar" style="width:{(len(low_performers)/len(df)*100):.0f}%;background:#c84040;"></div></div>
                    <div class="rec-body" style="margin-top:10px;">
                        <div class="names-list">📌 {lp_names}</div>
                        يُوصى بتوجيههم ميدانياً وإعداد خطة تطوير فردية لرفع نسبة أدائهم فوق
                        <span class="tag tag-warn">{avg_pct:.1f}%</span> (متوسط الفريق).
                    </div>
                </div>"""

            # ── بطاقة 3: نسبة الزيارات ──
            recs_html += f"""
            <div class="rec-card rc-blue">
                <div class="rec-head">
                    <span class="rec-icon-big">📍</span>
                    <span class="rec-title" style="color:#4db8ff;">مؤشر الزيارات</span>
                </div>
                <div class="pct-badge" style="color:#4db8ff;">{avg_v_pct:.1f}%</div>
                <div class="pct-label">متوسط نسبة مساهمة كل مراقب بالزيارات</div>
                <div class="mini-bar-wrap"><div class="mini-bar" style="width:{min(avg_v_pct*5,100):.0f}%;background:#4db8ff;"></div></div>
                <div class="rec-body" style="margin-top:10px;">
                    المراقبون الذين تقل نسبة مساهمتهم عن
                    <span class="tag tag-warn">{avg_v_pct*0.6:.1f}%</span>
                    يحتاجون متابعة ميدانية مكثفة.
                    {'✅ الفريق يحقق توزيعاً متوازناً للزيارات.' if len(low_visits) == 0 else f'⚠️ {len(low_visits)} مراقب دون المستوى المطلوب.'}
                </div>
            </div>"""

            # ── بطاقة 4: نسبة البلاغات ──
            recs_html += f"""
            <div class="rec-card rc-green">
                <div class="rec-head">
                    <span class="rec-icon-big">📢</span>
                    <span class="rec-title" style="color:#50e8a0;">مؤشر البلاغات</span>
                </div>
                <div class="pct-badge" style="color:#50e8a0;">{avg_r_pct:.1f}%</div>
                <div class="pct-label">متوسط نسبة مساهمة كل مراقب بالبلاغات</div>
                <div class="mini-bar-wrap"><div class="mini-bar" style="width:{min(avg_r_pct*5,100):.0f}%;background:#3da66e;"></div></div>
                <div class="rec-body" style="margin-top:10px;">
                    البلاغات تمثّل <span class="tag tag-green">25%</span> من وزن تقييم الأداء.
                    رفع نسبة البلاغات يُحسّن الأداء الكلي مباشرةً.
                    يُنصح بتحفيز المراقبين على تسجيل كل بلاغ ميداني فور رصده.
                </div>
            </div>"""

            # ── بطاقة 5: نسبة قبول المخالفات ──
            acc_color  = '#50e8a0' if avg_app_pct >= 70 else '#ffc060'
            acc_cls    = 'rc-green' if avg_app_pct >= 70 else 'rc-orange'
            acc_status = '✅ ممتاز — دقة التوثيق عالية.' if avg_app_pct >= 70 else '⚠️ يحتاج تحسين — بعض المخالفات تُرفض لخلل في التوثيق.'
            recs_html += f"""
            <div class="rec-card {acc_cls}">
                <div class="rec-head">
                    <span class="rec-icon-big">✅</span>
                    <span class="rec-title" style="color:{acc_color};">نسبة قبول المخالفات</span>
                </div>
                <div class="pct-badge" style="color:{acc_color};">{avg_app_pct:.1f}%</div>
                <div class="pct-label">متوسط نسبة المخالفات المقبولة لكل مراقب</div>
                <div class="mini-bar-wrap"><div class="mini-bar" style="width:{min(avg_app_pct,100):.0f}%;background:{acc_color};"></div></div>
                <div class="rec-body" style="margin-top:10px;">
                    {acc_status}
                    {'نسبة الرفض ' + f'<span class="tag tag-red">{avg_rej_pct:.1f}%</span>' if avg_rej_pct > 0 else ''}
                    {f'<br>المراقبون ذوو نسبة قبول أقل من 50% ({len(low_acc)} مراقب) يحتاجون تدريباً على متطلبات التوثيق.' if len(low_acc) > 0 else ''}
                </div>
            </div>"""

            # ── بطاقة 6: المتميزون ونجوم الفريق ──
            stars_html_content = ''
            if len(stars) > 0:
                for _, s in stars.head(3).iterrows():
                    sp = float(s.get('نسبة الأداء الكلية %', 0))
                    stars_html_content += f'<span class="tag tag-gold">{s["اسم المراقب"]} {sp:.0f}%</span> '
            else:
                stars_html_content = '<span style="color:#8a9bb5;">لا يوجد مراقبون بنسبة فوق 85% حتى الآن</span>'

            recs_html += f"""
            <div class="rec-card rc-purple">
                <div class="rec-head">
                    <span class="rec-icon-big">⭐</span>
                    <span class="rec-title" style="color:#9b72ff;">نجوم الفريق (نسبة ≥ 85%)</span>
                </div>
                <div class="pct-badge" style="color:#9b72ff;">{len(stars)}</div>
                <div class="pct-label">عدد المراقبين المتميزين</div>
                <div class="mini-bar-wrap"><div class="mini-bar" style="width:{(len(stars)/max(len(df),1)*100):.0f}%;background:#9b72ff;"></div></div>
                <div class="rec-body" style="margin-top:10px;">
                    {stars_html_content}
                    <br>يُنصح بتكريم هؤلاء المراقبين رسمياً وتوثيق ممارساتهم كمرجع للفريق.
                </div>
            </div>
            </div>"""

            components.html(recs_html, height=600, scrolling=True)
    
    # ═══════════════════════════════════════════════
    elif "تحليل البيانات" in page:
        st.markdown('<div class="section-title">📋 تحليل البيانات التفصيلي</div>', unsafe_allow_html=True)

        if not analytics:
            # ── إذا لا توجد بيانات، عرض التقارير المحفوظة مباشرة ──
            conn_sv2 = sqlite3.connect(DB_PATH)
            sv_reps2 = pd.read_sql(
                "SELECT id, report_name, report_type, report_ext, created_at "
                "FROM saved_reports WHERE report_type='HTML' ORDER BY created_at DESC",
                conn_sv2
            )
            conn_sv2.close()
            if not sv_reps2.empty:
                st.warning("⚠️ لا توجد بيانات مرفوعة — يمكنك تحميل تقرير محفوظ:")
                rep_opts2 = {
                    f"{r['report_name']}.{r['report_ext']}  —  {r['created_at']}": r['id']
                    for _, r in sv_reps2.iterrows()
                }
                c1, c2 = st.columns([5, 2])
                chosen2 = c1.selectbox("اختر تقريراً:", list(rep_opts2.keys()), key='analysis_rep_sel')
                with c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📊 تحميل للتحليل", use_container_width=True, key='analysis_load_btn'):
                        rep_analytics2 = load_analytics_from_saved_report(rep_opts2[chosen2])
                        if rep_analytics2 and 'unified' in rep_analytics2:
                            st.session_state['analytics']           = rep_analytics2
                            st.session_state['report_loaded_name'] = chosen2
                            st.rerun()
                        else:
                            st.error("⚠️ تعذّر استخراج البيانات من هذا التقرير.")
            else:
                st.warning("⚠️ الرجاء رفع البيانات أولاً")
            return

        # ── إشعار مصدر البيانات ──
        if st.session_state.get('report_loaded_name'):
            st.info(f"📂 البيانات من التقرير المحفوظ: **{st.session_state['report_loaded_name']}**")

        # Debug: show violation status values if available
        if '_violation_status_unique' in analytics:
            with st.expander("🔍 قيم حالة الاعتماد المكتشفة في الملف (للتشخيص)"):
                st.write(analytics['_violation_status_unique'])

        tab1, tab2, tab3, tab4 = st.tabs(["📍 الزيارات", "📢 البلاغات", "⚖️ المخالفات", "📊 ملخص أداء المراقبين"])

        # ─── Tab 1: Visits ───
        with tab1:
            if 'visits' in analytics:
                visits_df_disp = analytics['visits'].copy()
                visits_df_disp.index += 1
                total_v = int(visits_df_disp['عدد الزيارات'].sum())

                kc1, kc2, kc3 = st.columns(3)
                kc1.metric("📍 إجمالي الزيارات", f"{total_v:,}")
                kc2.metric("👥 عدد المراقبين", len(visits_df_disp))
                kc3.metric("📊 متوسط الزيارات/مراقب", f"{total_v/max(len(visits_df_disp),1):.1f}")

                _v_sorted = visits_df_disp.sort_values('عدد الزيارات', ascending=False)
                fig_v = px.bar(
                    _v_sorted,
                    x='اسم المراقب', y='عدد الزيارات',
                    template='plotly_dark',
                    color='عدد الزيارات',
                    color_continuous_scale=[[0,'#1A3A6E'],[0.5,'#2E6FD8'],[1,'#C9A84C']],
                    title='توزيع الزيارات على المراقبين',
                    text='عدد الزيارات',
                )
                fig_v.update_traces(
                    texttemplate='%{text:,}',
                    textposition='inside',
                    textangle=0,
                    textfont=dict(size=14, color='#FFFFFF', family='Cairo'),
                    insidetextanchor='middle',
                )
                fig_v.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(8,12,20,0.97)',
                    xaxis_tickangle=-45,
                    height=500,
                    coloraxis_showscale=False,
                    font=dict(color='#CBD5E8', family='Cairo'),
                    xaxis=dict(gridcolor='#1C2E4A', tickfont=dict(color='#CBD5E8', size=11)),
                    yaxis=dict(gridcolor='#1C2E4A'),
                    title=dict(font=dict(color='#C9A84C', size=15)),
                    uniformtext_minsize=10,
                    uniformtext_mode='hide',
                    margin=dict(t=60, b=120),
                )
                st.plotly_chart(fig_v, use_container_width=True)
                st.dataframe(visits_df_disp, use_container_width=True)
            else:
                st.info("لا تتوفر بيانات زيارات")

        # ─── Tab 2: Reports ───
        with tab2:
            if 'reports' in analytics:
                rep_df = analytics['reports'].copy()
                rep_df.index += 1
                total_r = int(rep_df['عدد البلاغات'].sum())

                rc1, rc2, rc3 = st.columns(3)
                rc1.metric("📢 إجمالي البلاغات", f"{total_r:,}")
                rc2.metric("👥 عدد المراقبين", len(rep_df))
                rc3.metric("📊 متوسط البلاغات/مراقب", f"{total_r/max(len(rep_df),1):.1f}")

                _r_sorted = rep_df.sort_values('عدد البلاغات', ascending=False)
                fig_r = px.bar(
                    _r_sorted,
                    x='اسم المراقب', y='عدد البلاغات',
                    template='plotly_dark',
                    color='عدد البلاغات',
                    color_continuous_scale=[[0,'#0A3020'],[0.5,'#15876A'],[1,'#C9A84C']],
                    title='توزيع البلاغات على المراقبين',
                    text='عدد البلاغات',
                )
                fig_r.update_traces(
                    texttemplate='%{text:,}',
                    textposition='inside',
                    textangle=0,
                    textfont=dict(size=14, color='#FFFFFF', family='Cairo'),
                    insidetextanchor='middle',
                )
                fig_r.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(8,12,20,0.97)',
                    xaxis_tickangle=-45,
                    height=500,
                    coloraxis_showscale=False,
                    font=dict(color='#CBD5E8', family='Cairo'),
                    xaxis=dict(gridcolor='#1C2E4A', tickfont=dict(color='#CBD5E8', size=11)),
                    yaxis=dict(gridcolor='#1C2E4A'),
                    title=dict(font=dict(color='#C9A84C', size=15)),
                    uniformtext_minsize=10,
                    uniformtext_mode='hide',
                    margin=dict(t=60, b=120),
                )
                st.plotly_chart(fig_r, use_container_width=True)

                if 'municipality' in analytics:
                    st.markdown('<div class="section-title">🏛️ إجمالي الزيارات والبلاغات لكل بلدية</div>', unsafe_allow_html=True)
                    muni_df = analytics['municipality'].copy()
                    total_muni_reports = int(muni_df['عدد البلاغات'].sum()) if 'عدد البلاغات' in muni_df.columns else 0
                    total_muni_visits  = int(muni_df['إجمالي الزيارات'].sum()) if 'إجمالي الزيارات' in muni_df.columns else 0
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("🏛️ عدد البلديات", len(muni_df))
                    mc2.metric("📢 إجمالي البلاغات", f"{total_muni_reports:,}")
                    if total_muni_visits > 0:
                        mc3.metric("📍 إجمالي الزيارات", f"{total_muni_visits:,}")

                    has_visits_muni = 'إجمالي الزيارات' in muni_df.columns and muni_df['إجمالي الزيارات'].sum() > 0
                    muni_sorted = muni_df.sort_values('عدد البلاغات', ascending=False) if 'عدد البلاغات' in muni_df.columns else muni_df

                    fig_m = go.Figure()
                    if has_visits_muni:
                        fig_m.add_trace(go.Bar(
                            x=muni_sorted['البلدية'], y=muni_sorted['إجمالي الزيارات'],
                            name='الزيارات', marker_color='#2E6FD8',
                            text=muni_sorted['إجمالي الزيارات'], textposition='outside',
                            textfont=dict(size=10, color='#CBD5E8', family='Cairo'),
                        ))
                    if 'عدد البلاغات' in muni_sorted.columns:
                        fig_m.add_trace(go.Bar(
                            x=muni_sorted['البلدية'], y=muni_sorted['عدد البلاغات'],
                            name='البلاغات', marker_color='#15876A',
                            text=muni_sorted['عدد البلاغات'], textposition='outside',
                            textfont=dict(size=10, color='#CBD5E8', family='Cairo'),
                        ))
                    fig_m.update_layout(
                        barmode='group', template='plotly_dark',
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,12,20,0.97)',
                        font=dict(color='#CBD5E8', size=11, family='Cairo'),
                        height=380,
                        xaxis=dict(tickangle=-35, gridcolor='#1C2E4A', tickfont=dict(color='#CBD5E8', size=10)),
                        yaxis=dict(gridcolor='#1C2E4A'),
                        legend=dict(orientation='h', y=1.08, bgcolor='rgba(0,0,0,0)'),
                        margin=dict(l=10, r=10, t=50, b=60),
                        title=dict(text='الزيارات والبلاغات حسب البلدية', font=dict(size=13, color='#C9A84C')),
                    )
                    st.plotly_chart(fig_m, use_container_width=True)

                    muni_tbl = muni_df.copy()
                    if 'عدد البلاغات' in muni_tbl.columns and total_muni_reports > 0:
                        muni_tbl['نسبة البلاغات %'] = (muni_tbl['عدد البلاغات'] / total_muni_reports * 100).round(1)
                    if has_visits_muni and total_muni_visits > 0:
                        muni_tbl['نسبة الزيارات %'] = (muni_tbl['إجمالي الزيارات'] / total_muni_visits * 100).round(1)
                    muni_tbl = muni_tbl.sort_values('عدد البلاغات', ascending=False).reset_index(drop=True) if 'عدد البلاغات' in muni_tbl.columns else muni_tbl
                    muni_tbl.index += 1
                    st.dataframe(muni_tbl, use_container_width=True)

                st.dataframe(rep_df, use_container_width=True)
            else:
                st.info("لا تتوفر بيانات بلاغات")

        # ─── Tab 3: Violations ───
        with tab3:
            if 'violations' in analytics:
                viol_df = analytics['violations'].copy()

                # KPI row
                total_viol = int(viol_df['إجمالي المخالفات'].sum())
                total_app  = int(viol_df['مخالفات مقبولة'].sum()) if 'مخالفات مقبولة' in viol_df.columns else 0
                total_rej  = int(viol_df['مخالفات مرفوضة'].sum()) if 'مخالفات مرفوضة' in viol_df.columns else 0
                acc_rate   = (total_app / total_viol * 100) if total_viol > 0 else 0

                vc1, vc2, vc3, vc4 = st.columns(4)
                vc1.metric("⚖️ إجمالي المخالفات",    f"{total_viol:,}")
                vc2.metric("✅ مخالفات مقبولة",      f"{total_app:,}")
                vc3.metric("❌ مخالفات مرفوضة",      f"{total_rej:,}")
                vc4.metric("📈 نسبة القبول",         f"{acc_rate:.1f}%")

                # Stacked bar — أفقي مع ظهور جميع الأسماء والأرقام
                fig_viol = go.Figure()
                vd_sorted = viol_df.sort_values('إجمالي المخالفات', ascending=True)
                if 'مخالفات مقبولة' in vd_sorted.columns:
                    fig_viol.add_trace(go.Bar(
                        y=vd_sorted['اسم المراقب'], x=vd_sorted['مخالفات مقبولة'],
                        name='مقبولة', marker_color='#15876A',
                        orientation='h',
                        text=[str(int(v)) if v > 0 else '' for v in vd_sorted['مخالفات مقبولة']],
                        textposition='inside',
                        textangle=0,
                        textfont=dict(size=13, color='#FFFFFF', family='Cairo'),
                        insidetextanchor='middle',
                    ))
                if 'مخالفات مرفوضة' in vd_sorted.columns:
                    fig_viol.add_trace(go.Bar(
                        y=vd_sorted['اسم المراقب'], x=vd_sorted['مخالفات مرفوضة'],
                        name='مرفوضة', marker_color='#C03030',
                        orientation='h',
                        text=[str(int(v)) if v > 0 else '' for v in vd_sorted['مخالفات مرفوضة']],
                        textposition='inside',
                        textangle=0,
                        textfont=dict(size=13, color='#FFFFFF', family='Cairo'),
                        insidetextanchor='middle',
                    ))
                fig_viol.update_layout(
                    barmode='stack', template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,12,20,0.97)',
                    height=max(550, len(vd_sorted) * 38),
                    font=dict(color='#CBD5E8', family='Cairo', size=13),
                    xaxis=dict(
                        gridcolor='#1C2E4A',
                        title='عدد المخالفات',
                        tickfont=dict(color='#6B7A9A', size=12),
                    ),
                    yaxis=dict(
                        gridcolor='#1C2E4A',
                        tickfont=dict(color='#E6EAF2', size=13, family='Cairo'),
                        automargin=True,
                    ),
                    legend=dict(
                        bgcolor='rgba(0,0,0,0)', bordercolor='#1C2E4A', borderwidth=1,
                        orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                        font=dict(size=14),
                    ),
                    margin=dict(l=10, r=30, t=50, b=10),
                    bargap=0.25,
                    title=dict(text='المخالفات المقبولة والمرفوضة لكل مراقب', font=dict(color='#C9A84C', size=15)),
                )
                st.plotly_chart(fig_viol, use_container_width=True)

                # Top articles overall
                if 'top_articles' in analytics:
                    st.markdown('<div class="section-title">📑 بنود اللائحة الأكثر تكراراً (إجمالي)</div>', unsafe_allow_html=True)
                    art_df = analytics['top_articles'].head(15)
                    if len(art_df) > 0:
                        top_art   = art_df.iloc[0]['رقم البند']
                        top_count = art_df.iloc[0]['التكرار']
                        st.markdown(f"""
                        <div class="warning-box">
                            🔴 البند الأكثر تكراراً: <strong>{top_art}</strong> — تكرر <strong>{top_count:,}</strong> مرة
                        </div>
                        """, unsafe_allow_html=True)

                        # Bar chart for top articles
                        fig_art = go.Figure(go.Bar(
                            x=art_df['رقم البند'].astype(str),
                            y=art_df['التكرار'],
                            marker_color='#C9A84C',
                            text=art_df['التكرار'],
                            textposition='outside',
                            textfont=dict(size=11, color='#CBD5E8', family='Cairo'),
                        ))
                        fig_art.update_layout(
                            template='plotly_dark',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,12,20,0.97)',
                            height=350, font=dict(color='#CBD5E8', family='Cairo'),
                            xaxis=dict(title='رقم البند', gridcolor='#1C2E4A', tickfont=dict(color='#CBD5E8', size=10)),
                            yaxis=dict(title='عدد التكرار', gridcolor='#1C2E4A'),
                            title=dict(text='أكثر بنود اللائحة تكراراً', font=dict(color='#C9A84C', size=13)),
                            margin=dict(l=10, r=10, t=50, b=40),
                        )
                        st.plotly_chart(fig_art, use_container_width=True)
                        st.dataframe(art_df, use_container_width=True)

                # Violations detail table
                viol_df.index += 1
                cols_to_show = [c for c in ['اسم المراقب', 'إجمالي المخالفات', 'مخالفات مقبولة', 'مخالفات مرفوضة'] if c in viol_df.columns]
                st.dataframe(viol_df[cols_to_show], use_container_width=True)
            else:
                st.info("لا تتوفر بيانات مخالفات")

        # ─── Tab 4: Monitor Performance Summary ───
        with tab4:
            if 'unified' not in analytics:
                st.info("لا تتوفر بيانات كافية لعرض ملخص الأداء")
            else:
                perf_df = analytics['unified'].copy()

                st.markdown('<div class="section-title">📊 تفاصيل أداء جميع المراقبين</div>', unsafe_allow_html=True)

                # Select columns to display — clean and ordered
                display_cols = ['الترتيب', 'اسم المراقب']
                for c in ['عدد الزيارات', 'عدد البلاغات', 'إجمالي المخالفات',
                          'مخالفات مقبولة', 'مخالفات مرفوضة',
                          'نسبة قبول المخالفات %', 'أكثر_بند', 'عدد_تكرار_البند',
                          'درجة الأداء', 'نسبة الأداء الكلية %', 'تبرير الأداء']:
                    if c in perf_df.columns:
                        display_cols.append(c)

                perf_display = perf_df[display_cols].copy()

                # Rename columns for display
                rename_map = {
                    'أكثر_بند':          'أكثر بند مستخدم',
                    'عدد_تكرار_البند':   'تكرار البند',
                }
                perf_display = perf_display.rename(columns=rename_map)
                perf_display = perf_display.reset_index(drop=True)

                st.dataframe(
                    perf_display,
                    use_container_width=True,
                    height=600,
                )

                # Top article per monitor chart
                if 'أكثر_بند' in perf_df.columns:
                    st.markdown('<div class="section-title">📋 أكثر بند مستخدم لكل مراقب</div>', unsafe_allow_html=True)

                    art_mon_df = perf_df[['اسم المراقب', 'أكثر_بند', 'عدد_تكرار_البند']].copy()
                    art_mon_df = art_mon_df[art_mon_df['أكثر_بند'] != '—'].sort_values('عدد_تكرار_البند', ascending=False)

                    if not art_mon_df.empty:
                        fig_art_mon = go.Figure(go.Bar(
                            y=art_mon_df['اسم المراقب'],
                            x=art_mon_df['عدد_تكرار_البند'],
                            orientation='h',
                            marker_color='#C9A84C',
                            text=[f"بند {b} ({n}×)" for b, n in zip(art_mon_df['أكثر_بند'], art_mon_df['عدد_تكرار_البند'])],
                            textposition='outside',
                            textangle=0,
                            textfont=dict(size=10, color='#CBD5E8', family='Cairo'),
                            cliponaxis=False,
                        ))
                        fig_art_mon.update_layout(
                            template='plotly_dark',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,12,20,0.97)',
                            height=max(400, len(art_mon_df) * 28 + 80),
                            font=dict(color='#CBD5E8', family='Cairo'),
                            xaxis=dict(title='عدد التكرار', gridcolor='#1C2E4A', tickfont=dict(color='#6B7A9A', size=10)),
                            yaxis=dict(gridcolor='#1C2E4A', tickfont=dict(color='#CBD5E8', size=11, family='Cairo')),
                            title=dict(text='أكثر بند مستخدم لكل مراقب مع عدد تكراراته', font=dict(color='#C9A84C', size=13)),
                            margin=dict(l=10, r=120, t=50, b=20),
                        )
                        st.plotly_chart(fig_art_mon, use_container_width=True)

                        # Table: monitor → top article
                        art_tbl = art_mon_df.rename(columns={
                            'أكثر_بند': 'أكثر بند مستخدم',
                            'عدد_تكرار_البند': 'عدد التكرار'
                        }).reset_index(drop=True)
                        art_tbl.index += 1
                        st.dataframe(art_tbl, use_container_width=True)
    
    # ═══════════════════════════════════════════════
    elif "إدارة المراقبين" in page:
        st.markdown('<div class="section-title">⚙️ إدارة المراقبين وتعديل الأداء</div>', unsafe_allow_html=True)
        
        if not analytics or 'unified' not in analytics:
            st.warning("⚠️ الرجاء رفع البيانات أولاً")
            return
        
        df = analytics['unified']
        monitor_names = df['اسم المراقب'].tolist()
        
        tab_ext, tab_just = st.tabs(["➕ إضافة مهام خارجية", "📝 تبرير انخفاض الأداء"])
        
        with tab_ext:
            st.markdown("**أضف مهام خارجية لمراقب لتُحتسب ضمن إنتاجيته**")
            
            col1, col2 = st.columns(2)
            with col1:
                selected_monitor = st.selectbox("اختر المراقب", monitor_names, key='ext_monitor')
                task_count = st.number_input("عدد المهام", min_value=1, max_value=100, value=1, key='ext_count')
            with col2:
                task_desc = st.text_area("وصف المهمة", placeholder="مثال: مسح ميداني لمنطقة العزيزية", key='ext_desc')
                task_date = st.date_input("تاريخ المهمة", key='ext_date')
            
            if st.button("✅ إضافة المهمة", key='add_task'):
                if task_desc.strip():
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("INSERT INTO external_tasks (monitor_name, task_description, task_count, task_date) VALUES (?,?,?,?)",
                             (selected_monitor, task_desc, task_count, str(task_date)))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم إضافة {task_count} مهمة للمراقب {selected_monitor}")
                    # Recompute analytics
                    conn = sqlite3.connect(DB_PATH)
                    ext_tasks = pd.read_sql("SELECT * FROM external_tasks", conn)
                    notes = pd.read_sql("SELECT * FROM performance_notes", conn)
                    conn.close()
                    new_analytics = compute_analytics(
                        st.session_state.get('visits_df'),
                        st.session_state.get('reports_df'),
                        st.session_state.get('violations_df'),
                        ext_tasks, notes,
                        st.session_state.get('visits_raw_df')
                    )
                    st.session_state['analytics'] = new_analytics
                    st.rerun()
                else:
                    st.error("يرجى إدخال وصف المهمة")
            
            # Show existing tasks
            conn = sqlite3.connect(DB_PATH)
            tasks_df = pd.read_sql("SELECT * FROM external_tasks ORDER BY created_at DESC", conn)
            conn.close()
            
            if not tasks_df.empty:
                st.markdown('<div class="section-title">📋 المهام الخارجية المسجلة</div>', unsafe_allow_html=True)
                st.dataframe(tasks_df[['monitor_name', 'task_description', 'task_count', 'task_date']].rename(
                    columns={'monitor_name': 'المراقب', 'task_description': 'الوصف', 
                             'task_count': 'العدد', 'task_date': 'التاريخ'}
                ), use_container_width=True)
        
        with tab_just:
            st.markdown("**سجّل تبريراً لانخفاض أداء مراقب معين**")
            
            col1, col2 = st.columns(2)
            with col1:
                just_monitor = st.selectbox("اختر المراقب", monitor_names, key='just_monitor')
                justification = st.selectbox("سبب انخفاض الأداء", 
                                           ["إجازة", "مشكلة بالنظام", "مسح ميداني", "مأموريات خارجية", "تدريب"],
                                           key='just_reason')
            with col2:
                just_details = st.text_area("تفاصيل إضافية", placeholder="أضف تفاصيل...", key='just_details')
            
            if st.button("💾 حفظ التبرير", key='save_just'):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # Remove old justification for this monitor
                c.execute("DELETE FROM performance_notes WHERE monitor_name=?", (just_monitor,))
                c.execute("INSERT INTO performance_notes (monitor_name, justification, details) VALUES (?,?,?)",
                         (just_monitor, justification, just_details))
                conn.commit()
                conn.close()
                st.success(f"✅ تم حفظ تبرير الأداء للمراقب {just_monitor}")
                # Recompute
                conn = sqlite3.connect(DB_PATH)
                ext_tasks = pd.read_sql("SELECT * FROM external_tasks", conn)
                notes = pd.read_sql("SELECT * FROM performance_notes", conn)
                conn.close()
                new_analytics = compute_analytics(
                    st.session_state.get('visits_df'),
                    st.session_state.get('reports_df'),
                    st.session_state.get('violations_df'),
                    ext_tasks, notes,
                    st.session_state.get('visits_raw_df')
                )
                st.session_state['analytics'] = new_analytics
                st.rerun()
            
            # Show existing notes
            conn = sqlite3.connect(DB_PATH)
            notes_df = pd.read_sql("SELECT * FROM performance_notes ORDER BY created_at DESC", conn)
            conn.close()
            
            if not notes_df.empty:
                st.markdown('<div class="section-title">📋 التبريرات المسجلة</div>', unsafe_allow_html=True)
                st.dataframe(notes_df[['monitor_name', 'justification', 'details', 'created_at']].rename(
                    columns={'monitor_name': 'المراقب', 'justification': 'السبب',
                             'details': 'التفاصيل', 'created_at': 'التاريخ'}
                ), use_container_width=True)
    
    # ═══════════════════════════════════════════════
    elif "تصدير التقارير" in page:
        st.markdown('<div class="section-title">📄 تصدير التقارير وحفظها</div>', unsafe_allow_html=True)

        current_user = st.session_state.get('username', 'admin')

        # ── Helper: save report to DB ──
        def db_save_report(name, rtype, ext, mime, data_bytes):
            try:
                conn2 = sqlite3.connect(DB_PATH)
                c2 = conn2.cursor()
                c2.execute("""INSERT INTO saved_reports
                    (report_name, report_type, report_ext, report_mime, report_data, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (name, rtype, ext, mime,
                     sqlite3.Binary(data_bytes),
                     current_user,
                     datetime.now().strftime('%Y-%m-%d %H:%M')))
                conn2.commit()
                conn2.close()
                return True
            except Exception as e:
                st.error(f"خطأ في الحفظ: {e}")
                return False

        if not analytics or 'unified' not in analytics:
            st.warning("⚠️ الرجاء رفع البيانات أولاً")
        else:
            df = analytics['unified']

            # ── Config ──
            col_cfg1, col_cfg2 = st.columns(2)
            with col_cfg1:
                report_month = st.text_input("📅 فترة التقرير", value="يناير 2026", key="report_month")
            with col_cfg2:
                report_name = st.text_input(
                    "📝 اسم التقرير",
                    value=f"تقرير_الأداء_{datetime.now().strftime('%Y%m%d')}",
                    key="report_name"
                )

            st.markdown("---")

            # ── Export cards ──
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#0a1e3a,#122040);border:1px solid #2d4a6e;
                            border-radius:12px;padding:20px;text-align:center;min-height:130px;">
                    <div style="font-size:40px;">📄</div>
                    <h4 style="color:#4db8ff;direction:rtl;margin:8px 0 4px;">تقرير PDF</h4>
                    <p style="color:#5a7a9a;direction:rtl;font-size:11px;">يُحفظ تلقائياً في قاعدة البيانات</p>
                </div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📥 توليد وحفظ PDF", use_container_width=True, key='pdf_btn'):
                    with st.spinner("⏳ جاري إنشاء التقرير..."):
                        result = generate_pdf_report(analytics, report_month)
                        buf, fmt = result if isinstance(result, tuple) else (result, 'pdf')
                        data_bytes = buf.getvalue()
                        if fmt == 'pdf':
                            saved_ok = db_save_report(report_name, 'PDF', 'pdf',
                                                       'application/pdf', data_bytes)
                            st.download_button("⬇️ تحميل PDF الآن", data=data_bytes,
                                file_name=f"{report_name}.pdf", mime="application/pdf",
                                use_container_width=True, key='pdf_dl')
                            if saved_ok:
                                st.success("✅ تم الحفظ في قاعدة البيانات — سيبقى بعد تسجيل الخروج!")
                        else:
                            st.warning("⚠️ wkhtmltopdf غير متوفر — تم الحفظ كـ HTML")
                            saved_ok = db_save_report(report_name, 'HTML', 'html', 'text/html', data_bytes)
                            st.download_button("⬇️ تحميل HTML", data=data_bytes,
                                file_name=f"{report_name}.html", mime="text/html",
                                use_container_width=True)

            with c2:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#0a2010,#122a18);border:1px solid #1e6040;
                            border-radius:12px;padding:20px;text-align:center;min-height:130px;">
                    <div style="font-size:40px;">📊</div>
                    <h4 style="color:#3da66e;direction:rtl;margin:8px 0 4px;">تصدير Excel</h4>
                    <p style="color:#3a7050;direction:rtl;font-size:11px;">يُحفظ تلقائياً في قاعدة البيانات</p>
                </div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📥 توليد وحفظ Excel", use_container_width=True, key='excel_btn'):
                    with st.spinner("⏳ جاري إنشاء الملف..."):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='الأداء الكلي', index=False)
                            for sh, key in [('الزيارات','visits'),('البلاغات','reports'),
                                            ('المخالفات','violations'),('البلديات','municipality'),
                                            ('بنود اللائحة','top_articles')]:
                                if key in analytics:
                                    analytics[key].to_excel(writer, sheet_name=sh, index=False)
                        xl_bytes = output.getvalue()
                        saved_ok = db_save_report(report_name, 'Excel', 'xlsx',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', xl_bytes)
                        st.download_button("⬇️ تحميل Excel الآن", data=xl_bytes,
                            file_name=f"{report_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, key='xl_dl')
                        if saved_ok:
                            st.success("✅ تم الحفظ في قاعدة البيانات!")

            with c3:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#20100a,#2a1812);border:1px solid #6a3020;
                            border-radius:12px;padding:20px;text-align:center;min-height:130px;">
                    <div style="font-size:40px;">🌐</div>
                    <h4 style="color:#ff8c42;direction:rtl;margin:8px 0 4px;">تقرير HTML</h4>
                    <p style="color:#8a5040;direction:rtl;font-size:11px;">يُحفظ تلقائياً في قاعدة البيانات</p>
                </div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🌐 توليد وحفظ HTML", use_container_width=True, key='html_btn'):
                    with st.spinner("⏳ جاري إنشاء التقرير..."):
                        html_bytes = get_report_html(analytics, report_month).encode('utf-8')
                        saved_ok = db_save_report(report_name, 'HTML', 'html', 'text/html', html_bytes)
                        st.download_button("⬇️ تحميل HTML", data=html_bytes,
                            file_name=f"{report_name}.html", mime="text/html",
                            use_container_width=True, key='html_dl')
                        if saved_ok:
                            st.success("✅ تم الحفظ في قاعدة البيانات!")

        # ══════════════════════════════════════════════
        # ── Saved Reports Archive (from SQLite) ──
        # ══════════════════════════════════════════════
        st.markdown("---")
        st.markdown('<div class="section-title">📂 أرشيف التقارير المحفوظة</div>', unsafe_allow_html=True)

        conn_r = sqlite3.connect(DB_PATH)
        all_reps = pd.read_sql(
            "SELECT id, report_name, report_type, report_ext, report_mime, created_by, created_at "
            "FROM saved_reports ORDER BY created_at DESC",
            conn_r
        )
        conn_r.close()

        if all_reps.empty:
            st.info("📭 لا توجد تقارير محفوظة بعد. قم بتوليد تقرير أعلاه وسيُحفظ هنا تلقائياً.")
        else:
            type_icons  = {'PDF':'📄', 'Excel':'📊', 'HTML':'🌐'}
            type_colors = {'PDF':'#4db8ff', 'Excel':'#3da66e', 'HTML':'#ff8c42'}

            # Stats row
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
              <div style="background:#1a2035;border:1px solid #2d4a6e;border-radius:8px;
                          padding:10px 18px;text-align:center;min-width:100px;">
                <div style="color:#4db8ff;font-size:20px;font-weight:900;">{len(all_reps)}</div>
                <div style="color:#5a7a9a;font-size:11px;">إجمالي التقارير</div>
              </div>
              <div style="background:#1a2035;border:1px solid #2d4a6e;border-radius:8px;
                          padding:10px 18px;text-align:center;min-width:100px;">
                <div style="color:#3da66e;font-size:20px;font-weight:900;">
                  {len(all_reps[all_reps['report_type']=='PDF'])}
                </div>
                <div style="color:#5a7a9a;font-size:11px;">📄 PDF</div>
              </div>
              <div style="background:#1a2035;border:1px solid #2d4a6e;border-radius:8px;
                          padding:10px 18px;text-align:center;min-width:100px;">
                <div style="color:#3da66e;font-size:20px;font-weight:900;">
                  {len(all_reps[all_reps['report_type']=='Excel'])}
                </div>
                <div style="color:#5a7a9a;font-size:11px;">📊 Excel</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # List each report
            for _, rep in all_reps.iterrows():
                icon  = type_icons.get(rep['report_type'], '📄')
                color = type_colors.get(rep['report_type'], '#4db8ff')
                col_info, col_dl, col_del = st.columns([6, 2, 1])

                with col_info:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#141c2e,#1a2540);
                         border:1px solid #253660;border-radius:10px;
                         padding:12px 16px;direction:rtl;">
                      <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:26px;">{icon}</span>
                        <div>
                          <div style="color:{color};font-weight:700;font-size:14px;">
                            {rep['report_name']}.{rep['report_ext']}
                          </div>
                          <div style="color:#4a6a8a;font-size:11px;margin-top:2px;">
                            📅 {rep['created_at']}  •  👤 {rep['created_by']}  •  نوع: {rep['report_type']}
                          </div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_dl:
                    # Load binary data from DB on demand
                    if st.button(f"⬇️ تحميل", key=f"dl_{rep['id']}",
                                 use_container_width=True):
                        conn_dl = sqlite3.connect(DB_PATH)
                        row_data = conn_dl.execute(
                            "SELECT report_data FROM saved_reports WHERE id=?", (rep['id'],)
                        ).fetchone()
                        conn_dl.close()
                        if row_data:
                            st.download_button(
                                label="⬇️ اضغط للتحميل",
                                data=bytes(row_data[0]),
                                file_name=f"{rep['report_name']}.{rep['report_ext']}",
                                mime=rep['report_mime'],
                                use_container_width=True,
                                key=f"dl2_{rep['id']}"
                            )

                with col_del:
                    if st.button("🗑️", key=f"del_{rep['id']}", help="حذف نهائي"):
                        conn_del = sqlite3.connect(DB_PATH)
                        conn_del.execute("DELETE FROM saved_reports WHERE id=?", (rep['id'],))
                        conn_del.commit()
                        conn_del.close()
                        st.success("تم الحذف")
                        st.rerun()

            if st.button("🗑️ حذف جميع التقارير", key='clear_all_reports',
                         type="secondary"):
                conn_ca = sqlite3.connect(DB_PATH)
                conn_ca.execute("DELETE FROM saved_reports")
                conn_ca.commit()
                conn_ca.close()
                st.warning("تم حذف جميع التقارير")
                st.rerun()

        # ── Full table preview ──
        if analytics and 'unified' in analytics:
            df = analytics['unified']
            st.markdown("---")
            st.markdown('<div class="section-title">📋 جدول النسب التفصيلي لكل مراقب</div>', unsafe_allow_html=True)

            st.markdown("""
            <div style="background:#1a2035;border:1px solid #2d4a6e;border-radius:8px;
                        padding:10px 16px;direction:rtl;margin-bottom:12px;font-size:12px;color:#7a9ab5;">
                ℹ️ <b style="color:#4db8ff;">طريقة حساب النسب:</b>
                نسبة الزيارات والبلاغات = أداء المراقب ÷ أعلى أداء في الفريق × 100
                (المراقب الأعلى = 100% والبقية بالنسبة له)  |
                نسبة قبول المخالفات = مقبولة ÷ إجمالي مخالفاته × 100
            </div>
            """, unsafe_allow_html=True)

            display_cols = [c for c in [
                'الترتيب', 'اسم المراقب',
                'عدد الزيارات',       'نسبة الزيارات %',
                'عدد البلاغات',       'نسبة البلاغات %',
                'إجمالي المخالفات',   'مخالفات مقبولة',  'مخالفات مرفوضة',
                'نسبة قبول المخالفات %', 'نسبة رفض المخالفات %',
                'نسبة الأداء الكلية %',
                'مهام خارجية', 'درجة الأداء', 'تبرير الأداء'
            ] if c in df.columns]

            st.dataframe(df[display_cols], use_container_width=True, height=500)
    
    # ═══════════════════════════════════════════════
    elif "إدارة الحسابات" in page:
        st.markdown('<div class="section-title">👤 إدارة الحسابات والصلاحيات</div>', unsafe_allow_html=True)
        
        current_role = st.session_state.get('role', 'viewer')
        current_user = st.session_state.get('username', '')
        
        tab_pw, tab_users = st.tabs(["🔑 تغيير كلمة المرور", "👥 إدارة المستخدمين"])
        
        # ── Tab 1: Change Password ──
        with tab_pw:
            st.markdown("#### 🔑 تغيير كلمة المرور الخاصة بك")
            st.info(f"أنت مسجّل الدخول بالحساب: **{current_user}**")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                old_pw  = st.text_input("كلمة المرور الحالية", type="password", key="old_pw", placeholder="أدخل كلمة المرور الحالية")
                new_pw  = st.text_input("كلمة المرور الجديدة", type="password", key="new_pw", placeholder="أدخل كلمة المرور الجديدة")
                new_pw2 = st.text_input("تأكيد كلمة المرور الجديدة", type="password", key="new_pw2", placeholder="أعد إدخال كلمة المرور الجديدة")
                
                if st.button("💾 تحديث كلمة المرور", use_container_width=True, key="btn_chgpw"):
                    if not old_pw or not new_pw or not new_pw2:
                        st.error("❌ يرجى ملء جميع الحقول")
                    elif new_pw != new_pw2:
                        st.error("❌ كلمة المرور الجديدة وتأكيدها غير متطابقتين")
                    elif len(new_pw) < 6:
                        st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    else:
                        # Verify old password
                        role_check = verify_login(current_user, old_pw)
                        if role_check is None:
                            st.error("❌ كلمة المرور الحالية غير صحيحة")
                        else:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute("UPDATE users SET password_hash=? WHERE username=?",
                                     (hash_password(new_pw), current_user))
                            conn.commit()
                            conn.close()
                            st.success("✅ تم تحديث كلمة المرور بنجاح!")
            
            with col2:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#1a2035,#1f2b45);border:1px solid #2d4a6e;
                     border-radius:12px;padding:20px 24px;direction:rtl;margin-top:4px;">
                    <p style="color:#4db8ff;font-weight:700;font-size:14px;margin-bottom:12px;">💡 نصائح لكلمة مرور قوية</p>
                    <ul style="color:#8a9bb5;font-size:13px;line-height:2;">
                        <li>استخدم 8 أحرف أو أكثر</li>
                        <li>امزج بين الأحرف والأرقام</li>
                        <li>أضف رموزاً خاصة مثل @، #، !</li>
                        <li>لا تستخدم معلومات شخصية</li>
                        <li>لا تشارك كلمة المرور مع أحد</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # ── Tab 2: Manage Users (admin only) ──
        with tab_users:
            if current_role != 'admin':
                st.warning("⚠️ هذه الميزة متاحة للمسؤول (admin) فقط.")
            else:
                st.markdown("#### 👥 إنشاء وإدارة الحسابات")
                
                # Show existing users
                conn = sqlite3.connect(DB_PATH)
                users_df = pd.read_sql("SELECT username, role FROM users", conn)
                conn.close()
                
                st.markdown("**المستخدمون الحاليون:**")
                
                # Display users as styled cards via components
                
                role_labels = {'admin': ('🔴 مسؤول كامل', '#c84040', '#2e0a0a'),
                               'supervisor': ('🟡 مشرف', '#d4a017', '#2e1f00'),
                               'manager': ('🔵 مدير', '#4db8ff', '#0a1e2e'),
                               'viewer': ('⚪ مشاهد', '#8a9bb5', '#1a2035')}
                
                user_cards = """<style>
                @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
                .u-card { font-family:'Cairo',sans-serif; display:flex; justify-content:space-between; align-items:center;
                    border-radius:10px; padding:12px 16px; margin:6px 0; direction:rtl; border:1px solid; }
                .u-name { font-weight:700; color:#fff; font-size:14px; }
                .u-role { font-size:12px; margin-top:3px; font-weight:600; }
                </style>"""
                
                for _, row in users_df.iterrows():
                    uname = row['username']
                    urole = row['role']
                    label, color, bg = role_labels.get(urole, ('⚪ مشاهد', '#8a9bb5', '#1a2035'))
                    user_cards += f"""
                    <div class="u-card" style="background:linear-gradient(135deg,{bg},{bg}dd);border-color:{color}40;">
                        <div>
                            <div class="u-name">👤 {uname}</div>
                            <div class="u-role" style="color:{color};">{label}</div>
                        </div>
                        <div style="font-size:20px;">{'🔒' if uname == 'admin' else '✏️'}</div>
                    </div>"""
                
                components.html(user_cards, height=len(users_df)*80 + 40, scrolling=False)
                
                st.markdown("---")
                st.markdown("#### ➕ إنشاء حساب جديد")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    new_username = st.text_input("اسم المستخدم الجديد", key="new_uname", placeholder="مثال: supervisor1")
                    new_user_pw  = st.text_input("كلمة المرور", type="password", key="new_upw", placeholder="كلمة مرور قوية")
                    new_user_pw2 = st.text_input("تأكيد كلمة المرور", type="password", key="new_upw2", placeholder="أعد إدخال كلمة المرور")
                
                with col_b:
                    new_role = st.selectbox("الدور والصلاحية", 
                                           options=['viewer', 'supervisor', 'manager'],
                                           format_func=lambda x: {
                                               'viewer': '⚪ مشاهد — عرض البيانات فقط',
                                               'supervisor': '🟡 مشرف — عرض + إدارة المراقبين',
                                               'manager': '🔵 مدير — عرض + تصدير التقارير'
                                           }[x],
                                           key="new_urole")
                    
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#1a2035,#1f2b45);border:1px solid #2d4a6e;
                         border-radius:10px;padding:14px 18px;direction:rtl;margin-top:8px;">
                        <p style="color:#4db8ff;font-weight:700;font-size:13px;margin-bottom:8px;">📋 الصلاحيات</p>
                        <p style="color:#8a9bb5;font-size:12px;line-height:1.8;margin:0;">
                        ⚪ <b style="color:#c8ddf5;">مشاهد:</b> عرض لوحة الأداء والتقارير<br>
                        🟡 <b style="color:#c8ddf5;">مشرف:</b> + إضافة مهام وتبريرات<br>
                        🔵 <b style="color:#c8ddf5;">مدير:</b> + تصدير PDF وExcel<br>
                        🔴 <b style="color:#c8ddf5;">مسؤول:</b> صلاحيات كاملة
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("✅ إنشاء الحساب", use_container_width=True, key="btn_create"):
                    if not new_username.strip():
                        st.error("❌ يرجى إدخال اسم المستخدم")
                    elif len(new_username.strip()) < 3:
                        st.error("❌ اسم المستخدم يجب أن يكون 3 أحرف على الأقل")
                    elif not new_user_pw:
                        st.error("❌ يرجى إدخال كلمة المرور")
                    elif new_user_pw != new_user_pw2:
                        st.error("❌ كلمة المرور وتأكيدها غير متطابقتين")
                    elif len(new_user_pw) < 6:
                        st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    else:
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute("INSERT INTO users VALUES (?,?,?)",
                                     (new_username.strip(), hash_password(new_user_pw), new_role))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ تم إنشاء حساب **{new_username}** بنجاح بدور: {new_role}")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"❌ اسم المستخدم '{new_username}' مستخدم مسبقاً")
                
                st.markdown("---")
                st.markdown("#### 🗑️ حذف حساب")
                
                deletable = [u for u in users_df['username'].tolist() if u != 'admin']
                if deletable:
                    del_user = st.selectbox("اختر الحساب للحذف", deletable, key="del_user")
                    if st.button(f"🗑️ حذف حساب {del_user}", key="btn_del", type="secondary"):
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (del_user,))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ تم حذف حساب {del_user}")
                        st.rerun()
                else:
                    st.info("لا توجد حسابات أخرى قابلة للحذف.")

# ─── Entry Point ─────────────────────────────────────────────────────────────────
def main():
    init_db()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
