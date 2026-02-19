import os
from pathlib import Path
import streamlit as st

# ---------------- Configuration ----------------
BASE_PNG = Path("/Users/michal/Dropbox/NAPR13/michal/code/deploy-streamlit-magpy/output_data/forecast_files/forecast_pngs")
BASE_TXT = Path("/Users/michal/Dropbox/NAPR13/michal/code/deploy-streamlit-magpy/output_data/forecast_files/forecast_text_files")

PNG_TYPES = {
    "LOS": "los_forecast_pngs",
    "MHD": "mhd_forecast_pngs",
    "VEC": "vec_forecast_pngs",
}

TXT_TYPES = {
    "LOS": "los_full_disk_forecasts",
    "MHD": "mhd_fl_forecasts",
    "VEC": "vec_full_disk_forecasts",
}

# Try these text layouts in order:
# 1) .../<run_subdir>/old_forecasts/YYYY/MM/DD
# 2) .../<run_subdir>/YYYY/MM/DD
TXT_VARIANTS = [
    ("old_forecasts",),
    tuple(),
]

# ---------------- Helpers ----------------
def list_ymd_dates(root: Path) -> list[str]:
    """Return dates like 'YYYY/MM/DD' that exist under root (root/YYYY/MM/DD)."""
    dates: list[str] = []
    if not root.exists():
        return dates

    for y in sorted([p for p in root.iterdir() if p.is_dir() and p.name.isdigit() and len(p.name) == 4]):
        for m in sorted([p for p in y.iterdir() if p.is_dir() and p.name.isdigit()]):
            for d in sorted([p for p in m.iterdir() if p.is_dir() and p.name.isdigit()]):
                dates.append(f"{y.name}/{m.name}/{d.name}")
    return dates

def sort_dates_ymd(dates: list[str]) -> list[str]:
    def key(s: str):
        y, m, d = s.split("/")
        return (int(y), int(m), int(d))
    return sorted(set(dates), key=key)

def list_pngs(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([p for p in path.glob("*.png") if p.is_file()])

def list_txts(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([p for p in path.glob("*.txt") if p.is_file()])

def resolve_text_day_dir(run_type: str, selected_date: str) -> Path | None:
    """Return the first existing text directory for the given run type and date."""
    run_subdir = TXT_TYPES[run_type]
    for variant in TXT_VARIANTS:
        candidate = BASE_TXT / run_subdir
        for v in variant:
            candidate = candidate / v
        candidate = candidate / selected_date
        if candidate.exists():
            return candidate
    return None

# ---------------- UI ----------------
st.title("MagPy Forecast Results Viewer")

# 1) Date first: build date list from the UNION of all PNG trees
all_dates: list[str] = []
for run_type, subdir in PNG_TYPES.items():
    all_dates.extend(list_ymd_dates(BASE_PNG / subdir))

date_options = sort_dates_ymd(all_dates)

if not date_options:
    st.error("No date folders found under any PNG directories.")
    st.stop()

selected_date = st.selectbox("Select date (YYYY/MM/DD)", date_options)

# 2) After date selection, offer ONLY run types that exist for that date
available_types: list[str] = []
for run_type, subdir in PNG_TYPES.items():
    day_dir = BASE_PNG / subdir / selected_date
    if day_dir.exists() and list_pngs(day_dir):
        available_types.append(run_type)

if not available_types:
    st.warning("No run types (LOS/VEC/MHD) have PNGs for this date.")
    st.stop()

run_type = st.selectbox("Select run type", available_types)

png_day_dir = BASE_PNG / PNG_TYPES[run_type] / selected_date
txt_day_dir = resolve_text_day_dir(run_type, selected_date)

tabs = st.tabs(["PNG", "Text"])

with tabs[0]:
    st.subheader(f"{run_type} PNGs")
    st.caption(f"Folder: {png_day_dir}")

    pngs = list_pngs(png_day_dir)
    if not pngs:
        st.warning("No PNG files found for this date/run type.")
    else:
        png_choice = st.selectbox(
            "Choose PNG",
            options=pngs,
            format_func=lambda p: p.name,
            key="png_select",
        )
        st.image(str(png_choice), caption=png_choice.name, width='content')

        with st.expander("Show all PNGs in this folder"):
            cols = st.columns(2)
            for i, p in enumerate(pngs):
                with cols[i % 2]:
                    st.image(str(p), caption=p.name, width='content')

with tabs[1]:
    st.subheader(f"{run_type} Text")

    if txt_day_dir is None:
        st.warning("Text directory not found for this run type/date.")
        st.caption("Tried:")
        for variant in TXT_VARIANTS:
            candidate = BASE_TXT / TXT_TYPES[run_type]
            for v in variant:
                candidate = candidate / v
            candidate = candidate / selected_date
            st.code(str(candidate), language="text")
    else:
        st.caption(f"Folder: {txt_day_dir}")
        txts = list_txts(txt_day_dir)

        if not txts:
            st.info("No .txt files found for this date/run type.")
            other_files = sorted([p for p in txt_day_dir.iterdir() if p.is_file()])
            if other_files:
                with st.expander("Other files found (not .txt)"):
                    for p in other_files:
                        st.write(p.name)
        else:
            txt_choice = st.selectbox(
                "Choose text file",
                options=txts,
                format_func=lambda p: p.name,
                key="txt_select",
            )
            st.code(txt_choice.read_text(errors="replace"), language="text")
