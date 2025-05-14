
import altair as alt
import pandas as pd
import streamlit as st

# Show the page title and description.
st.set_page_config(page_title="Search Engine", page_icon="🔍")
st.title("🔍 Search Engine")
st.write(
    """
    Just click on the widgets below to explore!
    """
)


# Load the fake data. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    data = {'CLAIM_NO': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
        'CLAIM_TYPE': ['CLAIM', 'SUIT', 'ALERT', 'CLAIM', 'SUIT', 'SUIT', 'ALERT', 'CLAIM', 'SUIT', 'SUIT'], 
        'LOSS_TYPE': ['PROF LIAB', 'GL', 'PROF LIAB', 'GL', 'PROF LIAB', 'PROF LIAB',  'PROF LIAB', 'GL', 'PROF LIAB', 'PROF LIAB'], 
        'AGENCY_ID': ["001", "002", "003", "001", "002", "003", "001", "002", "003", "001"], 
        'VAP_HOSP_INDICATOR': [1, 1, 0, 1, 1, 0, 1, 1, 1, 0], 
        'LOSS_DATE': ['2022-01-01', '2022-02-01', '2022-03-01', '2023-01-01', '2023-02-01', '2023-03-01', '2024-03-01', '2024-01-01', '2024-02-01', '2025-03-01'], 
        'ASSERTED_DATE': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-01-01', '2024-02-01', '2024-03-01', '2024-03-01', '2025-01-01', '2025-02-01', '2025-03-01'], 
        'TOTAL_INCURRED': [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000], 
        'NOTE_CREATION_DATE': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-01-01', '2024-02-01', '2024-03-01', '2024-03-01', '2025-01-01', '2025-02-01', '2025-03-01'], 
        'NOTE_TYPE': ['EXPERT', 'REPORT', 'EXPERT', 'EXPERT', 'REPORT', 'EXPERT', 'EXPERT', 'REPORT', 'EXPERT', 'REPORT'], 
        'NOTE_DESCRIPTION': ['The fox jumped over the cat, and the cat ran away.', 
                             'Jack and Jill ran up the hill to fetch a cat.', 
                             'The fox lives in a hole on  a hill with his pet rabbit, Joe. Joe is 10 years old.',
                             'Jack and Jill are guilty of theft.',
                             'The fox is a very clever animal. That is a pathologist',
                             'Tim lives in England and he plays cricket on the weekends.',
                             'Shelby is a oncologist who treats patients with cancer.',
                             'Failure to diagnose fox in a 62 year old male with a history of hypertension.',
                             'Some foxes have failure to play cricket',
                             'Coding is fun as long as you are not a fox.']}
    df = pd.DataFrame(data)
    #manipulate data
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
    ["PROF LIAB", "GL"],
)

# Show a slider widget with the years using `st.slider`.
years = st.slider("Years", 1995, 2006, (2020, 2025))

# Filter the dataframe based on the widget input and reshape it.
df_filtered = df[(df["CLAIM_TYPE"].isin(claim_type)) & (df["CLAIM_TYPE"].isin(claim_type)) & (df["ASSERTED_YEAR"].between(years[0], years[1]))]
df_reshaped = df_filtered[['CLAIM_NO','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION']]
    #.pivot_table(
    #index="ASSERTED_YEAR", columns="CLAIM_TYPE", values="TOTAL_INCURRED", aggfunc="sum", fill_value=0
    #)
df_reshaped = df_reshaped.sort_values(by="ASSERTED_YEAR", ascending=False)


st.header("Search", divider=True)
st.write("Try the following combinations: fox & hole & rabbit, Jack & Jill & hill, England & cricket & weekend, fox & cat & over, failure & diagnosis & hypertension, fox & clever & jumped")

# Use a text_input to get the keywords to filter the dataframe
text_search1 = st.text_input("Primary Search (Diagnosis)", value="fox")
text_search2 = st.text_input("Secondary Search (Service)", value="pathologist")
text_search3 = st.text_input("Tertiary Search (Issue)", value="clever")

# Filter the dataframe using masks
m1 = df_reshaped["NOTE_DESCRIPTION"].str.contains(text_search1)
m2 = df_reshaped["NOTE_DESCRIPTION"].str.contains(text_search2)
m3 = df_reshaped["NOTE_DESCRIPTION"].str.contains(text_search3)
df_search = df_reshaped[m1 & m2 & m3]
num_rec = df_search.shape[0]

# Show the results, if you have a text_search
if text_search2:
    st.write("Number of Records Found: ", num_rec)
    st.write(df_search)
