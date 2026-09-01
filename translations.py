TRANSLATIONS = {
    "ar": {
        "app_title": "Smart Analytics Pro",
        "sidebar": {
            "home": "الرئيسية",
            "pricing": "باقات الاشتراك",
            "dashboard": "لوحة التحكم",
            "data_import": "استيراد البيانات",
            "eda": "التحليل الاستكشافي (EDA)",
            "diagnostic": "التحليل التشخيصي",
            "predictive": "التحليل التنبؤي",
            "prescriptive": "التحليل الإرشادي",
            "ai_chat": "المساعد الذكي",
            "export": "مركز التصدير"
        },
        "messages": {
            "welcome": "مرحباً بك في منصة Smart Analytics Pro لتحليل البيانات",
            "upload_data": "يرجى استيراد البيانات أولاً من القائمة الجانبية",
            "success_upload": "تم تحميل البيانات بنجاح! عدد الصفوف: {}",
            "no_data": "لا توجد بيانات محملة حالياً.",
            "ai_thinking": "جاري تحليل البيانات واستخراج الرؤى..."
        },
        "buttons": {
            "login": "تسجيل الدخول",
            "upload": "رفع الملف",
            "analyze": "تحليل",
            "export_csv": "تصدير كـ CSV",
            "export_excel": "تصدير كـ Excel"
        },
        "ai_insights": {
            "high_correlation": "🔍 تم اكتشاف علاقة قوية جداً بين {} و {} (نسبة ارتباط {})",
            "missing_values": "⚠️ تنبيه: العمود {} يحتوي على {} قيمة مفقودة (نسبة {}%). يُنصح بمعالجتها.",
            "top_category": "🏆 الفئة الأعلى أداءً هي {} بقيمة إجمالية {}."
        }
    },
    "en": {
        "app_title": "Smart Analytics Pro",
        "sidebar": {
            "home": "Home",
            "pricing": "Pricing",
            "dashboard": "Dashboard",
            "data_import": "Data Import",
            "eda": "Exploratory Data Analysis",
            "diagnostic": "Diagnostic Analysis",
            "predictive": "Predictive Analysis",
            "prescriptive": "Prescriptive Analysis",
            "ai_chat": "AI Assistant",
            "export": "Export Center"
        },
        "messages": {
            "welcome": "Welcome to Smart Analytics Pro Data Platform",
            "upload_data": "Please import data first from the sidebar",
            "success_upload": "Data uploaded successfully! Rows: {}",
            "no_data": "No data loaded currently.",
            "ai_thinking": "Analyzing data and generating insights..."
        },
        "buttons": {
            "login": "Login",
            "upload": "Upload File",
            "analyze": "Analyze",
            "export_csv": "Export as CSV",
            "export_excel": "Export as Excel"
        },
        "ai_insights": {
            "high_correlation": "🔍 Strong correlation detected between {} and {} (Correlation: {})",
            "missing_values": "⚠️ Warning: Column {} has {} missing values ({}%). Processing recommended.",
            "top_category": "🏆 Top performing category is {} with total value {}."
        }
    }
}

def get_text(key, lang="ar", *args):
    keys = key.split(".")
    val = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])
    for k in keys:
        val = val.get(k, key)
    if args:
        return val.format(*args)
    return val
