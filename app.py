import streamlit as st
import pandas as pd

# ============================================================
# НАЛАШТУВАННЯ СТОРІНКИ
# ============================================================
st.set_page_config(
    page_title="Моніторинг ЄДРА",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# СТИЛІ (сучасний вигляд: картки, тіні, акуратна типографіка)
# ============================================================
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }

    .hero {
        background: linear-gradient(135deg, #1A365D 0%, #2C5282 100%);
        padding: 28px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(26,54,93,0.25);
    }
    .hero h1 { margin: 0; font-size: 26px; }
    .hero p { margin: 6px 0 0 0; opacity: 0.85; font-size: 15px; }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricValue"] { color: #1A365D; }

    .badge-card {
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 8px;
        font-size: 14.5px;
    }
    .badge-leader { background: #F0FFF4; border-left: 5px solid #38A169; }
    .badge-outsider { background: #FFF5F5; border-left: 5px solid #E53E3E; }

    h3 { color: #1A365D; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📊 Моніторинг динаміки верифікації адрес у ЄДРА</h1>
    <p>Завантажте два CSV-файли за різні періоди, щоб порівняти прогрес по містах.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ЗАВАНТАЖЕННЯ ФАЙЛІВ
# ============================================================
col1, col2 = st.columns(2)
with col1:
    file_past = st.file_uploader("1️⃣ Попередній період (наприклад, 10.07)", type=["csv"])
with col2:
    file_current = st.file_uploader("2️⃣ Поточний період (наприклад, 14.07)", type=["csv"])

if not (file_past and file_current):
    st.info("⬆️ Завантажте обидва файли, щоб побачити звіт.")
    st.stop()

# ============================================================
# ОБРОБКА ДАНИХ
# ============================================================
df_past = pd.read_csv(file_past)
df_current = pd.read_csv(file_current)

df_past.columns = df_past.columns.str.strip()
df_current.columns = df_current.columns.str.strip()

df = pd.merge(df_current, df_past, on='Назва міста', suffixes=('_current', '_past'))

df['Динаміка %'] = df['% Опрацьованих_current'] - df['% Опрацьованих_past']
df['Динаміка Кількість'] = df['Верифіковані_current'] - df['Верифіковані_past']

df = df.sort_values(by='% Опрацьованих_current', ascending=False).reset_index(drop=True)
df['№'] = df.index + 1
total_rows = len(df)


def trend_icon(v):
    if v > 0.0001:
        return '🟢 Зростання'
    elif v < -0.0001:
        return '🔴 Спад'
    return '🟡 Без змін'


df['Статус'] = df['Динаміка %'].apply(trend_icon)

# ============================================================
# KPI-КАРТКИ
# ============================================================
avg_curr = df['% Опрацьованих_current'].mean()
avg_diff = df['Динаміка %'].mean()
total_curr_verified = df['Верифіковані_current'].sum()
total_diff_verified = df['Динаміка Кількість'].sum()
improved = (df['Динаміка %'] > 0.0001).sum()
declined = (df['Динаміка %'] < -0.0001).sum()
stalled = total_rows - improved - declined

k1, k2, k3, k4 = st.columns(4)
k1.metric("Міст у звіті", total_rows)
k2.metric("Середній % опрацювання", f"{avg_curr*100:.2f}%", f"{avg_diff*100:+.2f}%")
k3.metric("Всього верифіковано", f"{total_curr_verified:,.0f}".replace(",", " "),
          f"{total_diff_verified:+,.0f}".replace(",", " "))
k4.metric("Зростання / Спад / Стабільно", f"🟢{improved}  🔴{declined}  🟡{stalled}")

st.write("")

# ============================================================
# ЛІДЕРИ ТА АУТСАЙДЕРИ
# ============================================================
top3 = df.nsmallest(3, '№')
bottom3 = df.nlargest(3, '№')

lc, rc = st.columns(2)
with lc:
    st.markdown("#### 🏆 Лідери")
    for _, row in top3.iterrows():
        st.markdown(
            f"""<div class="badge-card badge-leader">
            <b>#{row['№']} {row['Назва міста']}</b> — {row['% Опрацьованих_current']*100:.2f}% опрацьовано
            ({row['Динаміка %']*100:+.2f}% з минулого періоду)
            </div>""",
            unsafe_allow_html=True
        )
with rc:
    st.markdown("#### ⚠️ Потребують уваги")
    for _, row in bottom3.iterrows():
        st.markdown(
            f"""<div class="badge-card badge-outsider">
            <b>#{row['№']} {row['Назва міста']}</b> — {row['% Опрацьованих_current']*100:.2f}% опрацьовано
            ({row['Динаміка %']*100:+.2f}% з минулого періоду)
            </div>""",
            unsafe_allow_html=True
        )

st.divider()

# ============================================================
# ОСНОВНА ТАБЛИЦЯ (сортована, з кольоровим підсвічуванням)
# ============================================================
st.subheader("📋 Рейтинг міст")
st.caption("Клікніть на заголовок стовпця, щоб відсортувати таблицю.")

display_df = df[[
    '№', 'Назва міста', 'Область_current', 'Завантажено ОФ_current',
    '% Опрацьованих_current', '% Верифікованих адрес_current',
    'Верифіковані_current', '% Уточнення_current',
    'Динаміка %', 'Динаміка Кількість', 'Статус'
]].copy()

display_df.columns = [
    '№', 'Місто', 'Область', 'Завантажено ОФ',
    '% Опрацьованих', '% Верифікованих', 'Кількість верифікованих', '% Уточнення',
    'Динаміка %', 'Динаміка (шт.)', 'Статус'
]


def color_dynamics(v):
    if v > 0.0001:
        return 'color: #22863A; font-weight: 600;'
    elif v < -0.0001:
        return 'color: #D9363E; font-weight: 600;'
    return 'color: #B7791F; font-weight: 600;'


def highlight_extremes(row):
    styles = [''] * len(row)
    if row['№'] <= 3:
        styles = ['background-color: #FFF7D6'] * len(row)
    elif row['№'] > total_rows - 3:
        styles = ['background-color: #FFE3E3'] * len(row)
    return styles


styled = (
    display_df.style
    .format({
        '% Опрацьованих': '{:.2%}',
        '% Верифікованих': '{:.2%}',
        '% Уточнення': '{:.2%}',
        'Динаміка %': '{:+.2%}',
        'Кількість верифікованих': '{:,.0f}',
        'Динаміка (шт.)': '{:+,.0f}',
    })
    .background_gradient(subset=['% Опрацьованих'], cmap='Greens', vmin=0, vmax=1)
    .applymap(color_dynamics, subset=['Динаміка %'])
    .apply(highlight_extremes, axis=1, subset=['№', 'Місто', 'Область', 'Завантажено ОФ'])
    .set_properties(**{'text-align': 'center'})
    .set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1A365D'), ('color', 'white'),
                                      ('text-align', 'center'), ('padding', '8px')]},
        {'selector': 'td', 'props': [('padding', '6px')]},
    ])
)

