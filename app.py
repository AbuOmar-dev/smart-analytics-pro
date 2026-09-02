import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from scipy import stats
import io
from datetime import datetime
from supabase import create_client, Client

import config

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="Smart Analytics Pro",
    page_icon="📊",
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
if "cleaning_stats" not in st.session_state: st.session_state.cleaning_stats = {}

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
            <div style="font-size: 50px; margin-bottom: 10px;"></div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📍 التنقل السريع")
    menu = {"home": " الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "readiness": "✅ جاهزية البيانات", "cleaning": "🧹 تنظيف البيانات", "eda": "📊 التحليل الاستكشافي"}
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
        st.markdown(f"""<div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; margin-top: 40px; border-left: 5px solid #48bb78;"><h3>👋 مرحباً {current_user['name']}!</h3><p><strong>ابدأ الآن في 4 خطوات:</strong></p><ol><li>📥 استيراد البيانات</li><li>✅ فحص جاهزية البيانات</li><li>🧹 تنظيف البيانات</li><li> التحليل الاستكشافي</li></ol></div>""", unsafe_allow_html=True)

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
        try:
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
            else: df = pd.read_excel(uploaded_file)
            st.session_state.df = df; st.session_state.df_clean = None
            st.success(f"✅ تم الرفع! {len(df)} صف، {len(df.columns)} عمود")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e: st.error(f"خطأ: {e}")

elif st.session_state.page == "readiness":
    st.markdown("## ✅ جاهزية البيانات")
    if st.session_state.df is None: st.warning("️ ارفع بيانات أولاً"); st.stop()
    df = st.session_state.df
    st.metric("الصفوف", len(df)); st.metric("الأعمدة", len(df.columns))
    st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    st.dataframe(pd.DataFrame({'العمود': df.columns, 'النوع': df.dtypes.astype(str), 'المفقودة': df.isnull().sum().values}), use_container_width=True)

# ==================== صفحة تنظيف البيانات المتقدمة ====================
elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف البيانات ومعالجتها")
    st.markdown("---")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
        st.stop()
    
    df = st.session_state.df.copy()
    
    st.markdown("### 📊 حالة البيانات الأصلية")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("الصفوف", len(df))
    with col2: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    with col3: st.metric("الأعمدة", len(df.columns))
    
    st.markdown("---")
    
    # ====== معالجة القيم المفقودة ======
    st.markdown("### 1️⃣ معالجة القيم المفقودة (Missing Values)")
    
    missing_cols = df.columns[df.isnull().sum() > 0].tolist()
    
    if missing_cols:
        st.markdown(f"**الأعمدة التي تحتوي على قيم مفقودة:** {len(missing_cols)} عمود")
        
        missing_method = st.selectbox("اختر طريقة المعالجة", 
                                     ["حذف الصفوف", "تعويض بالمتوسط (للأعمدة الرقمية)", 
                                      "تعويض بالوسيط (للأعمدة الرقمية)", "تعويض بالقيمة الأكثر تكراراً",
                                      "تعويض بالقيمة السابقة (Forward Fill)", "تعويض بالقيمة التالية (Backward Fill)"],
                                     key="missing_method")
        
        if st.button("تطبيق معالجة القيم المفقودة", type="primary", key="apply_missing"):
            before_missing = int(df.isnull().sum().sum())
            
            if missing_method == "حذف الصفوف":
                df = df.dropna()
            elif missing_method == "تعويض بالمتوسط (للأعمدة الرقمية)":
                for col in df.select_dtypes(include=[np.number]).columns:
                    df[col] = df[col].fillna(df[col].mean())
            elif missing_method == "تعويض بالوسيط (للأعمدة الرقمية)":
                for col in df.select_dtypes(include=[np.number]).columns:
                    df[col] = df[col].fillna(df[col].median())
            elif missing_method == "تعويض بالقيمة الأكثر تكراراً":
                for col in df.columns:
                    mode_val = df[col].mode()
                    if len(mode_val) > 0:
                        df[col] = df[col].fillna(mode_val[0])
            elif missing_method == "تعويض بالقيمة السابقة (Forward Fill)":
                df = df.fillna(method='ffill')
            elif missing_method == "تعويض بالقيمة التالية (Backward Fill)":
                df = df.fillna(method='bfill')
            
            after_missing = int(df.isnull().sum().sum())
            st.success(f"✅ تم معالجة {before_missing - after_missing} قيمة مفقودة")
            st.session_state.df = df
    else:
        st.success("✅ لا توجد قيم مفقودة في البيانات")
    
    st.markdown("---")
    
    # ====== معالجة القيم المتطرفة ======
    st.markdown("### 2️⃣ معالجة القيم المتطرفة (Outliers)")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_cols:
        outlier_method = st.selectbox("اختر طريقة الكشف عن القيم المتطرفة",
                                     ["IQR Method", "Z-Score Method", "Percentile Method"],
                                     key="outlier_method")
        
        outlier_action = st.selectbox("اختر الإجراء", 
                                     ["حذف القيم المتطرفة", "استبدال بالحدود", "لا تفعل شيئاً"],
                                     key="outlier_action")
        
        if outlier_method == "IQR Method":
            iqr_multiplier = st.slider("مضاعف IQR", 1.0, 3.0, 1.5, key="iqr_mult")
        elif outlier_method == "Z-Score Method":
            z_threshold = st.slider("حد Z-Score", 2.0, 4.0, 3.0, key="z_thresh")
        else:
            lower_pct = st.slider("النسبة المئوية الدنيا", 0.0, 5.0, 1.0, key="low_pct")
            upper_pct = st.slider("النسبة المئوية العليا", 95.0, 100.0, 99.0, key="up_pct")
        
        if st.button("تطبيق معالجة القيم المتطرفة", type="primary", key="apply_outliers"):
            before_outliers = len(df)
            
            if outlier_action != "لا تفعل شيئاً":
                for col in numeric_cols:
                    if outlier_method == "IQR Method":
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower = Q1 - iqr_multiplier * IQR
                        upper = Q3 + iqr_multiplier * IQR
                        
                        if outlier_action == "حذف القيم المتطرفة":
                            df = df[(df[col] >= lower) & (df[col] <= upper)]
                        else:
                            df[col] = df[col].clip(lower=lower, upper=upper)
                    
                    elif outlier_method == "Z-Score Method":
                        mean = df[col].mean()
                        std = df[col].std()
                        lower = mean - z_threshold * std
                        upper = mean + z_threshold * std
                        
                        if outlier_action == "حذف القيم المتطرفة":
                            df = df[(df[col] >= lower) & (df[col] <= upper)]
                        else:
                            df[col] = df[col].clip(lower=lower, upper=upper)
                    
                    else:
                        lower = df[col].quantile(lower_pct / 100)
                        upper = df[col].quantile(upper_pct / 100)
                        
                        if outlier_action == "حذف القيم المتطرفة":
                            df = df[(df[col] >= lower) & (df[col] <= upper)]
                        else:
                            df[col] = df[col].clip(lower=lower, upper=upper)
            
            after_outliers = len(df)
            st.success(f"✅ تم معالجة {before_outliers - after_outliers} سجل")
            st.session_state.df = df
    else:
        st.info("لا توجد أعمدة رقمية للكشف عن القيم المتطرفة")
    
    st.markdown("---")
    
    # ====== تحويل الفئات (Encoding) ======
    st.markdown("### 3️ تحويل الفئات (Encoding)")
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if categorical_cols:
        encoding_method = st.selectbox("اختر طريقة التحويل",
                                      ["Label Encoding", "One-Hot Encoding", "لا تفعل شيئاً"],
                                      key="encoding_method")
        
        if st.button("تطبيق تحويل الفئات", type="primary", key="apply_encoding"):
            if encoding_method == "Label Encoding":
                le = LabelEncoder()
                for col in categorical_cols:
                    df[col] = le.fit_transform(df[col].astype(str))
                st.success("✅ تم تطبيق Label Encoding")
            elif encoding_method == "One-Hot Encoding":
                df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
                st.success("✅ تم تطبيق One-Hot Encoding")
            
            st.session_state.df = df
    else:
        st.info("لا توجد أعمدة فئوية للتحويل")
    
    st.markdown("---")
    
    # ====== حفظ البيانات المنظفة ======
    st.markdown("### 💾 حفظ البيانات المنظفة")
    
    if st.button("حفظ البيانات المنظفة والانتقال للتحليل", type="primary", key="save_clean"):
        st.session_state.df_clean = df
        st.success("✅ تم حفظ البيانات المنظفة!")
        
        st.markdown("---")
        st.markdown("### 📊 ملخص التنظيف")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("الصفوف النهائية", len(df))
        with col2: st.metric("الأعمدة النهائية", len(df.columns))
        with col3: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
        
        st.dataframe(df.head(10), use_container_width=True)
        
        if st.button("الانتقال إلى التحليل الاستكشافي", type="primary", key="go_eda"):
            st.session_state.page = "eda"
            st.rerun()

# ==================== صفحة التحليل الاستكشافي ====================
elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    st.markdown("---")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
        st.stop()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # ====== دالة بناء جدول HTML ======
    def build_html_table(dataframe, title=""):
        html = f"<h3 style='color:#667eea; margin-top:25px; margin-bottom:15px;'>{title}</h3>"
        html += "<table style='width:100%; border-collapse:collapse; margin:20px 0; font-size:14px;'>"
        html += "<thead><tr style='background:#667eea; color:white;'>"
        for col in dataframe.columns:
            html += f"<th style='padding:12px; text-align:right;'>{col}</th>"
        html += "</tr></thead><tbody>"
        for idx, row in dataframe.iterrows():
            bg = "#f7fafc" if idx % 2 == 0 else "white"
            html += f"<tr style='background:{bg};'>"
            for val in row:
                val_str = str(val) if pd.notna(val) else "-"
                html += f"<td style='padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;'>{val_str}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        return html
    
    # ====== تبويبات التحليل ======
    tab1, tab2, tab3, tab4 = st.tabs(["📋 الجداول التكرارية", " التصور البياني", "📊 الإحصائيات", "📦 Box Plots"])
    
    with tab1:
        st.markdown("### 📋 الجداول التكرارية")
        if categorical_cols:
            for col in categorical_cols[:5]:
                freq = df[col].value_counts().head(15).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                st.markdown(build_html_table(freq, f"📊 {col}"))
        else:
            st.info("لا توجد متغيرات فئوية")
    
    with tab2:
        st.markdown("### 📈 التصور البياني")
        if numeric_cols:
            for col in numeric_cols[:3]:
                fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 📊 المقاييس الإحصائية")
        if numeric_cols:
            for col in numeric_cols:
                cd = df[col].dropna()
                stats_df = pd.DataFrame({
                    'المقياس': ['المتوسط', 'الوسيط', 'الانحراف المعياري', 'التباين', 'الحد الأدنى', 'Q1', 'Q2', 'Q3', 'الحد الأقصى', 'IQR'],
                    'القيمة': [f"{cd.mean():.2f}", f"{cd.median():.2f}", f"{cd.std():.2f}", f"{cd.var():.2f}", 
                              f"{cd.min():.2f}", f"{cd.quantile(0.25):.2f}", f"{cd.quantile(0.50):.2f}", 
                              f"{cd.quantile(0.75):.2f}", f"{cd.max():.2f}", f"{(cd.quantile(0.75)-cd.quantile(0.25)):.2f}"]
                })
                st.markdown(build_html_table(stats_df, f"📊 {col}"))
    
    with tab4:
        st.markdown("### 📦 Box Plots")
        if numeric_cols:
            for col in numeric_cols[:3]:
                fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ====== تقرير EDA شامل ======
    st.markdown("###  تصدير تقرير EDA شامل")
    
    if st.button("إنشاء وتحميل التقرير الشامل", type="primary", key="export_eda_report"):
        with st.spinner("جاري إنشاء التقرير..."):
            html_parts = []
            
            html_parts.append(f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير التحليل الاستكشافي الشامل</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #f8f9fa; color: #2d3748; line-height: 1.6; direction: rtl; text-align: right; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}
        .section {{ background: white; padding: 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: right; }}
        td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; }}
        tr:nth-child(even) {{ background: #f7fafc; }}
        .chart-box {{ margin: 25px 0; padding: 20px; background: white; border-radius: 12px; }}
        .footer {{ text-align: center; padding: 30px; color: #718096; background: white; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 تقرير التحليل الاستكشافي الشامل</h1>
        <p>Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="container">""")
            
            # 1. الجداول التكرارية
            html_parts.append("<div class='section'><h2>📋 1. الجداول التكرارية</h2>")
            for col in categorical_cols[:5]:
                freq = df[col].value_counts().head(15).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                html_parts.append(build_html_table(freq, f"📊 {col}"))
            html_parts.append("</div>")
            
            # 2. المقاييس الإحصائية
            html_parts.append("<div class='section'><h2>📊 2. المقاييس الإحصائية الشاملة</h2>")
            for col in numeric_cols:
                cd = df[col].dropna()
                stats_df = pd.DataFrame({
                    'المقياس': ['المتوسط', 'الوسيط', 'الانحراف المعياري', 'التباين', 'الحد الأدنى', 'Q1', 'Q2', 'Q3', 'الحد الأقصى', 'IQR'],
                    'القيمة': [f"{cd.mean():.2f}", f"{cd.median():.2f}", f"{cd.std():.2f}", f"{cd.var():.2f}", 
                              f"{cd.min():.2f}", f"{cd.quantile(0.25):.2f}", f"{cd.quantile(0.50):.2f}", 
                              f"{cd.quantile(0.75):.2f}", f"{cd.max():.2f}", f"{(cd.quantile(0.75)-cd.quantile(0.25)):.2f}"]
                })
                html_parts.append(build_html_table(stats_df, f"📊 {col}"))
            html_parts.append("</div>")
            
            # 3. Box Plots
            html_parts.append("<div class='section'><h2>📦 3. مخططات الصندوق (Box Plots)</h2>")
            for col in numeric_cols:
                q1, q2, q3 = df[col].quantile(0.25), df[col].quantile(0.50), df[col].quantile(0.75)
                iqr = q3 - q1
                outliers = len(df[(df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)])
                box_df = pd.DataFrame({
                    'المقياس': ['Min', 'Q1', 'Median', 'Q3', 'Max', 'IQR', 'Outliers'],
                    'القيمة': [f"{df[col].min():.2f}", f"{q1:.2f}", f"{q2:.2f}", f"{q3:.2f}", f"{df[col].max():.2f}", f"{iqr:.2f}", str(outliers)]
                })
                html_parts.append(build_html_table(box_df, f"📦 {col}"))
            html_parts.append("</div>")
            
            html_parts.append("""
        <div class="footer">
            <p>تم إنشاء هذا التقرير تلقائياً بواسطة <b>Smart Analytics Pro</b></p>
            <p>© 2026 جميع الحقوق محفوظة</p>
        </div>
    </div>
</body>
</html>""")
            
            final_html = "".join(html_parts)
            
            st.download_button(
                label=" تحميل التقرير الشامل (HTML)",
                data=final_html,
                file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
            st.success("✅ تم إنشاء التقرير بنجاح!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
