import streamlit as st
import pandas as pd
import numpy as np
import chardet
import io
from datetime import datetime
from supabase import create_client, Client

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
        st.info(" **بيانات تجريبية:**\n- المستخدم: `admin`\n- كلمة المرور: `Smart@2026`")
        st.stop()

# ==================== المنصة الرئيسية ====================
current_user = st.session_state.current_user

# ==================== دوال المرحلة 1: رفع البيانات ====================
def detect_encoding(file_bytes):
    """كشف تشفير الملف تلقائياً"""
    result = chardet.detect(file_bytes[:10000])  # فحص أول 10KB فقط للسرعة
    return result.get('encoding', 'utf-8')

def load_data(file):
    """تحميل البيانات مع دعم صيغ متعددة"""
    try:
        file_extension = file.name.split('.')[-1].lower()
        file_bytes = file.read()
        
        if file_extension == 'csv':
            encoding = detect_encoding(file_bytes)
            return pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
        elif file_extension in ['xlsx', 'xls']:
            return pd.read_excel(io.BytesIO(file_bytes))
        elif file_extension == 'json':
            return pd.read_json(io.BytesIO(file_bytes))
        elif file_extension == 'parquet':
            return pd.read_parquet(io.BytesIO(file_bytes))
        else:
            return None, f"صيغة غير مدعومة: {file_extension}"
    except Exception as e:
        return None, f"خطأ في قراءة الملف: {str(e)}"

def validate_file(file):
    """التحقق من صحة الملف"""
    errors = []
    warnings = []
    
    # التحقق من الحجم (500MB كحد أقصى)
    file_size_mb = file.size / (1024 * 1024)
    if file_size_mb > 500:
        errors.append(f"حجم الملف كبير جداً: {file_size_mb:.2f} MB (الحد الأقصى 500 MB)")
    
    # التحقق من الصيغة
    file_extension = file.name.split('.')[-1].lower()
    allowed_extensions = ['csv', 'xlsx', 'xls', 'json', 'parquet']
    if file_extension not in allowed_extensions:
        errors.append(f"صيغة الملف غير مدعومة: {file_extension}")
    
    return errors, warnings, file_size_mb

