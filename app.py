import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import io
from datetime import datetime
from supabase import create_client, Client

# محاولة استيراد config بأمان
try:
    import config
except ImportError:
    pass

# ==================== إعدادات الصفحة ====================
st.set_page_config(page_title="Smart Analytics Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ==================== CSS Styling (آمن ومتوافق) ====================
st.markdown("""
<style>
    /* تحسين الخلفية والعناوين */
    .stApp { background: #f8f9fa; }
    h1, h2, h3 { color: #2d3748; font-weight: 700; }
    
    /* تحسين الأزرار */
    .stButton>button { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; border-radius: 8px; padding: 10px 24px; 
        font-weight: 600; border: none; 
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2); 
        transition: all 0.3s ease; 
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(102, 126, 234, 0.3); }
    
    /* بطاقات تسجيل الدخول */
    .login-container { max-width: 500px; margin: 60px auto; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    .login-header { text-align: center; margin-bottom: 30px; }
    .login-header h1 { font-size: 32px; color: #667eea; }
    
    /* بطاقات الصفحة الرئيسية */
    .feature-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; transition: transform 0.2s; }
    .feature-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    
    /* إخفاء عناصر Streamlit الافتراضية غير المرغوبة */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    
    /* تنسيق الجداول في التقرير المصدّر */
    .data-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border-radius: 8px; overflow: hidden; }
    .data-table th { background: #667eea; color: white; padding: 12px; text-align: right; }
    .data-table td { padding: 10px; border-bottom: 1px solid #edf2f7; text-align: right; }
    .data-table tr:nth-child(even) { background: #f7fafc; }
</style>
""", unsafe_allow_html=True)

# ==================== Supabase ====================
SUPABASE_URL = "https://llsoulwgpptlpatgivqk.supabase.co"
SUPABASE_KEY = "sb_publishable_OpzDbBV2XqSJchMJ6DqmLQ_DYyB9GVH"
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
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
    except Exception:
        return {}

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
    st.markdown("""<div class="login-container"><div class="login-header"><h1>📊 Smart Analytics Pro</h1><p style="color: #718096;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div></div>""", unsafe_allow_html=True)
    
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
                if not all([new_username, new_password, new_name, new_email]): 
                    st.error("❌ يرجى ملء جميع الحقول")
                elif new_password != confirm_password: 
                    st.error("❌ كلمات المرور غير متطابقة")
                elif len(new_password) < 6: 
                    st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    success, message = register_user(new_username, new_password, new_name, new_email)
                    if success: 
                        st.success(f"✅ {message}"); st.balloons()
                        st.session_state.show_register = False; st.rerun()
                    else: 
                        st.error(f"❌ {message}")
            if st.button("🔐 لديك حساب؟ دخول", use_container_width=True, type="secondary", key="btn_go_login"): 
                st.session_state.show_register = False; st.rerun()
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
                else: 
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown("---")
        if st.button("📝 ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"): 
            st.session_state.show_register = True; st.rerun()
        st.info("💡 **بيانات تجريبية:**\n- المستخدم: `admin`\n- كلمة المرور: `Smart@2026`")
        st.stop()

# ==================== المنصة الرئيسية ====================
current_user = st.session_state.current_user

def load_data(file):
    try:
        if file.name.endswith('.csv'): return pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')): return pd.read_excel(file)
        return None
    except Exception:
        return None

with st.sidebar:
    if current_user:
        st.markdown(f"""<div style="background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 40px; margin-bottom: 10px;">👤</div>
            <div style="font-size: 16px; font-weight: bold; color: #2d3748;">{current_user['name']}</div>
            <div style="font-size: 14px; color: #667eea; margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("### 📍 التنقل السريع")
    menu = {
        "home": "🏠 الرئيسية", 
        "data_import": "📥 استيراد البيانات", 
        "data_overview": "👁️ نظرة عامة على البيانات", 
        "cleaning": "🧹 تنظيف البيانات", 
        "eda": "📊 التحليل الاستكشافي (EDA)", 
        "final_dashboard": "💾 تصدير التقرير النهائي"
    }
    for key, label in menu.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"): 
            st.session_state.page = key; st.rerun()
    
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True, type="secondary", key="btn_logout"): 
        st.session_state.logged_in = False; st.session_state.current_user = None
        st.session_state.page = "home"; st.session_state.show_register = False; st.rerun()
    
    if st.session_state.df is not None:
        st.success(f"✅ البيانات محملة: {len(st.session_state.df)} صف")

# ==================== الصفحات ====================
if st.session_state.page == "home":
    st.markdown("<div style='text-align: center; margin-bottom: 40px;'><h1>📊 Smart Analytics Pro</h1><p style='color: #718096; font-size: 18px;'>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.markdown("<div class='feature-card'><div style='font-size: 40px; margin-bottom: 15px;'>📊</div><h3>التحليل الاستكشافي</h3><p style='color: #718096;'>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p></div>", unsafe_allow_html=True)
    with col2: 
        st.markdown("<div class='feature-card'><div style='font-size: 40px; margin-bottom: 15px;'>🧹</div><h3>تنظيف البيانات</h3><p style='color: #718096;'>معالجة القيم المفقودة والمتطرفة وتشفير الفئات</p></div>", unsafe_allow_html=True)
    with col3: 
        st.markdown("<div class='feature-card'><div style='font-size: 40px; margin-bottom: 15px;'>💾</div><h3>تقارير احترافية</h3><p style='color: #718096;'>تصدير تقارير HTML شاملة وجاهزة للطباعة</p></div>", unsafe_allow_html=True)

elif st.session_state.page == "data_import":
    st.markdown("## 📥 استيراد البيانات")
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.session_state.df_clean = None
            st.success(f"✅ تم الرفع بنجاح! {len(df)} صف و {len(df.columns)} عمود")
            
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("عدد الصفوف", f"{len(df):,}")
            with col2: st.metric("عدد الأعمدة", len(df.columns))
            with col3: st.metric("حجم الملف", f"{uploaded_file.size / 1024:.2f} KB")
            
            st.markdown("### معاينة البيانات")
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.error("❌ حدث خطأ أثناء قراءة الملف. تأكد من أن الملف غير تالف.")

elif st.session_state.page == "data_overview":
    st.markdown("## 👁️ نظرة عامة على البيانات")
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً من صفحة 'استيراد البيانات'")
        st.stop()
    
    df = st.session_state.df
    
    st.markdown("### 📋 عرض البيانات")
    view_option = st.radio("اختر العرض:", ["أول 10 صفوف", "آخر 10 صفوف"], horizontal=True)
    if view_option == "أول 10 صفوف":
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.dataframe(df.tail(10), use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📊 معلومات البيانات")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("عدد الصفوف", len(df))
    with col2: st.metric("عدد الأعمدة", len(df.columns))
    with col3: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    with col4: st.metric("الصفوف المكررة", int(df.duplicated().sum()))
    
    st.markdown("---")
    st.markdown("### 🔍 معلومات تفصيلية لكل عمود")
    info_data = []
    for col in df.columns:
        info_data.append({
            'العمود': col,
            'النوع': str(df[col].dtype),
            'القيم الفريدة': int(df[col].nunique()),
            'القيم المفقودة': int(df[col].isnull().sum()),
            'نسبة المفقود %': round((df[col].isnull().sum() / len(df)) * 100, 2) if len(df) > 0 else 0
        })
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)

elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف البيانات ومعالجتها")
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
        st.stop()
    
    df = st.session_state.df.copy()
    
    st.markdown("### 📊 حالة البيانات قبل التنظيف")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("الصفوف", len(df))
    with col2: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    with col3: st.metric("التكرارات", int(df.duplicated().sum()))
    
    st.markdown("---")
    
    # 1. معالجة القيم المفقودة
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
    
    # 2. معالجة القيم المتطرفة
    st.markdown("### 2️⃣ معالجة القيم المتطرفة (Outliers)")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        outlier_method = st.selectbox("اختر طريقة الكشف:", ["IQR Method", "Z-Score Method"], key="outlier_method")
        outlier_action = st.selectbox("اختر الإجراء:", ["حذف القيم المتطرفة", "استبدال بالحدود", "لا تفعل شيئاً"], key="outlier_action")
    else:
        st.info("لا توجد أعمدة رقمية")
        outlier_action = "لا تفعل شيئاً"
    
    st.markdown("---")
    
    # 3. تحويل الفئات
    st.markdown("### 3️⃣ تحويل الفئات (Encoding)")
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    if categorical_cols:
        encoding_method = st.selectbox("اختر طريقة التحويل:", ["Label Encoding", "لا تفعل شيئاً"], key="encoding_method")
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
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    # 🧠 فلترة ذكية: استبعاد الأعمدة غير المفيدة إحصائياً (مثل SKU، التواريخ، المعرفات)
    valid_categorical = []
    bad_keywords = ['sku', 'id', 'code', 'date', 'time', 'timestamp', 'رقم', 'كود', 'تاريخ', 'link', 'url', 'name']
    for col in categorical_cols:
        n_unique = df[col].nunique()
        if not any(kw in str(col).lower() for kw in bad_keywords) and n_unique <= len(df) * 0.5:
            valid_categorical.append(col)

    tab1, tab2, tab3 = st.tabs(["📋 الجداول التكرارية", "📊 التحليل الإحصائي الشامل", "📦 Box Plots"])
    
    with tab1:
        st.markdown("### 📋 الجداول التكرارية")
        if valid_categorical:
            for col in valid_categorical[:10]: # عرض أول 10 أعمدة فقط لتجنب ازدحام الواجهة
                st.markdown(f"#### 📊 {col}")
                freq = df[col].value_counts().head(15).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                st.dataframe(freq, use_container_width=True, hide_index=True)
                
                fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}", color='التكرار', color_continuous_scale='Blues')
                fig.update_layout(title={'x': 0.5, 'xanchor': 'center'})
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")
        else:
            st.info("لا توجد أعمدة فئوية مناسبة للعرض (تم استبعاد الأعمدة ذات القيم الفريدة العالية أو المعرفات تلقائياً).")
    
    with tab2:
        st.markdown("### 📊 التحليل الإحصائي الشامل")
        if numeric_cols:
            selected_col = st.selectbox("اختر العمود الرقمي:", numeric_cols)
            data = df[selected_col].dropna()
            
            st.markdown("#### 📍 مقاييس النزعة المركزية")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("المتوسط (Mean)", f"{data.mean():.4f}")
            with col2: st.metric("الوسيط (Median)", f"{data.median():.4f}")
            with col3: st.metric("المنوال (Mode)", f"{data.mode().iloc[0] if len(data.mode()) > 0 else np.nan:.4f}")
            
            st.markdown("---")
            st.markdown("#### 📏 مقاييس التشتت")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("المدى (Range)", f"{(data.max() - data.min()):.4f}")
            with col2: st.metric("التباين (Variance)", f"{data.var():.4f}")
            with col3: st.metric("الانحراف المعياري (Std)", f"{data.std():.4f}")
            with col4: st.metric("معامل الاختلاف (CV%)", f"{(data.std()/data.mean()*100):.2f}%" if data.mean() != 0 else "0.00%")
            
            st.markdown("---")
            st.markdown("#### 📐 مقاييس الموضع")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("الربيع الأول (Q1)", f"{data.quantile(0.25):.4f}")
            with col2: st.metric("الوسيط (Q2)", f"{data.quantile(0.50):.4f}")
            with col3: st.metric("الربيع الثالث (Q3)", f"{data.quantile(0.75):.4f}")
            with col4: st.metric("المدى الربيعي (IQR)", f"{(data.quantile(0.75) - data.quantile(0.25)):.4f}")
            
            st.markdown("---")
            st.markdown("#### 📈 الانحناء والتفلطح")
            skew = data.skew()
            kurt = data.kurtosis()
            
            skew_interp = "متماثل تقريباً" if abs(skew) < 0.5 else ("منحرف لليمين" if skew > 0 else "منحرف لليسار")
            kurt_interp = "مدبب (ذيول ثقيلة)" if kurt > 3 else ("متوسط التفلطح" if kurt > 0 else "مفلطح (ذيول خفيفة)")
            
            col1, col2 = st.columns(2)
            with col1: st.info(f"**الانحناء (Skewness):** {skew:.4f}\n\n*التفسير:* {skew_interp}")
            with col2: st.info(f"**التفلطح (Kurtosis):** {kurt:.4f}\n\n*التفسير:* {kurt_interp}")
            
            st.markdown("---")
            fig = px.histogram(df, x=selected_col, nbins=30, title=f"توزيع {selected_col}", color_discrete_sequence=['#667eea'])
            fig.add_vline(x=data.mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {data.mean():.2f}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد أعمدة رقمية")
    
    with tab3:
        st.markdown("### 📦 Box Plots")
        if numeric_cols:
            for col in numeric_cols[:5]:
                st.markdown(f"#### 📦 {col}")
                fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
                
                Q1, Q2, Q3 = df[col].quantile(0.25), df[col].quantile(0.50), df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                outliers = len(df[(df[col] < lower) | (df[col] > upper)])
                
                st.metric("عدد القيم المتطرفة", outliers)
                st.markdown("---")
        else:
            st.info("لا توجد أعمدة رقمية")

elif st.session_state.page == "final_dashboard":
    st.markdown("## 💾 تصدير التقرير النهائي الشامل")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
        st.stop()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    # فلترة ذكية للتقرير أيضاً
    valid_categorical = []
    bad_keywords = ['sku', 'id', 'code', 'date', 'time', 'timestamp', 'رقم', 'كود', 'تاريخ', 'link', 'url', 'name']
    for col in categorical_cols:
        n_unique = df[col].nunique()
        if not any(kw in str(col).lower() for kw in bad_keywords) and n_unique <= len(df) * 0.5:
            valid_categorical.append(col)
    
    if st.button("📥 إنشاء وتحميل التقرير الشامل (HTML)", type="primary", key="btn_export_report"):
        html_parts = []
        html_parts.append(f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
        <meta charset="UTF-8">
        <title>تقرير التحليل الشامل - Smart Analytics Pro</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: #f8f9fa; color: #2d3748; margin: 0; padding: 0; direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
            .container {{ max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
            .section {{ background: white; padding: 35px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; page-break-inside: avoid; }}
            .section h2 {{ color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 15px; margin-top: 0; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border-radius: 8px; overflow: hidden; }}
            .data-table th {{ background: #667eea; color: white; padding: 12px; text-align: right; }}
            .data-table td {{ padding: 10px; border-bottom: 1px solid #edf2f7; text-align: right; }}
            .data-table tr:nth-child(even) {{ background: #f7fafc; }}
            .chart-box {{ margin: 25px 0; padding: 20px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; min-height: 350px; page-break-inside: avoid; }}
            .footer {{ text-align: center; padding: 40px; color: #718096; background: white; margin-top: 40px; border-top: 1px solid #e2e8f0; }}
            @media print {{ .section, .chart-box {{ page-break-inside: avoid; }} }}
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
        if valid_categorical:
            for col in valid_categorical[:5]:
                freq = df[col].value_counts().head(10).reset_index()
                freq.columns = ['القيمة', 'التكرار']
                freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(2)
                html_parts.append(f"<h3>{col}</h3>")
                # استخدام to_html مع classes لضمان ظهور جدول HTML حقيقي وليس Markdown
                html_parts.append(freq.to_html(index=False, classes='data-table'))
        else:
            html_parts.append("<p>لا توجد أعمدة فئوية مناسبة للعرض.</p>")
        html_parts.append("</div>")
        
        # التحليل الإحصائي
        html_parts.append("<div class='section'><h2>📊 التحليل الإحصائي الشامل</h2>")
        for col in numeric_cols[:5]:
            data = df[col].dropna()
            skew_val = data.skew()
            kurt_val = data.kurtosis()
            skew_interp = "متماثل" if abs(skew_val) < 0.5 else ("منحرف" if skew_val > 0 else "منحرف سالب")
            kurt_interp = "مدبب" if kurt_val > 3 else "مفلطح"
            
            html_parts.append(f"""
            <h3>{col}</h3>
            <table class="data-table">
            <tr><th>المقياس</th><th>القيمة</th><th>التفسير</th></tr>
            <tr><td>المتوسط</td><td>{data.mean():.4f}</td><td>معدل القيم</td></tr>
            <tr><td>الوسيط</td><td>{data.median():.4f}</td><td>القيمة الوسطى</td></tr>
            <tr><td>الانحراف المعياري</td><td>{data.std():.4f}</td><td>مقياس التشتت</td></tr>
            <tr><td>Q1</td><td>{data.quantile(0.25):.4f}</td><td>25% من البيانات أقل من هذه القيمة</td></tr>
            <tr><td>Q3</td><td>{data.quantile(0.75):.4f}</td><td>75% من البيانات أقل من هذه القيمة</td></tr>
            <tr><td>الانحناء (Skewness)</td><td>{skew_val:.4f}</td><td>{skew_interp}</td></tr>
            <tr><td>التفلطح (Kurtosis)</td><td>{kurt_val:.4f}</td><td>{kurt_interp}</td></tr>
            </table>
            """)
        html_parts.append("</div>")
        
        html_parts.append("""
        <div class="footer">
        <p>تم إنشاء هذا التقرير تلقائياً بواسطة <b>Smart Analytics Pro</b></p>
        <p>© 2026 جميع الحقوق محفوظة</p>
        </div>
        </div>
        </body>
        </html>
        """)
        
        final_html = "".join(html_parts)
        st.download_button("📥 تحميل التقرير (HTML)", data=final_html, file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", mime="text/html")
        st.success("✅ تم إنشاء التقرير بنجاح! يمكنك فتحه في أي متصفح وطباعته كـ PDF (Ctrl+P).")

# ==================== Footer ====================
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
