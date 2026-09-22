from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Revival International | Attendance', page_icon='📊', layout='wide')
st.title('Revival International St Louis')
st.caption('Attendance dashboard · July–August 2026 · Exported records (not live data)')

@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).with_name('attendance.csv'), parse_dates=['date'])
    required = {'date', 'attendance', 'guests', 'children'}
    if not required.issubset(df.columns):
        raise ValueError(f'Missing columns: {required - set(df.columns)}')
    df = df.loc[(df.date >= '2026-07-01') & (df.date < '2026-09-01')].copy()
    for col in ['attendance', 'guests', 'children']:
        df[col] = pd.to_numeric(df[col], errors='raise')
    df['month'] = df.date.dt.strftime('%B %Y')
    return df.sort_values('date')

df = load_data()
selection = st.segmented_control('Reporting period', ['July 2026', 'August 2026', 'Compare months'], default='Compare months')
selected = df if selection == 'Compare months' else df[df.month == selection]
if selected.empty:
    st.warning('No records for this reporting period.')
    st.stop()

n = len(selected)
a, b, c, d = st.columns(4)
a.metric('Reported attendance', f'{selected.attendance.sum():,}')
b.metric('Average per record', f'{selected.attendance.mean():.1f}')
c.metric('Guest attendance', f'{selected.guests.sum():,}')
d.metric('Children attendance', f'{selected.children.sum():,}')
st.caption(f'{n} attendance records · Counts are attendance instances, not unique people. Guest and children counts may be included in total attendance.')

st.subheader('Weekly attendance')
weekly = selected.set_index('date')[['attendance', 'guests', 'children']]
st.line_chart(weekly, x_label='Service date', y_label='Reported attendance')

if selection == 'Compare months':
    st.subheader('Monthly comparison')
    monthly = df.groupby('month', sort=False).agg(records=('attendance', 'size'), total_attendance=('attendance', 'sum'), average_per_record=('attendance', 'mean'), guests=('guests', 'sum'), children=('children', 'sum'))
    st.dataframe(monthly.style.format({'average_per_record':'{:.1f}'}), use_container_width=True)
    july, aug = monthly.loc['July 2026'], monthly.loc['August 2026']
    change = (aug.average_per_record / july.average_per_record - 1) * 100 if july.average_per_record else None
    if change is not None:
        st.info(f'Average attendance per record changed by {change:+.1f}% from July to August. July has {int(july.records)} records and August has {int(aug.records)}; reporting frequency and the August 16 spike affect comparisons.')

st.subheader('Underlying attendance records')
st.dataframe(selected[['date','attendance','guests','children']], hide_index=True, use_container_width=True)
st.download_button('Download selected records', selected[['date','attendance','guests','children']].to_csv(index=False), file_name='selected_attendance.csv', mime='text/csv')
st.caption('Source: read-only PostgreSQL export. This dashboard does not connect to or modify the production database.')
