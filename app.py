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
        if st.button(" ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"):
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
                insights.append(f"️ العمود {col} يحتوي على {count} قيمة مفقودة ({pct}%)")

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
            <div style="font-size: 50px; margin-bottom: 10px;"></div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 5px;">{current_user['email']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("###  التنقل السريع")
    
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
    
    if st.button(" تسجيل الخروج", use_container_width=True, key="btn_logout"):
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
            <h3> مرحباً {current_user['name']}!</h3>
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**إجمالي الصفوف:** {len(df):,}")
        with col2:
            st.info(f"**إجمالي الأعمدة:** {len(df.columns)}")
        with col3:
            missing_total = df.isnull().sum().sum()
            st.info(f"**القيم المفقودة:** {missing_total}")
        
        st.markdown("---")
        st.markdown("###  الملخص الإحصائي الشامل")
        with st.expander("عرض الملخص الإحصائي", expanded=True):
            st.dataframe(df.describe(), use_container_width=True)
        
        st.markdown("###  تحليل القيم المفقودة")
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
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        st.markdown("###  كشف الشذوذ (Anomaly Detection)")
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
                    st.markdown("###  عينة من حالات الشذوذ:")
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
        st.warning("⚠️ ارفع بيانات أولاً")
    else:
        st.info("🤖 يتم استخدام نموذج Linear Regression للتنبؤ")
        
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                target = st.selectbox("اختر العمود المراد التنبؤ به (Target)", numeric_cols, key="pred_target")
            with col2:
                feature = st.selectbox("اختر عمود الميزة (Feature)", [c for c in numeric_cols if c != target], key="pred_feature")
            
            if st.button(" بناء النموذج والتنبؤ", type="primary", key="btn_predict"):
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
        st.markdown("### 💡 التوصيات المبنية على البيانات")
        
        with st.spinner("🤖 جاري تحليل البيانات واستخراج الرؤى..."):
            insights = generate_local_ai_insights(st.session_state.df)
            
            for i, insight in enumerate(insights, 1):
                if "️" in insight:
                    st.warning(insight)
                elif "🔗" in insight:
                    st.info(insight)
                elif "🏆" in insight:
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
        st.markdown("💡 **أمثلة على الأسئلة:**")
        st.markdown("- كم عدد الصفوف والأعمدة؟")
        st.markdown("- ما هي الأعمدة المتاحة؟")
        st.markdown("- ما هو متوسط القيم الرقمية؟")
        st.markdown("- كم عدد القيم المفقودة؟")
        
        prompt = st.text_input("اكتب سؤالك هنا:", 
                              placeholder="مثال: ما هو متوسط المبيعات؟",
                              label_visibility="collapsed",
                              key="chat_prompt")
        
        if prompt:
            with st.spinner("🤔 جاري التحليل..."):
                response = ""
                prompt_lower = prompt.lower()
                
                if "عدد" in prompt_lower or "rows" in prompt_lower or "shape" in prompt_lower:
                    response = f"📊 يحتوي جدول البيانات على **{len(st.session_state.df)} صف** و **{len(st.session_state.df.columns)} عمود**."
                
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
    st.markdown("##  مركز التصدير")
    
    if st.session_state.df is None:
        st.warning("️ يرجى رفع البيانات أولاً")
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
st.markdown("<div style='text-align: center; color: #718096; padding: 20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
