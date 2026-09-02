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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS Styling ====================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
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
    
    .login-container {
        max-width: 500px;
        margin: 60px auto;
        padding: 50px 40px;
        background: white;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
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
    
    .info-box {
        background: linear-gradient(135deg, #ebf8ff 0%, #c3cfe2 100%);
        border-left: 5px solid #667eea;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 5px solid #48bb78;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffaf0 0%, #feebc8 100%);
        border-left: 5px solid #ed8936;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
            new_name = st.text_input(" الاسم الكامل", key="reg_name")
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
                        st.error(f" {message}")
            
            if st.button(" لديك حساب؟ دخول", use_container_width=True, type="secondary", key="btn_go_login"):
                st.session_state.show_register = False
                st.rerun()
    else:
        st.markdown("### 🔐 تسجيل الدخول")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input(" اسم المستخدم", key="login_user")
            password = st.text_input("🔑 كلمة المرور", type="password", key="login_pass")
            
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
    st.markdown("### 📍 التنقل السريع")
    
    menu = {
        "home": "🏠 الرئيسية",
        "pricing": "💰 الأسعار",
        "data_import": "📥 استيراد البيانات",
        "eda": "📊 التحليل الاستكشافي",
        "diagnostic": "🔍 التحليل التشخيصي",
        "predictive": " التحليل التنبؤي",
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
            <div style="font-size: 60px; margin-bottom: 20px;"></div>
            <h3>التحليل الاستكشافي</h3>
            <p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 60px; margin-bottom: 20px;">🔍</div>
            <h3>التحليل التشخيصي</h3>
            <p>اكتشف الأنماط والشذوذ في بياناتك</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 60px; margin-bottom: 20px;"></div>
            <h3>التحليل التنبؤي</h3>
            <p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 60px; margin-bottom: 20px;">💡</div>
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
                <li> استكشف التحليلات والرؤى الذكية</li>
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
            "button_type": "secondary"
        },
        {
            "name": "⭐ Pro",
            "price": "$19",
            "period": "/شهر",
            "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل أنواع التحليلات الأربعة", "تصدير بكل الصيغ", "محرك الرؤى الذكي", "دعم فني بأولوية"],
            "button_type": "primary",
            "popular": True
        },
        {
            "name": "🏢 Enterprise",
            "price": "$99",
            "period": "/شهر",
            "features": ["كل مميزات Pro", "تخزين غير محدود", "White-Label كامل", "API Access", "مدير حساب مخصص", "SLA مضمون 99.9%"],
            "button_type": "secondary"
        }
    ]
    
    for i, plan in enumerate(plans):
        with [col1, col2, col3][i]:
            if plan.get("popular"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 30px; border-radius: 20px; margin-bottom: 20px;
                            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);">
                    <div style="text-align: center; background: rgba(255,255,255,0.2); 
                                padding: 8px; border-radius: 8px; margin-bottom: 15px;">
                        🌟 الأكثر شعبية
                    </div>
                    <h2 style="color: white; text-align: center;">{plan['name']}</h2>
                    <h1 style="color: white; text-align: center;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <h2 style="text-align: center;">{plan['name']}</h2>
                    <h1 style="text-align: center;">{plan['price']}<span style="font-size: 18px;">{plan['period']}</span></h1>
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
                numeric_cols_count = df.select_dtypes(include=[np.number]).shape[1]
                st.metric("الأعمدة الرقمية", numeric_cols_count)
            
            st.markdown("### معاينة البيانات")
            st.dataframe(df.head(10), use_container_width=True)

elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    st.markdown("---")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً من صفحة 'استيراد البيانات'")
    else:
        df = st.session_state.df
        
        # تعريف المتغيرات الأساسية
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # تعريف DataFrames بشكل صحيح
        dtype_df = pd.DataFrame({
            'العمود': df.columns,
            'النوع': [str(dtype) for dtype in df.dtypes]
        })
        
        info_df = pd.DataFrame({
            'العمود': df.columns,
            'النوع': [str(dtype) for dtype in df.dtypes],
            'القيم الفريدة': [df[col].nunique() for col in df.columns],
            'القيم المفقودة': [int(df[col].isnull().sum()) for col in df.columns],
            'نسبة المفقودين': [f"{(df[col].isnull().sum()/len(df))*100:.2f}%" for col in df.columns]
        })
        
        # ====== التبويبات الرئيسية ======
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 نظرة عامة",
            "📈 التوزيعات",
            "🔗 الارتباطات",
            "📊 التحليل الفئوي",
            "🔍 القيم المتطرفة",
            "📄 التقرير"
        ])
        
        # ====== التبويب 1: نظرة عامة ======
        with tab1:
            st.markdown("### 📋 نظرة عامة على البيانات")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("إجمالي الصفوف", f"{len(df):,}")
            with col2:
                st.metric("إجمالي الأعمدة", len(df.columns))
            with col3:
                st.metric("الذاكرة المستخدمة", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            with col4:
                st.metric("القيم المفقودة", f"{df.isnull().sum().sum():,}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### أنواع البيانات")
                st.dataframe(dtype_df, use_container_width=True)
            
            with col2:
                st.markdown("#### أول 5 صفوف")
                st.dataframe(df.head(), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### الإحصائيات الوصفية الشاملة")
            st.dataframe(df.describe(), use_container_width=True)
            
            with st.expander("📊 معلومات تفصيلية عن الأعمدة"):
                st.dataframe(info_df, use_container_width=True)
        
        # ====== التبويب 2: التوزيعات ======
        with tab2:
            st.markdown("### 📈 تحليل التوزيعات")
            
            if numeric_cols:
                st.markdown("#### توزيع المتغيرات الرقمية")
                
                selected_col = st.selectbox("اختر العمود للتحليل", numeric_cols, key="eda_dist_col")
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_hist = px.histogram(df, x=selected_col, 
                                           title=f"توزيع {selected_col}",
                                           nbins=30,
                                           color_discrete_sequence=['#667eea'])
                    fig_hist.update_layout(showlegend=False)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    fig_kde = px.histogram(df, x=selected_col,
                                          title=f"منحنى الكثافة لـ {selected_col}",
                                          histnorm='probability density',
                                          nbins=50,
                                          color_discrete_sequence=['#764ba2'])
                    fig_kde.update_layout(showlegend=False)
                    st.plotly_chart(fig_kde, use_container_width=True)
                
                fig_box = px.box(df, y=selected_col,
                               title=f"مخطط الصندوق لـ {selected_col}",
                               color_discrete_sequence=['#f093fb'])
                st.plotly_chart(fig_box, use_container_width=True)
                
                st.markdown("---")
                st.markdown("#### توزيع جميع المتغيرات الرقمية")
                
                if len(numeric_cols) <= 10:
                    fig_pair = px.scatter_matrix(df[numeric_cols],
                                                title="مصفوفة التشتت للمتغيرات الرقمية",
                                                dimensions=numeric_cols,
                                                color_discrete_sequence=['#667eea'])
                    fig_pair.update_layout(height=800)
                    st.plotly_chart(fig_pair, use_container_width=True)
            else:
                st.warning("لا توجد متغيرات رقمية في البيانات")
        
        # ====== التبويب 3: الارتباطات ======
        with tab3:
            st.markdown("###  تحليل الارتباطات")
            
            if len(numeric_cols) >= 2:
                st.markdown("#### مصفوفة الارتباط")
                
                corr_method = st.selectbox("طريقة الحساب", 
                                         ['pearson', 'spearman', 'kendall'],
                                         key="eda_corr_method")
                
                corr_matrix = df[numeric_cols].corr(method=corr_method)
                
                fig_heatmap = px.imshow(corr_matrix,
                                       text_auto=".2f",
                                       aspect="auto",
                                       title="مصفوفة الارتباط",
                                       color_continuous_scale="RdBu_r",
                                       zmin=-1, zmax=1)
                fig_heatmap.update_layout(height=600)
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                st.markdown("---")
                st.markdown("#### أقوى الارتباطات")
                
                corr_pairs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_pairs.append({
                            'المتغير 1': corr_matrix.columns[i],
                            'المتغير 2': corr_matrix.columns[j],
                            'الارتباط': float(corr_matrix.iloc[i, j])
                        })
                
                corr_df = pd.DataFrame(corr_pairs)
                top_positive = corr_df.nlargest(5, 'الارتباط')
                top_negative = corr_df.nsmallest(5, 'الارتباط')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**الأعلى إيجابياً**")
                    st.dataframe(top_positive, use_container_width=True)
                
                with col2:
                    st.markdown("**الأعلى سلبياً**")
                    st.dataframe(top_negative, use_container_width=True)
                
                if len(top_positive) > 0:
                    st.markdown("---")
                    st.markdown("#### تصور لأقوى ارتباط")
                    
                    var1 = top_positive.iloc[0]['المتغير 1']
                    var2 = top_positive.iloc[0]['المتغير 2']
                    
                    fig_scatter = px.scatter(df, x=var1, y=var2,
                                           title=f"العلاقة بين {var1} و {var2}",
                                           trendline="ols",
                                           color_discrete_sequence=['#667eea'])
                    st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("تحتاج متغيرين رقميين على الأقل لتحليل الارتباط")
        
        # ====== التبويب 4: التحليل الفئوي ======
        with tab4:
            st.markdown("### 📊 التحليل الفئوي")
            
            if categorical_cols:
                selected_cat = st.selectbox("اختر المتغير الفئوي", categorical_cols, key="eda_cat_col")
                
                value_counts = df[selected_cat].value_counts().head(10)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_bar = px.bar(x=value_counts.values,
                                   y=value_counts.index,
                                   orientation='h',
                                   title=f"توزيع {selected_cat}",
                                   color_discrete_sequence=['#667eea'])
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    fig_pie = px.pie(values=value_counts.values,
                                   names=value_counts.index,
                                   title=f"النسب المئوية لـ {selected_cat}",
                                   hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.markdown("---")
                st.markdown("#### جدول التكرارات")
                freq_df = pd.DataFrame({
                    'القيمة': value_counts.index.tolist(),
                    'التكرار': value_counts.values,
                    'النسبة': [(v / len(df) * 100) for v in value_counts.values]
                })
                st.dataframe(freq_df, use_container_width=True)
            else:
                st.warning("لا توجد متغيرات فئوية في البيانات")
        
        # ====== التبويب 5: القيم المتطرفة ======
        with tab5:
            st.markdown("### 🔍 كشف القيم المتطرفة")
            
            if numeric_cols:
                outlier_col = st.selectbox("اختر العمود", numeric_cols, key="eda_outlier_col")
                
                method = st.selectbox("طريقة الكشف", 
                                    ['IQR', 'Z-Score'],
                                    key="eda_outlier_method")
                
                if method == 'IQR':
                    Q1 = df[outlier_col].quantile(0.25)
                    Q3 = df[outlier_col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = df[(df[outlier_col] < lower_bound) | (df[outlier_col] > upper_bound)]
                else:
                    mean = df[outlier_col].mean()
                    std = df[outlier_col].std()
                    threshold = st.slider("الحد (Z-Score)", 2.0, 4.0, 3.0)
                    
                    z_scores = np.abs((df[outlier_col] - mean) / std)
                    outliers = df[z_scores > threshold]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("إجمالي السجلات", len(df))
                with col2:
                    st.metric("القيم المتطرفة", len(outliers))
                with col3:
                    pct = (len(outliers) / len(df) * 100) if len(df) > 0 else 0
                    st.metric("النسبة", f"{pct:.2f}%")
                
                fig_box = px.box(df, y=outlier_col,
                               title=f"مخطط الصندوق - {outlier_col}",
                               color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig_box, use_container_width=True)
                
                if len(outliers) > 0:
                    with st.expander(f"📋 عرض القيم المتطرفة ({len(outliers)} سجل)"):
                        st.dataframe(outliers, use_container_width=True)
            else:
                st.warning("لا توجد متغيرات رقمية للتحليل")
        
        # ====== التبويب 6: التقرير ======
        with tab6:
            st.markdown("### 📄 تصدير التقرير")
            
            st.markdown("#### اختر صيغة التقرير")
            
            report_format = st.selectbox("الصيغة", ["HTML", "Excel"], key="eda_report_format")
            
            if st.button("📊 إنشاء التقرير", type="primary", key="btn_gen_report"):
                html_report = f"""
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <title>تقرير التحليل الاستكشافي - Smart Analytics Pro</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                               margin: 40px; background: #f5f7fa; }}
                        .container {{ max-width: 1200px; margin: 0 auto; 
                                     background: white; padding: 40px; border-radius: 10px; 
                                     box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #667eea; text-align: center; }}
                        h2 {{ color: #764ba2; border-bottom: 2px solid #667eea; 
                             padding-bottom: 10px; margin-top: 30px; }}
                        .metric {{ display: inline-block; margin: 10px; padding: 20px; 
                                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                  color: white; border-radius: 8px; min-width: 150px; 
                                  text-align: center; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                        th {{ background: #667eea; color: white; }}
                        tr:nth-child(even) {{ background: #f5f7fa; }}
                        .footer {{ text-align: center; margin-top: 40px; color: #718096; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📊 تقرير التحليل الاستكشافي</h1>
                        <p style="text-align: center; color: #718096;">Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                        
                        <h2>📋 نظرة عامة</h2>
                        <div class="metric">الصفوف: {len(df):,}</div>
                        <div class="metric">الأعمدة: {len(df.columns)}</div>
                        <div class="metric">الذاكرة: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB</div>
                        <div class="metric">المفقودة: {df.isnull().sum().sum():,}</div>
                        
                        <h2>📈 الإحصائيات الوصفية</h2>
                        {df.describe().to_html()}
                        
                        <h2>📊 أنواع البيانات</h2>
                        {dtype_df.to_html(index=False)}
                        
                        <div class="footer">
                            <p>تم إنشاء هذا التقرير تلقائياً بواسطة Smart Analytics Pro</p>
                            <p>© 2026 جميع الحقوق محفوظة</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                if report_format == "HTML":
                    st.download_button(
                        label="📥 تحميل تقرير HTML",
                        data=html_report,
                        file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.describe().to_excel(writer, sheet_name='Descriptive Stats')
                        dtype_df.to_excel(writer, sheet_name='Data Types', index=False)
                        info_df.to_excel(writer, sheet_name='Column Info', index=False)
                        if len(numeric_cols) >= 2:
                            corr_matrix = df[numeric_cols].corr()
                            corr_matrix.to_excel(writer, sheet_name='Correlation Matrix')
                    
                    st.download_button(
                        label="📥 تحميل تقرير Excel",
                        data=output.getvalue(),
                        file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                st.success("✅ تم إنشاء التقرير بنجاح!")

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
        st.warning("️ ارفع بيانات أولاً")
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
            elif "🔗" in insight:
                st.info(insight)
            elif "🏆" in insight:
                st.success(insight)
            else:
                st.info(insight)

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    
    if st.session_state.df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
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
        st.warning("️ ارفع بيانات أولاً")
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(" CSV", csv, "data.csv", "text/csv", key="dl_csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.df.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "data.xlsx", key="dl_excel")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
