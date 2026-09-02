import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import io
from datetime import datetime
from supabase import create_client, Client
import config

# ==================== إعدادات الصفحة ====================
st.set_page_config(page_title="Smart Analytics Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

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
    st.markdown("""<div class="login-container"><div class="login-header"><div style="font-size: 80px; margin-bottom: 20px;"></div><h1>Smart Analytics Pro</h1><p style="color: #718096; font-size: 18px;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div></div>""", unsafe_allow_html=True)
    
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
                elif new_password != confirm_password: st.error(" كلمات المرور غير متطابقة")
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
        st.info(" **بيانات تجريبية:**\n- المستخدم: `admin`\n- كلمة المرور: `Smart@2026`")
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
    menu = {"home": "🏠 الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "data_overview": "️ نظرة عامة على البيانات", "cleaning": "🧹 تنظيف البيانات", "eda": " التحليل الاستكشافي", "final_dashboard": "📊 الداشبورد النهائية"}
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
                st.markdown(f"""<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);"><div style="text-align: center; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 8px; margin-bottom: 15px;"> الأكثر شعبية</div><h2 style="color: white; text-align: center;">{plan['name']}</h2><h1 style="color: white; text-align: center;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1></div>""", unsafe_allow_html=True)
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

elif st.session_state.page == "data_overview":
    st.markdown("## 👁️ نظرة عامة على البيانات")
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
        st.stop()
    
    df = st.session_state.df
    
    # عرض أول 10 وآخر 10 صفوف
    st.markdown("### 📋 عرض البيانات")
    view_option = st.radio("اختر العرض:", ["أول 10 صفوف", "آخر 10 صفوف"], horizontal=True)
    if view_option == "أول 10 صفوف":
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.dataframe(df.tail(10), use_container_width=True)
    
    st.markdown("---")
    
    # معلومات البيانات
    st.markdown("### 📊 معلومات البيانات")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("عدد الصفوف", len(df))
    with col2: st.metric("عدد الأعمدة", len(df.columns))
    with col3: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    with col4: st.metric("التكرارات", int(df.duplicated().sum()))
    
    st.markdown("---")
    
    # معلومات تفصيلية لكل عمود
    st.markdown("### 🔍 معلومات تفصيلية لكل عمود")
    info_data = []
    for col in df.columns:
        info_data.append({
            'العمود': col,
            'النوع': str(df[col].dtype),
            'القيم الفريدة': int(df[col].nunique()),
            'القيم المفقودة': int(df[col].isnull().sum()),
            'نسبة المفقود %': round((df[col].isnull().sum() / len(df)) * 100, 2)
        })
    st.dataframe(pd.DataFrame(info_data), use_container_width=True)
    
    st.markdown("---")
    
    # رسم بياني ملخص
    st.markdown("###  ملخص بصري سريع")
    chart_col = st.selectbox("اختر عمود للعرض البياني:", df.columns.tolist())
    if chart_col in df.select_dtypes(include=[np.number]).columns:
        fig = px.histogram(df, x=chart_col, title=f"توزيع {chart_col}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.bar(df[chart_col].value_counts().head(10), title=f"توزيع {chart_col}")
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف البيانات ومعالجتها")
    if st.session_state.df is None:
        st.warning("️ يرجى رفع البيانات أولاً")
        st.stop()
    
    df = st.session_state.df.copy()
    
    st.markdown("### 📊 حالة البيانات قبل التنظيف")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("الصفوف", len(df))
    with col2: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    with col3: st.metric("التكرارات", int(df.duplicated().sum()))
    
    st.markdown("---")
    
    # معالجة القيم المفقودة
    st.markdown("### 1️⃣ معالجة القيم المفقودة (Missing Values)")
    missing_cols = [col for col in df.columns if df[col].isnull().sum() > 0]
    if missing_cols:
        missing_method = st.selectbox("اختر طريقة المعالجة:", 
            ["حذف الصفوف التي تحتوي على قيم مفقودة", 
             "تعويض بالمتوسط (للأعمدة الرقمية)", 
             "تعويض بالوسيط (للأعمدة الرقمية)", 
             "تعويض بالقيمة الأكثر تكراراً", 
             "لا تفعل شيئاً"], key="missing_method")
    else:
        st.success("✅ لا توجد قيم مفقودة")
        missing_method = "لا تفعل شيئاً"
    
    st.markdown("---")
    
    # معالجة القيم المتطرفة
    st.markdown("### 2️⃣ معالجة القيم المتطرفة (Outliers)")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        outlier_method = st.selectbox("اختر طريقة الكشف:", ["IQR Method", "Z-Score Method"], key="outlier_method")
        outlier_action = st.selectbox("اختر الإجراء:", ["حذف القيم المتطرفة", "استبدال بالحدود", "لا تفعل شيئاً"], key="outlier_action")
    else:
        st.info("لا توجد أعمدة رقمية")
        outlier_action = "لا تفعل شيئاً"
    
    st.markdown("---")
    
    # تحويل الفئات
    st.markdown("### 3️⃣ تحويل الفئات (Encoding)")
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if categorical_cols:
        encoding_method = st.selectbox("اختر طريقة التحويل:", ["Label Encoding", "One-Hot Encoding", "لا تفعل شيئاً"], key="encoding_method")
    else:
        st.info("لا توجد أعمدة فئوية")
        encoding_method = "لا تفعل شيئاً"
    
    st.markdown("---")
    
    if st.button("🧹 تطبيق التنظيف", type="primary", key="btn_apply_clean"):
        df_clean = df.copy()
        steps = []
        
        # تطبيق معالجة القيم المفقودة
        if "حذف الصفوف" in missing_method:
            before = len(df_clean)
            df_clean = df_clean.dropna()
            steps.append(f"✅ حذف {before - len(df_clean)} صف يحتوي على قيم مفقودة")
        elif "بالمتوسط" in missing_method:
            for col in df_clean.select_dtypes(include=[np.number]).columns:
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            steps.append("✅ تعويض القيم المفقودة بالمتوسط")
        elif "بالوسيط" in missing_method:
            for col in df_clean.select_dtypes(include=[np.number]).columns:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            steps.append("✅ تعويض القيم المفقودة بالوسيط")
        elif "بالأكثر تكراراً" in missing_method:
            for col in df_clean.columns:
                mode_val = df_clean[col].mode()
                if len(mode_val) > 0:
                    df_clean[col] = df_clean[col].fillna(mode_val[0])
            steps.append("✅ تعويض القيم المفقودة بالقيمة الأكثر تكراراً")
        
        # تطبيق معالجة القيم المتطرفة
        if outlier_action != "لا تفعل شيئاً" and numeric_cols:
            for col in numeric_cols:
                if outlier_method == "IQR Method":
                    Q1, Q3 = df_clean[col].quantile(0.25), df_clean[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                else:
                    mean, std = df_clean[col].mean(), df_clean[col].std()
                    lower, upper = mean - 3 * std, mean + 3 * std
                
                if outlier_action == "حذف القيم المتطرفة":
                    before = len(df_clean)
                    df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
                    if before - len(df_clean) > 0:
                        steps.append(f"✅ حذف {before - len(df_clean)} قيمة متطرفة من {col}")
                elif outlier_action == "استبدال بالحدود":
                    df_clean[col] = df_clean[col].clip(lower=lower, upper=upper)
                    steps.append(f"✅ استبدال القيم المتطرفة بالحدود في {col}")
        
        # تطبيق تحويل الفئات
        if encoding_method != "لا تفعل شيئاً" and categorical_cols:
            if encoding_method == "Label Encoding":
                le = LabelEncoder()
                for col in categorical_cols:
                    df_clean[col] = le.fit_transform(df_clean[col].astype(str))
                steps.append("✅ تطبيق Label Encoding")
            elif encoding_method == "One-Hot Encoding":
                df_clean = pd.get_dummies(df_clean, columns=categorical_cols, drop_first=True)
                steps.append("✅ تطبيق One-Hot Encoding")
        
        st.session_state.df_clean = df_clean
        
        st.markdown("### ✅ خطوات التنظيف المنفذة")
        for step in steps:
            st.success(step)
        
        st.markdown("---")
        st.markdown("### 📊 حالة البيانات بعد التنظيف")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("الصفوف", len(df_clean))
        with col2: st.metric("القيم المفقودة", int(df_clean.isnull().sum().sum()))
        with col3: st.metric("الأعمدة", len(df_clean.columns))

elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
        st.stop()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    tab1, tab2, tab3 = st.tabs(["📋 الجداول التكرارية", "📊 التحليل الإحصائي الشامل", "📦 Box Plots"])
    
    with tab1:
        st.markdown("###  الجداول التكرارية")
        if categorical_cols:
            for col in categorical_cols[:10]:
                st.markdown(f"####  {col}")
                freq = df[col].value_counts().head(15).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                st.dataframe(freq, use_container_width=True)
                fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد أعمدة فئوية")
    
    with tab2:
        st.markdown("### 📊 التحليل الإحصائي الشامل")
        if numeric_cols:
            selected_col = st.selectbox("اختر العمود الرقمي:", numeric_cols)
            data = df[selected_col].dropna()
            
            # مقاييس النزعة المركزية
            st.markdown("#### 📍 مقاييس النزعة المركزية")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("المتوسط (Mean)", f"{data.mean():.4f}")
            with col2: st.metric("الوسيط (Median)", f"{data.median():.4f}")
            with col3: st.metric("المنوال (Mode)", f"{data.mode().iloc[0]:.4f}")
            
            st.markdown("---")
            
            # مقاييس التشتت
            st.markdown("#### 📏 مقاييس التشتت")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("المدى (Range)", f"{(data.max() - data.min()):.4f}")
            with col2: st.metric("التباين (Variance)", f"{data.var():.4f}")
            with col3: st.metric("الانحراف المعياري (Std)", f"{data.std():.4f}")
            with col4: st.metric("معامل الاختلاف (CV%)", f"{(data.std()/data.mean()*100):.2f}%")
            
            st.markdown("---")
            
            # مقاييس الموضع
            st.markdown("#### 📐 مقاييس الموضع")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("الربيع الأول (Q1)", f"{data.quantile(0.25):.4f}")
            with col2: st.metric("الوسيط (Q2)", f"{data.quantile(0.50):.4f}")
            with col3: st.metric("الربيع الثالث (Q3)", f"{data.quantile(0.75):.4f}")
            with col4: st.metric("المدى الربيعي (IQR)", f"{(data.quantile(0.75) - data.quantile(0.25)):.4f}")
            
            st.markdown("---")
            
            # الانحناء والتفلطح
            st.markdown("#### 📈 الانحناء والتفلطح")
            skew = data.skew()
            kurt = data.kurtosis()
            
            skew_interp = "متماثل تقريباً" if abs(skew) < 0.5 else ("منحرف لليمين" if skew > 0 else "منحرف لليسار")
            kurt_interp = "مدبب (ذيول ثقيلة)" if kurt > 3 else ("متوسط التفلطح" if kurt > 0 else "مفلطح (ذيول خفيفة)")
            
            col1, col2 = st.columns(2)
            with col1: st.info(f"**الانحناء (Skewness):** {skew:.4f}\n\n*التفسير:* {skew_interp}")
            with col2: st.info(f"**التفلطح (Kurtosis):** {kurt:.4f}\n\n*التفسير:* {kurt_interp}")
            
            st.markdown("---")
            
            # رسم بياني
            fig = px.histogram(df, x=selected_col, nbins=30, title=f"توزيع {selected_col}")
            fig.add_vline(x=data.mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {data.mean():.2f}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد أعمدة رقمية")
    
    with tab3:
        st.markdown("### 📦 Box Plots")
        if numeric_cols:
            for col in numeric_cols[:5]:
                st.markdown(f"#### 📦 {col}")
                fig = px.box(df, y=col, title=f"Box Plot - {col}")
                st.plotly_chart(fig, use_container_width=True)
                
                Q1, Q2, Q3 = df[col].quantile(0.25), df[col].quantile(0.50), df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                outliers = len(df[(df[col] < lower) | (df[col] > upper)])
                
                st.metric("عدد القيم المتطرفة", outliers)
        else:
            st.info("لا توجد أعمدة رقمية")

elif st.session_state.page == "final_dashboard":
    st.markdown("## 📊 الداشبورد النهائية للتقرير")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None:
        st.warning("️ يرجى رفع البيانات أولاً")
        st.stop()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if st.button("📥 تصدير التقرير الشامل", type="primary", key="btn_export_report"):
        html_parts = []
        html_parts.append(f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
        <meta charset="UTF-8">
        <title>تقرير التحليل الشامل - Smart Analytics Pro</title>
        <style>
        body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #f8f9fa; color: #2d3748; margin: 0; padding: 0; direction: rtl; text-align: right; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 20px; text-align: center; }}
        .container {{ max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
        .section {{ background: white; padding: 35px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }}
        .section h2 {{ color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #667eea; color: white; padding: 14px 12px; text-align: right; }}
        td {{ padding: 12px; border-bottom: 1px solid #edf2f7; text-align: right; }}
        tr:nth-child(even) {{ background: #f7fafc; }}
        .footer {{ text-align: center; padding: 40px; color: #718096; background: white; margin-top: 40px; }}
        </style>
        </head>
        <body>
        <div class="header">
        <h1>📊 تقرير التحليل الشامل</h1>
        <p>Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        <div class="container">
        """)
        
        # معلومات البيانات
        html_parts.append(f"""
        <div class="section">
        <h2>📋 معلومات البيانات</h2>
        <p><strong>عدد الصفوف:</strong> {len(df)}</p>
        <p><strong>عدد الأعمدة:</strong> {len(df.columns)}</p>
        <p><strong>القيم المفقودة:</strong> {int(df.isnull().sum().sum())}</p>
        </div>
        """)
        
        # الجداول التكرارية
        html_parts.append("<div class='section'><h2>📋 الجداول التكرارية</h2>")
        for col in categorical_cols[:5]:
            freq = df[col].value_counts().head(10).reset_index()
            freq.columns = ['القيمة', 'التكرار']
            freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
            html_parts.append(f"<h3>{col}</h3>{freq.to_html(index=False)}")
        html_parts.append("</div>")
        
        # التحليل الإحصائي
        html_parts.append("<div class='section'><h2> التحليل الإحصائي الشامل</h2>")
        for col in numeric_cols[:5]:
            data = df[col].dropna()
            html_parts.append(f"""
            <h3>{col}</h3>
            <table>
            <tr><th>المقياس</th><th>القيمة</th><th>التفسير</th></tr>
            <tr><td>المتوسط</td><td>{data.mean():.4f}</td><td>معدل القيم</td></tr>
            <tr><td>الوسيط</td><td>{data.median():.4f}</td><td>القيمة الوسطى</td></tr>
            <tr><td>الانحراف المعياري</td><td>{data.std():.4f}</td><td>مقياس التشتت</td></tr>
            <tr><td>Q1</td><td>{data.quantile(0.25):.4f}</td><td>25% من البيانات أقل من هذه القيمة</td></tr>
            <tr><td>Q3</td><td>{data.quantile(0.75):.4f}</td><td>75% من البيانات أقل من هذه القيمة</td></tr>
            <tr><td>الانحناء</td><td>{data.skew():.4f}</td><td>{"متماثل" if abs(data.skew()) < 0.5 else "منحرف"}</td></tr>
            <tr><td>التفلطح</td><td>{data.kurtosis():.4f}</td><td>{"مدبب" if data.kurtosis() > 3 else "مفلطح"}</td></tr>
            </table>
            """)
        html_parts.append("</div>")
        
        html_parts.append("""
        <div class="footer">
        <p>تم إنشاء هذا التقرير بواسطة Smart Analytics Pro</p>
        <p>© 2026 جميع الحقوق محفوظة</p>
        </div>
        </div>
        </body>
        </html>
        """)
        
        final_html = "".join(html_parts)
        st.download_button("📥 تحميل التقرير", data=final_html, file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", mime="text/html")
        st.success("✅ تم إنشاء التقرير!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
