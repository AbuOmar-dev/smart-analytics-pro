import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
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

# ==================== CSS ====================
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border-radius: 12px; padding: 12px 28px;
        font-weight: 600; border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .login-container {
        max-width: 500px; margin: 60px auto; padding: 50px 40px;
        background: white; border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    .login-header { text-align: center; margin-bottom: 40px; }
    .login-header h1 {
        font-size: 36px; margin-bottom: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-section {
        text-align: center; padding: 80px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border-radius: 24px; margin-bottom: 40px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    .hero-section h1 {
        font-size: 48px; margin-bottom: 20px;
        color: white !important;
        -webkit-text-fill-color: white !important;
    }
    .feature-card {
        background: white; padding: 30px; border-radius: 20px;
        text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.3s ease; margin: 10px;
    }
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    .readiness-box {
        background: white; padding: 25px; border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 15px 0;
    }
    .score-good { color: #48bb78; font-weight: bold; font-size: 24px; }
    .score-warning { color: #ed8936; font-weight: bold; font-size: 24px; }
    .score-bad { color: #f56565; font-weight: bold; font-size: 24px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None
if "is_cleaned" not in st.session_state:
    st.session_state.is_cleaned = False

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
            new_username = st.text_input(" اسم المستخدم", key="reg_username")
            new_name = st.text_input("👤 الاسم الكامل", key="reg_name")
            new_email = st.text_input("📧 البريد الإلكتروني", key="reg_email")
            new_password = st.text_input(" كلمة المرور", type="password", key="reg_password")
            confirm_password = st.text_input(" تأكيد كلمة المرور", type="password", key="reg_confirm")
            
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
        "readiness": "✅ جاهزية البيانات",
        "cleaning": " تنظيف البيانات",
        "summary": " ملخص البيانات",
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

# ===== الصفحة الرئيسية =====
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
            <div style="font-size: 60px; margin-bottom: 20px;">📊</div>
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
        <div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; margin-top: 40px; border-left: 5px solid #48bb78;">
            <h3> مرحباً {current_user['name']}!</h3>
            <p><strong>ابدأ الآن في 4 خطوات:</strong></p>
            <ol>
                <li> استيراد البيانات</li>
                <li>✅ فحص جاهزية البيانات</li>
                <li>🧹 تنظيف البيانات (إذا لزم الأمر)</li>
                <li>📊 التحليل الاستكشافي</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

# ===== صفحة الأسعار =====
elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    st.markdown("اختر الباقة المناسبة لاحتياجاتك")
    
    col1, col2, col3 = st.columns(3)
    
    plans = [
        {
            "name": " Free",
            "price": "$0",
            "period": "/شهر",
            "features": ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط"],
            "button_type": "secondary"
        },
        {
            "name": "⭐ Pro",
            "price": "$19",
            "period": "/شهر",
            "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل التحليلات"],
            "button_type": "primary",
            "popular": True
        },
        {
            "name": "🏢 Enterprise",
            "price": "$99",
            "period": "/شهر",
            "features": ["كل المميزات", "تخزين غير محدود", "API Access"],
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

# ===== صفحة استيراد البيانات =====
elif st.session_state.page == "data_import":
    st.markdown("##  استيراد البيانات")
    st.markdown("ارفع ملف CSV أو Excel لبدء التحليل")
    
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.session_state.df_clean = None
            st.session_state.is_cleaned = False
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

# ===== صفحة جاهزية البيانات =====
elif st.session_state.page == "readiness":
    st.markdown("## ✅ فحص جاهزية البيانات للتحليل")
    st.markdown("---")
    
    if st.session_state.df is None:
        st.warning("️ يرجى رفع البيانات أولاً من صفحة 'استيراد البيانات'")
    else:
        df = st.session_state.df
        
        st.markdown("### 📋 جدول تشخيص حالة البيانات")
        
        # حساب المؤشرات
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols
        
        missing_values = df.isnull().sum().sum()
        missing_pct = (missing_values / total_cells) * 100 if total_cells > 0 else 0
        
        duplicates = df.duplicated().sum()
        dup_pct = (duplicates / total_rows) * 100 if total_rows > 0 else 0
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # حساب القيم المتطرفة
        outlier_count = 0
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outlier_count += ((df[col] < lower) | (df[col] > upper)).sum()
        
        # حساب Score الجاهزية
        score = 100
        issues = []
        
        if missing_pct > 0:
            score -= missing_pct * 2
            issues.append(f"⚠️ قيم مفقودة: {missing_values} ({missing_pct:.1f}%)")
        
        if dup_pct > 0:
            score -= dup_pct * 3
            issues.append(f"⚠️ تكرارات: {duplicates} ({dup_pct:.1f}%)")
        
        if outlier_count > 0:
            score -= min(outlier_count / total_rows * 100, 20)
            issues.append(f"⚠️ قيم متطرفة: {outlier_count}")
        
        score = max(0, min(100, score))
        
        # عرض Score
        col1, col2, col3 = st.columns(3)
        with col1:
            if score >= 80:
                score_class = "score-good"
                status = "✅ جاهزة للتحليل"
            elif score >= 50:
                score_class = "score-warning"
                status = "⚠️ تحتاج تنظيف بسيط"
            else:
                score_class = "score-bad"
                status = "❌ تحتاج تنظيف شامل"
            
            st.markdown(f"""
            <div class="readiness-box" style="text-align: center;">
                <div style="font-size: 18px; color: #718096; margin-bottom: 10px;">جاهزية البيانات</div>
                <div class="{score_class}">{score:.0f}%</div>
                <div style="margin-top: 10px; font-size: 16px;">{status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="readiness-box">
                <div style="font-size: 14px; color: #718096;">حجم البيانات</div>
                <div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{total_rows:,} صف × {total_cols} عمود</div>
                <div style="font-size: 12px; color: #a0aec0; margin-top: 5px;">{total_cells:,} خلية</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="readiness-box">
                <div style="font-size: 14px; color: #718096;">أنواع الأعمدة</div>
                <div style="font-size: 16px; margin-top: 5px;">📊 رقمية: {len(numeric_cols)}</div>
                <div style="font-size: 16px;">📝 نصية: {len(categorical_cols)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # جدول التشخيص التفصيلي
        st.markdown("---")
        st.markdown("### 🔍 التشخيص التفصيلي لكل عمود")
        
        readiness_data = []
        for col in df.columns:
            missing = int(df[col].isnull().sum())
            missing_p = (missing / total_rows) * 100 if total_rows > 0 else 0
            unique = int(df[col].nunique())
            dtype = str(df[col].dtype)
            
            # تحديد الحالة
            if missing_p == 0:
                status_col = "✅"
            elif missing_p < 5:
                status_col = "⚠️"
            else:
                status_col = ""
            
            readiness_data.append({
                'العمود': col,
                'النوع': dtype,
                'القيم المفقودة': missing,
                'نسبة المفقود': f"{missing_p:.1f}%",
                'القيم الفريدة': unique,
                'الحالة': status_col
            })
        
        readiness_df = pd.DataFrame(readiness_data)
        st.dataframe(readiness_df, use_container_width=True)
        
        # قائمة المشاكل
        if issues:
            st.markdown("---")
            st.markdown("### ️ المشاكل المكتشفة")
            for issue in issues:
                st.warning(issue)
            
            st.markdown("---")
            st.info("💡 **التوصية:** انتقل إلى صفحة 'تنظيف البيانات' لمعالجة هذه المشاكل قبل التحليل")
            
            if st.button("🧹 انتقل إلى تنظيف البيانات", type="primary", key="btn_go_clean"):
                st.session_state.page = "cleaning"
                st.rerun()
        else:
            st.success("🎉 البيانات جاهزة تماماً للتحليل! يمكنك الانتقال مباشرة إلى التحليل الاستكشافي")
            
            if st.button(" انتقل إلى التحليل الاستكشافي", type="primary", key="btn_go_eda"):
                st.session_state.page = "eda"
                st.rerun()

# ===== صفحة تنظيف البيانات =====
elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف وإعداد البيانات")
    st.markdown("---")
    
    if st.session_state.df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        df = st.session_state.df.copy()
        
        st.markdown("###  حالة البيانات قبل التنظيف")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("الصفوف", len(df))
        with col2:
            st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
        with col3:
            st.metric("التكرارات", int(df.duplicated().sum()))
        
        st.markdown("---")
        st.markdown("### 🛠️ خيارات التنظيف")
        
        # خيار 1: القيم المفقودة
        st.markdown("#### 1️ معالجة القيم المفقودة")
        missing_option = st.selectbox(
            "اختر طريقة معالجة القيم المفقودة",
            ["حذف الصفوف التي تحتوي على قيم مفقودة",
             "حذف الأعمدة التي تحتوي على قيم مفقودة",
             "تعويض القيم المفقودة بالمتوسط (للأعمدة الرقمية)",
             "تعويض القيم المفقودة بالوسيط (للأعمدة الرقمية)",
             "تعويض القيم المفقودة بالقيمة الأكثر تكراراً",
             "لا تفعل شيئاً"],
            key="missing_option"
        )
        
        # خيار 2: التكرارات
        st.markdown("#### 2️⃣ معالجة التكرارات")
        dup_option = st.selectbox(
            "اختر طريقة معالجة التكرارات",
            ["حذف التكرارات (الاحتفاظ بالأول)",
             "حذف التكرارات (الاحتفاظ بالأخير)",
             "لا تفعل شيئاً"],
            key="dup_option"
        )
        
        # خيار 3: القيم المتطرفة
        st.markdown("#### 3️⃣ معالجة القيم المتطرفة")
        outlier_option = st.selectbox(
            "اختر طريقة معالجة القيم المتطرفة",
            ["لا تفعل شيئاً",
             "حذف القيم المتطرفة (طريقة IQR)",
             "استبدال القيم المتطرفة بالحدود"],
            key="outlier_option"
        )
        
        st.markdown("---")
        
        if st.button("🧹 تطبيق التنظيف", type="primary", key="btn_apply_clean"):
            df_clean = df.copy()
            steps = []
            
            # تطبيق معالجة القيم المفقودة
            if "حذف الصفوف" in missing_option:
                before = len(df_clean)
                df_clean = df_clean.dropna()
                after = len(df_clean)
                steps.append(f"✅ حذف {before - after} صف يحتوي على قيم مفقودة")
            elif "حذف الأعمدة" in missing_option:
                before = len(df_clean.columns)
                df_clean = df_clean.dropna(axis=1)
                after = len(df_clean.columns)
                steps.append(f"✅ حذف {before - after} عمود يحتوي على قيم مفقودة")
            elif "بالمتوسط" in missing_option:
                numeric_cols_clean = df_clean.select_dtypes(include=[np.number]).columns
                for col in numeric_cols_clean:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
                steps.append("✅ تعويض القيم المفقودة بالمتوسط للأعمدة الرقمية")
            elif "بالوسيط" in missing_option:
                numeric_cols_clean = df_clean.select_dtypes(include=[np.number]).columns
                for col in numeric_cols_clean:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                steps.append("✅ تعويض القيم المفقودة بالوسيط للأعمدة الرقمية")
            elif "بالقيمة الأكثر تكراراً" in missing_option:
                for col in df_clean.columns:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0] if len(df_clean[col].mode()) > 0 else df_clean[col])
                steps.append("✅ تعويض القيم المفقودة بالقيمة الأكثر تكراراً")
            
            # تطبيق معالجة التكرارات
            if "الاحتفاظ بالأول" in dup_option:
                before = len(df_clean)
                df_clean = df_clean.drop_duplicates(keep='first')
                after = len(df_clean)
                steps.append(f"✅ حذف {before - after} صف مكرر")
            elif "الاحتفاظ بالأخير" in dup_option:
                before = len(df_clean)
                df_clean = df_clean.drop_duplicates(keep='last')
                after = len(df_clean)
                steps.append(f"✅ حذف {before - after} صف مكرر")
            
            # تطبيق معالجة القيم المتطرفة
            if "حذف القيم المتطرفة" in outlier_option:
                numeric_cols_clean = df_clean.select_dtypes(include=[np.number]).columns
                removed = 0
                for col in numeric_cols_clean:
                    Q1 = df_clean[col].quantile(0.25)
                    Q3 = df_clean[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    before_len = len(df_clean)
                    df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
                    removed += before_len - len(df_clean)
                if removed > 0:
                    steps.append(f"✅ حذف {removed} قيمة متطرفة")
            elif "استبدال" in outlier_option:
                numeric_cols_clean = df_clean.select_dtypes(include=[np.number]).columns
                replaced = 0
                for col in numeric_cols_clean:
                    Q1 = df_clean[col].quantile(0.25)
                    Q3 = df_clean[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    mask_lower = df_clean[col] < lower
                    mask_upper = df_clean[col] > upper
                    df_clean.loc[mask_lower, col] = lower
                    df_clean.loc[mask_upper, col] = upper
                    replaced += mask_lower.sum() + mask_upper.sum()
                if replaced > 0:
                    steps.append(f"✅ استبدال {replaced} قيمة متطرفة بالحدود")
            
            # حفظ البيانات المنظفة
            st.session_state.df_clean = df_clean
            st.session_state.is_cleaned = True
            
            st.markdown("---")
            st.markdown("### ✅ خطوات التنظيف المنفذة")
            for step in steps:
                st.success(step)
            
            st.markdown("---")
            st.markdown("### 📊 حالة البيانات بعد التنظيف")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("الصفوف", len(df_clean))
            with col2:
                st.metric("القيم المفقودة", int(df_clean.isnull().sum().sum()))
            with col3:
                st.metric("التكرارات", int(df_clean.duplicated().sum()))
            
            if st.button(" عرض ملخص البيانات", type="primary", key="btn_go_summary"):
                st.session_state.page = "summary"
                st.rerun()

# ===== صفحة ملخص البيانات =====
elif st.session_state.page == "summary":
    st.markdown("## 📋 ملخص البيانات الجاهزة للتحليل")
    st.markdown("---")
    
    # استخدام البيانات المنظفة إذا موجودة، وإلا الأصلية
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ لا توجد بيانات")
    else:
        st.success("✅ البيانات جاهزة للتحليل")
        
        # الملخص السريع
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("إجمالي الصفوف", f"{len(df):,}")
        with col2:
            st.metric("إجمالي الأعمدة", len(df.columns))
        with col3:
            st.metric("القيم المفقودة", f"{df.isnull().sum().sum():,}")
        with col4:
            st.metric("التكرارات", f"{df.duplicated().sum():,}")
        
        st.markdown("---")
        
        # معلومات الأعمدة
        st.markdown("### 📊 معلومات الأعمدة")
        
        col_info = []
        for col in df.columns:
            col_info.append({
                'العمود': col,
                'النوع': str(df[col].dtype),
                'القيم الفريدة': int(df[col].nunique()),
                'القيم المفقودة': int(df[col].isnull().sum()),
                'أول قيمة': str(df[col].iloc[0]) if len(df) > 0 else '',
                'آخر قيمة': str(df[col].iloc[-1]) if len(df) > 0 else ''
            })
        
        col_info_df = pd.DataFrame(col_info)
        st.dataframe(col_info_df, use_container_width=True)
        
        st.markdown("---")
        
        # معاينة البيانات
        st.markdown("### 👁️ معاينة البيانات (أول 10 صفوف)")
        st.dataframe(df.head(10), use_container_width=True)
        
        st.markdown("---")
        
        # الإحصائيات الأساسية
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            st.markdown("### 📈 الإحصائيات الأساسية للأعمدة الرقمية")
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
        
        st.markdown("---")
        
        if st.button("📊 الانتقال إلى التحليل الاستكشافي", type="primary", key="btn_go_eda_from_summary"):
            st.session_state.page = "eda"
            st.rerun()

# ===== صفحة التحليل الاستكشافي =====
elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    st.markdown("---")
    
    # استخدام البيانات المنظفة إذا موجودة
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
    else:
        # تعريف المتغيرات الأساسية
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # التبويبات الرئيسية
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 الجداول التكرارية",
            " التصور البياني",
            "📊 المقاييس الإحصائية",
            " Box Plots"
        ])
        
        # ===== التبويب 1: الجداول التكرارية =====
        with tab1:
            st.markdown("### 📋 الجداول التكرارية")
            st.markdown("---")
            
            if categorical_cols:
                st.markdown("#### الجداول التكرارية للمتغيرات الفئوية")
                selected_cat = st.selectbox("اختر المتغير الفئوي", categorical_cols, key="eda_freq_cat")
                
                if selected_cat:
                    freq_table = df[selected_cat].value_counts().reset_index()
                    freq_table.columns = ['القيمة', 'التكرار']
                    freq_table['النسبة المئوية'] = (freq_table['التكرار'] / len(df) * 100).round(2)
                    freq_table['النسبة التراكمية'] = freq_table['النسبة المئوية'].cumsum().round(2)
                    
                    st.dataframe(freq_table, use_container_width=True)
                    
                    # رسم بياني للتكرارات
                    fig = px.bar(freq_table, x='القيمة', y='التكرار',
                               title=f"التكرارات لـ {selected_cat}",
                               color='التكرار',
                               color_continuous_scale='Blues')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد متغيرات فئوية في البيانات")
            
            st.markdown("---")
            
            if numeric_cols:
                st.markdown("#### الجداول التكرارية للمتغيرات الرقمية (مجمعات)")
                selected_num = st.selectbox("اختر المتغير الرقمي", numeric_cols, key="eda_freq_num")
                
                if selected_num:
                    # تقسيم البيانات إلى مجموعات
                    bins = st.slider("عدد المجموعات", 5, 30, 10, key="eda_bins")
                    df_temp = df.copy()
                    df_temp['مجموعة'] = pd.cut(df_temp[selected_num], bins=bins)
                    
                    freq_num = df_temp['مجموعة'].value_counts().sort_index().reset_index()
                    freq_num.columns = ['المجموعة', 'التكرار']
                    freq_num['النسبة المئوية'] = (freq_num['التكرار'] / len(df) * 100).round(2)
                    
                    st.dataframe(freq_num, use_container_width=True)
            else:
                st.info("لا توجد متغيرات رقمية في البيانات")
        
        # ===== التبويب 2: التصور البياني =====
        with tab2:
            st.markdown("### 📈 التصور البياني")
            st.markdown("---")
            
            viz_type = st.selectbox("اختر نوع التصور", 
                                   ["Histogram", "Bar Chart", "Pie Chart", "Scatter Plot", "Line Chart", "Heatmap"],
                                   key="eda_viz_type")
            
            if viz_type == "Histogram" and numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols, key="eda_hist_col")
                bins = st.slider("عدد الأعمدة", 10, 100, 30, key="eda_hist_bins")
                
                fig = px.histogram(df, x=col, nbins=bins,
                                 title=f"توزيع {col}",
                                 color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Bar Chart" and categorical_cols:
                col = st.selectbox("اختر العمود", categorical_cols, key="eda_bar_col")
                top_n = st.slider("عدد القيم العليا", 5, 50, 10, key="eda_bar_top")
                
                value_counts = df[col].value_counts().head(top_n)
                fig = px.bar(x=value_counts.values, y=value_counts.index,
                           orientation='h',
                           title=f"توزيع {col}",
                           color=value_counts.values,
                           color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Pie Chart" and categorical_cols:
                col = st.selectbox("اختر العمود", categorical_cols, key="eda_pie_col")
                top_n = st.slider("عدد القيم", 3, 20, 10, key="eda_pie_top")
                
                value_counts = df[col].value_counts().head(top_n)
                fig = px.pie(values=value_counts.values, names=value_counts.index,
                           title=f"النسب المئوية لـ {col}",
                           hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Scatter Plot" and len(numeric_cols) >= 2:
                col1_select = st.selectbox("المحور X", numeric_cols, key="eda_scatter_x")
                col2_select = st.selectbox("المحور Y", [c for c in numeric_cols if c != col1_select], key="eda_scatter_y")
                color_col = st.selectbox("اللون (اختياري)", ['None'] + categorical_cols, key="eda_scatter_color")
                
                if color_col == 'None':
                    fig = px.scatter(df, x=col1_select, y=col2_select,
                                   title=f"العلاقة بين {col1_select} و {col2_select}",
                                   trendline="ols",
                                   color_discrete_sequence=['#667eea'])
                else:
                    fig = px.scatter(df, x=col1_select, y=col2_select,
                                   color=color_col,
                                   title=f"العلاقة بين {col1_select} و {col2_select} حسب {color_col}",
                                   trendline="ols")
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Line Chart" and numeric_cols:
                col = st.selectbox("اختر العمود", numeric_cols, key="eda_line_col")
                fig = px.line(df, y=col,
                            title=f"الاتجاه الزمني/التسلسلي لـ {col}",
                            color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Heatmap" and len(numeric_cols) >= 2:
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(corr_matrix,
                               text_auto=".2f",
                               aspect="auto",
                               title="مصفوفة الارتباط",
                               color_continuous_scale="RdBu_r",
                               zmin=-1, zmax=1)
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
        
        # ===== التبويب 3: المقاييس الإحصائية =====
        with tab3:
            st.markdown("### 📊 المقاييس الإحصائية الشاملة")
            st.markdown("---")
            
            if numeric_cols:
                selected_stat_col = st.selectbox("اختر العمود الرقمي", numeric_cols, key="eda_stat_col")
                
                if selected_stat_col:
                    col_data = df[selected_stat_col].dropna()
                    
                    # 1. مقاييس النزعة المركزية
                    st.markdown("#### 1️ مقاييس النزعة المركزية (Measures of Central Tendency)")
                    
                    mean_val = col_data.mean()
                    median_val = col_data.median()
                    mode_val = col_data.mode().iloc[0] if len(col_data.mode()) > 0 else np.nan
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 14px; color: #718096;">المتوسط (Mean)</div>
                            <div style="font-size: 24px; font-weight: bold; color: #667eea; margin-top: 10px;">{mean_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 14px; color: #718096;">الوسيط (Median)</div>
                            <div style="font-size: 24px; font-weight: bold; color: #764ba2; margin-top: 10px;">{median_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 14px; color: #718096;">المنوال (Mode)</div>
                            <div style="font-size: 24px; font-weight: bold; color: #f093fb; margin-top: 10px;">{mode_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 2. مقاييس التشتت
                    st.markdown("#### 2️⃣ مقاييس التشتت (Measures of Dispersion)")
                    
                    range_val = col_data.max() - col_data.min()
                    variance_val = col_data.var()
                    std_val = col_data.std()
                    cv_val = (std_val / mean_val * 100) if mean_val != 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">المدى (Range)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #667eea; margin-top: 10px;">{range_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">التباين (Variance)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #764ba2; margin-top: 10px;">{variance_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">الانحراف المعياري (Std)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #f093fb; margin-top: 10px;">{std_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">معامل الاختلاف (CV%)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #48bb78; margin-top: 10px;">{cv_val:.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 3. مقاييس الموضع
                    st.markdown("#### 3️⃣ مقاييس الموضع (Measures of Position)")
                    
                    q1_val = col_data.quantile(0.25)
                    q2_val = col_data.quantile(0.50)
                    q3_val = col_data.quantile(0.75)
                    p10_val = col_data.quantile(0.10)
                    p90_val = col_data.quantile(0.90)
                    iqr_val = q3_val - q1_val
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">الربيع الأول (Q1)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #667eea; margin-top: 10px;">{q1_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">الربيع الثاني (Q2)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #764ba2; margin-top: 10px;">{q2_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">الربيع الثالث (Q3)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #f093fb; margin-top: 10px;">{q3_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">المدى الربيعي (IQR)</div>
                            <div style="font-size: 20px; font-weight: bold; color: #48bb78; margin-top: 10px;">{iqr_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">النسبة المئوية 10%</div>
                            <div style="font-size: 20px; font-weight: bold; color: #ed8936; margin-top: 10px;">{p10_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="readiness-box" style="text-align: center;">
                            <div style="font-size: 12px; color: #718096;">النسبة المئوية 90%</div>
                            <div style="font-size: 20px; font-weight: bold; color: #ed8936; margin-top: 10px;">{p90_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 4. الانحناء والتفلطح
                    st.markdown("#### 4️⃣ الانحناء والتفلطح (Skewness & Kurtosis)")
                    
                    skew_val = col_data.skew()
                    kurt_val = col_data.kurtosis()
                    
                    # تفسير الانحناء
                    if skew_val > 1:
                        skew_interpretation = "التوزيع منحرف بشدة لليمين (إيجابي)"
                    elif skew_val > 0.5:
                        skew_interpretation = "التوزيع منحرف moderately لليمين"
                    elif skew_val > -0.5:
                        skew_interpretation = "التوزيع متماثل تقريباً"
                    elif skew_val > -1:
                        skew_interpretation = "التوزيع منحرف moderately لليسار"
                    else:
                        skew_interpretation = "التوزيع منحرف بشدة لليسار (سلبي)"
                    
                    # تفسير التفلطح
                    if kurt_val > 3:
                        kurt_interpretation = "التوزيع مدبب (Leptokurtic) - ذيول ثقيلة"
                    elif kurt_val > 0:
                        kurt_interpretation = "التوزيع متوسط التفلطح"
                    else:
                        kurt_interpretation = "التوزيع مفلطح (Platykurtic) - ذيول خفيفة"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div class="readiness-box">
                            <div style="font-size: 14px; color: #718096; text-align: center;">الانحناء (Skewness)</div>
                            <div style="font-size: 28px; font-weight: bold; color: #667eea; text-align: center; margin: 10px 0;">{skew_val:.4f}</div>
                            <div style="font-size: 12px; color: #4a5568; text-align: center; background: #f7fafc; padding: 8px; border-radius: 8px;">{skew_interpretation}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="readiness-box">
                            <div style="font-size: 14px; color: #718096; text-align: center;">التفلطح (Kurtosis)</div>
                            <div style="font-size: 28px; font-weight: bold; color: #764ba2; text-align: center; margin: 10px 0;">{kurt_val:.4f}</div>
                            <div style="font-size: 12px; color: #4a5568; text-align: center; background: #f7fafc; padding: 8px; border-radius: 8px;">{kurt_interpretation}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # ملخص شامل
                    st.markdown("#### 📋 الملخص الإحصائي الشامل")
                    
                    summary_data = {
                        'المقياس': [
                            'العدد (Count)',
                            'المتوسط (Mean)',
                            'الوسيط (Median)',
                            'المنوال (Mode)',
                            'الانحراف المعياري (Std)',
                            'التباين (Variance)',
                            'المدى (Range)',
                            'الحد الأدنى (Min)',
                            'الربيع الأول (Q1)',
                            'الربيع الثاني (Q2)',
                            'الربيع الثالث (Q3)',
                            'الحد الأقصى (Max)',
                            'الانحناء (Skewness)',
                            'التفلطح (Kurtosis)'
                        ],
                        'القيمة': [
                            len(col_data),
                            f"{mean_val:.4f}",
                            f"{median_val:.4f}",
                            f"{mode_val:.4f}",
                            f"{std_val:.4f}",
                            f"{variance_val:.4f}",
                            f"{range_val:.4f}",
                            f"{col_data.min():.4f}",
                            f"{q1_val:.4f}",
                            f"{q2_val:.4f}",
                            f"{q3_val:.4f}",
                            f"{col_data.max():.4f}",
                            f"{skew_val:.4f}",
                            f"{kurt_val:.4f}"
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
            else:
                st.warning("لا توجد متغيرات رقمية في البيانات")
        
        # ===== التبويب 4: Box Plots =====
        with tab4:
            st.markdown("### 📦 Box Plots (مخططات الصندوق)")
            st.markdown("---")
            
            if numeric_cols:
                # Box Plot لعمود واحد
                st.markdown("#### Box Plot لعمود واحد")
                selected_box = st.selectbox("اختر العمود", numeric_cols, key="eda_box_col")
                
                fig_box = px.box(df, y=selected_box,
                               title=f"Box Plot لـ {selected_box}",
                               color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig_box, use_container_width=True)
                
                st.markdown("---")
                
                # Box Plot لجميع الأعمدة الرقمية
                if len(numeric_cols) <= 10:
                    st.markdown("#### Box Plot لجميع المتغيرات الرقمية")
                    
                    # تطبيع البيانات للمقارنة
                    df_melted = df[numeric_cols].melt(var_name='المتغير', value_name='القيمة')
                    
                    fig_box_all = px.box(df_melted, x='المتغير', y='القيمة',
                                        title="Box Plot لجميع المتغيرات الرقمية",
                                        color='المتغير',
                                        color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#48bb78', '#ed8936'])
                    fig_box_all.update_layout(height=500)
                    st.plotly_chart(fig_box_all, use_container_width=True)
                
                st.markdown("---")
                
                # Box Plot حسب متغير فئوي
                if categorical_cols and len(numeric_cols) >= 1:
                    st.markdown("#### Box Plot حسب متغير فئوي")
                    
                    box_num_col = st.selectbox("اختر المتغير الرقمي", numeric_cols, key="eda_box_num")
                    box_cat_col = st.selectbox("اختر المتغير الفئوي", categorical_cols, key="eda_box_cat")
                    
                    fig_box_cat = px.box(df, x=box_cat_col, y=box_num_col,
                                        title=f"Box Plot لـ {box_num_col} حسب {box_cat_col}",
                                        color=box_cat_col)
                    st.plotly_chart(fig_box_cat, use_container_width=True)
            else:
                st.warning("لا توجد متغيرات رقمية في البيانات")

# ===== باقي الصفحات (مبسطة) =====
elif st.session_state.page == "diagnostic":
    st.markdown("## 🔍 التحليل التشخيصي")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            col = st.selectbox("اختر العمود", numeric_cols)
            threshold = st.slider("الحد", 2.0, 4.0, 3.0)
            if st.button("🔍 تحليل", key="btn_diag"):
                mean = np.mean(df[col])
                std = np.std(df[col])
                z_scores = np.abs((df[col] - mean) / std)
                df['Anomaly'] = z_scores > threshold
                anomalies = df[df['Anomaly']]
                st.metric("حالات الشذوذ", len(anomalies))
                if len(anomalies) > 0:
                    st.dataframe(anomalies)

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("️ ارفع بيانات أولاً")
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= 2:
            target = st.selectbox("الهدف", numeric_cols, key="pred_target")
            feature = st.selectbox("الميزة", [c for c in numeric_cols if c != target], key="pred_feat")
            if st.button(" تنبؤ", key="btn_pred"):
                X = df[[feature]].values
                y = df[target].values
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
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        st.success("✅ البيانات جاهزة للتحليل")
        st.info("💡 التوصيات ستظهر هنا بناءً على التحليل")

elif st.session_state.page == "ai_chat":
    st.markdown("## 🤖 المساعد الذكي")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        prompt = st.text_input("اسأل عن بياناتك:", key="chat_q")
        if prompt:
            if "عدد" in prompt or "rows" in prompt:
                st.write(f"📊 عدد الصفوف: {len(df)}")
            elif "أعمدة" in prompt or "columns" in prompt:
                st.write(f"📋 الأعمدة: {', '.join(df.columns.tolist())}")
            elif "متوسط" in prompt:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                for col in num_cols[:3]:
                    st.write(f"- {col}: {df[col].mean():.2f}")

elif st.session_state.page == "export":
    st.markdown("## 💾 التصدير")
    
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("️ ارفع بيانات أولاً")
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv, "data.csv", "text/csv", key="dl_csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "data.xlsx", key="dl_excel")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
