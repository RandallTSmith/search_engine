import pandas as pd
import streamlit as st
import re

# --- Helper Functions ---
def parse_terms(term_string):
    return [t.strip() for t in term_string.split(",") if t.strip()]

def get_max_threshold(terms_list):
    return max(1, len(terms_list))

def show_mask_sum(label, mask):
    with st.expander(f"Show {label} mask sum", expanded=False):
        st.write(f"Rows matching {label} threshold:", int(mask.sum()))

# --- Streamlit UI ---
st.set_page_config(page_title="Search Engine", page_icon="🔍", layout="wide")
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1500px;
        margin: auto;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    html, body, [class*="css"]  {
        font-size: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔍 Search Engine")
st.info(
    """
    **How to use:**  
    1. **Filter claims** using the options below.  
    2. **Search notes** for specific terms.  
    3. **View and export results** at the bottom.
    """,
    icon="ℹ️"
)

@st.cache_data
def load_data():
    df = pd.read_csv('test_claim_data.csv')
    df['ASSERTED_YEAR'] = pd.DatetimeIndex(df['ASSERTED_DATE']).year
    df['NOTE_DESCRIPTION_ORIG'] = df['NOTE_DESCRIPTION']
    df['NOTE_DESCRIPTION'] = df['NOTE_DESCRIPTION'].astype(str).str.replace(r'[^A-Za-z0-9 ]+', '', regex=True)
    return df

df = load_data()

# --- Filters Section ---
st.markdown("## 1. Filter Claims")
with st.expander("Show/Hide Claim Filters", expanded=True):
    claim_type = st.multiselect(
        "Claim Type",
        df.CLAIM_TYPE.unique(),
        ["SUIT", "CLAIM", "ALERT"],
    )
    loss_type = st.multiselect(
        "Loss Type",
        df.LOSS_TYPE.unique(),
        ["PROF LIAB", "GEN LIAB", "ADMIN"],
    )
    agency_parent = st.multiselect(
        "Agency Parent",
        df.AGENCY_PARENT.unique(),
        df.AGENCY_PARENT.unique()[:3] if len(df.AGENCY_PARENT.unique()) > 3 else df.AGENCY_PARENT.unique(),
        help="Select one or more parent agencies. Agency Name options will update based on your selection."
    )
    agency_name_options = (
        sorted(df[df["AGENCY_PARENT"].isin(agency_parent)]["AGENCY_NAME"].unique())
        if agency_parent else sorted(df["AGENCY_NAME"].unique())
    )
    agency_name = st.multiselect(
        "↳ Agency Name (filtered by Agency Parent)",
        agency_name_options,
        agency_name_options[:3] if len(agency_name_options) > 3 else agency_name_options,
        help="Agency Name options are filtered by your Agency Parent selection."
    )

years = st.slider("Years (Asserted)", 1995, 2006, (2015, 2025))

df_filtered = df[
    (df["CLAIM_TYPE"].isin(claim_type)) &
    (df["LOSS_TYPE"].isin(loss_type)) &
    (df["AGENCY_PARENT"].isin(agency_parent)) &
    (df["AGENCY_NAME"].isin(agency_name)) &
    (df["ASSERTED_YEAR"].between(years[0], years[1]))
]
df_reshaped = df_filtered[['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION','NOTE_DESCRIPTION_ORIG']]
df_reshaped = df_reshaped.sort_values(by="ASSERTED_YEAR", ascending=False)

# --- Search Section ---
st.markdown("## 2. Search Notes")

match_type = st.radio(
    "**Search Match Type**",
    ("Exact match (default)", "Any part of word"),
    index=0,
    horizontal=True,
)

if match_type == "Exact match (default)":
    st.info(
        "🔎 **Exact match:** Finds your search term as a whole word or exact phrase anywhere in the text (case-insensitive).<br>"
        "E.g., searching for `pain` will match `pain`, `the pain`, or `pain management`, but **not** `painful` or `inpain`.",
        icon="ℹ️"
    )
else:
    st.info(
        "🔎 **Any part of word:** Matches your search term as a substring anywhere in the text."
        "E.g., searching for `deliver` will match `deliver`, `delivers`, `delivery`, `redelivered`, `undelivered`, and even `adeliverance`.",
        icon="ℹ️"
    )

# --- Primary Search ---
st.markdown("### Primary Search")
col1, col2 = st.columns([3, 1])
with col1:
    primary_terms = st.text_input(
        "Service or Department (comma-separated words/phrases)", 
        value=""
    )
with col2:
    primary_terms_list = parse_terms(primary_terms)
    max_threshold = get_max_threshold(primary_terms_list)
    primary_threshold = st.number_input(
        "Threshold", 
        min_value=1, 
        max_value=max_threshold, 
        value=1, 
        step=1,
        help="Minimum number of primary search terms that must appear in a note."
    )

def primary_mask(series, search_text, threshold, match_type):
    terms = parse_terms(search_text)
    if not terms:
        return pd.Series([True] * len(series), index=series.index)
    if match_type == "Exact match (default)":
        def count_matches(text):
            return sum(bool(re.search(r"\b{}\b".format(re.escape(term)), str(text), flags=re.IGNORECASE)) for term in terms)
    else:
        def count_matches(text):
            text_lower = str(text).lower()
            return sum(term.lower() in text_lower for term in terms)
    count = series.apply(count_matches)
    return count >= threshold

m1 = primary_mask(df_reshaped["NOTE_DESCRIPTION"], primary_terms, primary_threshold, match_type)
show_mask_sum("primary", m1)
df_after_primary = df_reshaped[m1].reset_index(drop=True)

# --- Secondary Search ---
if df_after_primary.empty:
    st.warning("No records found after primary search.")
    secondary_terms = ""
    df_after_secondary = df_after_primary  # will be empty
else:
    if primary_terms.strip():
        st.markdown("### Secondary Search")
        col3, col4 = st.columns([3, 1])
        with col3:
            secondary_terms = st.text_input(
                "Diagnosis (comma-separated words/phrases)", 
                value=""
            )
        with col4:
            secondary_terms_list = parse_terms(secondary_terms)
            max_threshold2 = get_max_threshold(secondary_terms_list)
            secondary_threshold = st.number_input(
                "Secondary Threshold", 
                min_value=1, 
                max_value=max_threshold2, 
                value=1, 
                step=1,
                help="Minimum number of secondary search terms that must appear in a note."
            )

        m2 = primary_mask(df_after_primary["NOTE_DESCRIPTION"], secondary_terms, secondary_threshold, match_type)
        show_mask_sum("secondary", m2)
        df_after_secondary = df_after_primary[m2].reset_index(drop=True)
        if df_after_secondary.empty:
            st.warning("No records found after secondary search.")
    else:
        secondary_terms = ""
        df_after_secondary = df_after_primary

# --- Tertiary Search ---
if primary_terms.strip() and secondary_terms.strip():
    st.markdown("### Tertiary Search")
    col5, col6 = st.columns([3, 1])
    with col5:
        tertiary_terms = st.text_input(
            "Issue (comma-separated words/phrases)", 
            value=""
        )
    with col6:
        tertiary_terms_list = parse_terms(tertiary_terms)
        max_threshold3 = get_max_threshold(tertiary_terms_list)
        tertiary_threshold = st.number_input(
            "Tertiary Threshold", 
            min_value=1, 
            max_value=max_threshold3, 
            value=1, 
            step=1,
            help="Minimum number of tertiary search terms that must appear in a note."
        )

    if df_after_secondary.empty:
        st.warning("No records found after secondary search.")
        df_search = df_after_secondary  # will be empty
        tertiary_mask_sum = 0
    else:
        m3 = primary_mask(df_after_secondary["NOTE_DESCRIPTION"], tertiary_terms, tertiary_threshold, match_type)
        show_mask_sum("tertiary", m3)
        df_search = df_after_secondary[m3].reset_index(drop=True)
        tertiary_mask_sum = m3.sum()
else:
    df_search = df_after_secondary

# --- Results Section ---
st.markdown("---")
st.markdown("## 3. Results")
num_rec = df_search.shape[0]
num_unique_cases = df_search["CLAIM_NUMBER"].nunique() if not df_search.empty else 0

st.success(f"**Number of Records Found:** {num_rec}")
st.info(f"**Number of Unique Case Numbers Found:** {num_unique_cases}")

display_cols = ['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION_ORIG']
existing_cols = [col for col in display_cols if col in df_search.columns]
df_display = df_search[existing_cols].rename(columns={"NOTE_DESCRIPTION_ORIG": "NOTE_DESCRIPTION"})
st.dataframe(df_display, use_container_width=True)