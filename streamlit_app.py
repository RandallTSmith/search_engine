
import altair as alt
import pandas as pd
import streamlit as st
import re

# Show the page title and description.
st.set_page_config(page_title="Search Engine", page_icon="🔍")
st.title("🔍 Search Engine")
st.write(
    """
    Just click on the widgets below to explore!
    """
)

# Load the fake data. Caching data so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    # path to test data CSV file
    df = pd.read_csv('test_claim_data.csv')
    # manipulate data
    df['ASSERTED_YEAR'] = pd.DatetimeIndex(df['ASSERTED_DATE']).year
    return df

df = load_data()

# Show a multiselect widget with the claim type using `st.multiselect`.
claim_type = st.multiselect(
    "Claim Type",
    df.CLAIM_TYPE.unique(),
    ["SUIT", "CLAIM", "ALERT"],
)
# Show a multiselect widget with the claim type using `st.multiselect`.
loss_type = st.multiselect(
    "Loss Type",
    df.LOSS_TYPE.unique(),
    ["PROF LIAB", "GEN LIAB", "ADMIN"],
)
# Show a multiselect widget with the agency parent.
agency_parent = st.multiselect(
    "Agency Parent",
    df.AGENCY_PARENT.unique(),
    df.AGENCY_PARENT.unique()[:3] if len(df.AGENCY_PARENT.unique()) > 3 else df.AGENCY_PARENT.unique(),
)

# Dynamically filter AGENCY_NAME options based on selected AGENCY_PARENT
if agency_parent:
    agency_name_options = sorted(df[df["AGENCY_PARENT"].isin(agency_parent)]["AGENCY_NAME"].unique())
else:
    agency_name_options = sorted(df["AGENCY_NAME"].unique())

# Show a multiselect widget for AGENCY_NAME
agency_name = st.multiselect(
    "Agency Name",
    agency_name_options,
    agency_name_options[:3] if len(agency_name_options) > 3 else agency_name_options,
)

# Show a slider widget with the years using `st.slider`.
years = st.slider("Years (Asserted)", 1995, 2006, (2015, 2025))

# Filter the dataframe based on the widget input and reshape it.
df_filtered = df[
    (df["CLAIM_TYPE"].isin(claim_type)) &
    (df["LOSS_TYPE"].isin(loss_type)) &
    (df["AGENCY_PARENT"].isin(agency_parent)) &
    (df["AGENCY_NAME"].isin(agency_name)) &
    (df["ASSERTED_YEAR"].between(years[0], years[1]))
]
df_reshaped = df_filtered[['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION']]
    #.pivot_table(
    #index="ASSERTED_YEAR", columns="CLAIM_TYPE", values="TOTAL_INCURRED", aggfunc="sum", fill_value=0
    #)
df_reshaped = df_reshaped.sort_values(by="ASSERTED_YEAR", ascending=False)

def primary_mask(series, search_text, threshold, match_type):
    terms = [t.strip() for t in search_text.split(",") if t.strip()]
    if not terms:
        return pd.Series([True] * len(series))
    if match_type == "Word boundary (default)":
        def count_matches(text):
            return sum(bool(re.search(r"\b{}\b".format(re.escape(term)), str(text), flags=re.IGNORECASE)) for term in terms)
    else:
        def count_matches(text):
            text_lower = str(text).lower()
            return sum(term.lower() in text_lower for term in terms)
    count = series.apply(count_matches)
    return count >= threshold

def or_mask(series, search_text, match_type):
    terms = [t.strip() for t in search_text.split(",") if t.strip()]
    if not terms:
        return pd.Series([True] * len(series))
    if match_type == "Word boundary (default)":
        pattern = "|".join([r"\b{}\b".format(re.escape(term)) for term in terms])
        return series.str.contains(pattern, case=False, regex=True, na=False)
    else:
        return series.apply(lambda x: any(term.lower() in str(x).lower() for term in terms))
# --- Search Section ---
st.header("Search", divider=True)

st.write(
    """
    **Search Match Type**  
    - *Word boundary* matches whole words/phrases (e.g. 'root' matches 'root', 'root’s', but not 'roots').  
    - *Any part of word* matches substrings (e.g. 'root' matches 'roots', 'uprooting', etc).
    """
)

# Match type toggle
match_type = st.radio(
    "Search Match Type",
    ("Word boundary (default)", "Any part of word"),
    index=0,
    horizontal=True,
)

st.markdown("### Primary Search")
col1, col2 = st.columns([3, 1])
with col1:
    primary_terms = st.text_input(
        "Service or Department (comma-separated words/phrases)", 
        value="Pain, Hospital, fail"
    )
with col2:
    primary_terms_list = [t.strip() for t in primary_terms.split(",") if t.strip()]
    max_threshold = max(1, len(primary_terms_list))
    primary_threshold = st.number_input(
        "Threshold", 
        min_value=1, 
        max_value=max_threshold, 
        value=1, 
        step=1,
        help="Minimum number of primary search terms that must appear in a note."
    )

m1 = primary_mask(df_reshaped["NOTE_DESCRIPTION"], primary_terms, primary_threshold, match_type)
with st.expander("Show primary mask sum", expanded=False):
    st.write("Rows matching threshold:", m1.sum())
df_after_primary = df_reshaped[m1].reset_index(drop=True)

st.markdown("### Secondary Search")
secondary_terms = st.text_input(
    "Diagnosis (comma-separated words/phrases)", 
    value="legal, time"
)
m2 = or_mask(df_after_primary["NOTE_DESCRIPTION"], secondary_terms, match_type)
with st.expander("Show secondary mask sum", expanded=False):
    st.write("Rows matching secondary search:", m2.sum())
df_after_secondary = df_after_primary[m2].reset_index(drop=True)

st.markdown("### Tertiary Search")
tertiary_terms = st.text_input(
    "Issue (comma-separated words/phrases)", 
    value="treatment"
)
m3 = or_mask(df_after_secondary["NOTE_DESCRIPTION"], tertiary_terms, match_type)
with st.expander("Show tertiary mask sum", expanded=False):
    st.write("Rows matching tertiary search:", m3.sum())
df_search = df_after_secondary[m3].reset_index(drop=True)

# --- Results Section ---
st.markdown("## Results")
num_rec = df_search.shape[0]
num_unique_cases = df_search["CLAIM_NUMBER"].nunique()

st.success(f"**Number of Records Found:** {num_rec}")
st.info(f"**Number of Unique Case Numbers Found:** {num_unique_cases}")

st.dataframe(df_search)