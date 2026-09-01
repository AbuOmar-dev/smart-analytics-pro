import streamlit as st

# إعدادات المنصة العامة
APP_CONFIG = {
    "app_name": "Smart Analytics Pro",
    "version": "1.0.0",
    "default_language": "ar",
    "max_file_size_mb": 500,
    "theme": {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730",
        "font": "sans serif"
    }
}

# إعدادات محاكاة نظام الاشتراكات (للعرض المحلي)
SUBSCRIPTION_PLANS = {
    "Free": {"projects": 3, "storage_mb": 100, "features": ["EDA", "PDF_Export_Watermarked"]},
    "Pro": {"projects": -1, "storage_mb": 10240, "features": ["EDA", "Diagnostic", "Predictive", "Prescriptive", "AI_Chat", "All_Exports"]},
    "Enterprise": {"projects": -1, "storage_mb": -1, "features": ["All", "White_Label", "API_Access", "SSO"]}
}

# إعدادات المحاكاة المحلية للذكاء الاصطناعي (بدون API Keys مدفوعة)
AI_LOCAL_CONFIG = {
    "enable_mock_insights": True,
    "correlation_threshold": 0.7,
    "anomaly_z_score_threshold": 3.0
}
