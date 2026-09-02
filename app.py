import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import io
from datetime import datetime
from supabase import create_client, Client

import config

# ==================== إعدادات الصفحة ====================
st.set_page_config(page_title="Smart Analytics Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
pio.templates.default = "plotly_white"

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
    menu = {"home": "🏠 الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "readiness": "✅ جاهزية البيانات", "cleaning": "🧹 تنظيف البيانات", "summary": "📋 ملخص البيانات", "eda": "📊 التحليل الاستكشافي", "diagnostic": "🔍 التحليل التشخيصي", "predictive": "🔮 التحليل التنبؤي", "prescriptive": "💡 التحليل الإرشادي", "ai_chat": "🤖 المساعد الذكي", "export": "💾 التصدير"}
    for key, label in menu.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"): st.session_state.page = key; st.rerun()
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True, key="btn_logout"): st.session_state.logged_in = False; st.session_state.current_user = None; st.session_state.page = "home"; st.session_state.show_register = False; st.rerun()
    if st.session_state.df is not None:
        st.markdown(f"""<div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 12px; margin-top: 20px;"><div style="color: white; font-size: 14px;">✅ البيانات محملة: {len(st.session_state.df)} صف</div></div>""", unsafe_allow_html=True)

# ==================== الصفحات ====================
if st.session_state.page == "home":
    st.markdown("""<div class="hero-section"><h1>Smart Analytics Pro</h1><p>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">📊</div><h3>التحليل الاستكشافي</h3><p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">🔍</div><h3>التحليل التشخيصي</h3><p>اكتشف الأنماط والشذوذ في بياناتك</p></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">🔮</div><h3>التحليل التنبؤي</h3><p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    with col4: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">💡</div><h3>التحليل الإرشادي</h3><p>توصيات عملية لزيادة العائد على الاستثمار</p></div>""", unsafe_allow_html=True)
    if current_user:
        st.markdown(f"""<div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; margin-top: 40px; border-left: 5px solid #48bb78;"><h3>👋 مرحباً {current_user['name']}!</h3><p><strong>ابدأ الآن في 4 خطوات:</strong></p><ol><li>📥 استيراد البيانات</li><li>✅ فحص جاهزية البيانات</li><li>🧹 تنظيف البيانات (إذا لزم الأمر)</li><li>📊 التحليل الاستكشافي</li></ol></div>""", unsafe_allow_html=True)

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    col1, col2, col3 = st.columns(3)
    plans = [{"name": "🆓 Free", "price": "$0", "period": "/شهر", "features": ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط"], "button_type": "secondary"},
             {"name": "⭐ Pro", "price": "$19", "period": "/شهر", "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل التحليلات"], "button_type": "primary", "popular": True},
             {"name": "🏢 Enterprise", "price": "$99", "period": "/شهر", "features": ["كل المميزات", "تخزين غير محدود", "API Access"], "button_type": "secondary"}]
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
    st.markdown("## 📥 استيراد البيانات")
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df; st.session_state.df_clean = None
            st.success(f"✅ تم الرفع بنجاح! {len(df)} صف")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("عدد الصفوف", f"{len(df):,}")
            with col2: st.metric("عدد الأعمدة", len(df.columns))
            with col3: st.metric("حجم الملف", f"{uploaded_file.size / 1024:.2f} KB")
            with col4: st.metric("الأعمدة الرقمية", df.select_dtypes(include=[np.number]).shape[1])
            st.markdown("### معاينة البيانات"); st.dataframe(df.head(10), use_container_width=True)

elif st.session_state.page == "readiness":
    st.markdown("## ✅ فحص جاهزية البيانات للتحليل"); st.markdown("---")
    if st.session_state.df is None: st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        df = st.session_state.df
        total_rows, total_cols = len(df), len(df.columns)
        missing_values = int(df.isnull().sum().sum())
        missing_pct = (missing_values / (total_rows * total_cols)) * 100 if (total_rows * total_cols) > 0 else 0
        duplicates = int(df.duplicated().sum())
        dup_pct = (duplicates / total_rows) * 100 if total_rows > 0 else 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        outlier_count = 0
        for col in numeric_cols:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count += int(((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum())
        
        score = max(0, min(100, 100 - (missing_pct * 2) - (dup_pct * 3) - min((outlier_count / total_rows * 100) if total_rows>0 else 0, 20)))
        issues = []
        if missing_pct > 0: issues.append(f"⚠️ قيم مفقودة: {missing_values} ({missing_pct:.1f}%)")
        if dup_pct > 0: issues.append(f"⚠️ تكرارات: {duplicates} ({dup_pct:.1f}%)")
        if outlier_count > 0: issues.append(f"⚠️ قيم متطرفة: {outlier_count}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            score_class = "score-good" if score >= 80 else ("score-warning" if score >= 50 else "score-bad")
            status = "✅ جاهزة للتحليل" if score >= 80 else ("⚠️ تحتاج تنظيف بسيط" if score >= 50 else "❌ تحتاج تنظيف شامل")
            st.markdown(f"""<div class="readiness-box" style="text-align: center;"><div style="font-size: 18px; color: #718096; margin-bottom: 10px;">جاهزية البيانات</div><div class="{score_class}">{score:.0f}%</div><div style="margin-top: 10px; font-size: 16px;">{status}</div></div>""", unsafe_allow_html=True)
        with col2: st.markdown(f"""<div class="readiness-box"><div style="font-size: 14px; color: #718096;">حجم البيانات</div><div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{total_rows:,} صف × {total_cols} عمود</div></div>""", unsafe_allow_html=True)
        with col3: st.markdown(f"""<div class="readiness-box"><div style="font-size: 14px; color: #718096;">أنواع الأعمدة</div><div style="font-size: 16px; margin-top: 5px;">📊 رقمية: {len(numeric_cols)}</div><div style="font-size: 16px;">📝 نصية: {len(categorical_cols)}</div></div>""", unsafe_allow_html=True)
        
        st.markdown("---"); st.markdown("### 🔍 التشخيص التفصيلي لكل عمود")
        readiness_data = [{'العمود': col, 'النوع': str(df[col].dtype), 'القيم المفقودة': int(df[col].isnull().sum()), 'نسبة المفقود': f"{(df[col].isnull().sum()/total_rows)*100:.1f}%" if total_rows>0 else "0%", 'القيم الفريدة': int(df[col].nunique()), 'الحالة': "✅" if df[col].isnull().sum()==0 else ("⚠️" if (df[col].isnull().sum()/total_rows)*100 < 5 else "❌")} for col in df.columns]
        st.dataframe(pd.DataFrame(readiness_data), use_container_width=True)
        
        if issues:
            st.markdown("---"); st.markdown("### ⚠️ المشاكل المكتشفة")
            for issue in issues: st.warning(issue)
            if st.button("🧹 انتقل إلى تنظيف البيانات", type="primary", key="btn_go_clean"): st.session_state.page = "cleaning"; st.rerun()
        else:
            st.success("🎉 البيانات جاهزة تماماً للتحليل!")
            if st.button("📊 انتقل إلى التحليل الاستكشافي", type="primary", key="btn_go_eda"): st.session_state.page = "eda"; st.rerun()

elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف وإعداد البيانات"); st.markdown("---")
    if st.session_state.df is None: st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        df = st.session_state.df.copy()
        st.markdown("### 📊 حالة البيانات قبل التنظيف")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("الصفوف", len(df))
        with col2: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
        with col3: st.metric("التكرارات", int(df.duplicated().sum()))
        
        st.markdown("---"); st.markdown("### 🛠️ خيارات التنظيف")
        missing_option = st.selectbox("1️⃣ معالجة القيم المفقودة", ["حذف الصفوف التي تحتوي على قيم مفقودة", "تعويض القيم المفقودة بالمتوسط (للأعمدة الرقمية)", "تعويض القيم المفقودة بالوسيط (للأعمدة الرقمية)", "لا تفعل شيئاً"], key="missing_option")
        dup_option = st.selectbox("2️⃣ معالجة التكرارات", ["حذف التكرارات (الاحتفاظ بالأول)", "لا تفعل شيئاً"], key="dup_option")
        outlier_option = st.selectbox("3️⃣ معالجة القيم المتطرفة", ["لا تفعل شيئاً", "حذف القيم المتطرفة (طريقة IQR)"], key="outlier_option")
        
        if st.button("🧹 تطبيق التنظيف", type="primary", key="btn_apply_clean"):
            df_clean = df.copy(); steps = []
            if "حذف الصفوف" in missing_option:
                before = len(df_clean); df_clean = df_clean.dropna(); steps.append(f"✅ حذف {before - len(df_clean)} صف يحتوي على قيم مفقودة")
            elif "بالمتوسط" in missing_option:
                for col in df_clean.select_dtypes(include=[np.number]).columns: df_clean[col] = df_clean[col].fillna(df_clean[col].mean()); steps.append("✅ تعويض القيم المفقودة بالمتوسط")
            elif "بالوسيط" in missing_option:
                for col in df_clean.select_dtypes(include=[np.number]).columns: df_clean[col] = df_clean[col].fillna(df_clean[col].median()); steps.append("✅ تعويض القيم المفقودة بالوسيط")
            
            if "الاحتفاظ بالأول" in dup_option:
                before = len(df_clean); df_clean = df_clean.drop_duplicates(keep='first'); steps.append(f"✅ حذف {before - len(df_clean)} صف مكرر")
            
            if "حذف القيم المتطرفة" in outlier_option:
                removed = 0
                for col in df_clean.select_dtypes(include=[np.number]).columns:
                    Q1, Q3 = df_clean[col].quantile(0.25), df_clean[col].quantile(0.75)
                    IQR = Q3 - Q1
                    before_len = len(df_clean)
                    df_clean = df_clean[(df_clean[col] >= (Q1 - 1.5 * IQR)) & (df_clean[col] <= (Q3 + 1.5 * IQR))]
                    removed += before_len - len(df_clean)
                if removed > 0: steps.append(f"✅ حذف {removed} قيمة متطرفة")
            
            st.session_state.df_clean = df_clean
            st.markdown("---"); st.markdown("### ✅ خطوات التنظيف المنفذة")
            for step in steps: st.success(step)
            if st.button("📋 عرض ملخص البيانات", type="primary", key="btn_go_summary"): st.session_state.page = "summary"; st.rerun()

elif st.session_state.page == "summary":
    st.markdown("## 📋 ملخص البيانات الجاهزة للتحليل"); st.markdown("---")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ لا توجد بيانات")
    else:
        st.success("✅ البيانات جاهزة للتحليل")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("إجمالي الصفوف", f"{len(df):,}")
        with col2: st.metric("إجمالي الأعمدة", len(df.columns))
        with col3: st.metric("القيم المفقودة", f"{int(df.isnull().sum().sum()):,}")
        with col4: st.metric("التكرارات", f"{int(df.duplicated().sum()):,}")
        st.markdown("---"); st.markdown("### 👁️ معاينة البيانات (أول 10 صفوف)"); st.dataframe(df.head(10), use_container_width=True)
        st.markdown("---")
        if st.button("📊 الانتقال إلى التحليل الاستكشافي", type="primary", key="btn_go_eda_from_summary"): st.session_state.page = "eda"; st.rerun()

# ==============================================================================
# ==================== صفحة التحليل الاستكشافي (EDA) ===========================
elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    st.markdown("---")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # الفلتر الذكي
        bad_keywords = ['sku', 'id', 'code', 'date', 'time', 'timestamp', 'رقم', 'كود', 'تاريخ']
        valid_categorical = []
        for col in df.select_dtypes(include=['object', 'category']).columns:
            n_unique = df[col].nunique()
            if any(kw in col.lower() for kw in bad_keywords) or (n_unique > len(df) * 0.5):
                continue
            valid_categorical.append(col)
        
        st.markdown("### 📥 تصدير التقارير")
        if st.button("📥 تصدير تقرير EDA شامل واحترافي (HTML)", type="primary", key="btn_export_comprehensive_eda"):
            with st.spinner("جاري إنشاء التقرير..."):
                try:
                    # بناء HTML كامل يدوياً
                    html = []
                    
                    html.append("""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<title>تقرير التحليل الاستكشافي الشامل</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #f5f7fa; color: #2d3748; line-height: 1.6; direction: rtl; text-align: right; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 20px; text-align: center; }
.header h1 { font-size: 36px; margin-bottom: 10px; }
.header p { opacity: 0.9; font-size: 16px; }
.container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
.cards { display: flex; gap: 20px; margin-bottom: 40px; flex-wrap: wrap; }
.card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); flex: 1; min-width: 200px; text-align: center; border-top: 4px solid #667eea; }
.card .label { color: #718096; font-size: 14px; margin-bottom: 8px; }
.card .value { color: #2d3748; font-size: 28px; font-weight: bold; }
.section { background: white; padding: 35px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 30px; }
.section h2 { color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 25px; font-size: 24px; }
.section h3 { color: #667eea; margin-top: 30px; margin-bottom: 15px; border-right: 5px solid #764ba2; padding-right: 15px; font-size: 20px; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }
thead { background: #667eea; }
th { color: white; padding: 14px 12px; text-align: right; font-weight: 600; }
td { padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right; }
tbody tr:nth-child(even) { background: #f7fafc; }
tbody tr:hover { background: #edf2f7; }
.chart { margin: 25px 0; padding: 20px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; min-height: 400px; }
.note { background: #fffaf0; border-right: 5px solid #ed8936; padding: 20px; margin: 20px 0; border-radius: 8px; color: #c05621; }
.footer { text-align: center; padding: 40px; color: #718096; background: white; margin-top: 40px; border-top: 1px solid #e2e8f0; }
@media print { .header, thead { -webkit-print-color-adjust: exact; print-color-adjust: exact; } .section { break-inside: avoid; } .chart { break-inside: avoid; } }
</style>
</head>
<body>
<div class="header">
<h1> تقرير التحليل الاستكشافي الشامل</h1>
<p>Smart Analytics Pro - """)
                    
                    html.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
                    html.append("""</p>
</div>
<div class="container">
<div class="cards">
<div class="card"><div class="label">إجمالي السجلات</div><div class="value">""")
                    html.append(f"{len(df):,}")
                    html.append("""</div></div>
<div class="card"><div class="label">إجمالي الأعمدة</div><div class="value">""")
                    html.append(str(len(df.columns)))
                    html.append("""</div></div>
<div class="card"><div class="label">الأعمدة الرقمية</div><div class="value">""")
                    html.append(str(len(numeric_cols)))
                    html.append("""</div></div>
<div class="card"><div class="label">الأعمدة الفئوية الصالحة</div><div class="value">""")
                    html.append(str(len(valid_categorical)))
                    html.append("""</div></div>
</div>""")
                    
                    # 1. الجداول التكرارية
                    html.append("""<div class="section">
<h2>📋 1. الجداول التكرارية (أعلى 15 قيمة)</h2>
<p style="color:#718096; margin-bottom:20px;">تم استبعاد المعرفات الفريدة وأعمدة التواريخ تلقائياً.</p>""")
                    
                    for col in valid_categorical:
                        freq = df[col].value_counts().head(15).reset_index()
                        freq.columns = ['القيمة', 'التكرار']
                        freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                        
                        html.append(f"<h3> {col}</h3>")
                        html.append("<table><thead><tr><th>القيمة</th><th>التكرار</th><th>النسبة %</th></tr></thead><tbody>")
                        for _, row in freq.iterrows():
                            html.append(f"<tr><td>{row['القيمة']}</td><td>{row['التكرار']}</td><td>{row['النسبة %']}</td></tr>")
                        html.append("</tbody></table>")
                        
                        # رسم بياني
                        fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}", color='التكرار', color_continuous_scale='Blues')
                        fig.update_layout(height=350, xaxis_tickangle=-45)
                        html.append('<div class="chart">')
                        html.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html.append('</div>')
                    
                    skipped = [c for c in df.select_dtypes(include=['object', 'category']).columns if c not in valid_categorical]
                    if skipped:
                        html.append(f'<div class="note">ℹ️ <strong>ملاحظة:</strong> تم استبعاد: <strong>{", ".join(skipped)}</strong></div>')
                    
                    html.append("</div>")
                    
                    # 2. المقاييس الإحصائية
                    html.append("""<div class="section">
<h2>📈 2. المقاييس الإحصائية الشاملة</h2>""")
                    
                    for col in numeric_cols:
                        cd = df[col].dropna()
                        if len(cd) == 0: continue
                        
                        m, med, s = cd.mean(), cd.median(), cd.std()
                        v = cd.var()
                        min_v, max_v = cd.min(), cd.max()
                        q1, q2, q3 = cd.quantile(0.25), cd.quantile(0.50), cd.quantile(0.75)
                        iqr = q3 - q1
                        sk, ku = cd.skew(), cd.kurtosis()
                        
                        sk_i = "متماثل" if abs(sk) < 0.5 else ("منحرف لليمين" if sk > 0 else "منحرف لليسار")
                        ku_i = "مدبب" if ku > 0 else "مفلطح"
                        
                        html.append(f"<h3>📊 {col}</h3>")
                        html.append("<table><thead><tr><th>المتوسط</th><th>الوسيط</th><th>الانحراف المعياري</th><th>التباين</th><th>الحد الأدنى</th><th>Q1</th><th>Q2</th><th>Q3</th><th>الحد الأقصى</th><th>IQR</th></tr></thead><tbody>")
                        html.append(f"<tr><td>{m:.2f}</td><td>{med:.2f}</td><td>{s:.2f}</td><td>{v:.2f}</td><td>{min_v:.2f}</td><td>{q1:.2f}</td><td>{q2:.2f}</td><td>{q3:.2f}</td><td>{max_v:.2f}</td><td>{iqr:.2f}</td></tr>")
                        html.append("</tbody></table>")
                        
                        html.append("<table><thead><tr><th>الانحناء</th><th>التفسير</th><th>التفلطح</th><th>التفسير</th></tr></thead><tbody>")
                        html.append(f"<tr><td>{sk:.2f}</td><td>{sk_i}</td><td>{ku:.2f}</td><td>{ku_i}</td></tr>")
                        html.append("</tbody></table>")
                        
                        fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
                        fig.add_vline(x=m, line_dash="dash", line_color="red", annotation_text=f"Mean: {m:.1f}")
                        fig.update_layout(height=350)
                        html.append('<div class="chart">')
                        html.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html.append('</div>')
                    
                    html.append("</div>")
                    
                    # 3. Box Plots
                    html.append("""<div class="section">
<h2>📦 3. مخططات الصندوق (Box Plots)</h2>""")
                    
                    for col in numeric_cols:
                        q1, q2, q3 = df[col].quantile(0.25), df[col].quantile(0.50), df[col].quantile(0.75)
                        iqr = q3 - q1
                        outliers = len(df[(df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)])
                        
                        html.append(f"<h3>📦 {col}</h3>")
                        html.append("<table><thead><tr><th>Min</th><th>Q1</th><th>Median</th><th>Q3</th><th>Max</th><th>IQR</th><th>Outliers</th></tr></thead><tbody>")
                        html.append(f"<tr><td>{df[col].min():.2f}</td><td>{q1:.2f}</td><td>{q2:.2f}</td><td>{q3:.2f}</td><td>{df[col].max():.2f}</td><td>{iqr:.2f}</td><td>{outliers}</td></tr>")
                        html.append("</tbody></table>")
                        
                        fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
                        fig.update_layout(height=350)
                        html.append('<div class="chart">')
                        html.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                        html.append('</div>')
                    
                    html.append("</div>")
                    
                    html.append("""<div class="footer">
<p>تم إنشاء هذا التقرير بواسطة <b>Smart Analytics Pro</b></p>
<p>© 2026 جميع الحقوق محفوظة</p>
</div>
</div>
</body>
</html>""")
                    
                    final_html = "".join(html)
                    
                    st.download_button(
                        label="📥 تحميل التقرير",
                        data=final_html,
                        file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                    st.success("✅ تم إنشاء التقرير!")
                    
                except Exception as e:
                    st.error(f"❌ خطأ: {str(e)}")
                    st.exception(e)
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs([" الجداول", "📈 التصور", "📊 الإحصائيات", "📦 Box Plots"])
        
        with tab1:
            if valid_categorical:
                col = st.selectbox("اختر العمود", valid_categorical)
                freq = df[col].value_counts().head(20).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                st.dataframe(freq, use_container_width=True)
            else:
                st.info("لا توجد متغيرات فئوية")
        
        with tab2:
            if numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols)
                fig = px.histogram(df, x=col, nbins=30)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            if numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols)
                st.write(df[col].describe())
        
        with tab4:
            if numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols)
                fig = px.box(df, y=col)
                st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "diagnostic":           
    st.markdown("## 🔍 التحليل التشخيصي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً")
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            col = st.selectbox("اختر العمود", numeric_cols)
            threshold = st.slider("الحد (Z-Score)", 2.0, 4.0, 3.0)
            if st.button("🔍 تحليل الشذوذ", key="btn_diag"):
                mean, std = np.mean(df[col]), np.std(df[col])
                z_scores = np.abs((df[col] - mean) / std)
                df['Anomaly'] = z_scores > threshold
                anomalies = df[df['Anomaly']]
                st.metric("حالات الشذوذ", len(anomalies))
                if len(anomalies) > 0: st.dataframe(anomalies)

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً")
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= 2:
            target = st.selectbox("الهدف", numeric_cols, key="pred_target")
            feature = st.selectbox("الميزة", [c for c in numeric_cols if c != target], key="pred_feat")
            if st.button("🚀 تنبؤ", key="btn_pred"):
                X, y = df[[feature]].values, df[target].values
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                model = LinearRegression().fit(X_train, y_train)
                preds = model.predict(X_test)
                st.metric("R² Score", f"{r2_score(y_test, preds):.3f}")
                fig = px.scatter(x=y_test, y=preds, labels={'x': 'Actual', 'y': 'Predicted'}, trendline="ols")
                fig.update_layout(title={'x': 0, 'xanchor': 'right'})
                st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "prescriptive":
    st.markdown("## 💡 التحليل الإرشادي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً")
    else: st.success("✅ البيانات جاهزة. سيتم إضافة محرك التوصيات الذكي في التحديث القادم.")

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً")
    else:
        prompt = st.text_input("اسأل عن بياناتك (مثال: ما هو متوسط المبيعات؟):", key="chat_q")
        if prompt:
            if "عدد" in prompt or "rows" in prompt: st.write(f"📊 عدد الصفوف: {len(df)}")
            elif "أعمدة" in prompt or "columns" in prompt: st.write(f"📋 الأعمدة: {', '.join(df.columns.tolist())}")
            elif "متوسط" in prompt:
                for col in df.select_dtypes(include=[np.number]).columns.tolist()[:3]:
                    st.write(f"- {col}: {df[col].mean():.2f}")

elif st.session_state.page == "export":
    st.markdown("## 💾 التصدير")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً")
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv, "data.csv", "text/csv", key="dl_csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "data.xlsx", key="dl_excel")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
