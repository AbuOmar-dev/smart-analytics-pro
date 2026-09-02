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

# ==================== CSS متقدم ====================
st.markdown("""
<style>
    /* الألوان الأساسية */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #4ade80;
        --warning-color: #fbbf24;
        --danger-color: #f87171;
        --dark-bg: #1a202c;
        --light-bg: #f7fafc;
    }
    
    /* الخلفية الرئيسية */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* العناوين */
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* الأزرار */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* البطاقات */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* الشريط الجانبي */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-right: none;
    }
    
    /* الصناديق الملونة */
    .info-box {
        background: linear-gradient(135deg, #ebf8ff 0%, #c3cfe2 100%);
        border-left: 5px solid #667eea;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .success-box {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 5px solid #48bb78;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffaf0 0%, #feebc8 100%);
        border-left: 5px solid #ed8936;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* صفحة تسجيل الدخول */
    .login-container {
        max-width: 500px;
        margin: 60px auto;
        padding: 50px 40px;
        background: white;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        animation: slideIn 0.5s ease;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .login-header h1 {
        font-size: 36px;
        margin-bottom: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* الصفحة الرئيسية */
    .hero-section {
        text-align: center;
        padding: 80px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 24px;
        margin-bottom: 40px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    
    .hero-section h1 {
        font-size: 48px;
        margin-bottom: 20px;
        color: white !important;
        -webkit-text-fill-color: white !important;
    }
    
    .hero-section p {
        font-size: 20px;
        opacity: 0.95;
    }
    
    /* البطاقات المميزة */
    .feature-card {
        background: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        margin: 10px;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 60px;
        margin-bottom: 20px;
    }
    
    /* إخفاء العناصر الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تأثيرات إضافية */
    .stAlert {
        border-radius: 12px;
        padding: 15px;
    }
    
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==================== إعدادات Supabase ====================
SUPABASE_URL = "https://llsoulwgpptlpatgivqk.supabase.co"
SUPABASE_KEY = "sb_publishable_OpzDbBV2XqSJchMJ6DqmLQ_DYyB9GVH"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    supabase = None

# ==================== تهيئة الحالة ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "df" not in st.session_state:
    st.session_state.df = None

# ==================== دوال المستخدمين ====================
def load_users():
    if supabase is None:
        return {}
    try:
        response = supabase.table("users").select("*").execute()
        users = {}
        for user in response.data:
            users[user['username']] = {
                'password': user['password'],
                'name': user['name'],
                'email': user['email'],
                'plan': user.get('plan', 'Free'),
                'role': user.get('role', 'user')
            }
        return users
    except Exception as e:
        st.error(f"خطأ: {e}")
        return {}

def register_user(username, password, name, email, plan='Free'):
    if supabase is None:
        return False, "خطأ في الاتصال"
    try:
        response = supabase.table("users").select("username").eq("username", username).execute()
        if len(response.data) > 0:
            return False, "اسم المستخدم موجود بالفعل"
        data = {
            'username': username,
            'password': password,
            'name': name,
            'email': email,
            'plan': plan,
            'role': 'user'
        }
        supabase.table("users").insert(data).execute()
        return True, "تم التسجيل بنجاح!"
    except Exception as e:
        return False, f"خطأ: {e}"

# ==================== صفحة تسجيل الدخول ====================
if not st.session_state.logged_in:
    st.markdown("""
    <div class="login-container">
        <div class="login-header">
            <div style="font-size: 80px; margin-bottom: 20px;">📊</div>
            <h1>Smart Analytics Pro</h1>
            <p style="color: #718096; font-size: 18px;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.show_register:
        st.markdown("### 📝 إنشاء حساب جديد")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_username = st.text_input("👤 اسم المستخدم", key="reg_username")
            new_name = st.text_input("👤 الاسم الكامل", key="reg_name")
            new_email = st.text_input("📧 البريد الإلكتروني", key="reg_email")
            new_password = st.text_input("🔑 كلمة المرور", type="password", key="reg_password")
            confirm_password = st.text_input("🔑 تأكيد كلمة المرور", type="password", key="reg_confirm")
            
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
            
            if st.button("🔐 لديك حساب؟ دخول", use_container_width=True, type="secondary", key="btn_go_login"):
                st.session_state.show_register = False
                st.rerun()
    else:
        st.markdown("### 🔐 تسجيل الدخول")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("👤 اسم المستخدم", key="login_user")
            password = st.text_input(" كلمة المرور", type="password", key="login_pass")
            
            if st.button("🚪 دخول", use_container_width=True, type="primary", key="btn_login"):
                users = load_users()
                if username in users and users[username]['password'] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {
                        'username': username,
                        'name': users[username]['name'],
                        'email': users[username]['email'],
                        'plan': users[username]['plan'],
                        'role': users[username]['role']
                    }
                    st.success(f"✅ مرحباً {users[username]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown("---")
        if st.button("📝 ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"):
            st.session_state.show_register = True
            st.rerun()
        
        st.info("💡 **بيانات تجريبية:**\n- المستخدم: `admin`\n- كلمة المرور: `Smart@2026`")
        st.stop()

# ==================== المنصة الرئيسية ====================
current_user = st.session_state.current_user

def load_data(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
        return None
    except:
        return None

def generate_local_ai_insights(df):
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
    if current_user:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 16px; text-align: center; margin: 10px 0;">
            <div style="font-size: 50px; margin-bottom: 10px;">👤</div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px;">{current_user['email']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📍 التنقل السريع", style="color: white; font-weight: bold; margin: 20px 0 10px 0;")
    
    menu = {
        "home": "🏠 الرئيسية",
        "pricing": "💰 الأسعار",
        "data_import": "📥 استيراد البيانات",
        "eda": "📊 التحليل الاستكشافي",
        "diagnostic": "🔍 التحليل التشخيصي",
        "predictive": "🔮 التحليل التنبؤي",
        "prescriptive": "💡 التحليل الإرشادي",
        "ai_chat": "🤖 المساعد الذكي",
        "export": "💾 التصدير"
    }
    
    for key, label in menu.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state.page = key
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🚪 تسجيل الخروج", use_container_width=True, key="btn_logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.page = "home"
        st.session_state.show_register = False
        st.rerun()
    
    if st.session_state.df is not None:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 12px; margin-top: 20px;">
            <div style="color: white; font-size: 14px;">
                ✅ البيانات محملة: {len(st.session_state.df)} صف
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== الصفحات ====================

if st.session_state.page == "home":
    st.markdown("""
    <div class="hero-section">
        <h1>Smart Analytics Pro</h1>
        <p>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>التحليل الاستكشافي</h3>
            <p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3>التحليل التشخيصي</h3>
            <p>اكتشف الأنماط والشذوذ في بياناتك</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔮</div>
            <h3>التحليل التنبؤي</h3>
            <p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💡</div>
            <h3>التحليل الإرشادي</h3>
            <p>توصيات عملية لزيادة العائد على الاستثمار</p>
        </div>
        """, unsafe_allow_html=True)
    
    if current_user:
        st.markdown(f"""
        <div class="success-box" style="margin-top: 40px;">
            <h3>👋 مرحباً {current_user['name']}!</h3>
            <p><strong>ابدأ الآن في 3 خطوات بسيطة:</strong></p>
            <ol>
                <li>📥 اضغط على "استيراد البيانات" من القائمة الجانبية</li>
                <li>📊 ارفع ملف CSV أو Excel</li>
                <li>🎯 استكشف التحليلات والرؤى الذكية</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    st.markdown("اختر الباقة المناسبة لاحتياجاتك")
    
    col1, col2, col3 = st.columns(3)
    
    plans = [
        {
            "name": "🆓 Free",
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
            "name": "🏢 Enterprise",
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
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 30px; border-radius: 20px; margin-bottom: 20px;
                            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4); transform: scale(1.05);">
                    <div style="text-align: center; font-size: 14px; margin-bottom: 15px; background: rgba(255,255,255,0.2); 
                                padding: 8px; border-radius: 8px;">
                        🌟 الأكثر شعبية
                    </div>
                    <h2 style="color: white; text-align: center; margin: 0;">{plan['name']}</h2>
                    <h1 style="color: white; text-align: center; margin: 15px 0;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <h2 style="color: {plan['color']}; text-align: center; margin: 0;">{plan['name']}</h2>
                    <h1 style="color: {plan['color']}; text-align: center; margin: 15px 0;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### المميزات:")
            for feature in plan["features"]:
                st.markdown(f"✅ {feature}")
            
            st.button("اشترك الآن", use_container_width=True, type=plan["button_type"], key=f"sub_{i}")

elif st.session_state.page == "data_import":
    st.markdown("## 📥 استيراد البيانات")
    st.markdown("ارفع ملف CSV أو Excel لبدء التحليل")
    
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ تم الرفع بنجاح! {len(df)} صف")
            
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

elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        df = st.session_state.df
        st.write(f"**إجمالي:** {len(df)} صف، {len(df.columns)} عمود")
        st.dataframe(df.describe())
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            fig = px.imshow(df[numeric_cols].corr(), text_auto=".2f")
            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "diagnostic":
    st.markdown("## 🔍 التحليل التشخيصي")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            col = st.selectbox("اختر العمود", numeric_cols)
            threshold = st.slider("الحد", 2.0, 4.0, 3.0)
            
            if st.button("🔍 تحليل", key="btn_diag"):
                mean = np.mean(st.session_state.df[col])
                std = np.std(st.session_state.df[col])
                z_scores = np.abs((st.session_state.df[col] - mean) / std)
                
                st.session_state.df['Anomaly'] = z_scores > threshold
                anomalies = st.session_state.df[st.session_state.df['Anomaly']]
                
                st.metric("حالات الشذوذ", len(anomalies))
                if len(anomalies) > 0:
                    st.dataframe(anomalies)

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            target = st.selectbox("الهدف", numeric_cols, key="pred_target")
            feature = st.selectbox("الميزة", [c for c in numeric_cols if c != target], key="pred_feat")
            
            if st.button("🚀 تنبؤ", key="btn_pred"):
                X = st.session_state.df[[feature]].values
                y = st.session_state.df[target].values
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                model = LinearRegression()
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                
                r2 = r2_score(y_test, preds)
                st.metric("R² Score", f"{r2:.3f}")
                
                fig = px.scatter(x=y_test, y=preds, labels={'x': 'Actual', 'y': 'Predicted'})
                st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "prescriptive":
    st.markdown("## 💡 التحليل الإرشادي")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        insights = generate_local_ai_insights(st.session_state.df)
        for insight in insights:
            if "⚠️" in insight:
                st.warning(insight)
            elif "" in insight:
                st.info(insight)
            elif "🏆" in insight:
                st.success(insight)
            else:
                st.info(insight)

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    
    if st.session_state.df is None:
        st.warning("️ ارفع بيانات أولاً")
    else:
        prompt = st.text_input("اسأل عن بياناتك:", key="chat_q")
        if prompt:
            if "عدد" in prompt or "rows" in prompt:
                st.write(f"📊 عدد الصفوف: {len(st.session_state.df)}")
            elif "أعمدة" in prompt or "columns" in prompt:
                st.write(f"📋 الأعمدة: {', '.join(st.session_state.df.columns.tolist())}")
            elif "متوسط" in prompt:
                num_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
                for col in num_cols[:3]:
                    st.write(f"- {col}: {st.session_state.df[col].mean():.2f}")

elif st.session_state.page == "export":
    st.markdown("## 💾 التصدير")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv, "data.csv", "text/csv", key="dl_csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.df.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "data.xlsx", key="dl_excel")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
