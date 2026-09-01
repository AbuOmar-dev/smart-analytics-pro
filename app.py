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
import json
import os

# استيراد الملفات المحلية
import config

# إعدادات الصفحة
st.set_page_config(
    page_title=config.APP_CONFIG["app_name"],
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling احترافي
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
    }
    
    h1, h2, h3 {
        color: #1a202c;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #2c5282;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }
    
    .info-box {
        background-color: #ebf8ff;
        border-left: 4px solid #3182ce;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #f0fff4;
        border-left: 4px solid #38a169;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .warning-box {
        background-color: #fffaf0;
        border-left: 4px solid #dd6b20;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .login-container {
        max-width: 450px;
        margin: 80px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-header h1 {
        color: #2d3748;
        font-size: 32px;
        margin-bottom: 10px;
    }
    
    .login-header p {
        color: #718096;
        font-size: 16px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== نظام إدارة المستخدمين ====================

# المستخدمين الافتراضيين
DEFAULT_USERS = {
    'admin': {
        'password': 'Smart@2026',
        'name': 'مدير النظام',
        'email': 'admin@smartanalytics.com',
        'role': 'admin',
        'plan': 'Enterprise'
    },
    'demo_user': {
        'password': 'Demo@2026',
        'name': 'مستخدم تجريبي',
        'email': 'demo@smartanalytics.com',
        'role': 'user',
        'plan': 'Pro'
    }
}

def load_users():
    """تحميل قائمة المستخدمين من الملف"""
    try:
        # محاولة تحميل المستخدمين من GitHub
        import requests
        url = "https://raw.githubusercontent.com/AbuOmar-dev/smart-analytics-pro/main/users.json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            users = {}
            for user in data.get('users', []):
                users[user['username']] = {
                    'password': user['password'],
                    'name': user['name'],
                    'email': user['email'],
                    'plan': user.get('plan', 'Free'),
                    'role': user.get('role', 'user')
                }
            # دمج مع المستخدمين الافتراضيين
            users.update(DEFAULT_USERS)
            return users
    except:
        pass
    
    # لو فشل التحميل، استخدم المستخدمين الافتراضيين
    return DEFAULT_USERS.copy()

def register_user(username, password, name, email, plan='Free'):
    """تسجيل مستخدم جديد"""
    users = load_users()
    
    if username in users:
        return False, "اسم المستخدم موجود بالفعل"
    
    # إضافة المستخدم الجديد
    users[username] = {
        'password': password,
        'name': name,
        'email': email,
        'plan': plan,
        'role': 'user'
    }
    
    return True, "تم التسجيل بنجاح!"

# تهيئة الحالة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "df" not in st.session_state:
    st.session_state.df = None

# ==================== صفحة تسجيل الدخول والتسجيل ====================

if not st.session_state.logged_in:
    st.markdown("""
    <div class="login-container">
        <div class="login-header">
            <div style="font-size: 64px; margin-bottom: 20px;"></div>
            <h1>Smart Analytics Pro</h1>
            <p>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # التبديل بين تسجيل الدخول والتسجيل
    if st.session_state.show_register:
        st.markdown("### 📝 إنشاء حساب جديد")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_username = st.text_input("👤 اسم المستخدم", key="reg_username")
            new_name = st.text_input("👤 الاسم الكامل", key="reg_name")
            new_email = st.text_input("📧 البريد الإلكتروني", key="reg_email")
            new_password = st.text_input("🔑 كلمة المرور", type="password", key="reg_password")
            confirm_password = st.text_input("🔑 تأكيد كلمة المرور", type="password", key="reg_confirm")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ تسجيل الحساب", use_container_width=True, type="primary", key="btn_register"):
                    if not new_username or not new_password or not new_name or not new_email:
                        st.error("❌ يرجى ملء جميع الحقول")
                    elif new_password != confirm_password:
                        st.error("❌ كلمات المرور غير متطابقة")
                    elif len(new_password) < 6:
                        st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    else:
                        success, message = register_user(new_username, new_password, new_name, new_email)
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            with col_btn2:
                if st.button("🔐 لديك حساب؟ دخول", use_container_width=True, type="secondary", key="btn_go_login"):
                    st.session_state.show_register = False
                    st.rerun()
    else:
        st.markdown("### 🔐 تسجيل الدخول")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم", key="login_username")
            password = st.text_input("🔑 كلمة المرور", type="password", placeholder="أدخل كلمة المرور", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚪 دخول", use_container_width=True, type="primary", key="btn_login"):
                    users = load_users()
                    if username in users and users[username]['password'] == password:
                        st.session_state.logged_in = True
                        st.session_state.current_user = {
                            'username': username,
                            'name': users[username]['name'],
                            'email': users[username]['email'],
                            'role': users[username]['role'],
                            'plan': users[username]['plan']
                        }
                        st.success(f"✅ مرحباً {users[username]['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            
            with col_btn2:
                st.markdown("")
            
            st.markdown("---")
            if st.button("📝 ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"):
                st.session_state.show_register = True
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #718096; font-size: 12px;">
            <p><strong>بيانات تجريبية:</strong></p>
            <p>المستخدم: <code>admin</code> | كلمة المرور: <code>Smart@2026</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()

# ==================== المنصة الرئيسية (بعد تسجيل الدخول) ====================

current_user = st.session_state.current_user

def set_language(lang):
    st.session_state.lang = lang

def navigate_to(page):
    st.session_state.page = page

def load_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            st.error("صيغة الملف غير مدعومة. يرجى استخدام CSV أو Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
        return None

def generate_local_ai_insights(df, lang):
    insights = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            pct = round((count / len(df)) * 100, 1)
            if pct > 5:
                insights.append(f"⚠️ العمود {col} يحتوي على {count} قيمة مفقودة ({pct}%)")

    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr().abs()
        np.fill_diagonal(corr_matrix.values, 0)
        max_corr = corr_matrix.unstack().dropna().sort_values(ascending=False)
        if len(max_corr) > 0:
            top_corr = max_corr.index[0]
            val = round(max_corr.iloc[0], 2)
            if val > 0.7:
                insights.append(f"🔗 ارتباط قوي بين {top_corr[0]} و {top_corr[1]} ({val})")

    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        if df[cat_col].nunique() < 20:
            top_cat = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(1)
            insights.append(f"🏆 {top_cat.index[0]} هو الأعلى أداءً بـ {round(top_cat.values[0], 2)}")

    if not insights:
        return ["✅ البيانات تبدو نظيفة وجيدة للتحليل المتقدم."]
    return insights

# ==================== الشريط الجانبي ====================

with st.sidebar:
    # معلومات المستخدم - مع فحص إذا كان current_user موجود
    if current_user is not None:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 15px; border-radius: 10px; margin: 10px 0;
                    text-align: center;">
            <div style="font-size: 14px;">👤 {current_user.get('name', 'مستخدم')}</div>
            <div style="font-size: 12px; margin-top: 5px;">⭐ {current_user.get('plan', 'Free')} Plan</div>
            <div style="font-size: 11px; margin-top: 3px; opacity: 0.9;">{current_user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #e2e8f0;
                    color: #4a5568; padding: 15px; border-radius: 10px; margin: 10px 0;
                    text-align: center;">
            <div style="font-size: 14px;">👤 غير مسجل الدخول</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # اختيار اللغة
    st.markdown("###  اللغة / Language")
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("🇪🇬 عربي", use_container_width=True, type="primary" if st.session_state.lang == "ar" else "secondary", key="btn_ar"):
            set_language("ar")
            st.rerun()
    with lang_col2:
        if st.button("🇬🇧 English", use_container_width=True, type="primary" if st.session_state.lang == "en" else "secondary", key="btn_en"):
            set_language("en")
            st.rerun()

    st.markdown("---")
    
    # قائمة التنقل
    st.markdown("### 📍 التنقل السريع")
    menu = {
        "home": " الرئيسية",
        "pricing": "💰 الأسعار",
        "data_import": "📥 استيراد البيانات",
        "eda": " التحليل الاستكشافي",
        "diagnostic": "🔍 التحليل التشخيصي",
        "predictive": "🔮 التحليل التنبؤي",
        "prescriptive": "💡 التحليل الإرشادي",
        "ai_chat": "🤖 المساعد الذكي",
        "export": "💾 التصدير"
    }
    
    for key, label in menu.items():
        if st.button(label, use_container_width=True, type="primary" if st.session_state.page == key else "secondary", key=f"nav_{key}"):
            navigate_to(key)
            st.rerun()
    
    st.markdown("---")
    
    # زر تسجيل الخروج
    if st.button("🚪 تسجيل الخروج", use_container_width=True, type="secondary", key="btn_logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.page = "home"
        st.session_state.show_register = False
        st.rerun()
    
    if st.session_state.df is not None:
        st.markdown(f"""
        <div class="success-box">
            <div style="font-size: 12px; color: #2f855a;">
                ✅ البيانات محملة: {len(st.session_state.df)} صف
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== الصفحات ====================

if st.session_state.page == "home":
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="font-size: 48px; color: #2d3748; margin-bottom: 20px;">
            Smart Analytics Pro
        </h1>
        <p style="font-size: 20px; color: #4a5568; margin-bottom: 30px;">
            منصة احترافية لتحليل البيانات والذكاء الاصطناعي
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="info-box" style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">📊</div>
            <h3>التحليل الاستكشافي</h3>
            <p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-box" style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">🔍</div>
            <h3>التحليل التشخيصي</h3>
            <p>اكتشف الأنماط والشذوذ في بياناتك</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="warning-box" style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">🔮</div>
            <h3>التحليل التنبؤي</h3>
            <p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="info-box" style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">💡</div>
            <h3>التحليل الإرشادي</h3>
            <p>توصيات عملية لزيادة العائد على الاستثمار</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if current_user:
        st.info(f"""
        ### مرحباً {current_user.get('name', 'مستخدم')}! 👋
        
        **ابدأ الآن في 3 خطوات بسيطة:**
        1. 📥 اضغط على "استيراد البيانات" من القائمة الجانبية
        2. 📊 ارفع ملف CSV أو Excel
        3. 🎯 استكشف التحليلات والرؤى الذكية
        
        *💡 المنصة تعمل محلياً 100% بدون الحاجة لأي API Keys*
        """)

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    st.markdown("اختر الباقة المناسبة لاحتياجاتك")
    
    col1, col2, col3 = st.columns(3)
    
    plans = [
        {
            "name": " Free",
            "price": "$0",
            "period": "/شهر",
            "features": ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط", "تصدير PDF بعلامة مائية"],
            "color": "#718096",
            "button_type": "secondary"
        },
        {
            "name": "⭐ Pro",
            "price": "$19",
            "period": "/شهر",
            "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل أنواع التحليلات الأربعة", "تصدير بكل الصيغ", "محرك الرؤى الذكي", "دعم فني بأولوية"],
            "color": "#3182ce",
            "button_type": "primary",
            "popular": True
        },
        {
            "name": " Enterprise",
            "price": "$99",
            "period": "/شهر",
            "features": ["كل مميزات Pro", "تخزين غير محدود", "White-Label كامل", "API Access", "مدير حساب مخصص", "SLA مضمون 99.9%"],
            "color": "#805ad5",
            "button_type": "secondary"
        }
    ]
    
    for i, plan in enumerate(plans):
        with [col1, col2, col3][i]:
            if plan.get("popular"):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
                            box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
                    <div style="text-align: center; font-size: 14px; margin-bottom: 10px;">
                        🌟 الأكثر شعبية
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<h2 style='color: white; text-align: center; margin: 0;'>{plan['name']}</h2>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color: white; text-align: center; margin: 10px 0;'>{plan['price']}<span style='font-size: 16px;'>{plan['period']}</span></h1>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: {plan['color']}; text-align: center; margin: 0;">{plan['name']}</h2>
                    <h1 style="color: {plan['color']}; text-align: center; margin: 10px 0;">{plan['price']}<span style="font-size: 16px;'>{plan['period']}</span></h1>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### المميزات:")
            for feature in plan["features"]:
                st.markdown(f"✅ {feature}")
            
            # إضافة key فريد لكل زر
            st.button("اشترك الآن", use_container_width=True, type=plan["button_type"], key=f"subscribe_{i}")

elif st.session_state.page == "data_import":
    st.markdown("## 📥 استيراد البيانات")
    st.markdown("ارفع ملف CSV أو Excel لبدء التحليل")
    
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'], 
                                     help="يمكنك رفع ملفات حتى 500MB", key="file_uploader")
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ تم رفع البيانات بنجاح! عدد الصفوف: {len(df)}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("عدد الصفوف", f"{len(df):,}")
            with col2:
                st.metric("عدد الأعمدة", len(df.columns))
            with col3:
                st.metric("حجم الملف", f"{uploaded_file.size / 1024:.2f} KB")
            with col4:
                numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
                st.metric("الأعمدة الرقمية", numeric_cols)
            
            st.markdown("### معاينة البيانات")
            st.dataframe(df.head(10), use_container_width=True)
            
            with st.expander(" معلومات عن الأعمدة"):
                col_info = pd.DataFrame({
                    'العمود': df.columns.tolist(),
                    'النوع': [str(dtype) for dtype in df.dtypes],
                    'القيم الفريدة': [df[col].nunique() for col in df.columns],
                    'القيم المفقودة': [df[col].isnull().sum() for col in df.columns]
                })
                st.dataframe(col_info, use_container_width=True)

elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي (EDA)")
    
    if st.session_state.df is None:
        st.warning("️ يرجى رفع البيانات أولاً من صفحة استيراد البيانات")
    else:
        df = st.session_state.df
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**إجمالي الصفوف:** {len(df):,}")
        with col2:
            st.info(f"**إجمالي الأعمدة:** {len(df.columns)}")
        with col3:
            missing_total = df.isnull().sum().sum()
            st.info(f"**القيم المفقودة:** {missing_total}")
        
        st.markdown("---")
        
        st.markdown("### 📈 الملخص الإحصائي الشامل")
        with st.expander("عرض الملخص الإحصائي", expanded=True):
            st.dataframe(df.describe(), use_container_width=True)
        
        st.markdown("### 🔍 تحليل القيم المفقودة")
        missing_data = df.isnull().sum().reset_index()
        missing_data.columns = ['Column', 'Missing Count']
        missing_data = missing_data[missing_data['Missing Count'] > 0]
        
        if not missing_data.empty:
            fig = px.bar(missing_data, x='Column', y='Missing Count', 
                        title="القيم المفقودة لكل عمود", 
                        color='Missing Count',
                        color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ ممتاز! لا توجد قيم مفقودة في البيانات.")
        
        st.markdown("### 🔗 مصفوفة الارتباط")
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr = numeric_df.corr()
            fig_heatmap = px.imshow(corr, text_auto=".2f", aspect="auto", 
                                   color_continuous_scale="RdBu_r",
                                   title="مصفوفة الارتباط بين المتغيرات الرقمية")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("لا توجد أعمدة رقمية كافية لرسم مصفوفة الارتباط.")

elif st.session_state.page == "diagnostic":
    st.markdown("## 🔍 التحليل التشخيصي")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        st.markdown("### 🔍 كشف الشذوذ (Anomaly Detection)")
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            target_col = st.selectbox("اختر العمود الرقمي للفحص", numeric_cols, key="diag_target")
            threshold = st.slider("حد الشذوذ (Z-Score Threshold)", 2.0, 4.0, 3.0,
                                 help="القيم الأقل من -threshold أو الأكبر من +threshold تعتبر شاذة",
                                 key="diag_threshold")
            
            if st.button("🔍 تشخيص البيانات", type="primary", key="btn_diagnose"):
                mean = np.mean(st.session_state.df[target_col])
                std = np.std(st.session_state.df[target_col])
                z_scores = np.abs((st.session_state.df[target_col] - mean) / std)
                
                st.session_state.df['Is_Anomaly'] = z_scores > threshold
                anomalies = st.session_state.df[st.session_state.df['Is_Anomaly']]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("إجمالي السجلات", len(st.session_state.df))
                with col2:
                    st.metric("حالات الشذوذ", len(anomalies))
                with col3:
                    pct = (len(anomalies)/len(st.session_state.df))*100
                    st.metric("نسبة الشذوذ", f"{pct:.2f}%")
                
                if len(anomalies) > 0:
                    st.markdown("### 📋 عينة من حالات الشذوذ:")
                    st.dataframe(anomalies.head(10), use_container_width=True)
                    
                    fig = px.scatter(st.session_state.df, 
                                    x=range(len(st.session_state.df)), 
                                    y=target_col,
                                    color='Is_Anomaly',
                                    title=f'توزيع القيم مع تحديد الشذوذ - {target_col}',
                                    color_discrete_map={True: 'red', False: 'blue'})
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("لا توجد أعمدة رقمية للتحليل.")

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        st.info(" يتم استخدام نموذج Linear Regression للتنبؤ")
        
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                target = st.selectbox("اختر العمود المراد التنبؤ به (Target)", numeric_cols, key="pred_target")
            with col2:
                feature = st.selectbox("اختر عمود الميزة (Feature)", [c for c in numeric_cols if c != target], key="pred_feature")
            
            if st.button("🚀 بناء النموذج والتنبؤ", type="primary", key="btn_predict"):
                X = st.session_state.df[[feature]].values
                y = st.session_state.df[target].values
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                model = LinearRegression()
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                r2 = r2_score(y_test, predictions)
                mse = mean_squared_error(y_test, predictions)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("دقة النموذج (R² Score)", f"{r2:.3f}")
                with col2:
                    st.metric("خطأ التربيعي (MSE)", f"{mse:.3f}")
                
                st.success(f"**معادلة الانحدار:** {target} = {model.coef_[0]:.3f} × {feature} + {model.intercept_:.3f}")
                
                fig = px.scatter(x=y_test, y=predictions, 
                                labels={'x': 'القيم الفعلية', 'y': 'القيم المتوقعة'}, 
                                title="القيم الفعلية مقابل المتوقعة",
                                color_discrete_sequence=['#3182ce'])
                fig.add_shape(type="line", line=dict(dash='dash', color='red'), 
                             x0=min(y_test), y0=min(y_test), x1=max(y_test), y1=max(y_test))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("تحتاج إلى عمودين رقميين على الأقل لإجراء التحليل التنبؤي.")

elif st.session_state.page == "prescriptive":
    st.markdown("## 💡 التحليل الإرشادي")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        st.markdown("###  التوصيات المبنية على البيانات")
        
        with st.spinner("🤖 جاري تحليل البيانات واستخراج الرؤى..."):
            insights = generate_local_ai_insights(st.session_state.df, st.session_state.lang)
            
            for i, insight in enumerate(insights, 1):
                if "⚠️" in insight:
                    st.warning(insight)
                elif "🔗" in insight:
                    st.info(insight)
                elif "" in insight:
                    st.success(insight)
                else:
                    st.markdown(f"""
                    <div class="info-box">
                        {insight}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📋 خطة العمل المقترحة")
        
        st.markdown("""
        <div class="success-box">
            <h4>الخطوات العملية:</h4>
            <ol>
                <li><strong>معالجة البيانات:</strong> ابدأ بتنظيف القيم المفقودة التي تم تحديدها في التحليل الاستكشافي</li>
                <li><strong>التحسين:</strong> ركز على الفئات ذات الأداء الأعلى لتعزيز العائد (ROI)</li>
                <li><strong>المراقبة:</strong> راقب حالات الشذوذ التي تم اكتشافها بشكل دوري</li>
                <li><strong>التنفيذ:</strong> طبق التوصيات وقيّم النتائج</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    st.markdown("اسأل أسئلة عملية عن بياناتك")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        st.markdown(" **أمثلة على الأسئلة:**")
        st.markdown("- كم عدد الصفوف والأعمدة؟")
        st.markdown("- ما هي الأعمدة المتاحة؟")
        st.markdown("- ما هو متوسط القيم الرقمية؟")
        st.markdown("- كم عدد القيم المفقودة؟")
        
        prompt = st.text_input("اكتب سؤالك هنا:", 
                              placeholder="مثال: ما هو متوسط المبيعات؟",
                              label_visibility="collapsed",
                              key="chat_prompt")
        
        if prompt:
            with st.spinner(" جاري التحليل..."):
                response = ""
                prompt_lower = prompt.lower()
                
                if "عدد" in prompt_lower or "rows" in prompt_lower or "shape" in prompt_lower:
                    response = f" يحتوي جدول البيانات على **{len(st.session_state.df)} صف** و **{len(st.session_state.df.columns)} عمود**."
                
                elif "أعمدة" in prompt_lower or "columns" in prompt_lower:
                    cols_list = ", ".join(st.session_state.df.columns.tolist())
                    response = f"📋 الأعمدة المتاحة هي:\n\n{cols_list}"
                
                elif "متوسط" in prompt_lower or "mean" in prompt_lower or "average" in prompt_lower:
                    num_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
                    if num_cols:
                        response = "📈 متوسط القيم للأعمدة الرقمية:\n\n"
                        for col in num_cols[:5]:
                            response += f"- **{col}**: {st.session_state.df[col].mean():.2f}\n"
                    else:
                        response = "❌ لا توجد أعمدة رقمية لحساب المتوسط."
                
                elif "فقد" in prompt_lower or "missing" in prompt_lower:
                    missing = st.session_state.df.isnull().sum().sum()
                    response = f"⚠️ يوجد إجمالي **{missing} قيمة مفقودة** في كامل مجموعة البيانات."
                
                else:
                    response = "💭 عذراً، أنا أركز حالياً على الإحصائيات الوصفية الأساسية. جرب السؤال عن:\n- عدد الصفوف والأعمدة\n- الأعمدة المتاحة\n- المتوسطات\n- القيم المفقودة"
                
                st.markdown(f"""
                <div class="info-box">
                    <strong>🤖 المساعد الذكي:</strong><br>
                    {response}
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.page == "export":
    st.markdown("## 💾 مركز التصدير")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        st.markdown("### تصدير البيانات المعالجة")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 تصدير كـ CSV")
            csv = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل CSV",
                data=csv,
                file_name=f"smart_analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_download_csv"
            )
        
        with col2:
            st.markdown("#### 📊 تصدير كـ Excel")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.df.to_excel(writer, index=False, sheet_name='Data')
            st.download_button(
                label="📥 تحميل Excel",
                data=output.getvalue(),
                file_name=f"smart_analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_download_excel"
            )
        
        st.success("✅ تم تجهيز الملفات للتصدير بنجاح!")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 20px;">
    <div style="font-size: 14px;">
        Smart Analytics Pro © 2026 | Built for Business ROI
    </div>
    <div style="font-size: 12px; margin-top: 5px;">
        منصة احترافية لتحليل البيانات والذكاء الاصطناعي
    </div>
</div>
""", unsafe_allow_html=True)
