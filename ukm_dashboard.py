import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="UKM Schedule Analyzer",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main {
        background-color: #0f1117;
    }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%);
    }

    .metric-card {
        background: linear-gradient(135deg, #1e2535 0%, #252d40 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
        border-left: 4px solid;
    }

    .metric-card.green { border-left-color: #48bb78; }
    .metric-card.red { border-left-color: #fc8181; }
    .metric-card.blue { border-left-color: #63b3ed; }
    .metric-card.yellow { border-left-color: #f6e05e; }

    .metric-card .label {
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #718096;
        margin-bottom: 6px;
    }

    .metric-card .value {
        font-size: 32px;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1;
    }

    .metric-card .sub {
        font-size: 13px;
        color: #a0aec0;
        margin-top: 4px;
    }

    .student-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        margin: 3px;
        font-family: 'DM Mono', monospace;
    }

    .chip-available {
        background: rgba(72, 187, 120, 0.15);
        color: #68d391;
        border: 1px solid rgba(72, 187, 120, 0.3);
    }

    .chip-late {
        background: rgba(246, 224, 94, 0.15);
        color: #f6e05e;
        border: 1px solid rgba(246, 224, 94, 0.3);
    }

    .chip-unavailable {
        background: rgba(252, 129, 74, 0.15);
        color: #fc8181;
        border: 1px solid rgba(252, 129, 74, 0.3);
    }

    .section-title {
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #4a5568;
        margin: 24px 0 12px 0;
        border-bottom: 1px solid #2d3748;
        padding-bottom: 8px;
    }

    .insight-box {
        background: linear-gradient(135deg, #1a2744 0%, #1e2a4a 100%);
        border: 1px solid #2d4a8a;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }

    .insight-box .icon { font-size: 20px; margin-right: 8px; }
    .insight-box .text { color: #a0c4ff; font-size: 14px; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141821 0%, #1a1f2e 100%);
        border-right: 1px solid #2d3748;
    }

    .sidebar-header {
        text-align: center;
        padding: 20px 0 10px 0;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 20px;
    }

    .sidebar-header h2 {
        font-size: 22px;
        font-weight: 700;
        color: #e2e8f0;
        margin: 0;
    }

    .sidebar-header p {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: #4a5568;
        letter-spacing: 2px;
        margin: 4px 0 0 0;
    }

    .stSelectbox > div > div {
        background-color: #1e2535 !important;
        border-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }

    .stMultiSelect > div > div {
        background-color: #1e2535 !important;
        border-color: #2d3748 !important;
    }

    h1, h2, h3 { color: #e2e8f0 !important; }
    p { color: #a0aec0; }

    .grace-badge {
        display: inline-block;
        background: rgba(246, 173, 85, 0.2);
        border: 1px solid rgba(246, 173, 85, 0.4);
        color: #f6ad55;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-family: 'DM Mono', monospace;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# DATA LOADING
# =========================
@st.cache_data
def load_and_process(path, grace_minutes=20):
    df = pd.read_csv(path)
    df['start_time'] = pd.to_datetime(df['start_time'], format='%H:%M')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%H:%M')
    df['day'] = df['day'].str.capitalize()

    last_class = (
        df.groupby(['student_id', 'student_name', 'major', 'day'])
        .agg(
            last_end_time=('end_time', 'max'),
            last_course=('course', lambda x: x.loc[df.loc[x.index, 'end_time'].idxmax()])
        )
        .reset_index()
    )

    return df, last_class


def analyze(last_class, training_start_str, grace_minutes, selected_days, selected_majors):
    training_start = pd.to_datetime(training_start_str, format='%H:%M')
    grace_limit = training_start + pd.Timedelta(minutes=grace_minutes)

    filtered = last_class.copy()
    if selected_days:
        filtered = filtered[filtered['day'].isin(selected_days)]
    if selected_majors:
        filtered = filtered[filtered['major'].isin(selected_majors)]

    results = []
    for day in filtered['day'].unique():
        df_day = filtered[filtered['day'] == day]

        for _, row in df_day.iterrows():
            end = row['last_end_time']

            if end <= training_start:
                status = "Hadir Tepat Waktu"
            elif end <= grace_limit:
                status = "Hadir (Toleransi)"
            else:
                status = "Tidak Bisa Hadir"

            results.append({
                "day": day,
                "student_id": row['student_id'],
                "student_name": row['student_name'],
                "major": row['major'],
                "last_course": row['last_course'],
                "last_end_time": end.strftime('%H:%M'),
                "last_end_dt": end,
                "training_start": training_start_str,
                "status": status,
                "menit_setelah_mulai": max(0, int((end - training_start).total_seconds() / 60))
            })

    return pd.DataFrame(results)


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h2>🏋️ UKM Analyzer</h2>
        <p>SCHEDULE INTELLIGENCE TOOL</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload CSV Jadwal", type=["csv"])
    use_sample = st.checkbox("Pakai data sample", value=True if not uploaded else False)

    st.markdown("---")
    st.markdown("**⚙️ Konfigurasi Latihan**")

    training_start = st.selectbox(
        "Jam Mulai Latihan (Target)",
        ["14:00", "15:00", "16:00", "17:00", "17:30"],
        index=3,
        help="Jam yang ingin dianalisis sebagai waktu mulai latihan"
    )

    grace_minutes = st.slider(
        "Toleransi Keterlambatan (menit)",
        min_value=0, max_value=60, value=20, step=5,
        help="Mahasiswa yang selesai dalam rentang toleransi ini tetap dianggap bisa hadir"
    )

    st.markdown("---")
    st.markdown("**🔍 Filter Data**")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    selected_days = st.multiselect(
        "Hari",
        options=day_order,
        default=day_order,
        help="Pilih hari yang ingin dianalisis"
    )

# =========================
# LOAD DATA
# =========================
if uploaded:
    raw_df, last_class = load_and_process(uploaded)
elif use_sample:
    try:
        raw_df, last_class = load_and_process('data/jadwal_mahasiswa.csv')
    except:
        st.error("⚠️ File sample tidak ditemukan. Silakan upload CSV jadwal.")
        st.stop()
else:
    st.info("👆 Upload file CSV jadwal untuk memulai analisis.")
    st.stop()

# filter major (dynamic)
all_majors = sorted(last_class['major'].unique())
with st.sidebar:
    selected_majors = st.multiselect(
        "Jurusan / Major",
        options=all_majors,
        default=all_majors
    )

# =========================
# MAIN ANALYSIS
# =========================
result_df = analyze(last_class, training_start, grace_minutes, selected_days, selected_majors)

# =========================
# HEADER
# =========================
st.markdown(f"""
<div style="padding: 30px 0 20px 0;">
    <h1 style="font-size: 32px; font-weight: 700; margin: 0; color: #e2e8f0;">
        Analisis Jadwal UKM
        <span class="grace-badge">+{grace_minutes} menit toleransi</span>
    </h1>
    <p style="color: #718096; margin-top: 6px; font-size: 14px;">
        Target latihan: <strong style="color: #63b3ed;">{training_start}</strong> · 
        Hari dianalisis: <strong style="color: #63b3ed;">{len(selected_days)}</strong> hari · 
        Total mahasiswa: <strong style="color: #63b3ed;">{result_df['student_id'].nunique()}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# =========================
# SUMMARY METRICS
# =========================
if not result_df.empty:
    total_unique = result_df['student_id'].nunique()

    # per mahasiswa, ambil worst case (kalau di salah satu hari ga bisa, hitung)
    per_student = result_df.groupby('student_id').apply(
        lambda x: "Tidak Bisa Hadir" if "Tidak Bisa Hadir" in x['status'].values
        else ("Hadir (Toleransi)" if "Hadir (Toleransi)" in x['status'].values else "Hadir Tepat Waktu")
    ).reset_index()
    per_student.columns = ['student_id', 'overall_status']

    tepat = (per_student['overall_status'] == 'Hadir Tepat Waktu').sum()
    toleransi = (per_student['overall_status'] == 'Hadir (Toleransi)').sum()
    tidak = (per_student['overall_status'] == 'Tidak Bisa Hadir').sum()
    bisa_hadir = tepat + toleransi

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card blue">
            <div class="label">Total Mahasiswa</div>
            <div class="value">{total_unique}</div>
            <div class="sub">dalam filter aktif</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card green">
            <div class="label">Bisa Hadir</div>
            <div class="value">{bisa_hadir}</div>
            <div class="sub">{round(bisa_hadir/total_unique*100)}% dari total</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card yellow">
            <div class="label">Hadir Toleransi</div>
            <div class="value">{toleransi}</div>
            <div class="sub">Terlambat ≤ {grace_minutes} menit</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card red">
            <div class="label">Tidak Bisa Hadir</div>
            <div class="value">{tidak}</div>
            <div class="sub">{round(tidak/total_unique*100)}% dari total</div>
        </div>""", unsafe_allow_html=True)

# =========================
# TAB LAYOUT
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visualisasi",
    "📋 Per Hari",
    "👤 Per Mahasiswa",
    "🔎 Data Mentah"
])

# ------- TAB 1: VISUALISASI -------
with tab1:
    if result_df.empty:
        st.warning("Tidak ada data untuk ditampilkan.")
    else:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<div class="section-title">Ketersediaan per Hari & Jam Latihan</div>', unsafe_allow_html=True)

            summary_day = result_df.groupby(['day', 'status']).size().reset_index(name='count')
            color_map = {
                "Hadir Tepat Waktu": "#48bb78",
                "Hadir (Toleransi)": "#f6e05e",
                "Tidak Bisa Hadir": "#fc8181"
            }

            ordered_days = [d for d in day_order if d in result_df['day'].unique()]
            summary_day['day'] = pd.Categorical(summary_day['day'], categories=ordered_days, ordered=True)
            summary_day = summary_day.sort_values('day')

            fig_bar = px.bar(
                summary_day,
                x='day', y='count',
                color='status',
                color_discrete_map=color_map,
                barmode='stack',
                labels={'count': 'Jumlah Mahasiswa', 'day': 'Hari', 'status': 'Status'},
                template='plotly_dark'
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='DM Sans', color='#a0aec0'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(gridcolor='#2d3748'),
                yaxis=dict(gridcolor='#2d3748')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-title">Distribusi Status Keseluruhan</div>', unsafe_allow_html=True)

            pie_data = result_df['status'].value_counts().reset_index()
            pie_data.columns = ['status', 'count']

            fig_pie = px.pie(
                pie_data,
                names='status',
                values='count',
                color='status',
                color_discrete_map=color_map,
                hole=0.55,
                template='plotly_dark'
            )
            fig_pie.update_traces(textposition='outside', textfont_size=12)
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='DM Sans', color='#a0aec0'),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=-0.2),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Heatmap: jam pulang per mahasiswa per hari
        st.markdown('<div class="section-title">Heatmap — Jam Selesai Kelas Terakhir per Mahasiswa</div>', unsafe_allow_html=True)

        pivot = result_df.pivot_table(
            index='student_name',
            columns='day',
            values='menit_setelah_mulai',
            aggfunc='max'
        )
        pivot = pivot[[c for c in ordered_days if c in pivot.columns]]

        training_start_dt = pd.to_datetime(training_start, format='%H:%M')

        # Ambil jam selesai aktual untuk annotation
        pivot_time = result_df.pivot_table(
            index='student_name',
            columns='day',
            values='last_end_dt',
            aggfunc='max'
        )
        pivot_time = pivot_time[[c for c in ordered_days if c in pivot_time.columns]]
        annotation_text = pivot_time.map(
            lambda x: x.strftime('%H:%M') if pd.notna(x) else ''
        )

        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            text=annotation_text.values,
            texttemplate="%{text}",
            colorscale=[
                [0.0, '#1a3a2a'],
                [0.3, '#48bb78'],
                [0.6, '#f6e05e'],
                [1.0, '#fc8181']
            ],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text=f"Menit setelah<br>{training_start}",
                    font=dict(color='#a0aec0')
                ),
                tickfont=dict(color='#a0aec0')
            )
        ))

        fig_heat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Mono', color='#a0aec0', size=11),
            margin=dict(l=0, r=0, t=10, b=0),
            height=max(300, len(pivot) * 28),
            xaxis=dict(side='top'),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(f"🟢 Hijau = selesai sebelum {training_start} · 🟡 Kuning = dalam toleransi · 🔴 Merah = terlalu telat")

        # Distribusi jam selesai kelas terakhir
        st.markdown('<div class="section-title">Distribusi Jam Selesai Kelas Terakhir</div>', unsafe_allow_html=True)

        result_df['jam_selesai_float'] = result_df['last_end_dt'].dt.hour + result_df['last_end_dt'].dt.minute / 60

        fig_hist = px.histogram(
            result_df,
            x='jam_selesai_float',
            color='status',
            color_discrete_map=color_map,
            nbins=20,
            template='plotly_dark',
            labels={'jam_selesai_float': 'Jam Selesai', 'count': 'Jumlah'},
            barmode='overlay',
            opacity=0.8
        )
        training_hour = pd.to_datetime(training_start, format='%H:%M').hour + pd.to_datetime(training_start, format='%H:%M').minute / 60
        fig_hist.add_vline(
            x=training_hour,
            line_dash="dash",
            line_color="#63b3ed",
            annotation_text=f"Target: {training_start}",
            annotation_font_color="#63b3ed"
        )
        fig_hist.add_vline(
            x=training_hour + grace_minutes / 60,
            line_dash="dot",
            line_color="#f6e05e",
            annotation_text=f"Batas toleransi",
            annotation_font_color="#f6e05e"
        )
        fig_hist.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Sans', color='#a0aec0'),
            xaxis=dict(gridcolor='#2d3748', tickformat='.1f'),
            yaxis=dict(gridcolor='#2d3748'),
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig_hist, use_container_width=True)


# ------- TAB 2: PER HARI -------
with tab2:
    st.markdown(f'<div class="section-title">Breakdown per Hari — Target Latihan {training_start}</div>', unsafe_allow_html=True)

    for day in [d for d in day_order if d in result_df['day'].values]:
        day_data = result_df[result_df['day'] == day]

        tepat_w = day_data[day_data['status'] == 'Hadir Tepat Waktu']
        toleransi_w = day_data[day_data['status'] == 'Hadir (Toleransi)']
        tidak_w = day_data[day_data['status'] == 'Tidak Bisa Hadir']
        bisa = len(tepat_w) + len(toleransi_w)

        with st.expander(f"📅 {day}  —  {bisa}/{len(day_data)} bisa hadir", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Tepat Waktu", len(tepat_w))
            c2.metric(f"🕐 Toleransi (≤{grace_minutes}m)", len(toleransi_w))
            c3.metric("❌ Tidak Bisa", len(tidak_w))

            if not tepat_w.empty:
                st.markdown("**✅ Hadir Tepat Waktu**")
                chips = "".join([
                    f'<span class="student-chip chip-available">🟢 {r["student_name"]} ({r["last_end_time"]})</span>'
                    for _, r in tepat_w.iterrows()
                ])
                st.markdown(chips, unsafe_allow_html=True)

            if not toleransi_w.empty:
                st.markdown(f"**🕐 Hadir dengan Toleransi** (selesai ≤ {training_start} +{grace_minutes}m)")
                chips = "".join([
                    f'<span class="student-chip chip-late">🟡 {r["student_name"]} ({r["last_end_time"]})</span>'
                    for _, r in toleransi_w.iterrows()
                ])
                st.markdown(chips, unsafe_allow_html=True)

            if not tidak_w.empty:
                st.markdown("**❌ Tidak Bisa Hadir**")
                chips = "".join([
                    f'<span class="student-chip chip-unavailable">🔴 {r["student_name"]} ({r["last_end_time"]})</span>'
                    for _, r in tidak_w.iterrows()
                ])
                st.markdown(chips, unsafe_allow_html=True)

            # Mini detail table
            st.dataframe(
                day_data[['student_name', 'major', 'last_course', 'last_end_time', 'status']]
                .rename(columns={
                    'student_name': 'Nama',
                    'major': 'Jurusan',
                    'last_course': 'Matkul Terakhir',
                    'last_end_time': 'Jam Selesai',
                    'status': 'Status'
                })
                .sort_values('Jam Selesai'),
                use_container_width=True,
                hide_index=True
            )


# ------- TAB 3: PER MAHASISWA -------
with tab3:
    st.markdown('<div class="section-title">Ringkasan per Mahasiswa</div>', unsafe_allow_html=True)

    student_summary = result_df.groupby(['student_id', 'student_name', 'major']).apply(
        lambda x: pd.Series({
            'Bisa Hadir (Hari)': (x['status'] != 'Tidak Bisa Hadir').sum(),
            'Tidak Bisa (Hari)': (x['status'] == 'Tidak Bisa Hadir').sum(),
            'Total Hari': len(x),
            'Jam Terakhir Paling Telat': x['last_end_time'].max(),
            'Hari Terpadat': x.loc[x['last_end_dt'].idxmax(), 'day'] if not x.empty else '-',
            'Availability %': f"{round((x['status'] != 'Tidak Bisa Hadir').sum() / len(x) * 100)}%"
        })
    ).reset_index()

    # Filter search
    search = st.text_input("🔍 Cari nama mahasiswa...", placeholder="Ketik nama...")
    if search:
        student_summary = student_summary[
            student_summary['student_name'].str.contains(search, case=False)
        ]

    st.dataframe(
        student_summary.rename(columns={'student_id': 'ID', 'student_name': 'Nama', 'major': 'Jurusan'}),
        use_container_width=True,
        hide_index=True
    )

    # Availability bar chart per mahasiswa
    st.markdown('<div class="section-title">Tingkat Kehadiran per Mahasiswa</div>', unsafe_allow_html=True)

    avail_pct = result_df.groupby('student_name').apply(
        lambda x: round((x['status'] != 'Tidak Bisa Hadir').sum() / len(x) * 100)
    ).reset_index()
    avail_pct.columns = ['student_name', 'pct']
    avail_pct = avail_pct.sort_values('pct', ascending=True)

    fig_avail = go.Figure(go.Bar(
        x=avail_pct['pct'],
        y=avail_pct['student_name'],
        orientation='h',
        marker=dict(
            color=avail_pct['pct'],
            colorscale=[[0, '#fc8181'], [0.5, '#f6e05e'], [1, '#48bb78']],
            showscale=False
        ),
        text=avail_pct['pct'].astype(str) + '%',
        textposition='outside',
        textfont=dict(color='#a0aec0', size=11)
    ))
    fig_avail.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans', color='#a0aec0'),
        xaxis=dict(gridcolor='#2d3748', range=[0, 115], ticksuffix='%'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=60, t=10, b=0),
        height=max(400, len(avail_pct) * 26)
    )
    st.plotly_chart(fig_avail, use_container_width=True)


# ------- TAB 4: RAW DATA -------
with tab4:
    st.markdown('<div class="section-title">Data Lengkap Hasil Analisis</div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_status = st.multiselect(
            "Filter Status",
            options=result_df['status'].unique(),
            default=list(result_df['status'].unique())
        )
    with col_f2:
        filter_day_raw = st.multiselect(
            "Filter Hari",
            options=[d for d in day_order if d in result_df['day'].values],
            default=[d for d in day_order if d in result_df['day'].values]
        )

    filtered_raw = result_df[
        (result_df['status'].isin(filter_status)) &
        (result_df['day'].isin(filter_day_raw))
    ]

    st.dataframe(
        filtered_raw[[
            'day', 'student_id', 'student_name', 'major',
            'last_course', 'last_end_time', 'menit_setelah_mulai', 'status'
        ]].rename(columns={
            'day': 'Hari',
            'student_id': 'ID',
            'student_name': 'Nama',
            'major': 'Jurusan',
            'last_course': 'Matkul Terakhir',
            'last_end_time': 'Jam Selesai',
            'menit_setelah_mulai': 'Terlambat (menit)',
            'status': 'Status'
        }).sort_values(['Hari', 'Jam Selesai']),
        use_container_width=True,
        hide_index=True
    )

    csv_export = filtered_raw.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Hasil sebagai CSV",
        data=csv_export,
        file_name=f"ukm_analysis_{training_start.replace(':', '')}.csv",
        mime="text/csv"
    )

