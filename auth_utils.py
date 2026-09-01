import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from datetime import datetime
import pandas as pd

def load_config():
    """تحميل ملف التكوين"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return None

def initialize_authenticator():
    """تهيئة نظام المصادقة"""
    config = load_config()
    if config is None:
        return None
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    return authenticator

def check_authentication():
    """التحقق من تسجيل الدخول"""
    if 'authentication_status' not in st.session_state:
        return False
    
    if st.session_state['authentication_status']:
        return True
    return False

def get_current_user():
    """الحصول على المستخدم الحالي"""
    if check_authentication():
        return {
            'username': st.session_state['username'],
            'name': st.session_state['name'],
            'email': st.session_state['email']
        }
    return None

def check_user_role(required_role=None):
    """التحقق من صلاحية المستخدم"""
    user = get_current_user()
    if user is None:
        return False
    
    config = load_config()
    if config is None:
        return False
    
    username = user['username']
    if username not in config['credentials']['usernames']:
        return False
    
    user_role = config['credentials']['usernames'][username].get('role', 'user')
    
    if required_role is None:
        return True
    
    if required_role == 'admin' and user_role == 'admin':
        return True
    elif required_role == 'user':
        return True
    
    return False

def log_user_activity(username, activity):
    """تسجيل نشاط المستخدم"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'activity': activity
    }
    
    # هنا يمكن حفظ السجل في قاعدة بيانات لاحقاً
    # حالياً بنطبعه فقط
    st.write(f"📝 Activity Log: {log_entry}")

def get_user_subscription_plan(username):
    """الحصول على خطة اشتراك المستخدم"""
    config = load_config()
    if config is None:
        return 'Free'
    
    if username in config['credentials']['usernames']:
        return config['credentials']['usernames'][username].get('subscription_plan', 'Free')
    return 'Free'

def check_feature_access(feature_name):
    """التحقق من صلاحية الوصول للميزة"""
    user = get_current_user()
    if user is None:
        return False
    
    plan = get_user_subscription_plan(user['username'])
    
    # تحديد الميزات المتاحة لكل خطة
    feature_permissions = {
        'Free': ['basic_eda', 'basic_export'],
        'Pro': ['basic_eda', 'advanced_eda', 'diagnostic', 'predictive', 'advanced_export', 'ai_chat'],
        'Enterprise': ['basic_eda', 'advanced_eda', 'diagnostic', 'predictive', 'prescriptive', 
                      'advanced_export', 'ai_chat', 'white_label', 'api_access']
    }
    
    return feature_name in feature_permissions.get(plan, [])

def display_user_info():
    """عرض معلومات المستخدم في الشريط الجانبي"""
    user = get_current_user()
    if user:
        plan = get_user_subscription_plan(user['username'])
        st.sidebar.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 15px; border-radius: 10px; margin: 10px 0;
                    text-align: center;">
            <div style="font-size: 14px;">👤 {user['name']}</div>
            <div style="font-size: 12px; margin-top: 5px;">⭐ {plan} Plan</div>
        </div>
        """, unsafe_allow_html=True)
