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
            <div style="font-size: 50px; margin-bottom: 10px;">👤</div>
            <div style="font-size: 18px; font-weight: bold; color: white;">{current_user['name']}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;">⭐ {current_user['plan']} Plan</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📍 التنقل السريع")
    menu = {"home": "🏠 الرئيسية", "pricing": "💰 الأسعار", "data_import": "📥 استيراد البيانات", "readiness": "✅ جاهزية البيانات", "cleaning": "🧹 تنظيف البيانات", "summary": "📋 ملخص البيانات", "eda": "📊 التحليل الاستكشافي", "diagnostic": "🔍 التحليل التشخيصي", "predictive": "🔮 التحليل التنبؤي", "prescriptive": "💡 التحليل الإرشادي", "ai_chat": " المساعد الذكي", "export": "💾 التصدير"}
    for key, label in menu.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"): st.session_state.page = key; st.rerun()
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True, key="btn_logout"): st.session_state.logged_in = False; st.session_state.current_user = None; st.session_state.page = "home"; st.session_state.show_register = False; st.rerun()
    if st.session_state.df is not None:
        st.markdown(f"""<div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 12px; margin-top: 20px;"><div style="color: white; font-size: 14px;">✅ البيانات محملة: {len(st.session_state.df)} صف</div></div>""", unsafe_allow_html=True)

# ==================== الصفحات الأساسية ====================
if st.session_state.page == "home":
    st.markdown("""<div class="hero-section"><h1>Smart Analytics Pro</h1><p>منصة احترافية لتحليل البيانات والذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">📊</div><h3>التحليل الاستكشافي</h3><p>فهم شامل لبياناتك مع رسوم بيانية تفاعلية</p></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;"></div><h3>التحليل التشخيصي</h3><p>اكتشف الأنماط والشذوذ في بياناتك</p></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">🔮</div><h3>التحليل التنبؤي</h3><p>تنبؤات دقيقة باستخدام الذكاء الاصطناعي</p></div>""", unsafe_allow_html=True)
    with col4: st.markdown("""<div class="feature-card"><div style="font-size: 60px; margin-bottom: 20px;">💡</div><h3>التحليل الإرشادي</h3><p>توصيات عملية لزيادة العائد على الاستثمار</p></div>""", unsafe_allow_html=True)
    if current_user:
        st.markdown(f"""<div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; margin-top: 40px; border-left: 5px solid #48bb78;"><h3>👋 مرحباً {current_user['name']}!</h3><p><strong>ابدأ الآن في 4 خطوات:</strong></p><ol><li>📥 استيراد البيانات</li><li>✅ فحص جاهزية البيانات</li><li>🧹 تنظيف البيانات (إذا لزم الأمر)</li><li> التحليل الاستكشافي</li></ol></div>""", unsafe_allow_html=True)

