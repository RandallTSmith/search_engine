import pandas as pd
import streamlit as st
import re
import io

# --- Load Data ---
df = pd.read_csv("test_claim_data_update1.csv")
df["ASSERTED_YEAR"] = pd.to_datetime(df["ASSERTED_DATE"], errors="coerce").dt.year

# --- Helper Functions ---
def parse_terms(term_string):
    return [t.strip() for t in term_string.split(",") if t.strip()]

def get_max_threshold(terms_list):
    return max(1, len(terms_list))

def show_mask_sum(label, mask):
    st.write(f"Records matching after {label} search: {int(mask.sum())}")

def select_all_multiselect(label, options, default=None, key_prefix="", help=None):
    """
    Renders a filter with a large label, a small 'Select All' checkbox next to it, and a multiselect.
    Keeps the checkbox and multiselect in sync using session_state.
    Returns the selected values.
    """
    key_select_all = f"select_all_{key_prefix}"
    key_multi = key_prefix

    # Initialize session state if not present
    if key_multi not in st.session_state:
        st.session_state[key_multi] = default if default is not None else options
    if key_select_all not in st.session_state:
        st.session_state[key_select_all] = False

    # Sync logic
    def sync_select_all():
        if st.session_state[key_select_all]:
            st.session_state[key_multi] = options
        else:
            if set(st.session_state[key_multi]) == set(options):
                st.session_state[key_multi] = []

    def sync_multiselect():
        st.session_state[key_select_all] = set(st.session_state[key_multi]) == set(options)

    with st.container():
        col_label, col_checkbox = st.columns([3, 1])
        with col_label:
            st.markdown(f"<span style='font-size:1.2em; font-weight:bold'>{label}</span>", unsafe_allow_html=True)
        with col_checkbox:
            st.markdown(
                """
                <style>
                .small-checkbox label {
                    font-size: 0.85em !important;
                    color: #666 !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.checkbox(
                "Select All",
                value=st.session_state[key_select_all],
                key=key_select_all,
                on_change=sync_select_all,
                help=f"Select all {label.lower()}s." if help is None else help,
                label_visibility="visible",
            )
        selected = st.multiselect(
            "Select options",
            options,
            key=key_multi,
            on_change=sync_multiselect,
            help=help,
            label_visibility="collapsed"
        )
    return selected

def reset_all_filters():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["primary_terms"] = ""
    st.session_state["secondary_terms"] = ""
    st.session_state["tertiary_terms"] = ""

try:
    st.set_page_config(page_title="Search Engine", page_icon="🔍", layout="wide")
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1500px;
            margin: auto;
            padding-top: 2.5rem;
            padding-bottom: 1rem;
        }
        html, body, [class*="css"]  {
            font-size: 20px !important;
        }
        .small-checkbox label {
            font-size: 0.85em !important;
            color: #666 !important;
        }
        .select-all-small label {
            font-size: 0.85em !important;
            color: #666 !important;
            margin-bottom: 0.5em !important;
        }
        mark {
            background-color: #ffe066;
            color: black;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Sticky Reset Button in Sidebar ---
    with st.sidebar:
        st.button("🔄 Reset All Filters & Searches", on_click=reset_all_filters)
        st.markdown("---")

    # --- Section Headings and Dividers ---
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
    st.markdown("## 1. Filter Claims")
    st.divider()

    # --- Show Filter Counts in Labels ---
    def label_with_count(label, options):
        return f"{label} ({len(options)})"

    with st.expander("Claim Info Filters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            claim_type_options = sorted(df.CLAIM_TYPE.dropna().unique())
            top_claim_types = df["CLAIM_TYPE"].value_counts().head(3).index.tolist()
            claim_type = select_all_multiselect(
                label_with_count("Claim Type", claim_type_options),
                claim_type_options,
                default=top_claim_types,
                key_prefix="claim_type"
            )
            loss_type_options = sorted(df.LOSS_TYPE.dropna().unique())
            top_loss_types = df["LOSS_TYPE"].value_counts().head(3).index.tolist()
            loss_type = select_all_multiselect(
                label_with_count("Loss Type", loss_type_options),
                loss_type_options,
                default=top_loss_types,
                key_prefix="loss_type"
            )
            years = st.slider("Years (Asserted)", int(df['ASSERTED_YEAR'].min()), int(df['ASSERTED_YEAR'].max()), (int(df['ASSERTED_YEAR'].min()), int(df['ASSERTED_YEAR'].max())))
        with col2:
            agency_parent_options = sorted(df.AGENCY_PARENT.dropna().unique())
            top_agency_parents = df["AGENCY_PARENT"].value_counts().head(3).index.tolist()
            agency_parent = select_all_multiselect(
                label_with_count("Agency Parent", agency_parent_options),
                agency_parent_options,
                default=top_agency_parents,
                key_prefix="agency_parent",
                help="Select one or more parent agencies. Agency Name options will update based on your selection."
            )
            agency_name_options = (
                sorted(df[df["AGENCY_PARENT"].isin(agency_parent)]["AGENCY_NAME"].dropna().unique())
                if agency_parent else sorted(df["AGENCY_NAME"].dropna().unique())
            )
            # Toast/info message for dynamic default
            agency_name_key = "agency_name"
            if agency_name_key in st.session_state:
                prev_options = set(st.session_state.get(f"{agency_name_key}_options", []))
                new_options = set(agency_name_options)
                if prev_options != new_options:
                    st.session_state[agency_name_key] = agency_name_options
            st.session_state[f"{agency_name_key}_options"] = agency_name_options
            top_agency_names = pd.Series(agency_name_options).value_counts().head(3).index.tolist()
            agency_name = select_all_multiselect(
                label_with_count("Agency Name", agency_name_options),
                agency_name_options,
                default=top_agency_names,
                key_prefix="agency_name",
                help="Agency Name options are filtered by your Agency Parent selection."
            )

    with st.expander("Department, Injury, and Severity Filters", expanded=False):
        col3, col4 = st.columns(2)
        with col3:
            department_desc_options = sorted(df["DEPARTMENT_DESC"].dropna().unique())
            top_departments = df["DEPARTMENT_DESC"].value_counts().head(3).index.tolist()
            department_desc = select_all_multiselect(
                label_with_count("Department", department_desc_options),
                department_desc_options,
                default=top_departments,
                key_prefix="department_desc",
                help="Filter by department description."
            )
            injury_desc_options = sorted(df["INJURY_DESC"].dropna().unique())
            top_injuries = df["INJURY_DESC"].value_counts().head(3).index.tolist()
            injury_desc = select_all_multiselect(
                label_with_count("Injury", injury_desc_options),
                injury_desc_options,
                default=top_injuries,
                key_prefix="injury_desc",
                help="Filter by injury description."
            )
        with col4:
            severity_options = sorted(df["SEVERITY"].dropna().unique())
            top_severities = df["SEVERITY"].value_counts().head(3).index.tolist()
            severity = select_all_multiselect(
                label_with_count("Severity", severity_options),
                severity_options,
                default=top_severities,
                key_prefix="severity",
                help="Filter by severity."
            )

    if not (claim_type and loss_type and agency_parent and agency_name and department_desc and injury_desc and severity):
        st.warning("Please select at least one option in **every filter** above to see results.", icon="⚠️")



    def isin_or_na(series, selected):
        return series.isin(selected) | series.isna()

    df_filtered = df[
        (df["CLAIM_TYPE"].isin(claim_type)) &
        (df["LOSS_TYPE"].isin(loss_type)) &
        (df["AGENCY_PARENT"].isin(agency_parent)) &
        (df["AGENCY_NAME"].isin(agency_name)) &
        (df["ASSERTED_YEAR"].between(years[0], years[1])) &
        isin_or_na(df["DEPARTMENT_DESC"], department_desc) &
        isin_or_na(df["INJURY_DESC"], injury_desc) &
        isin_or_na(df["SEVERITY"], severity)
    ]
    df_reshaped = df_filtered[['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION']]
    df_reshaped = df_reshaped.sort_values(by="ASSERTED_YEAR", ascending=False)

    # --- Search Section ---
    st.markdown("---")
    st.markdown("## 2. Search Notes")

    match_type = st.radio(
        "**Search Match Type**",
        ("Exact match (default)", "Any part of word"),
        index=0,
        horizontal=True,
    )

    if match_type == "Exact match (default)":
        st.info(
            "🔎 **Exact match:** Finds your search term as a whole word or exact phrase anywhere in the text (case-insensitive)."
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
            "comma-separated words/phrases", 
            value="",
            key="primary_terms"
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
    st.markdown("### Secondary Search")
    col3, col4 = st.columns([3, 1])
    with col3:
        secondary_terms = st.text_input(
            "comma-separated words/phrases", 
            value="",
            key="secondary_terms"
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

    m2 = primary_mask(df_after_primary["NOTE_DESCRIPTION"], secondary_terms, secondary_threshold, match_type) if not df_after_primary.empty else pd.Series([False]*len(df_after_primary))
    show_mask_sum("secondary", m2)
    df_after_secondary = df_after_primary[m2].reset_index(drop=True) if not df_after_primary.empty else df_after_primary

    # --- Tertiary Search ---
    st.markdown("### Tertiary Search")
    col5, col6 = st.columns([3, 1])
    with col5:
        tertiary_terms = st.text_input(
            "comma-separated words/phrases", 
            value="",
            key="tertiary_terms"
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


    # --- Results Section (Paginate Results) ---
    st.markdown("---")
    st.markdown("## 3. Results")

    # Show summary stats
    num_records = len(df_search)
    num_unique_cases = df_search["CLAIM_NUMBER"].nunique() if not df_search.empty else 0
    st.info(f"**{num_records} records found** | **{num_unique_cases} unique cases**")

    # Show all found records in the preview
    st.dataframe(df_search, use_container_width=True)

    # Download all found records
    csv = df_search.to_csv(index=False)
    st.download_button(
        "📥 Download Results as CSV",
        csv,
        "search_results.csv",
        "text/csv",
        key="download-csv"
    )

except Exception as e:
    st.error("😬 Oops, something went wrong. Please try again.")
    with st.expander("Show error details"):
        st.exception(e)