import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(
    page_title="Моніторинг ЄДРА",
    layout="wide"
)

# Стильний заголовок
st.title("📊 Моніторинг динаміки верифікації адрес в ЄДРА")
st.write("Завантажте два файли за різні періоди для порівняння.")

# Завантаження файлів
col1, col2 = st.columns(2)
with col1:
    file_past = st.file_uploader("1. Попередній період (наприклад, 10.07)", type=["csv"])
with col2:
    file_current = st.file_uploader("2. Поточний період (наприклад, 14.07)", type=["csv"])

if file_past and file_current:
    # Зчитування файлів
    df_past = pd.read_csv(file_past)
    df_current = pd.read_csv(file_current)
    
    # Очищення назв колонок від будь-яких пробілів (важливо!)
    df_past.columns = df_past.columns.str.strip()
    df_current.columns = df_current.columns.str.strip()
    
    # Спільні колонки для злиття
    merge_cols = ['Назва міста', 'Область']
    
    # Визначаємо, які ще колонки збігаються, щоб об'єднати їх з суфіксами
    df = pd.merge(
        df_current, 
        df_past, 
        on='Назва міста', 
        suffixes=('_current', '_past')
    )
    
    # Розрахунок динаміки
    df['Динаміка %'] = df['% Опрацьованих_current'] - df['% Опрацьованих_past']
    df['Динаміка Кількість'] = df['Верифіковані_current'] - df['Верифіковані_past']
    
    # Сортування
    df = df.sort_values(by='% Опрацьованих_current', ascending=False).reset_index(drop=True)
    df['№'] = df.index + 1

    # Розрахунок загальних підсумків
    total_past_verified = df['Верифіковані_past'].sum()
    total_curr_verified = df['Верифіковані_current'].sum()
    total_diff_verified = total_curr_verified - total_past_verified
    
    avg_past_processed = df['% Опрацьованих_past'].mean()
    avg_curr_processed = df['% Опрацьованих_current'].mean()
    avg_diff_processed = avg_curr_processed - avg_past_processed

    # Кольори клітинок для % Опрацьованих
    def get_row_colors(val):
        if val >= 0.99: return '#C6F6D5'
        elif val >= 0.90: return '#E6FFFA'
        elif val >= 0.70: return '#F0FFF4'
        else: return '#FFFFFF'

    cell_colors_processed = [get_row_colors(x) for x in df['% Опрацьованих_current']]
    
    # Тренд-статус
    def get_trend_indicator(val):
        if val > 0.0001: return '🟢'
        elif val < -0.0001: return '🔴'
        else: return '🟡'
            
    df['Індикатор'] = df['Динаміка %'].apply(get_trend_indicator)
    
    # Списки даних для таблиці (використовуємо очищені назви колонок)
    col_no = df['№'].tolist() + ['']
    col_city = df['Назва міста'].tolist() + ['Всього']
    col_of = df['Завантажено ОФ_current'].tolist() + [str(df['Завантажено ОФ_current'].eq('так').sum())]
    
    col_proc = [f"{x*100:.2f}%" for x in df['% Опрацьованих_current']] + [f"{avg_curr_processed*100:.2f}%"]
    col_verif = [f"{x*100:.2f}%" for x in df['% Верифікованих адрес_current']] + [f"{df['% Верифікованих адрес_current'].mean()*100:.2f}%"]
    col_count = [f"{int(x):,}".replace(",", " ") for x in df['Верифіковані_current']] + [f"{int(total_curr_verified):,}".replace(",", " ")]
    col_ref = [f"{x*100:.2f}%" for x in df['% Уточнення_current']] + [f"{df['% Уточнення_current'].mean()*100:.2f}%"]
    
    col_dyn_proc = [f"{x*100:+.2f}%" for x in df['Динаміка %']] + [f"{avg_diff_processed*100:+.2f}%"]
    col_indicator = df['Індикатор'].tolist() + ['']

    # Побудова Plotly Table у стилі референсу
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[
                '<b>№</b>', '<b>Місто</b>', '<b>Завантажено ОФ</b>', 
                '<b>% Опрацьованих</b>', '<b>% Верифікованих</b>', 
                '<b>Кількість</b>', '<b>% Уточнення</b>', 
                '<b>Динаміка %</b>', '<b>Статус</b>'
            ],
            fill_color='#1A365D',
            align='center',
            font=dict(color='#ffffff', size=12, family="Arial"),
            height=40
        ),
        cells=dict(
            values=[
                col_no, col_city, col_of, 
                col_proc, col_verif, col_count, 
                col_ref, col_dyn_proc, col_indicator
            ],
            fill_color=[
                ['#F8FAFC'] * len(col_no), # №
                ['#E2E8F0' if c == 'Всього' else '#EDF2F7' for c in col_city], # Місто
                ['#F8FAFC'] * len(col_no), # ОФ
                cell_colors_processed + ['#E2E8F0'], # % Опрацьованих
                ['#F8FAFC'] * len(col_no), # % Верифікованих
                ['#F8FAFC'] * len(col_no), # Кількість
                ['#F8FAFC'] * len(col_no), # % Уточнення
                ['#EDF2F7'] * len(col_no), # Динаміка
                ['#F8FAFC'] * len(col_no)  # Індикатор
            ],
            align='center',
            font=dict(color='#2D3748', size=11, family="Arial"),
            height=30
        )
    )])

    fig.update_layout(
        title={
            'text': "<b>Рейтинг найбільших міст по роботі в ЄДРА (за відсотком опрацьованих адрес)</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=16, color='#1A365D')
        },
        margin=dict(l=10, r=10, t=60, b=10),
        width=1100,
        height=1000
    )

    st.subheader("📋 Результат аналізу")
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("📸 **Експорт в PNG:** Просто наведіть мишку на таблицю вище та натисніть на іконку **камери (Download plot as a png)** у верхньому правому кутку таблиці.")

    # Експорт у CSV
    df_export = df[[
        '№', 'Назва міста', 'Область_current', 'Завантажено ОФ_current',
        '% Опрацьованих_past', '% Опрацьованих_current', 'Динаміка %',
        'Верифіковані_past', 'Верифіковані_current', 'Динаміка Кількість'
    ]].copy()
    df_export.columns = [
        '№', 'Місто', 'Область', 'Завантажено ОФ', 
        '% Опрацьованих (Минулий)', '% Опрацьованих (Поточний)', 'Динаміка %',
        'Верифіковані (Минулий)', 'Верифіковані (Поточний)', 'Динаміка Кількість'
    ]
    
    csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Завантажити розраховані дані (CSV)",
        data=csv_data,
        file_name="zvit_dinamika.csv",
        mime="text/csv"
    )
