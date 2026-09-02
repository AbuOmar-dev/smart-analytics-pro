import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import io
from datetime import datetime
from supabase import create_client, Client

import config

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="Smart Analytics Pro",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS Styling ====================
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
    h1, h2, h3 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; }
    .stButton>button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; padding: 12px 28px; font-weight: 600; border: none; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); transition: all 0.3s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }
    .login-container { max-width: 500px; margin: 60px auto; padding: 50px 40px; background: white; border-radius: 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.15); }
    .login-header { text-align: center; margin-bottom: 40px; }
    .login-header h1 { font-size: 36px; margin-bottom: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-section { text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 24px; margin-bottom: 40px; box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4); }
    .hero-section h1 { font-size: 48px; margin-bottom: 20px; color: white !important; -webkit-text-fill-color: white !important; }
    .feature-card { background: white; padding: 30px; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: all 0.3s ease; margin: 10px; }
    .feature-card:hover { transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.15); }
    .readiness-box { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 15px 0; }
    .score-good { color: #48bb78; font-weight: bold; font-size: 24px; }
    .score-warning { color: #ed8936; font-weight: bold; font-size: 24px; }
    .score-bad { color: #f56565; font-weight: bold; font-size: 24px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== Supabase ====================
SUPABASE_URL = "https://llsoulwgpptlpatgivqk.supabase.co"
SUPABASE_KEY = "sb_publishable_OpzDbBV2XqSJchMJ6DqmLQ_DYyB9GVH"
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    supabase = None

# ==================== تهيئة الحالة ====================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = None
if "show_register" not in st.session_state: st.session_state.show_register = False
if "page" not in st.session_state: st.session_state.page = "home"
if "df" not in st.session_state: st.session_state.df = None
if "df_clean" not in st.session_state: st.session_state.df_clean = None

# ==================== دوال المستخدمين ====================
def load_users():
    if supabase is None: return {}
    try:
        response = supabase.table("users").select("*").execute()
        return {user['username']: {'password': user['password'], 'name': user['name'], 'email': user['email'], 'plan': user.get('plan', 'Free'), 'role': user.get('role', 'user')} for user in response.data}
    except Exception as e:
        st.error(f"خطأ: {e}"); return {}

def register_user(username, password, name, email, plan='Free'):
    if supabase is None: return False, "خطأ في الاتصال"
    try:
        if len(supabase.table("users").select("username").eq("username", username).execute().data) > 0:
            return False, "اسم المستخدم موجود بالفعل"
        supabase.table("users").insert({'username': username, 'password': password, 'name': name, 'email': email, 'plan': plan, 'role': 'user'}).execute()
        return True, "تم التسجيل بنجاح!"
    except Exception as e:
        return False, f"خطأ: {e}"

# ==================== صفحة تسجيل الدخول ====================
if not st.session_state.logged_in:
    st.markdown("""<div class="login-container"><div class="login-header"><div style="font-size: 80px; margin-bottom: 20px;">📊</div><h1>Smart Analytics Pro</h1><p style="color: #718096; font-size: 18px;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div></div>""", unsafe_allow_html=True)
    
    if st.session_state.show_register:
        st.markdown("### 📝 إنشاء حساب جديد")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_username = st.text_input("اسم المستخدم", key="reg_username")
            new_name = st.text_input("الاسم الكامل", key="reg_name")
            new_email = st.text_input("البريد الإلكتروني", key="reg_email")
            new_password = st.text_input("كلمة المرور", type="password", key="reg_password")
            confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
            if st.button("✅ تسجيل الحساب", use_container_width=True, type="primary", key="btn_register"):
                if not all([new_username, new_password, new_name, new_email]): st.error("❌ يرجى ملء جميع الحقول")
                elif new_password != confirm_password: st.error("❌ كلمات المرور غير متطابقة")
                elif len(new_password) < 6: st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    success, message = register_user(new_username, new_password, new_name, new_email)
                    if success: st.success(f"✅ {message}"); st.balloons(); st.session_state.show_register = False; st.rerun()
                    else: st.error(f"❌ {message}")
            if st.button("🔐 لديك حساب؟ دخول", use_container_width=True, type="secondary", key="btn_go_login"): st.session_state.show_register = False; st.rerun()
    else:
        st.markdown("### 🔐 تسجيل الدخول")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("اسم المستخدم", key="login_user")
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            if st.button("🚪 دخول", use_container_width=True, type="primary", key="btn_login"):
                users = load_users()
                if username in users and users[username]['password'] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {'username': username, 'name': users[username]['name'], 'email': users[username]['email'], 'plan': users[username]['plan'], 'role': users[username]['role']}
                    st.success(f"✅ مرحباً {users[username]['name']}!"); st.rerun()
                else: st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        st.markdown("---")
        if st.button("📝 ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"): st.session_state.show_register = True; st.rerun()
        st.info("💡 **بيانات تجريبية:**\n- المستخدم: `admin`\n- كلمة المرور: `Smart@2026`")
        st.stop()

# ==================== المنصة الرئيسية ====================
current_user = st.session_state.current_user
def load_data(file):
    try:
        if file.name.endswith('.csv'): return pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')): return pd.read_excel(file)
        return None
    except: return None

with st.sidebar:
    if current_user:
        st.markdown(f"""<div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 16px; text-align: center; margin: 10px 0;">
            <div style="font-size: 50px; margin-bottom: 10px;">👤</div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📍 التنقل السريع")
    menu = {"home": "🏠 الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "readiness": "✅ جاهزية البيانات", "cleaning": "🧹 تنظيف البيانات", "summary": "📋 ملخص البيانات", "eda": "📊 التحليل الاستكشافي", "diagnostic": "🔍 التحليل التشخيصي", "predictive": "🔮 التحليل التنبؤي", "prescriptive": "💡 التحليل الإرشادي", "ai_chat": " المساعد الذكي", "export": "💾 التصدير"}
    for key, label in menu.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"): st.session_state.page = key; st.rerun()
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True, key="btn_logout"): st.session_state.logged_in = False; st.session_state.current_user = None; st.session_state.page = "home"; st.session_state.show_register = False; st.rerun()
    if st.session_state.df is not None:
        st.markdown(f"""<div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 12px; margin-top: 20px;"><div style="color: white; font-size: 14px;">✅ البيانات محملة: {len(st.session_state.df)} صف</div></div>""", unsafe_allow_html=True)

# ==================== الصفحات الأساسية ====================
if st.session_state.page == "home":
    st.markdown("""<div class="hero-section"><h1>Smart Analytics Pro</h1><p>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">📊</div><h3>التحليل الاستكشافي</h3><p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;"></div><h3>التحليل التشخيصي</h3><p>اكتشف الأنماط والشذوذ في بياناتك</p></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">🔮</div><h3>التحليل التنبؤي</h3><p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    with col4: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">💡</div><h3>التحليل الإرشادي</h3><p>توصيات عملية لزيادة العائد على الاستثمار</p></div>""", unsafe_allow_html=True)
    if current_user:
        st.markdown(f"""<div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; margin-top: 40px; border-left: 5px solid #48bb78;"><h3>👋 مرحباً {current_user['name']}!</h3><p><strong>ابدأ الآن في 4 خطوات:</strong></p><ol><li>📥 استيراد البيانات</li><li>✅ فحص جاهزية البيانات</li><li>🧹 تنظيف البيانات (إذا لزم الأمر)</li><li> التحليل الاستكشافي</li></ol></div>""", unsafe_allow_html=True)

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    col1, col2, col3 = st.columns(3)
    plans = [{"name": "🆓 Free", "price": "$0", "period": "/شهر", "features": ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط"], "button_type": "secondary"},
             {"name": "⭐ Pro", "price": "$19", "period": "/شهر", "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل التحليلات"], "button_type": "primary", "popular": True},
             {"name": " Enterprise", "price": "$99", "period": "/شهر", "features": ["كل المميزات", "تخزين غير محدود", "API Access"], "button_type": "secondary"}]
    for i, plan in enumerate(plans):
        with [col1, col2, col3][i]:
            if plan.get("popular"):
                st.markdown(f"""<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);"><div style="text-align: center; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 8px; margin-bottom: 15px;">🌟 الأكثر شعبية</div><h2 style="color: white; text-align: center;">{plan['name']}</h2><h1 style="color: white; text-align: center;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);"><h2 style="text-align: center;">{plan['name']}</h2><h1 style="text-align: center;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1></div>""", unsafe_allow_html=True)
            st.markdown("### المميزات:"); 
            for feature in plan["features"]: st.markdown(f"✅ {feature}")
            st.button("اشترك الآن", use_container_width=True, type=plan["button_type"], key=f"sub_{i}")

elif st.session_state.page == "data_import":
    st.markdown("##  استيراد البيانات")
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
            else: df = pd.read_excel(uploaded_file)
            st.session_state.df = df; st.session_state.df_clean = None
            st.success(f"✅ تم الرفع! {len(df)} صف، {len(df.columns)} عمود")
            st.dataframe(df.head())
        except Exception as e: st.error(f"خطأ: {e}")

elif st.session_state.page == "readiness":
    st.markdown("## ✅ جاهزية البيانات")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    df = st.session_state.df
    st.metric("الصفوف", len(df)); st.metric("الأعمدة", len(df.columns))
    st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    st.dataframe(pd.DataFrame({'العمود': df.columns, 'النوع': df.dtypes.astype(str), 'المفقودة': df.isnull().sum().values}))

elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف البيانات")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    if st.button("تنظيف تلقائي"):
        df = st.session_state.df.copy()
        df = df.dropna()
        df = df.drop_duplicates()
        st.session_state.df_clean = df
        st.success(f"✅ تم التنظيف! {len(df)} صف متبقي")

elif st.session_state.page == "summary":
    st.markdown("## 📋 ملخص البيانات")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    st.metric("الصفوف", len(df)); st.metric("الأعمدة", len(df.columns))
    st.dataframe(df.head(10))

# ==============================================================================
# ==================== صفحة EDA الاحترافية الكاملة =============================
# ==============================================================================
elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA) - المحرك الديناميكي")
    st.markdown("---")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        # 1. المحرك الديناميكي لتصنيف الأعمدة
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        bad_keywords = ['id', 'date', 'time', 'url', 'link', 'desc', 'notes', 'رقم', 'تاريخ', 'رابط']
        valid_categorical = []
        for col in df.select_dtypes(include=['object', 'category', 'bool']).columns:
            n_unique = df[col].nunique()
            # شرط ذكي: استبعاد إذا كان الاسم يحتوي على كلمات سيئة، أو إذا كانت القيم الفريدة كثيرة جداً (>30) أو تساوي حجم البيانات
            if not any(kw in col.lower() for kw in bad_keywords) and n_unique < 30 and n_unique < len(df) * 0.5:
                valid_categorical.append(col)
        
        # دالة مساعدة لتوليد جداول HTML نقية 100%
        def generate_pure_html_table(dataframe, title=""):
            html = f"<h3 style='color:#667eea; margin-top:25px; margin-bottom:15px; border-right: 4px solid #764ba2; padding-right: 12px;'>{title}</h3>"
            html += "<table class='data-table'><thead><tr>"
            for c in dataframe.columns:
                html += f"<th>{str(c)}</th>"
            html += "</tr></thead><tbody>"
            for _, row in dataframe.iterrows():
                html += "<tr>"
                for val in row:
                    val_str = str(val) if pd.notna(val) else "-"
                    html += f"<td>{val_str}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            return html

        st.markdown("### 📥 تصدير التقرير الديناميكي الشامل")
        if st.button("📥 إنشاء وتحميل تقرير HTML احترافي", type="primary", key="btn_export_dynamic_eda"):
            with st.spinner("جاري المعالجة الديناميكية للبيانات وإنشاء التقرير..."):
                try:
                    html_parts = []
                    html_parts.append(f"""<!DOCTYPE html>
                    <html dir="rtl" lang="ar">
                    <head>
                        <meta charset="UTF-8">
                        <title>تقرير التحليل الاستكشافي الديناميكي</title>
                        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                        <style>
                            body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #f8f9fa; color: #2d3748; line-height: 1.6; direction: rtl; text-align: right; }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; border-radius: 0 0 16px 16px; margin-bottom: 30px; }}
                            .container {{ max-width: 1100px; margin: 0 auto; padding: 0 20px 40px 20px; }}
                            .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
                            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #667eea; }}
                            .card .label {{ color: #718096; font-size: 14px; margin-bottom: 8px; }}
                            .card .value {{ color: #2d3748; font-size: 28px; font-weight: bold; }}
                            .section {{ background: white; padding: 35px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; page-break-inside: avoid; }}
                            .section h2 {{ color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 15px; margin-top: 0; }}
                            .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
                            .data-table th {{ background: #667eea; color: white; padding: 14px 12px; text-align: right; font-weight: 600; }}
                            .data-table td {{ padding: 12px; border-bottom: 1px solid #edf2f7; text-align: right; }}
                            .data-table tr:nth-child(even) {{ background: #f7fafc; }}
                            .chart-box {{ margin: 25px 0; background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; page-break-inside: avoid; }}
                            .insight-box {{ background: #fffaf0; border-right: 5px solid #ed8936; padding: 20px; margin: 20px 0; border-radius: 8px; color: #c05621; }}
                            .footer {{ text-align: center; padding: 40px; color: #718096; background: white; margin-top: 40px; border-top: 1px solid #e2e8f0; }}
                            @media print {{ .section, .chart-box {{ break-inside: avoid; }} th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>📊 تقرير التحليل الاستكشافي الديناميكي</h1>
                            <p>Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                        </div>
                        <div class="container">
                            <div class="summary-cards">
                                <div class="card"><div class="label">إجمالي السجلات</div><div class="value">{len(df):,}</div></div>
                                <div class="card"><div class="label">إجمالي الأعمدة</div><div class="value">{len(df.columns)}</div></div>
                                <div class="card"><div class="label">الأعمدة الرقمية</div><div class="value">{len(numeric_cols)}</div></div>
                                <div class="card"><div class="label">الأعمدة الفئوية الصالحة</div><div class="value">{len(valid_categorical)}</div></div>
                            </div>
                    """)
                    
                    # 2. الجداول التكرارية الديناميكية
                    html_parts.append("<div class='section'><h2>📋 1. الجداول التكرارية (أعلى 15 قيمة)</h2>")
                    html_parts.append("<p style='color:#718096; margin-bottom:20px;'>تم استبعاد المعرفات الفريدة وأعمدة التواريخ والنصوص الطويلة تلقائياً لضمان وضوح التقرير.</p>")
                    
                    for col in valid_categorical:
                        freq = df[col].value_counts().head(15).reset_index()
                        freq.columns = ['القيمة', 'التكرار']
                        freq['النسبة المئوية %'] = (freq['التكرار'] / len(df) * 100).round(2)
                        
                        html_parts.append(generate_pure_html_table(freq, f"📊 {col}"))
                        
                        fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}", color='التكرار', color_continuous_scale='Blues')
                        fig.update_layout(height=350, xaxis_tickangle=-45, margin=dict(t=40, b=60, l=40, r=40))
                        html_parts.append('<div class="chart-box">')
                        html_parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html_parts.append('</div>')
                    
                    skipped = [c for c in df.columns if c not in valid_categorical + numeric_cols]
                    if skipped:
                        html_parts.append(f"<div class='insight-box'>ℹ️ <strong>ملاحظة:</strong> تم استبعاد الأعمدة التالية تلقائياً (معرفات، تواريخ، أو نصوص حرة): <strong>{', '.join(skipped)}</strong></div>")
                    
                    html_parts.append("</div>")
                    
                    # 3. المقاييس الإحصائية الديناميكية
                    html_parts.append("<div class='section'><h2>📈 2. المقاييس الإحصائية الشاملة</h2>")
                    
                    for col in numeric_cols:
                        cd = df[col].dropna()
                        if len(cd) == 0: continue
                        
                        skew_val = cd.skew()
                        kurt_val = cd.kurtosis()
                        skew_i = "متماثل تقريباً" if abs(skew_val) < 0.5 else ("منحرف لليمين" if skew_val > 0 else "منحرف لليسار")
                        kurt_i = "متوسط التفلطح" if kurt_val > 0 else "مفلطح (ذيول خفيفة)"
                        
                        stats_df = pd.DataFrame({
                            'المقياس': ['المتوسط', 'الوسيط', 'الانحراف المعياري', 'التباين', 'الحد الأدنى', 'Q1', 'Q2 (الوسيط)', 'Q3', 'الحد الأقصى', 'IQR'],
                            'القيمة': [f"{cd.mean():.2f}", f"{cd.median():.2f}", f"{cd.std():.2f}", f"{cd.var():.2f}", 
                                      f"{cd.min():.2f}", f"{cd.quantile(0.25):.2f}", f"{cd.quantile(0.50):.2f}", 
                                      f"{cd.quantile(0.75):.2f}", f"{cd.max():.2f}", f"{(cd.quantile(0.75)-cd.quantile(0.25)):.2f}"]
                        })
                        
                        html_parts.append(generate_pure_html_table(stats_df, f"📊 {col}"))
                        
                        skew_df = pd.DataFrame({
                            'المقياس': ['الانحناء (Skewness)', 'التفلطح (Kurtosis)'],
                            'القيمة': [f"{skew_val:.2f}", f"{kurt_val:.2f}"],
                            'التفسير': [skew_i, kurt_i]
                        })
                        html_parts.append(generate_pure_html_table(skew_df, ""))
                        
                        fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
                        fig.add_vline(x=cd.mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {cd.mean():.1f}")
                        fig.update_layout(height=350, margin=dict(t=40, b=40, l=40, r=40))
                        html_parts.append('<div class="chart-box">')
                        html_parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html_parts.append('</div>')
                        
                    html_parts.append("</div>")
                    
                    # 4. مخططات الصندوق الديناميكية
                    html_parts.append("<div class='section'><h2>📦 3. مخططات الصندوق (Box Plots)</h2>")
                    for col in numeric_cols:
                        q1, q2, q3 = df[col].quantile(0.25), df[col].quantile(0.50), df[col].quantile(0.75)
                        iqr = q3 - q1
                        outliers = len(df[(df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)])
                        
                        box_df = pd.DataFrame({
                            'المقياس': ['Min', 'Q1', 'Median', 'Q3', 'Max', 'IQR', 'Outliers'],
                            'القيمة': [f"{df[col].min():.2f}", f"{q1:.2f}", f"{q2:.2f}", f"{q3:.2f}", f"{df[col].max():.2f}", f"{iqr:.2f}", str(outliers)]
                        })
                        html_parts.append(generate_pure_html_table(box_df, f"📦 {col}"))
                        
                        fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
                        fig.update_layout(height=350, margin=dict(t=40, b=40, l=40, r=40))
                        html_parts.append('<div class="chart-box">')
                        html_parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html_parts.append('</div>')
                    html_parts.append("</div>")
                    
                    html_parts.append("""
                            <div class="footer">
                                <p>تم إنشاء هذا التقرير ديناميكياً بواسطة <b>Smart Analytics Pro</b></p>
                                <p>© 2026 جميع الحقوق محفوظة</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """)
                    
                    final_html = "".join(html_parts)
                    
                    st.download_button(
                        label="📥 تحميل التقرير الديناميكي (HTML)",
                        data=final_html,
                        file_name=f"Dynamic_EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    st.success("✅ تم إنشاء التقرير بنجاح! افتحه في أي متصفح.")
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء الإنشاء: {str(e)}")
                    st.exception(e)
        
        st.markdown("---")
        
        # عرض تفاعلي سريع داخل التطبيق
        tab1, tab2 = st.tabs(["📋 الجداول التكرارية", "📈 الإحصائيات والرسوم"])
        
        with tab1:
            if valid_categorical:
                sel_cat = st.selectbox("اختر المتغير الفئوي", valid_categorical, key="dyn_tab1_cat")
                freq = df[sel_cat].value_counts().reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                st.dataframe(freq, use_container_width=True)
            else:
                st.info("لا توجد متغيرات فئوية صالحة للعرض (تم استبعادها جميعاً بناءً على معايير الديناميكية).")
                
        with tab2:
            if numeric_cols:
                sel_num = st.selectbox("اختر المتغير الرقمي", numeric_cols, key="dyn_tab2_num")
                cd = df[sel_num].dropna()
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("المتوسط", f"{cd.mean():.2f}")
                with c2: st.metric("الوسيط", f"{cd.median():.2f}")
                with c3: st.metric("الانحراف المعياري", f"{cd.std():.2f}")
                with c4: st.metric("الحد الأقصى", f"{cd.max():.2f}")
                
                fig = px.histogram(df, x=sel_num, nbins=30, title=f"توزيع {sel_num}", color_discrete_sequence=['#667eea'])
                fig.add_vline(x=cd.mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {cd.mean():.1f}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد متغيرات رقمية للعرض.")
