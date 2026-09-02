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

# استيراد الملفات المحلية
import config

# إعدادات الصفحة
st.set_page_config(
    page_title=config.APP_CONFIG["app_name"],
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== إعدادات Supabase ====================

SUPABASE_URL = "https://llsoulwgpptlpatgivqk.supabase.co"
SUPABASE_KEY = "sb_publishable_OpzDbBV2XqSJchMJ6DqmLQ_DYyB9GVH"

# تهيئة Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
    supabase = None

# CSS Styling
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    h1, h2, h3 { color: #1a202c; }
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== نظام المستخدمين ====================

# تهيئة الحالة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "df" not in st.session_state:
    st.session_state.df = None

def load_users():
    """تحميل المستخدمين من Supabase"""
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
        st.error(f"خطأ في تحميل المستخدمين: {e}")
        return {}

def register_user(username, password, name, email, plan='Free'):
    """تسجيل مستخدم جديد"""
    if supabase is None:
        return False, "خطأ في الاتصال بقاعدة البيانات"
    
    try:
        # التحقق من وجود المستخدم
        response = supabase.table("users").select("username").eq("username", username).execute()
        if len(response.data) > 0:
            return False, "اسم المستخدم موجود بالفعل"
        
        # إضافة المستخدم الجديد
        data = {
            'username': username,
            'password': password,
            'name': name,
            'email': email,
            'plan': plan,
            'role': 'user'
        }
        
        response = supabase.table("users").insert(data).execute()
        return True, "تم التسجيل بنجاح!"
    except Exception as e:
        return False, f"خطأ في التسجيل: {e}"

# ==================== صفحة تسجيل الدخول ====================

if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <div style="font-size: 80px; margin-bottom: 20px;"></div>
        <h1>Smart Analytics Pro</h1>
        <p style="color: #718096;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p>
    </div>
    """, unsafe_allow_html=True)
    
    # التبديل بين تسجيل الدخول والتسجيل
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    if st.session_state.show_register:
        st.markdown("### 📝 إنشاء حساب جديد")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_username = st.text_input("👤 اسم المستخدم", key="reg_username")
            new_name = st.text_input("👤 الاسم الكامل", key="reg_name")
            new_email = st.text_input(" البريد الإلكتروني", key="reg_email")
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
        if st.button("📝 ليس لديك حساب؟ سجل الآن", use_container_width=True, type="secondary", key="btn_go_register"):
            st.session_state.show_register = True
            st.rerun()
        
        st.markdown("---")
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
                insights.append(f" ارتباط قوي بين {top_corr[0]} و {top_corr[1]} ({val})")

    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        if df[cat_col].nunique() < 20:
            top_cat = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(1)
            insights.append(f"🏆 {top_cat.index[0]} هو الأعلى أداءً بـ {round(top_cat.values[0], 2)}")

    if not insights:
        return ["✅ البيانات تبدو نظيفة وجيدة للتحليل المتقدم."]
    return insights

# الشريط الجانبي
with st.sidebar:
    if current_user:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 15px; border-radius: 10px; text-align: center;">
            <div>👤 {current_user['name']}</div>
            <div style="font-size: 12px;">⭐ {current_user['plan']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu = {
        "home": "🏠 الرئيسية",
        "pricing": "💰 الأسعار",
        "data_import": "📥 استيراد البيانات",
        "eda": "📊 التحليل الاستكشافي",
        "diagnostic": "🔍 التحليل التشخيصي",
        "predictive": "🔮 التحليل التنبؤي",
        "prescriptive": "💡 التحليل الإرشادي",
        "ai_chat": "🤖 المساعد الذكي",
        "export": " التصدير"
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
        st.rerun()

# ==================== الصفحات ====================

if st.session_state.page == "home":
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1>Smart Analytics Pro</h1>
        <p style="font-size: 20px; color: #4a5568;">منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p>
    </div>
    """)
    
    if current_user:
        st.info(f"### مرحباً {current_user['name']}! 👋\n\n**ابدأ برفع بياناتك من صفحة 'استيراد البيانات'**")

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🆓 Free\n### $0/شهر")
        st.markdown("- 3 مشاريع\n- تحليل استكشافي")
        st.button("اشترك", use_container_width=True, key="sub_free")
    
    with col2:
        st.markdown("### ⭐ Pro\n### $19/شهر")
        st.markdown("- مشاريع غير محدودة\n- كل التحليلات")
        st.button("اشترك", use_container_width=True, type="primary", key="sub_pro")
    
    with col3:
        st.markdown("### 🏢 Enterprise\n### $99/شهر")
        st.markdown("- كل المميزات\n- White-Label")
        st.button("اشترك", use_container_width=True, key="sub_ent")

elif st.session_state.page == "data_import":
    st.markdown("## 📥 استيراد البيانات")
    
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ تم الرفع بنجاح! {len(df)} صف")
            st.dataframe(df.head())

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
        st.warning("️ ارفع بيانات أولاً")
    else:
        st.success("✅ البيانات جيدة للتحليل")
        st.markdown("**التوصيات:**\n1. راجع القيم المفقودة\n2. ركز على الفئات الأعلى أداءً")

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
                st.write(f" الأعمدة: {', '.join(st.session_state.df.columns.tolist())}")
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
st.markdown("<div style='text-align: center; color: #718096;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
