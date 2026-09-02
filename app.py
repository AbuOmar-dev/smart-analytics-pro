import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import io
from datetime import datetime

# ==================== إعدادات الصفحة ====================
st.set_page_config(page_title="Smart Analytics Pro", page_icon="📊", layout="wide")

# ==================== CSS ====================
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton>button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; font-weight: 600; }
    .metric-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; }
    .section-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 20px 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== تهيئة الحالة ====================
if "df" not in st.session_state: st.session_state.df = None
if "df_clean" not in st.session_state: st.session_state.df_clean = None
if "cleaning_steps" not in st.session_state: st.session_state.cleaning_steps = []

# ==================== الدوال المساعدة ====================
def detect_column_types(df):
    """اكتشاف أنواع الأعمدة ديناميكياً"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = []
    categorical_cols = []
    
    for col in df.select_dtypes(exclude=[np.number]).columns:
        try:
            pd.to_datetime(df[col].dropna().head(50))
            datetime_cols.append(col)
        except:
            if df[col].nunique() < min(50, len(df) * 0.5):
                categorical_cols.append(col)
            else:
                pass  # تجاهل الأعمدة النصية الفريدة
    
    return numeric_cols, categorical_cols, datetime_cols

def build_html_table(dataframe, title=""):
    """بناء جدول HTML نقي"""
    html = f"<h4 style='color:#667eea; margin:20px 0 10px 0;'>{title}</h4>"
    html += "<table style='width:100%; border-collapse:collapse; margin:10px 0; font-size:14px;'>"
    html += "<thead><tr style='background:#667eea; color:white;'>"
    for col in dataframe.columns:
        html += f"<th style='padding:10px; text-align:right;'>{col}</th>"
    html += "</tr></thead><tbody>"
    for idx, row in dataframe.iterrows():
        bg = "#f7fafc" if idx % 2 == 0 else "white"
        html += f"<tr style='background:{bg};'>"
        for val in row:
            val_str = str(val) if pd.notna(val) else "-"
            html += f"<td style='padding:8px; border-bottom:1px solid #e2e8f0; text-align:right;'>{val_str}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def interpret_skewness(val):
    if abs(val) < 0.5: return "متماثل تقريباً (توزيع طبيعي)"
    elif val > 0: return f"منحرف لليمين (إيجابي) - معظم البيانات集中在 القيم المنخفضة"
    else: return f"منحرف لليسار (سلبي) - معظم البيانات集中在 القيم العالية"

def interpret_kurtosis(val):
    if val > 3: return "مدبب (Leptokurtic) - ذيول ثقيلة، قيم متطرفة أكثر"
    elif val < 3: return "مفلطح (Platykurtic) - ذيول خفيفة، قيم متطرفة أقل"
    else: return "طبيعي (Mesokurtic) - توزيع طبيعي"

# ==================== الصفحة الرئيسية ====================
st.markdown("<div class='section-header'><h1>📊 Smart Analytics Pro - منصة التحليل الديناميكية</h1></div>", unsafe_allow_html=True)

# ====== المرحلة 1: رفع البيانات ======
st.markdown("### 📥 المرحلة 1: رفع البيانات")
uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=['csv', 'xlsx', 'xls'], key="uploader")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        st.session_state.df_clean = None
        st.success(f"✅ تم رفع البيانات بنجاح: {len(df)} صف، {len(df.columns)} عمود")
    except Exception as e:
        st.error(f" خطأ في قراءة الملف: {e}")
        st.stop()
else:
    st.info(" يرجى رفع ملف للبدء")
    st.stop()

df = st.session_state.df
numeric_cols, categorical_cols, datetime_cols = detect_column_types(df)

# ====== المرحلة 2: عرض البيانات ======
st.markdown("### 👁️ المرحلة 2: استعراض البيانات")
view_option = st.radio("اختر العرض:", ["أول 10 صفوف", "آخر 10 صفوف", "عينة عشوائية"], horizontal=True, key="view_radio")

if view_option == "أول 10 صفوف":
    st.dataframe(df.head(10), use_container_width=True)
elif view_option == "آخر 10 صفوف":
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.dataframe(df.sample(min(10, len(df))), use_container_width=True)

# ====== المرحلة 3: معلومات البيانات ======
st.markdown("### 📋 المرحلة 3: معلومات البيانات (Metadata)")

# معلومات عامة
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("عدد الصفوف", len(df))
with col2: st.metric("عدد الأعمدة", len(df.columns))
with col3: st.metric("الأعمدة الرقمية", len(numeric_cols))
with col4: st.metric("الأعمدة الفئوية", len(categorical_cols))

# معلومات تفصيلية لكل عمود
info_data = []
for col in df.columns:
    info_data.append({
        'العمود': col,
        'النوع': str(df[col].dtype),
        'القيم الفريدة': df[col].nunique(),
        'القيم المفقودة': int(df[col].isnull().sum()),
        'نسبة المفقود %': round(df[col].isnull().sum() / len(df) * 100, 2),
        'أول قيمة': str(df[col].iloc[0]) if len(df) > 0 else '-',
        'آخر قيمة': str(df[col].iloc[-1]) if len(df) > 0 else '-'
    })

st.markdown(build_html_table(pd.DataFrame(info_data), "📊 معلومات تفصيلية لكل عمود"), unsafe_allow_html=True)

# ====== المرحلة 4: ملخص بصري ======
st.markdown("### 📈 المرحلة 4: الملخص البصري للبيانات")
viz_col = st.selectbox("اختر عمود للعرض البصري:", df.columns.tolist(), key="viz_col")

if viz_col in numeric_cols:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(df, x=viz_col, title=f"توزيع {viz_col}", color_discrete_sequence=['#667eea'])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.box(df, y=viz_col, title=f"Box Plot لـ {viz_col}", color_discrete_sequence=['#764ba2'])
        st.plotly_chart(fig, use_container_width=True)
elif viz_col in categorical_cols:
    counts = df[viz_col].value_counts().head(15)
    fig = px.bar(x=counts.values, y=counts.index, orientation='h', title=f"توزيع {viz_col}", color=counts.values, color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"العمود {viz_col} من نوع تاريخ - لا يمكن عرضه بيانياً")

# ====== المرحلة 5: التنظيف والمعالجة ======
st.markdown("###  المرحلة 5: تنظيف ومعالجة البيانات")

if st.session_state.df_clean is not None:
    st.success(f"✅ البيانات المنظفة جاهزة ({len(st.session_state.df_clean)} صف)")
    if st.button("إعادة تعيين التنظيف", key="reset_clean"):
        st.session_state.df_clean = None
        st.session_state.cleaning_steps = []
        st.rerun()
else:
    st.markdown("#### 5.1 معالجة القيم المفقودة")
    missing_cols_with_data = [c for c in df.columns if df[c].isnull().sum() > 0]
    
    if missing_cols_with_data:
        st.info(f"الأعمدة التي تحتوي على قيم مفقودة: {len(missing_cols_with_data)}")
        missing_method = st.selectbox("طريقة المعالجة:", 
            ["حذف الصفوف", "حذف الأعمدة", "تعويض بالمتوسط (رقمي)", "تعويض بالوسيط (رقمي)", "تعويض بالأكثر تكراراً", "لا تفعل شيئاً"],
            key="missing_method")
        
        if st.button("تطبيق معالجة القيم المفقودة", key="apply_missing"):
            df_clean = df.copy()
            if missing_method == "حذف الصفوف":
                before = len(df_clean)
                df_clean = df_clean.dropna()
                st.session_state.cleaning_steps.append(f"حذف {before - len(df_clean)} صف")
            elif missing_method == "حذف الأعمدة":
                before = len(df_clean.columns)
                df_clean = df_clean.dropna(axis=1)
                st.session_state.cleaning_steps.append(f"حذف {before - len(df_clean.columns)} عمود")
            elif "بالمتوسط" in missing_method:
                for c in df_clean.select_dtypes(include=[np.number]).columns:
                    df_clean[c] = df_clean[c].fillna(df_clean[c].mean())
                st.session_state.cleaning_steps.append("تعويض بالمتوسط")
            elif "بالوسيط" in missing_method:
                for c in df_clean.select_dtypes(include=[np.number]).columns:
                    df_clean[c] = df_clean[c].fillna(df_clean[c].median())
                st.session_state.cleaning_steps.append("تعويض بالوسيط")
            elif "بالأكثر" in missing_method:
                for c in df_clean.columns:
                    mode = df_clean[c].mode()
                    if len(mode) > 0:
                        df_clean[c] = df_clean[c].fillna(mode[0])
                st.session_state.cleaning_steps.append("تعويض بالأكثر تكراراً")
            st.session_state.df_clean = df_clean
            st.success("✅ تم التطبيق")
            st.rerun()
    else:
        st.success("✅ لا توجد قيم مفقودة")
    
    st.markdown("#### 5.2 معالجة القيم المتطرفة (Outliers)")
    if numeric_cols:
        outlier_method = st.selectbox("طريقة الكشف:", ["IQR", "Z-Score"], key="outlier_method")
        outlier_action = st.selectbox("الإجراء:", ["لا تفعل شيئاً", "حذف", "استبدال بالحدود"], key="outlier_action")
        
        if st.button("تطبيق معالجة القيم المتطرفة", key="apply_outliers"):
            if st.session_state.df_clean is None:
                df_clean = df.copy()
            else:
                df_clean = st.session_state.df_clean.copy()
            
            for c in numeric_cols:
                if outlier_method == "IQR":
                    Q1, Q3 = df_clean[c].quantile(0.25), df_clean[c].quantile(0.75)
                    IQR = Q3 - Q1
                    lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
                else:
                    mean, std = df_clean[c].mean(), df_clean[c].std()
                    lower, upper = mean - 3*std, mean + 3*std
                
                if outlier_action == "حذف":
                    before = len(df_clean)
                    df_clean = df_clean[(df_clean[c] >= lower) & (df_clean[c] <= upper)]
                    st.session_state.cleaning_steps.append(f"حذف متطرفة من {c}")
                elif outlier_action == "استبدال":
                    df_clean[c] = df_clean[c].clip(lower=lower, upper=upper)
                    st.session_state.cleaning_steps.append(f"استبدال متطرفة في {c}")
            
            st.session_state.df_clean = df_clean
            st.success("✅ تم التطبيق")
            st.rerun()
    else:
        st.info("لا توجد أعمدة رقمية")
    
    st.markdown("#### 5.3 تحويل الفئات (Encoding)")
    if categorical_cols:
        encoding_method = st.selectbox("طريقة التحويل:", ["لا تفعل شيئاً", "Label Encoding", "One-Hot Encoding"], key="encoding_method")
        
        if st.button("تطبيق التحويل", key="apply_encoding"):
            if st.session_state.df_clean is None:
                df_clean = df.copy()
            else:
                df_clean = st.session_state.df_clean.copy()
            
            if encoding_method == "Label Encoding":
                le = LabelEncoder()
                for c in categorical_cols:
                    df_clean[c] = le.fit_transform(df_clean[c].astype(str))
                st.session_state.cleaning_steps.append("Label Encoding")
            elif encoding_method == "One-Hot Encoding":
                df_clean = pd.get_dummies(df_clean, columns=categorical_cols, drop_first=True)
                st.session_state.cleaning_steps.append("One-Hot Encoding")
            
            st.session_state.df_clean = df_clean
            st.success("✅ تم التطبيق")
            st.rerun()
    else:
        st.info("لا توجد أعمدة فئوية")

# ====== المرحلة 6-8: التحليل الاستكشافي ======
st.markdown("### 🔬 التحليل الاستكشافي (EDA)")
df_for_analysis = st.session_state.df_clean if st.session_state.df_clean is not None else df
numeric_a, categorical_a, datetime_a = detect_column_types(df_for_analysis)

eda_tab1, eda_tab2, eda_tab3, eda_tab4 = st.tabs(["📋 الجداول التكرارية", "📊 التحليل الإحصائي", "📦 Box Plots", " Dashboard النهائية"])

# ====== 6. الجداول التكرارية ======
with eda_tab1:
    st.markdown("#### 📋 الجداول التكرارية")
    if categorical_a:
        selected_cat = st.selectbox("اختر عمود فئوي:", categorical_a, key="freq_cat")
        freq_df = df_for_analysis[selected_cat].value_counts().reset_index()
        freq_df.columns = ['القيمة', 'التكرار']
        freq_df['النسبة %'] = (freq_df['التكرار'] / len(df_for_analysis) * 100).round(2)
        st.markdown(build_html_table(freq_df, f"توزيع {selected_cat}"), unsafe_allow_html=True)
        
        fig = px.bar(freq_df.head(15), x='القيمة', y='التكرار', title=f"توزيع {selected_cat}", color='التكرار')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد أعمدة فئوية")

# ====== 7. التحليل الإحصائي ======
with eda_tab2:
    st.markdown("#### 📊 التحليل الإحصائي الشامل")
    
    if numeric_a:
        selected_num = st.selectbox("اختر عمود رقمي:", numeric_a, key="stat_num")
        data = df_for_analysis[selected_num].dropna()
        
        # اختيار المقاييس
        st.markdown("**اختر المقاييس المراد عرضها:**")
        show_central = st.checkbox("مقاييس النزعة المركزية", value=True)
        show_dispersion = st.checkbox("مقاييس التشتت", value=True)
        show_position = st.checkbox("مقاييس الموضع", value=True)
        show_shape = st.checkbox("الانحناء والتفلطح", value=True)
        
        if show_central:
            st.markdown("##### 📍 مقاييس النزعة المركزية")
            central_data = pd.DataFrame({
                'المقياس': ['المتوسط (Mean)', 'الوسيط (Median)', 'المنوال (Mode)'],
                'القيمة': [f"{data.mean():.4f}", f"{data.median():.4f}", f"{data.mode().iloc[0]:.4f}"],
                'التفسير': [
                    'معدل القيم - يتأثر بالقيم المتطرفة',
                    'القيمة الوسطى - لا يتأثر بالمتطرفة',
                    'القيمة الأكثر تكراراً'
                ]
            })
            st.markdown(build_html_table(central_data), unsafe_allow_html=True)
        
        if show_dispersion:
            st.markdown("##### 📏 مقاييس التشتت")
            dispersion_data = pd.DataFrame({
                'المقياس': ['المدى (Range)', 'التباين (Variance)', 'الانحراف المعياري (Std)', 'معامل الاختلاف (CV%)'],
                'القيمة': [
                    f"{(data.max() - data.min()):.4f}",
                    f"{data.var():.4f}",
                    f"{data.std():.4f}",
                    f"{(data.std()/data.mean()*100):.2f}%"
                ],
                'التفسير': [
                    f"الفرق بين أعلى وأدنى قيمة",
                    'معدل تشتت القيم عن المتوسط',
                    'مقياس التشتت الأكثر استخداماً',
                    'التشتت النسبي مقارنة بالمتوسط'
                ]
            })
            st.markdown(build_html_table(dispersion_data), unsafe_allow_html=True)
        
        if show_position:
            st.markdown("##### 📐 مقاييس الموضع")
            position_data = pd.DataFrame({
                'المقياس': ['الحد الأدنى', 'الربيع الأول (Q1)', 'الوسيط (Q2)', 'الربيع الثالث (Q3)', 'الحد الأقصى', 'المدى الربيعي (IQR)', 'النسبة 10%', 'النسبة 90%'],
                'القيمة': [
                    f"{data.min():.4f}", f"{data.quantile(0.25):.4f}", f"{data.quantile(0.5):.4f}",
                    f"{data.quantile(0.75):.4f}", f"{data.max():.4f}", f"{(data.quantile(0.75)-data.quantile(0.25)):.4f}",
                    f"{data.quantile(0.10):.4f}", f"{data.quantile(0.90):.4f}"
                ],
                'التفسير': [
                    'أصغر قيمة في البيانات',
                    '25% من البيانات أقل من هذه القيمة',
                    '50% من البيانات أقل من هذه القيمة',
                    '75% من البيانات أقل من هذه القيمة',
                    'أكبر قيمة في البيانات',
                    'مقياس التشتت resistant للمتطرفة',
                    '10% من البيانات أقل من هذه القيمة',
                    '90% من البيانات أقل من هذه القيمة'
                ]
            })
            st.markdown(build_html_table(position_data), unsafe_allow_html=True)
        
        if show_shape:
            st.markdown("##### 📈 الانحناء والتفلطح")
            skew = data.skew()
            kurt = data.kurtosis()
            shape_data = pd.DataFrame({
                'المقياس': ['الانحناء (Skewness)', 'التفلطح (Kurtosis)'],
                'القيمة': [f"{skew:.4f}", f"{kurt:.4f}"],
                'التفسير الرقمي': [
                    interpret_skewness(skew),
                    interpret_kurtosis(kurt)
                ]
            })
            st.markdown(build_html_table(shape_data), unsafe_allow_html=True)
            
            # رسم بياني
            fig = px.histogram(df_for_analysis, x=selected_num, nbins=30, title=f"توزيع {selected_num}", marginal="box")
            fig.add_vline(x=data.mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {data.mean():.2f}")
            fig.add_vline(x=data.median(), line_dash="dot", line_color="green", annotation_text=f"Median: {data.median():.2f}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد أعمدة رقمية")

# ====== Box Plots ======
with eda_tab3:
    st.markdown("#### 📦 مخططات الصندوق (Box Plots)")
    if numeric_a:
        selected_box = st.selectbox("اختر عمود:", numeric_a, key="box_col")
        data = df_for_analysis[selected_box].dropna()
        
        Q1, Q2, Q3 = data.quantile(0.25), data.quantile(0.5), data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5*IQR
        upper = Q3 + 1.5*IQR
        outliers = data[(data < lower) | (data > upper)]
        
        box_data = pd.DataFrame({
            'المقياس': ['الحد الأدنى', 'Q1', 'الوسيط', 'Q3', 'الحد الأقصى', 'IQR', 'عدد المتطرفة'],
            'القيمة': [f"{data.min():.4f}", f"{Q1:.4f}", f"{Q2:.4f}", f"{Q3:.4f}", f"{data.max():.4f}", f"{IQR:.4f}", str(len(outliers))]
        })
        st.markdown(build_html_table(box_data, f"Box Plot لـ {selected_box}"), unsafe_allow_html=True)
        
        fig = px.box(df_for_analysis, y=selected_box, title=f"Box Plot - {selected_box}", points="all")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد أعمدة رقمية")

# ====== 8. Dashboard النهائية ======
with eda_tab4:
    st.markdown("#### 📊 Dashboard النهائية للتقرير")
    
    if st.button("إنشاء وتصدير التقرير", key="export_report"):
        html_parts = []
        html_parts.append(f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
        <title>تقرير التحليل الشامل</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma; background: #f8f9fa; padding: 20px; direction: rtl; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
            .section {{ background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th {{ background: #667eea; color: white; padding: 10px; text-align: right; }}
            td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right; }}
            tr:nth-child(even) {{ background: #f7fafc; }}
            .metric {{ display: inline-block; background: white; padding: 15px; border-radius: 8px; margin: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        </style></head><body>
        <div class="header"><h1>📊 تقرير التحليل الاستكشافي الشامل</h1><p>Smart Analytics Pro - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div>
        """)
        
        # ملخص البيانات
        html_parts.append(f"""<div class="section"><h2> ملخص البيانات</h2>
        <div class="metric">الصفوف: {len(df_for_analysis)}</div>
        <div class="metric">الأعمدة: {len(df_for_analysis.columns)}</div>
        <div class="metric">الرقمية: {len(numeric_a)}</div>
        <div class="metric">الفئوية: {len(categorical_a)}</div></div>""")
        
        # الجداول التكرارية
        html_parts.append("<div class='section'><h2>📋 الجداول التكرارية</h2>")
        for col in categorical_a[:5]:
            freq = df_for_analysis[col].value_counts().head(10).reset_index()
            freq.columns = ['القيمة', 'التكرار']
            freq['النسبة %'] = (freq['التكرar'] / len(df_for_analysis) * 100).round(2)
            html_parts.append(f"<h3>{col}</h3>{freq.to_html(index=False)}")
        html_parts.append("</div>")
        
        # التحليل الإحصائي
        html_parts.append("<div class='section'><h2>📊 التحليل الإحصائي</h2>")
        for col in numeric_a:
            data = df_for_analysis[col].dropna()
            html_parts.append(f"<h3>{col}</h3>")
            stats = pd.DataFrame({
                'المقياس': ['المتوسط', 'الوسيط', 'الانحراف المعياري', 'التباين', 'Q1', 'Q3', 'IQR', 'Skewness', 'Kurtosis'],
                'القيمة': [f"{data.mean():.2f}", f"{data.median():.2f}", f"{data.std():.2f}", f"{data.var():.2f}",
                          f"{data.quantile(0.25):.2f}", f"{data.quantile(0.75):.2f}", f"{(data.quantile(0.75)-data.quantile(0.25)):.2f}",
                          f"{data.skew():.4f}", f"{data.kurtosis():.4f}"],
                'التفسير': ['-', '-', '-', '-', '-', '-', '-', interpret_skewness(data.skew()), interpret_kurtosis(data.kurtosis())]
            })
            html_parts.append(stats.to_html(index=False))
        html_parts.append("</div>")
        
        html_parts.append("""</body></html>""")
        
        final_html = "".join(html_parts)
        
        st.download_button("📥 تحميل التقرير", data=final_html, 
                          file_name=f"EDA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                          mime="text/html")
        st.success("✅ تم إنشاء التقرير!")

st.markdown("---")
st.markdown("<div style='text-align:center; color:#718096; padding:20px;'>Smart Analytics Pro © 2026</div>", unsafe_allow_html=True)
