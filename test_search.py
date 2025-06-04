import pandas as pd
from streamlit2_app import primary_mask

def test_primary_mask_exact():
    s = pd.Series(["the pain", "painful", "hospital", "pain management"])
    mask = primary_mask(s, "pain", 1, "Exact match (default)")
    assert mask.tolist() == [True, False, False, True]

def test_primary_mask_any_part():
    s = pd.Series(["the pain", "painful", "hospital", "pain management"])
    mask = primary_mask(s, "pain", 1, "Any part of word")
    assert mask.tolist() == [True, True, False, True]

def test_primary_mask_multiple_terms_exact():
    s = pd.Series(["the pain", "painful", "hospital", "pain management"])
    mask = primary_mask(s, "pain,hospital", 1, "Exact match (default)")
    assert mask.tolist() == [True, False, True, True]

def test_primary_mask_multiple_terms_any_part():
    s = pd.Series(["the pain", "painful", "hospital", "pain management"])
    mask = primary_mask(s, "pain,hosp", 1, "Any part of word")
    assert mask.tolist() == [True, True, True, True]

def test_primary_mask_threshold():
    s = pd.Series(["pain pain", "pain hospital", "hospital", "pain management"])
    mask = primary_mask(s, "pain,hospital", 2, "Any part of word")
    assert mask.tolist() == [False, True, False, False]

def test_primary_mask_empty_terms():
    s = pd.Series(["the pain", "painful", "hospital", "pain management"])
    mask = primary_mask(s, "", 1, "Exact match (default)")
    assert mask.tolist() == [True, True, True, True]

def test_primary_mask_case_insensitive():
    s = pd.Series(["Pain", "PAIN", "painful", "Hospital"])
    mask = primary_mask(s, "pain", 1, "Exact match (default)")
    assert mask.tolist() == [True, True, False, False]

def test_primary_mask_no_matches():
    s = pd.Series(["apple", "banana", "cherry"])
    mask = primary_mask(s, "pain", 1, "Exact match (default)")
    assert mask.tolist() == [False, False, False]

def test_primary_mask_all_empty_strings():
    s = pd.Series(["", "", ""])
    mask = primary_mask(s, "pain", 1, "Any part of word")
    assert mask.tolist() == [False, False, False]

def test_primary_mask_nan_values():
    s = pd.Series(["pain", None, "hospital", float('nan')])
    mask = primary_mask(s, "pain", 1, "Exact match (default)")
    assert mask.tolist() == [True, False, False, False]

def test_primary_mask_multiple_terms_high_threshold():
    s = pd.Series(["pain hospital", "pain", "hospital", "none"])
    mask = primary_mask(s, "pain,hospital", 2, "Exact match (default)")
    assert mask.tolist() == [True, False, False, False]

def test_primary_mask_spaces_and_commas():
    s = pd.Series(["pain, hospital", " pain ", "hospital", ""])
    mask = primary_mask(s, " pain , hospital ", 1, "Any part of word")
    assert mask.tolist() == [True, True, True, False]