# =========================
# INSIGHT BOX
# =========================
st.markdown("---")
st.markdown('<div class="section-title">💡 Auto Insights</div>', unsafe_allow_html=True)

if not result_df.empty:
    best_day = result_df.groupby('day').apply(
        lambda x: (x['status'] != 'Tidak Bisa Hadir').sum() / len(x)
    ).idxmax()
    best_ratio = result_df.groupby('day').apply(
        lambda x: (x['status'] != 'Tidak Bisa Hadir').sum() / len(x)
    ).max()

    worst_day = result_df.groupby('day').apply(
        lambda x: (x['status'] != 'Tidak Bisa Hadir').sum() / len(x)
    ).idxmin()

    most_blocked = result_df[result_df['status'] == 'Tidak Bisa Hadir']['student_name'].value_counts()

    ic1, ic2 = st.columns(2)
    with ic1:
        st.markdown(f"""
        <div class="insight-box">
            <span class="icon">📅</span>
            <span class="text">Hari terbaik untuk latihan adalah <strong>{best_day}</strong> 
            dengan <strong>{round(best_ratio*100)}%</strong> mahasiswa bisa hadir pada jam {training_start}.</span>
        </div>
        """, unsafe_allow_html=True)

        if not most_blocked.empty:
            st.markdown(f"""
            <div class="insight-box">
                <span class="icon">⚠️</span>
                <span class="text">Mahasiswa yang paling sering bentrok: <strong>{most_blocked.index[0]}</strong> 
                ({most_blocked.iloc[0]} hari tidak bisa hadir dari jadwal yang dianalisis).</span>
            </div>
            """, unsafe_allow_html=True)

    with ic2:
        st.markdown(f"""
        <div class="insight-box">
            <span class="icon">🕐</span>
            <span class="text">Hari dengan ketersediaan terendah adalah <strong>{worst_day}</strong>. 
            Pertimbangkan untuk tidak menjadwalkan latihan di hari ini jika kehadiran penuh diperlukan.</span>
        </div>
        """, unsafe_allow_html=True)

        total_bisa = (result_df['status'] != 'Tidak Bisa Hadir').sum()
        total_all = len(result_df)
        st.markdown(f"""
        <div class="insight-box">
            <span class="icon">📊</span>
            <span class="text">Secara keseluruhan, <strong>{round(total_bisa/total_all*100)}%</strong> dari semua slot hari/mahasiswa 
            bisa hadir latihan jam {training_start} (termasuk toleransi {grace_minutes} menit).</span>
        </div>
        """, unsafe_allow_html=True)