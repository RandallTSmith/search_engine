
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
    # Replace 'your_data.csv' with the path to your CSV file
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

# Show a slider widget with the years using `st.slider`.
years = st.slider("Years", 1995, 2006, (2020, 2025))

# Filter the dataframe based on the widget input and reshape it.
df_filtered = df[(df["CLAIM_TYPE"].isin(claim_type)) & (df["LOSS_TYPE"].isin(loss_type)) & (df["ASSERTED_YEAR"].between(years[0], years[1]))]
df_reshaped = df_filtered[['CLAIM_NUMBER','ASSERTED_YEAR','TOTAL_INCURRED','NOTE_TYPE','NOTE_DESCRIPTION']]
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
