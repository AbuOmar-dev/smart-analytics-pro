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

# استيراد الملفات المحلية
import config
from translations import get_text

# إعدادات الصفحة
st.set_page_config(
    page_title=config.APP_CONFIG["app_name"],
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تهيئة الحالة (Session State)
if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "df" not in st.session_state:
    st.session_state.df = None

# دوال مساعدة
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
    """محرك رؤى ذكي محلي بدون الحاجة لـ API خارجي"""
    insights = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 1. تحليل القيم المفقودة
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            pct = round((count / len(df)) * 100, 1)
            if pct > 5:
                insights.append(get_text("ai_insights.missing_values", lang, col, count, pct))

    # 2. تحليل الارتباط (إذا وجد أكثر من عمود رقمي)
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr().abs()
        np.fill_diagonal(corr_matrix.values, 0)
        max_corr = corr_matrix.unstack().dropna().sort_values(ascending=False)
        if len(max_corr) > 0:
            top_corr = max_corr.index[0]
            val = round(max_corr.iloc[0], 2)
            if val > config.AI_LOCAL_CONFIG["correlation_threshold"]:
                insights.append(get_text("ai_insights.high_correlation", lang, top_corr[0], top_corr[1], val))

    # 3. تحليل الفئات الأعلى أداءً
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        if df[cat_col].nunique() < 20:
            top_cat = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(1)
            insights.append(get_text("ai_insights.top_category", lang, top_cat.index[0], round(top_cat.values[0], 2)))

    if not insights:
        return ["✅ البيانات تبدو نظيفة وجيدة للتحليل المتقدم."]
    return insights

# --- واجهة المستخدم ---

# الشريط الجانبي
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2702/2702602.png", width=60)
    st.title(config.APP_CONFIG["app_name"])
    
    # اختيار اللغة
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("🇪🇬 عربي", use_container_width=True):
            set_language("ar")
            st.rerun()
    with lang_col2:
        if st.button("🇧 English", use_container_width=True):
            set_language("en")
            st.rerun()

    st.divider()
    
    # قائمة التنقل
    menu = {
        "home": get_text("sidebar.home", st.session_state.lang),
        "pricing": get_text("sidebar.pricing", st.session_state.lang),
        "data_import": get_text("sidebar.data_import", st.session_state.lang),
        "eda": get_text("sidebar.eda", st.session_state.lang),
        "diagnostic": get_text("sidebar.diagnostic", st.session_state.lang),
        "predictive": get_text("sidebar.predictive", st.session_state.lang),
        "prescriptive": get_text("sidebar.prescriptive", st.session_state.lang),
        "ai_chat": get_text("sidebar.ai_chat", st.session_state.lang),
        "export": get_text("sidebar.export", st.session_state.lang)
    }
    
    for key, label in menu.items():
        if st.button(label, use_container_width=True, type="primary" if st.session_state.page == key else "secondary"):
            navigate_to(key)
            st.rerun()

# --- الصفحات ---

if st.session_state.page == "home":
    st.title(get_text("app_title", st.session_state.lang))
    st.markdown(f"### {get_text('messages.welcome', st.session_state.lang)}")
    st.markdown("""
    منصة متكاملة لتحليل البيانات تعتمد على منهجية 'من الداتا للداشبورد' المكونة من 4 مراحل رئيسية.
    
    ✅ **تحليل استكشافي (EDA)**: فهم شكل وتشتت ومركزية البيانات.
    ✅ **تحليل تشخيصي**: معرفة أسباب الأنماط والشذوذ.
    ✅ **تحليل تنبؤي**: بناء نماذج Machine Learning للتنبؤ بالمستقبل.
    ✅ **تحليل إرشادي**: توصيات عملية مبنية على البيانات لزيادة الـ ROI.
    
    *ابدأ رحلتك من خلال استيراد بياناتك من القائمة الجانبية.*
    """)
    st.info("💡 هذه النسخة تعمل محلياً بنسبة 100% بدون الحاجة لأي مفاتيح API مدفوعة.")

elif st.session_state.page == "pricing":
    st.title(get_text("sidebar.pricing", st.session_state.lang))
    col1, col2, col3 = st.columns(3)
    
    plans = [
        ("🆓 Free", "0$", ["3 مشاريع نشطة", "تخزين 100MB", "تحليل استكشافي فقط", "تصدير PDF بعلامة مائية"]),
        ("⭐ Pro", "19$/شهر", ["مشاريع غير محدودة", "تخزين 10GB", "كل أنواع التحليلات الأربعة", "تصدير بكل الصيغ", "محرك الرؤى الذكي"]),
        ("🏢 Enterprise", "99$/شهر", ["كل مميزات Pro", "تخزين غير محدود", "White-Label كامل", "API Access", "مدير حساب مخصص"])
    ]
    
    for i, (name, price, features) in enumerate(plans):
        with [col1, col2, col3][i]:
            st.subheader(name)
            st.header(price)
            for feature in features:
                st.markdown(f"- {feature}")
            st.button("اشترك الآن", use_container_width=True, type="primary" if i==1 else "secondary")

elif st.session_state.page == "data_import":
    st.title(get_text("sidebar.data_import", st.session_state.lang))
    uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success(get_text("messages.success_upload", st.session_state.lang, len(df)))
            st.subheader("معاينة البيانات (أول 5 صفوف)")
            st.dataframe(df.head())
            
            col1, col2, col3 = st.columns(3)
            col1.metric("عدد الصفوف", len(df))
            col2.metric("عدد الأعمدة", len(df.columns))
            col3.metric("حجم الملف", f"{uploaded_file.size / 1024:.2f} KB")

elif st.session_state.page == "eda":
    st.title(get_text("sidebar.eda", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        df = st.session_state.df
        st.subheader("1. ملخص إحصائي شامل")
        st.dataframe(df.describe())
        
        st.subheader("2. تحليل القيم المفقودة")
        missing_data = df.isnull().sum().reset_index()
        missing_data.columns = ['Column', 'Missing Count']
        missing_data = missing_data[missing_data['Missing Count'] > 0]
        if not missing_data.empty:
            fig = px.bar(missing_data, x='Column', y='Missing Count', title="القيم المفقودة لكل عمود", color='Missing Count')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("ممتاز! لا توجد قيم مفقودة في البيانات.")

        st.subheader("3. مصفوفة الارتباط (Correlation Matrix)")
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr = numeric_df.corr()
            fig_heatmap = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("لا توجد أعمدة رقمية كافية لرسم مصفوفة الارتباط.")

elif st.session_state.page == "diagnostic":
    st.title(get_text("sidebar.diagnostic", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        st.subheader("كشف الشذوذ (Anomaly Detection) - Z-Score Method")
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            target_col = st.selectbox("اختر العمود الرقمي للفحص", numeric_cols)
            threshold = st.slider("حد الشذوذ (Z-Score Threshold)", 2.0, 4.0, 3.0)
            
            if st.button("تشخيص البيانات"):
                mean = np.mean(st.session_state.df[target_col])
                std = np.std(st.session_state.df[target_col])
                z_scores = np.abs((st.session_state.df[target_col] - mean) / std)
                
                st.session_state.df['Is_Anomaly'] = z_scores > threshold
                anomalies = st.session_state.df[st.session_state.df['Is_Anomaly']]
                
                col1, col2 = st.columns(2)
                col1.metric("إجمالي السجلات", len(st.session_state.df))
                col2.metric("حالات الشذوذ المكتشفة", len(anomalies), delta=f"{(len(anomalies)/len(st.session_state.df))*100:.1f}%")
                
                if len(anomalies) > 0:
                    st.write("عينة من حالات الشذوذ:")
                    st.dataframe(anomalies.head(10))

elif st.session_state.page == "predictive":
    st.title(get_text("sidebar.predictive", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        st.info("يتم استخدام نموذج Linear Regression محلي للتنبؤ البسيط.")
        numeric_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= 2:
            target = st.selectbox("اختر العمود المراد التنبؤ به (Target)", numeric_cols)
            feature = st.selectbox("اختر عمود الميزة (Feature)", [c for c in numeric_cols if c != target])
            
            if st.button("بناء النموذج والتنبؤ"):
                X = st.session_state.df[[feature]].values
                y = st.session_state.df[target].values
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                model = LinearRegression()
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                r2 = r2_score(y_test, predictions)
                st.metric("دقة النموذج (R² Score)", f"{r2:.2f}")
                
                fig = px.scatter(x=y_test, y=predictions, labels={'x': 'Actual', 'y': 'Predicted'}, title="Actual vs Predicted")
                fig.add_shape(type="line", line=dict(dash='dash'), x0=min(y_test), y0=min(y_test), x1=max(y_test), y1=max(y_test))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("تحتاج إلى عمودين رقميين على الأقل لإجراء التحليل التنبؤي.")

elif st.session_state.page == "prescriptive":
    st.title(get_text("sidebar.prescriptive", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        st.subheader("التوصيات الإرشادية المبنية على البيانات")
        with st.spinner(get_text("messages.ai_thinking", st.session_state.lang)):
            insights = generate_local_ai_insights(st.session_state.df, st.session_state.lang)
            for insight in insights:
                st.info(insight)
        
        st.markdown("### خطة العمل المقترحة (Action Plan)")
        st.markdown("""
        1. **معالجة البيانات**: ابدأ بتنظيف القيم المفقودة التي تم تحديدها في التحليل الاستكشافي.
        2. **التحسين**: ركز على الفئات ذات الأداء الأعلى لتعزيز العائد (ROI).
        3. **المراقبة**: راقب حالات الشذوذ التي تم اكتشافها بشكل دوري.
        """)

elif st.session_state.page == "ai_chat":
    st.title(get_text("sidebar.ai_chat", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        st.markdown("اسأل أسئلة عملية عن بياناتك (محاكاة ذكية محلية).")
        prompt = st.text_input("اكتب سؤالك هنا:", placeholder="مثال: ما هو متوسط المبيعات؟ أو ما هي الأعمدة المتاحة؟")
        
        if prompt:
            with st.spinner("جاري التحليل..."):
                response = ""
                prompt_lower = prompt.lower()
                
                if "عدد" in prompt_lower or "rows" in prompt_lower or "shape" in prompt_lower:
                    response = f"يحتوي جدول البيانات على {len(st.session_state.df)} صف و {len(st.session_state.df.columns)} عمود."
                elif "أعمدة" in prompt_lower or "columns" in prompt_lower:
                    response = f"الأعمدة المتاحة هي: {', '.join(st.session_state.df.columns.tolist())}"
                elif "متوسط" in prompt_lower or "mean" in prompt_lower or "average" in prompt_lower:
                    num_cols = st.session_state.df.select_dtypes(include=[np.number]).columns.tolist()
                    if num_cols:
                        response = f"متوسط القيم للأعمدة الرقمية:\n" + "\n".join([f"- {col}: {st.session_state.df[col].mean():.2f}" for col in num_cols[:3]])
                    else:
                        response = "لا توجد أعمدة رقمية لحساب المتوسط."
                elif "فقد" in prompt_lower or "missing" in prompt_lower:
                    missing = st.session_state.df.isnull().sum().sum()
                    response = f"يوجد إجمالي {missing} قيمة مفقودة في كامل مجموعة البيانات."
                else:
                    response = "عذراً، أنا أركز حالياً على الإحصائيات الوصفية الأساسية. جرب السؤال عن عدد الصفوف، الأعمدة، المتوسطات، أو القيم المفقودة."
                
                st.markdown(f"**🤖 المساعد الذكي:**\n{response}")

elif st.session_state.page == "export":
    st.title(get_text("sidebar.export", st.session_state.lang))
    if st.session_state.df is None:
        st.warning(get_text("messages.upload_data", st.session_state.lang))
    else:
        st.subheader("تصدير البيانات المعالجة")
        col1, col2 = st.columns(2)
        
        csv = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
        col1.download_button(
            label=get_text("buttons.export_csv", st.session_state.lang),
            data=csv,
            file_name=f"smart_analytics_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.df.to_excel(writer, index=False, sheet_name='Data')
        col2.download_button(
            label=get_text("buttons.export_excel", st.session_state.lang),
            data=output.getvalue(),
            file_name=f"smart_analytics_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.success("تم تجهيز الملفات للتصدير بنجاح وبدون علامات مائية (محاكاة لخطة Pro).")

# تذييل الصفحة
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Smart Analytics Pro © 2026 | Built for Business ROI</div>", unsafe_allow_html=True)