st.dataframe(styled, use_container_width=True, height=min(45 * total_rows + 40, 900))

st.download_button(
    label="📥 Завантажити таблицю (CSV)",
    data=display_df.to_csv(index=False).encode('utf-8-sig'),
    file_name="zvit_dinamika.csv",
    mime="text/csv"
)

st.divider()

# ============================================================
# РЕДАГУВАННЯ ДАНИХ ВРУЧНУ
# ============================================================
st.subheader("✏️ Редагувати дані вручну")
st.caption("Тут можна виправити будь-яке значення (наприклад, після ручної перевірки) "
           "та вивантажити оновлений файл. Відсотки показані у форматі 0–100.")

edit_df = display_df.copy()
for col in ['% Опрацьованих', '% Верифікованих', '% Уточнення', 'Динаміка %']:
    edit_df[col] = (edit_df[col] * 100).round(2)

edited = st.data_editor(
    edit_df,
    use_container_width=True,
    num_rows="dynamic",
    key="editor",
    column_config={
        "№": st.column_config.NumberColumn(disabled=True),
        "% Опрацьованих": st.column_config.NumberColumn(format="%.2f %%", min_value=0, max_value=100),
        "% Верифікованих": st.column_config.NumberColumn(format="%.2f %%", min_value=0, max_value=100),
        "% Уточнення": st.column_config.NumberColumn(format="%.2f %%", min_value=0, max_value=100),
        "Динаміка %": st.column_config.NumberColumn(format="%.2f %%"),
        "Кількість верифікованих": st.column_config.NumberColumn(format="%d"),
        "Динаміка (шт.)": st.column_config.NumberColumn(format="%+d"),
    }
)

st.download_button(
    label="📥 Завантажити відредаговані дані (CSV)",
    data=edited.to_csv(index=False).encode('utf-8-sig'),
    file_name="zvit_dinamika_edited.csv",
    mime="text/csv"
)