with st.sidebar:
    if current_user:
        st.markdown(f"""<div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 16px; text-align: center; margin: 10px 0;">
            <div style="font-size: 50px; margin-bottom: 10px;">👤</div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📍 التنقل السريع")
    menu = {"home": "🏠 الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "readiness": "✅ جاهزية البيانات", "cleaning": " تنظيف البيانات", "summary": "📋 ملخص البيانات", "eda": "📊 التحليل الاستكشافي", "diagnostic": " التحليل التشخيصي", "predictive": "🔮 التحليل التنبؤي", "prescriptive": "💡 التحليل الإرشادي", "ai_chat": "🤖 المساعد الذكي", "export": "💾 التصدير"}
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

# ==============================================================================
# ==================== المرحلة 1: نظام رفع البيانات ===========================
# ==============================================================================
elif st.session_state.page == "data_import":
    st.markdown("## 📥 المرحلة 1: استيراد البيانات")
    st.markdown("---")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid #4299e1;">
        <h4 style="color: #2b6cb0; margin: 0;"> الصيغ المدعومة:</h4>
        <ul style="margin: 10px 0 0 20px; color: #2c5282;">
            <li>📄 CSV (.csv)</li>
            <li>📊 Excel (.xlsx, .xls)</li>
            <li>📋 JSON (.json)</li>
            <li>📦 Parquet (.parquet)</li>
        </ul>
        <p style="margin: 10px 0 0 0; color: #2c5282;"><strong>⚠️ الحد الأقصى للحجم:</strong> 500 MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "📁 اختر ملف البيانات",
        type=['csv', 'xlsx', 'xls', 'json', 'parquet'],
        help="اسحب الملف هنا أو انقر للاختيار"
    )
    
    if uploaded_file is not None:
        st.markdown("---")
        st.markdown("### 🔍 التحقق من الملف")
        
        # التحقق من صحة الملف
        errors, warnings, file_size_mb = validate_file(uploaded_file)
        
        # عرض التحذيرات
        if warnings:
            for warning in warnings:
                st.warning(f"⚠️ {warning}")
        
        # عرض الأخطاء
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
            st.stop()
        
        st.success(f"✅ الملف صالح - الحجم: {file_size_mb:.2f} MB")
        
        st.markdown("---")
        st.markdown("### 📊 تحميل البيانات")
        
        with st.spinner("جاري تحميل البيانات..."):
            result = load_data(uploaded_file)
            
            if isinstance(result, tuple):
                df, error_msg = result
                if df is None:
                    st.error(f"❌ {error_msg}")
                    st.stop()
            else:
                df = result
        
        # حفظ البيانات في Session State
        st.session_state.df = df
        st.session_state.df_clean = None
        
        st.success(f"✅ تم تحميل البيانات بنجاح!")
        
        st.markdown("---")
        st.markdown("### 📈 معلومات البيانات")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("عدد الصفوف", f"{len(df):,}")
        with col2: st.metric("عدد الأعمدة", len(df.columns))
        with col3: st.metric("حجم الملف", f"{file_size_mb:.2f} MB")
        with col4: 
            numeric_count = df.select_dtypes(include=[np.number]).shape[1]
            st.metric("الأعمدة الرقمية", numeric_count)
        
        st.markdown("---")
        st.markdown("### 👁️ معاينة البيانات")
        
        # خيارات العرض
        view_option = st.radio(
            "اختر طريقة العرض:",
            ["أول 10 صفوف", "آخر 10 صفوف", "عينة عشوائية (20 صف)"],
            horizontal=True
        )
        
        if view_option == "أول 10 صفوف":
            st.dataframe(df.head(10), use_container_width=True)
        elif view_option == "آخر 10 صفوف":
            st.dataframe(df.tail(10), use_container_width=True)
        else:
            st.dataframe(df.sample(min(20, len(df))), use_container_width=True)
        
        st.markdown("---")
        st.markdown("###  معلومات الأعمدة")
        
        col_info = []
        for col in df.columns:
            col_info.append({
                'اسم العمود': col,
                'نوع البيانات': str(df[col].dtype),
                'القيم الفريدة': df[col].nunique(),
                'القيم المفقودة': int(df[col].isnull().sum()),
                'نسبة المفقود %': round((df[col].isnull().sum() / len(df)) * 100, 2)
            })
        
        st.dataframe(pd.DataFrame(col_info), use_container_width=True)
        
        st.markdown("---")
        st.success("✅ البيانات جاهزة! يمكنك الآن الانتقال إلى المرحلة التالية: **فحص جاهزية البيانات**")
        
        if st.button("➡️ الانتقال إلى المرحلة التالية", type="primary", use_container_width=True):
            st.session_state.page = "readiness"
            st.rerun()

elif st.session_state.page == "readiness":
    st.markdown("## ✅ فحص جاهزية البيانات للتحليل"); st.markdown("---")
    if st.session_state.df is None: st.warning("⚠️ يرجى رفع البيانات أولاً"); st.stop()
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
            status = "✅ جاهزة للتحليل" if score >= 80 else ("️ تحتاج تنظيف بسيط" if score >= 50 else "❌ تحتاج تنظيف شامل")
            st.markdown(f"""<div class="readiness-box" style="text-align: center;"><div style="font-size: 18px; color: #718096; margin-bottom: 10px;">جاهزية البيانات</div><div class="{score_class}">{score:.0f}%</div><div style="margin-top: 10px; font-size: 16px;">{status}</div></div>""", unsafe_allow_html=True)
        with col2: st.markdown(f"""<div class="readiness-box"><div style="font-size: 14px; color: #718096;">حجم البيانات</div><div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{total_rows:,} صف × {total_cols} عمود</div></div>""", unsafe_allow_html=True)
        with col3: st.markdown(f"""<div class="readiness-box"><div style="font-size: 14px; color: #718096;">أنواع الأعمدة</div><div style="font-size: 16px; margin-top: 5px;"> رقمية: {len(numeric_cols)}</div><div style="font-size: 16px;"> نصية: {len(categorical_cols)}</div></div>""", unsafe_allow_html=True)
        st.markdown("---"); st.markdown("### 🔍 التشخيص التفصيلي لكل عمود")
        readiness_data = [{'العمود': col, 'النوع': str(df[col].dtype), 'القيم المفقودة': int(df[col].isnull().sum()), 'نسبة المفقود': f"{(df[col].isnull().sum()/total_rows)*100:.1f}%" if total_rows>0 else "0%", 'القيم الفريدة': int(df[col].nunique()), 'الحالة': "✅" if df[col].isnull().sum()==0 else ("️" if (df[col].isnull().sum()/total_rows)*100 < 5 else "❌")} for col in df.columns]
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
    if st.session_state.df is None: st.warning("⚠️ يرجى رفع البيانات أولاً"); st.stop()
    else:
        df = st.session_state.df.copy()
        st.markdown("### 📊 حالة البيانات قبل التنظيف")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("الصفوف", len(df))
        with col2: st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
        with col3: st.metric("التكرارات", int(df.duplicated().sum()))
        st.markdown("---"); st.markdown("### 🛠️ خيارات التنظيف")
        missing_option = st.selectbox("1️⃣ معالجة القيم المفقودة", ["حذف الصفوف التي تحتوي على قيم مفقودة", "تعويض القيم المفقودة بالمتوسط (للأعمدة الرقمية)", "تعويض القيم المفقودة بالوسيط (للأعمدة الرقمية)", "لا تفعل شيئاً"], key="missing_option")
        dup_option = st.selectbox("2️ معالجة التكرارات", ["حذف التكرارات (الاحتفاظ بالأول)", "لا تفعل شيئاً"], key="dup_option")
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
    if df is None: st.warning("⚠️ لا توجد بيانات"); st.stop()
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

elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)"); st.markdown("---")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ يرجى رفع البيانات أولاً"); st.stop()
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        bad_keywords = ['sku', 'id', 'code', 'date', 'time', 'timestamp', 'رقم', 'كود', 'تاريخ']
        valid_categorical = []
        for col in df.select_dtypes(include=['object', 'category']).columns:
            n_unique = df[col].nunique()
            if any(kw in col.lower() for kw in bad_keywords) or (n_unique > len(df) * 0.5):
                continue
            valid_categorical.append(col)
        st.markdown("### 📥 تصدير التقارير")
        if st.button("📥 تصدير تقرير EDA شامل واحترافي (HTML)", type="primary", key="btn_export_comprehensive_eda"):
            st.info("🔧 سيتم تطوير هذه الميزة في المرحلة 6: نظام توليد التقارير")
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs([" الجداول التكرارية", "📈 التصور البياني", "📊 المقاييس الإحصائية", "📦 Box Plots"])
        with tab1:
            st.markdown("### 📋 الجداول التكرارية")
            if valid_categorical:
                selected_cat = st.selectbox("اختر المتغير الفئوي", valid_categorical, key="eda_freq_cat")
                freq_table = df[selected_cat].value_counts().reset_index()
                freq_table.columns = ['القيمة', 'التكرار']
                freq_table['النسبة المئوية %'] = (freq_table['التكرار'] / len(df) * 100).round(2)
                st.dataframe(freq_table.head(20), use_container_width=True)
            else:
                st.info("لا توجد متغيرات فئوية صالحة.")
        with tab2:
            st.markdown("### 📈 التصور البياني")
            viz_type = st.selectbox("اختر نوع التصور", ["Histogram", "Bar Chart", "Heatmap"], key="eda_viz_type")
            if viz_type == "Histogram" and numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols, key="eda_hist_col")
                st.info(f"🔧 سيتم تطوير التصور البياني في المرحلة 4: EDA Engine")
            elif viz_type == "Bar Chart" and valid_categorical:
                col = st.selectbox("اختر العمود", valid_categorical, key="eda_bar_col")
                st.info(f"🔧 سيتم تطوير التصور البياني في المرحلة 4: EDA Engine")
            elif viz_type == "Heatmap" and len(numeric_cols) >= 2:
                st.info(f"🔧 سيتم تطوير التصور البياني في المرحلة 4: EDA Engine")
        with tab3:
            st.markdown("### 📊 المقاييس الإحصائية")
            if numeric_cols:
                selected_stat_col = st.selectbox("اختر العمود الرقمي", numeric_cols, key="eda_stat_col")
                cd = df[selected_stat_col].dropna()
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("المتوسط", f"{cd.mean():.2f}")
                with c2: st.metric("الوسيط", f"{cd.median():.2f}")
                with c3: st.metric("الانحراف المعياري", f"{cd.std():.2f}")
                with c4: st.metric("التباين", f"{cd.var():.2f}")
            else:
                st.info("لا توجد متغيرات رقمية")
        with tab4:
            st.markdown("### 📦 Box Plots")
            if numeric_cols:
                selected_box = st.selectbox("اختر العمود", numeric_cols, key="eda_box_col")
                st.info(f" سيتم تطوير Box Plots في المرحلة 4: EDA Engine")
            else:
                st.info("لا توجد متغيرات رقمية")

elif st.session_state.page == "diagnostic":
    st.markdown("## 🔍 التحليل التشخيصي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً"); st.stop()
    else:
        st.info("🔧 سيتم تطوير هذه المرحلة لاحقاً")

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً"); st.stop()
    else:
        st.info("🔧 سيتم تطوير هذه المرحلة لاحقاً")

elif st.session_state.page == "prescriptive":
    st.markdown("## 💡 التحليل الإرشادي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً"); st.stop()
    else:
        st.info("🔧 سيتم تطوير هذه المرحلة لاحقاً")

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("⚠️ ارفع بيانات أولاً"); st.stop()
    else:
        st.info("🔧 سيتم تطوير هذه المرحلة لاحقاً")

elif st.session_state.page == "export":
    st.markdown("## 💾 التصدير")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("️ ارفع بيانات أولاً"); st.stop()
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(" CSV", csv, "data.csv", "text/csv", key="dl_csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "data.xlsx", key="dl_excel")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