elif st.session_state.page == "pricing":
    st.markdown("## 💰 باقات الاشتراك")
    col1, col2, col3 = st.columns(3)
    plans = [{"name": "🆓 Free", "price": "$0", "period": "/شهر", "features": ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط"], "button_type": "secondary"},
             {"name": "⭐ Pro", "price": "$19", "period": "/شهر", "features": ["مشاريع غير محدودة", "تخزين 10GB", "كل التحليلات"], "button_type": "primary", "popular": True},
             {"name": " Enterprise", "price": "$99", "period": "/شهر", "features": ["كل المميزات", "تخزين غير محدود", "API Access"], "button_type": "secondary"}]
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
    st.markdown("##  استيراد البيانات")
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
            else: df = pd.read_excel(uploaded_file)
            st.session_state.df = df; st.session_state.df_clean = None
            st.success(f"✅ تم الرفع! {len(df)} صف، {len(df.columns)} عمود")
            st.dataframe(df.head())
        except Exception as e: st.error(f"خطأ: {e}")

elif st.session_state.page == "readiness":
    st.markdown("## ✅ جاهزية البيانات")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    df = st.session_state.df
    st.metric("الصفوف", len(df)); st.metric("الأعمدة", len(df.columns))
    st.metric("القيم المفقودة", int(df.isnull().sum().sum()))
    st.dataframe(pd.DataFrame({'العمود': df.columns, 'النوع': df.dtypes.astype(str), 'المفقودة': df.isnull().sum().values}))

elif st.session_state.page == "cleaning":
    st.markdown("## 🧹 تنظيف البيانات")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    if st.button("تنظيف تلقائي"):
        df = st.session_state.df.copy()
        df = df.dropna()
        df = df.drop_duplicates()
        st.session_state.df_clean = df
        st.success(f"✅ تم التنظيف! {len(df)} صف متبقي")

elif st.session_state.page == "summary":
    st.markdown("## 📋 ملخص البيانات")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    if df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    st.metric("الصفوف", len(df)); st.metric("الأعمدة", len(df.columns))
    st.dataframe(df.head(10))

# ==============================================================================
# ==================== صفحة EDA الاحترافية الكاملة =============================
# ==============================================================================
elif st.session_state.page == "eda":
    st.markdown("## 📊 التحليل الاستكشافي المتقدم (EDA)")
    st.markdown("---")
    df = st.session_state.df_clean if st.session_state.df_clean is not None else st.session_state.df
    
    if df is None:
        st.warning("⚠️ يرجى رفع البيانات أولاً")
        st.stop()
    
    # ==================== اكتشاف ديناميكي للأعمدة ====================
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # فلترة ذكية صارمة للأعمدة الفئوية
    bad_keywords = ['id', 'date', 'time', 'sku', 'code', 'رقم', 'تاريخ', 'كود', 'lastrestock']
    valid_categorical = []
    for col in df.select_dtypes(include=['object', 'category']).columns:
        if any(kw in col.lower() for kw in bad_keywords):
            continue
        n_unique = df[col].nunique()
        if n_unique > len(df) * 0.5:
            continue
        valid_categorical.append(col)
    
    # ==================== دوال مساعدة ====================
    def build_html_table_manual(dataframe, title=""):
        """تبني جدول HTML يدوياً 100%"""
        html = f"<h3 style='color:#667eea; margin-top:25px; margin-bottom:15px; border-right: 4px solid #764ba2; padding-right: 12px;'>{title}</h3>"
        html += "<table style='width:100%; border-collapse:collapse; margin:15px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05); border-radius:8px; overflow:hidden;'>"
        html += "<thead><tr style='background:#667eea; color:white;'>"
        for c in dataframe.columns:
            html += f"<th style='padding:12px; text-align:right; font-weight:600;'>{str(c)}</th>"
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
    
    def compute_all_statistics(series):
        """حساب جميع المقاييس الإحصائية"""
        cd = series.dropna()
        if len(cd) == 0: return None
        
        # النزعة المركزية
        mean_val = cd.mean()
        median_val = cd.median()
        mode_val = cd.mode().iloc[0] if len(cd.mode()) > 0 else np.nan
        
        # التشتت
        std_val = cd.std()
        var_val = cd.var()
        range_val = cd.max() - cd.min()
        min_val = cd.min()
        max_val = cd.max()
        
        # الموضع
        q1 = cd.quantile(0.25)
        q2 = cd.quantile(0.50)
        q3 = cd.quantile(0.75)
        iqr = q3 - q1
        p10 = cd.quantile(0.10)
        p90 = cd.quantile(0.90)
        
        # الانحناء والتفلطح
        skew_val = cd.skew()
        kurt_val = cd.kurtosis()
        
        # التفسيرات
        if abs(skew_val) < 0.5: skew_i = "متماثل تقريباً"
        elif skew_val > 1: skew_i = "منحرف بشدة لليمين"
        elif skew_val > 0: skew_i = "منحرف لليمين"
        elif skew_val > -1: skew_i = "منحرف لليسار"
        else: skew_i = "منحرف بشدة لليسار"
        
        if kurt_val > 3: kurt_i = "مدبب (ذيول ثقيلة)"
        elif kurt_val > 0: kurt_i = "متوسط التفلطح"
        else: kurt_i = "مفلطح (ذيول خفيفة)"
        
        return {
            'count': len(cd), 'mean': mean_val, 'median': median_val, 'mode': mode_val,
            'std': std_val, 'var': var_val, 'range': range_val, 'min': min_val, 'max': max_val,
            'q1': q1, 'q2': q2, 'q3': q3, 'iqr': iqr, 'p10': p10, 'p90': p90,
            'skew': skew_val, 'kurt': kurt_val, 'skew_i': skew_i, 'kurt_i': kurt_i
        }
    
    # ==================== زر التصدير ====================
    st.markdown("### 📥 تصدير التقارير")
    if st.button("📥 تصدير تقرير EDA شامل واحترافي (HTML)", type="primary", key="btn_export_eda"):
        with st.spinner("جاري إنشاء التقرير الشامل... يرجى الانتظار"):
            try:
                html_parts = []
                
                # بداية HTML
                html_parts.append(f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<title>تقرير التحليل الاستكشافي الشامل</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Cairo', 'Segoe UI', Tahoma, Arial, sans-serif; background: #f8f9fa; color: #2d3748; line-height: 1.6; direction: rtl; text-align: right; padding: 20px; }}
    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 12px; margin-bottom: 30px; }}
    .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
    .cards {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
    .card {{ background: white; padding: 20px; border-radius: 12px; flex: 1; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; border-top: 4px solid #667eea; }}
    .card .label {{ color: #718096; font-size: 14px; margin-bottom: 5px; }}
    .card .value {{ color: #2d3748; font-size: 28px; font-weight: bold; margin-top: 5px; }}
    .section {{ background: white; padding: 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
    .section h2 {{ color: #764ba2; border-bottom: 3px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; font-size: 22px; }}
    .chart {{ margin: 20px 0; padding: 15px; background: white; border-radius: 8px; min-height: 350px; border: 1px solid #e2e8f0; }}
    .note {{ background: #fffaf0; border-right: 5px solid #ed8936; padding: 15px; margin: 20px 0; border-radius: 8px; color: #c05621; font-size: 14px; }}
    .footer {{ text-align: center; padding: 30px; color: #718096; background: white; margin-top: 30px; border-top: 1px solid #e2e8f0; border-radius: 12px; }}
    @media print {{
        .section, .chart {{ break-inside: avoid; page-break-inside: avoid; }}
        th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
</style>
</head>
<body>
<div class="header">
    <h1>📊 تقرير التحليل الاستكشافي الشامل</h1>
    <p>Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
<div class="cards">
    <div class="card"><div class="label">إجمالي السجلات</div><div class="value">{len(df):,}</div></div>
    <div class="card"><div class="label">الأعمدة</div><div class="value">{len(df.columns)}</div></div>
    <div class="card"><div class="label">الرقمية</div><div class="value">{len(numeric_cols)}</div></div>
    <div class="card"><div class="label">الفئوية</div><div class="value">{len(valid_categorical)}</div></div>
</div>""")
                
                # 1. الجداول التكرارية
                html_parts.append("<div class='section'><h2>📋 1. الجداول التكرارية (أعلى 15 قيمة)</h2>")
                html_parts.append("<p style='color:#718096; margin-bottom:15px; font-size:14px;'>تم استبعاد الأعمدة الفريدة والتواريخ تلقائياً.</p>")
                
                for col in valid_categorical[:5]:
                    freq = df[col].value_counts().head(15).reset_index()
                    freq.columns = ['القيمة', 'التكرار']
                    freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(1)
                    
                    html_parts.append(build_html_table_manual(freq, f"📊 {col}"))
                    
                    fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}", color='التكرار', color_continuous_scale='Blues')
                    fig.update_layout(height=300, xaxis_tickangle=-45)
                    html_parts.append('<div class="chart">')
                    html_parts.append(fig.to_html(full_html=False, include_plotlyjs=True))
                    html_parts.append('</div>')
                
                skipped = [c for c in df.select_dtypes(include=['object', 'category']).columns if c not in valid_categorical]
                if skipped:
                    html_parts.append(f'<div class="note">ℹ️ <strong>ملاحظة:</strong> تم استبعاد: <strong>{", ".join(skipped)}</strong></div>')
                html_parts.append("</div>")
                
                # 2. المقاييس الإحصائية الشاملة
                html_parts.append("<div class='section'><h2> 2. المقاييس الإحصائية الشاملة</h2>")
                
                for col in numeric_cols:
                    stats = compute_all_statistics(df[col])
                    if stats is None: continue
                    
                    # جدول النزعة المركزية والتشتت
                    central_df = pd.DataFrame({
                        'المقياس': ['العدد', 'المتوسط', 'الوسيط', 'المنوال', 'الانحراف المعياري', 'التباين', 'المدى', 'الحد الأدنى', 'الحد الأقصى'],
                        'القيمة': [f"{stats['count']}", f"{stats['mean']:.2f}", f"{stats['median']:.2f}", f"{stats['mode']:.2f}", 
                                  f"{stats['std']:.2f}", f"{stats['var']:.2f}", f"{stats['range']:.2f}", f"{stats['min']:.2f}", f"{stats['max']:.2f}"]
                    })
                    html_parts.append(build_html_table_manual(central_df, f"📊 {col} - النزعة المركزية والتشتت"))
                    
                    # جدول مقاييس الموضع
                    position_df = pd.DataFrame({
                        'المقياس': ['Q1 (25%)', 'Q2 (50%)', 'Q3 (75%)', 'IQR', 'P10', 'P90'],
                        'القيمة': [f"{stats['q1']:.2f}", f"{stats['q2']:.2f}", f"{stats['q3']:.2f}", f"{stats['iqr']:.2f}", f"{stats['p10']:.2f}", f"{stats['p90']:.2f}"]
                    })
                    html_parts.append(build_html_table_manual(position_df, f" {col} - مقاييس الموضع"))
                    
                    # جدول الانحناء والتفلطح
                    shape_df = pd.DataFrame({
                        'المقياس': ['الانحناء (Skewness)', 'التفسير', 'التفلطح (Kurtosis)', 'التفسير'],
                        'القيمة': [f"{stats['skew']:.2f}", stats['skew_i'], f"{stats['kurt']:.2f}", stats['kurt_i']]
                    })
                    html_parts.append(build_html_table_manual(shape_df, f"📐 {col} - الانحناء والتفلطح"))
                    
                    # رسم بياني للتوزيع
                    fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
                    fig.add_vline(x=stats['mean'], line_dash="dash", line_color="red", annotation_text=f"Mean: {stats['mean']:.1f}")
                    fig.update_layout(height=300)
                    html_parts.append('<div class="chart">')
                    html_parts.append(fig.to_html(full_html=False, include_plotlyjs=True))
                    html_parts.append('</div>')
                html_parts.append("</div>")
                
                # 3. Box Plots
                html_parts.append("<div class='section'><h2>📦 3. مخططات الصندوق (Box Plots)</h2>")
                for col in numeric_cols:
                    stats = compute_all_statistics(df[col])
                    if stats is None: continue
                    
                    q1, q2, q3 = stats['q1'], stats['q2'], stats['q3']
                    iqr = stats['iqr']
                    outliers = len(df[(df[col] < q1-1.5*iqr) | (df[col] > q3+1.5*iqr)])
                    
                    box_df = pd.DataFrame({
                        'المقياس': ['Min', 'Q1', 'Median', 'Q3', 'Max', 'IQR', 'Outliers'],
                        'القيمة': [f"{stats['min']:.2f}", f"{q1:.2f}", f"{q2:.2f}", f"{q3:.2f}", f"{stats['max']:.2f}", f"{iqr:.2f}", str(outliers)]
                    })
                    
                    html_parts.append(build_html_table_manual(box_df, f"📦 {col}"))
                    
                    fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
                    fig.update_layout(height=300)
                    html_parts.append('<div class="chart">')
                    html_parts.append(fig.to_html(full_html=False, include_plotlyjs=True))
                    html_parts.append('</div>')
                html_parts.append("</div>")
                
                html_parts.append("""<div class="footer">
<p>تم إنشاء هذا التقرير بواسطة <b>Smart Analytics Pro</b></p>
<p>© 2026 جميع الحقوق محفوظة</p>
</div></div></body></html>""")
                
                st.download_button("📥 تحميل التقرير", data="".join(html_parts), 
                                 file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html")
                st.success("✅ تم إنشاء التقرير!")
            except Exception as e:
                st.error(f"خطأ: {e}")
                st.exception(e)
    
    # ==================== واجهة العرض التفاعلية ====================
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 الجداول التكرارية", " التصور البياني", "📊 المقاييس الإحصائية", "📦 Box Plots"])
    
    with tab1:
        st.markdown("### 📋 الجداول التكرارية")
        if valid_categorical:
            col = st.selectbox("اختر المتغير الفئوي", valid_categorical, key="tab1_cat")
            freq = df[col].value_counts().head(20).reset_index()
            freq.columns = ['القيمة', 'التكرار']
            freq['النسبة %'] = (freq['التكرار'] / len(df) * 100).round(1)
            st.dataframe(freq, use_container_width=True)
            fig = px.bar(freq, x='القيمة', y='التكرار', title=f"توزيع {col}", color='التكرار', color_continuous_scale='Blues')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, key="plot_tab1")
        else:
            st.info("لا توجد متغيرات فئوية صالحة")
    
    with tab2:
        st.markdown("###  التصور البياني")
        viz_type = st.selectbox("اختر نوع التصور", ["Histogram", "Bar Chart", "Heatmap"], key="tab2_viz")
        if viz_type == "Histogram" and numeric_cols:
            col = st.selectbox("اختر العمود", numeric_cols, key="tab2_hist")
            fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
            st.plotly_chart(fig, use_container_width=True, key="plot_tab2_hist")
        elif viz_type == "Bar Chart" and valid_categorical:
            col = st.selectbox("اختر العمود", valid_categorical, key="tab2_bar")
            vc = df[col].value_counts().head(15)
            fig = px.bar(x=vc.values, y=vc.index, orientation='h', title=f"توزيع {col}", color=vc.values, color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True, key="plot_tab2_bar")
        elif viz_type == "Heatmap" and len(numeric_cols) >= 2:
            fig = px.imshow(df[numeric_cols].corr(), text_auto=".2f", aspect="auto", title="مصفوفة الارتباط", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True, key="plot_tab2_heat")
    
    with tab3:
        st.markdown("### 📊 المقاييس الإحصائية الشاملة")
        if numeric_cols:
            col = st.selectbox("اختر العمود الرقمي", numeric_cols, key="tab3_stat")
            stats = compute_all_statistics(df[col])
            if stats:
                st.markdown("#### 📍 النزعة المركزية")
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("المتوسط (Mean)", f"{stats['mean']:.2f}")
                with c2: st.metric("الوسيط (Median)", f"{stats['median']:.2f}")
                with c3: st.metric("المنوال (Mode)", f"{stats['mode']:.2f}")
                
                st.markdown("#### 📏 مقاييس التشتت")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("الانحراف المعياري", f"{stats['std']:.2f}")
                with c2: st.metric("التباين", f"{stats['var']:.2f}")
                with c3: st.metric("المدى", f"{stats['range']:.2f}")
                with c4: st.metric("العدد", f"{stats['count']}")
                
                st.markdown("#### 📍 مقاييس الموضع")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Q1 (25%)", f"{stats['q1']:.2f}")
                with c2: st.metric("Q2 (50%)", f"{stats['q2']:.2f}")
                with c3: st.metric("Q3 (75%)", f"{stats['q3']:.2f}")
                with c4: st.metric("IQR", f"{stats['iqr']:.2f}")
                
                st.markdown("#### 📐 الانحناء والتفلطح")
                c1, c2 = st.columns(2)
                with c1: st.info(f"**الانحناء (Skewness):** {stats['skew']:.4f}\n\n*التفسير:* {stats['skew_i']}")
                with c2: st.info(f"**التفلطح (Kurtosis):** {stats['kurt']:.4f}\n\n*التفسير:* {stats['kurt_i']}")
                
                fig = px.histogram(df, x=col, nbins=30, title=f"توزيع {col}", color_discrete_sequence=['#667eea'])
                fig.add_vline(x=stats['mean'], line_dash="dash", line_color="red", annotation_text=f"Mean: {stats['mean']:.2f}")
                st.plotly_chart(fig, use_container_width=True, key="plot_tab3")
        else:
            st.info("لا توجد متغيرات رقمية")
    
    with tab4:
        st.markdown("### 📦 Box Plots")
        if numeric_cols:
            col = st.selectbox("اختر العمود", numeric_cols, key="tab4_box")
            fig = px.box(df, y=col, title=f"Box Plot - {col}", color_discrete_sequence=['#667eea'])
            st.plotly_chart(fig, use_container_width=True, key="plot_tab4_single")
            
            if len(numeric_cols) <= 10:
                st.markdown("#### Box Plot لجميع المتغيرات الرقمية")
                df_melted = df[numeric_cols].melt(var_name='المتغير', value_name='القيمة')
                fig_all = px.box(df_melted, x='المتغير', y='القيمة', title="Box Plot لجميع المتغيرات", color='المتغير')
                fig_all.update_layout(height=500)
                st.plotly_chart(fig_all, use_container_width=True, key="plot_tab4_all")
        else:
            st.info("لا توجد متغيرات رقمية")

elif st.session_state.page == "diagnostic":
    st.markdown("## 🔍 التحليل التشخيصي")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    st.info("سيتم التطوير قريباً")

elif st.session_state.page == "predictive":
    st.markdown("## 🔮 التحليل التنبؤي")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    st.info("سيتم التطوير قريباً")

elif st.session_state.page == "export":
    st.markdown("## 💾 التصدير")
    if st.session_state.df is None: st.warning("ارفع بيانات أولاً"); st.stop()
    df = st.session_state.df_clean if st.session_state.df_clean else st.session_state.df
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(" CSV", csv, "data.csv", "text/csv")

st.markdown("---")
st.markdown("<div style='text-align:center; color:#718096; padding:20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
