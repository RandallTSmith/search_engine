
import pandas as pd
import streamlit as st
import re


# Show the page title and description.
st.set_page_config(page_title="Search Engine", page_icon="🔍")
st.title("🔍 Search Engine")
st.write(
    """
    - Choose your search criteria using the widgets below.
    
    - You can also search for specific terms in the notes associated with each claim.
    
    - The results will be displayed in a table below.
        - You can export the results to a CSV file using the button at the bottom of the page.
    """
)

# Load the fake data. Caching data so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    df = pd.read_csv('test_claim_data.csv')
    df['ASSERTED_YEAR'] = pd.DatetimeIndex(df['ASSERTED_DATE']).year
    # Keep the original notes for display/export
    df['NOTE_DESCRIPTION_ORIG'] = df['NOTE_DESCRIPTION']
    # Remove special characters from NOTE_DESCRIPTION (keep letters, numbers, spaces) for searching
    df['NOTE_DESCRIPTION'] = df['NOTE_DESCRIPTION'].astype(str).str.replace(r'[^A-Za-z0-9 ]+', '', regex=True)
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
df_reshaped = df_filtered[['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION','NOTE_DESCRIPTION_ORIG']]
df_reshaped = df_reshaped.sort_values(by="ASSERTED_YEAR", ascending=False)

def primary_mask(series, search_text, threshold, match_type):
    terms = [t.strip() for t in search_text.split(",") if t.strip()]
    if not terms:
        return pd.Series([True] * len(series))
    if match_type == "Exact match (default)":
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
    if match_type == "Exact match (default)":
        pattern = "|".join([r"\b{}\b".format(re.escape(term)) for term in terms])
        return series.str.contains(pattern, case=False, regex=True, na=False)
    else:
        return series.apply(lambda x: any(term.lower() in str(x).lower() for term in terms))



# --- Search Section ---
st.header("Search", divider=True)


# Match type selection
match_type = st.radio(
    "**Search Match Type**",
    ("Exact match (default)", "Any part of word"),
    index=0,
    horizontal=True,
)

if match_type == "Exact match (default)":
    st.info(
        """
        **Note:**  
        "Exact match" finds your search term as a whole word or exact phrase anywhere in the text (case-insensitive).  
        For example, searching for `pain` will match `pain`, `the pain`, or `pain management`, but **not** `painful` or `inpain`.
        """
    )

if match_type == "Any part of word":
    st.info(
        """
        **Note:**  
        "Any part of word" matches your search term as a substring anywhere in the text.  
        For example, searching for `deliver` will match `deliver`, `delivers`, `delivery`, `redelivered`, `undelivered`, and even `adeliverance`.  
        This is broader than matching just the root word.
        """
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

# Secondary search section
if primary_terms.strip():
    st.markdown("### Secondary Search")
    col3, col4 = st.columns([3, 1])
    with col3:
        secondary_terms = st.text_input(
            "Diagnosis (comma-separated words/phrases)", 
            value="legal, time"
        )
    with col4:
        secondary_terms_list = [t.strip() for t in secondary_terms.split(",") if t.strip()]
        max_threshold2 = max(1, len(secondary_terms_list))
        secondary_threshold = st.number_input(
            "Secondary Threshold", 
            min_value=1, 
            max_value=max_threshold2, 
            value=1, 
            step=1,
            help="Minimum number of secondary search terms that must appear in a note."
        )

    m2 = primary_mask(df_after_primary["NOTE_DESCRIPTION"], secondary_terms, secondary_threshold, match_type)
    with st.expander("Show secondary mask sum", expanded=False):
        st.write("Rows matching secondary threshold:", m2.sum())
    df_after_secondary = df_after_primary[m2].reset_index(drop=True)
else:
    secondary_terms = ""
    df_after_secondary = df_after_primary

# third search section
if primary_terms.strip() and secondary_terms.strip():
    st.markdown("### Tertiary Search")
    col5, col6 = st.columns([3, 1])
    with col5:
        tertiary_terms = st.text_input(
            "Issue (comma-separated words/phrases)", 
            value="treatment"
        )
    with col6:
        tertiary_terms_list = [t.strip() for t in tertiary_terms.split(",") if t.strip()]
        max_threshold3 = max(1, len(tertiary_terms_list))
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
        with st.expander("Show tertiary mask sum", expanded=False):
            st.write("Rows matching tertiary threshold:", m3.sum())
        df_search = df_after_secondary[m3].reset_index(drop=True)
        tertiary_mask_sum = m3.sum()
else:
    df_search = df_after_secondary

#Results Section
st.markdown("## Results")
num_rec = df_search.shape[0]
num_unique_cases = df_search["CLAIM_NUMBER"].nunique() if not df_search.empty else 0

st.success(f"**Number of Records Found:** {num_rec}")
st.info(f"**Number of Unique Case Numbers Found:** {num_unique_cases}")

# Only show the original notes (with punctuation) to the user
display_cols = ['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION_ORIG']
df_display = df_search[display_cols].rename(columns={"NOTE_DESCRIPTION_ORIG": "NOTE_DESCRIPTION"})
st.dataframe(df_display)