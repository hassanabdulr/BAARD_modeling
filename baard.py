# This script houses main functions of the BAARD study. key functions like creating the master sheet, and the html dashboard.


#  libraries

import os
import glob
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from upsetplot import UpSet
from upsetplot import from_indicators
import matplotlib.pyplot as plt


######## helper functions ###########

def load_all_record_ids(baard_dir): ### used in generating the master sheet (to begin left joining)
    record_ids = []

    for root, dirs, files in os.walk(baard_dir):
        if os.path.basename(root) == "processed": # only pull from processed folder 
            for file in files:
                if file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    df = pd.read_csv(file_path, usecols=[0])  # record_id columns
                    df.columns = ["record_id"]  # rename just incase 
                    df['record_id'] = df['record_id'].str.upper() # and make the values in the record_id column uppercase
                    record_ids.append(df)


    record_id_df = pd.concat(record_ids, ignore_index=True)
    return record_id_df

# function that pulls record_id from csv file in mri directory and then makes a dataframe that outlines what mri data is available for each record_id

def add_mri_columns(df, baard_dir): ### used in master sheet
    def get_record_ids_from_csvs(folder):
        record_ids = set()
        for file in glob.glob(os.path.join(baard_dir, folder, "*.csv")):
            try:
                sub_df = pd.read_csv(file, usecols=[0])
                sub_df.columns = ["record_id"]
                record_ids.update(sub_df['record_id'].dropna().unique())
            except Exception as e:
                print(f"Skipping {file}: {e}")
        return record_ids

    smri_ids = get_record_ids_from_csvs("mri/smri/processed")
    fmri_ids = get_record_ids_from_csvs("mri/fmri/processed")
    dwi_ids  = get_record_ids_from_csvs("mri/dwi/processed")

    df['has_smri'] = df['record_id'].isin(smri_ids).astype(int)
    df['has_fmri'] = df['record_id'].isin(fmri_ids).astype(int)
    df['has_dwi']  = df['record_id'].isin(dwi_ids).astype(int)

    return df

# medication classification function --- used in master sheet
# this function takes in a row of the dataframe and checks the medication columns for each week, normalizes the values, and classifies the medication regimen
# it returns a string indicating the classification of the medication group, either "no_medications", "on_bupropion", "on_aripiprazole", "bupropion_augment", "aripiprazole_augment", "switch", or "mixed_or_other"
def normalize(val):
    if pd.isna(val): return None
    return val.strip().lower()

def classify_medication(row):
    meds_by_week = []
    med1_list = []

    for wk in [2, 4, 6, 8, 10]:
        m1 = normalize(row.get(f"week{wk}_med1"))
        m2 = normalize(row.get(f"week{wk}_med2"))
        meds_by_week.append((m1, m2))
        if m1: med1_list.append(m1)

    all_meds = [m for pair in meds_by_week for m in pair if m]
    unique_meds = set(all_meds)

    if not unique_meds:
        return "no_medications"

    # Augmentation logic
    for m1, m2 in meds_by_week:
        if m1 == "bupropion" and m2 == "aripiprazole":
            return "bupropion_augment"
        if m1 == "aripiprazole" and m2 == "bupropion":
            return "aripiprazole_augment"

    # Switch logic
    if "bupropion" in med1_list and "aripiprazole" in med1_list:
        return "switch"
    
    # Single-med cases
    if unique_meds == {"bupropion"}:
        return "on_bupropion"
    elif unique_meds == {"aripiprazole"}:
        return "on_aripiprazole"
    
    return "mixed_or_other"

# function that defines remission status based on the madras and phq9 scores, it will also handle the case where the madras score is missing and replaces it with the phq9 score
# remission is defined remission = 10 or lower to madras compared to baseline or lower than 5 to PHQ9 compared to baseline


def compute_remission_status(row): ## this function is used in the master sheet 
    madras_w10 = row.get("week10_madrs")
    phq9_w10 = row.get("week10_phq9")
    phq9_w8 = row.get("week8_phq9")
    phq9_w6 = row.get("week6_phq9")

    # All missing
    if pd.isna(madras_w10) and pd.isna(phq9_w10) and pd.isna(phq9_w8) and pd.isna(phq9_w6):
        return np.nan

    # 1. MADRS remission
    if pd.notna(madras_w10):
        return 1 if madras_w10 <= 10 else 0

    # 2. Fallback to PHQ9 as MADRS substitute 
    for score in [phq9_w10, phq9_w8, phq9_w6]:
        if pd.notna(score):
            return 1 if score <= 4 else 0

    return np.nan

# Function to trim extra missing_var_N columns based on total_missing -- in issues list
def trim_to_missing_count(row):
    count = int(row['total_missing'])
    # Keep record_id, total_missing, and exactly `count` missing_var_N columns
    return row[:2 + count]

# Function to upload a DataFrame to Google Sheets -- this is used in issues list
# this function takes in a dataframe, the name of the spreadsheet, the name of the worksheet, and the path to the credentials file
    # adapted from several stackoverflow posts

def upload_to_gsheet(df, spreadsheet_name, worksheet_name, creds_path):
    """
    Uploads a DataFrame to a specific worksheet in a Google Sheet. Security is maintained as we don't ask for credentails but rather a JSON key file.
    Args:
        df (pd.DataFrame): The DataFrame to upload.
        spreadsheet_name (str): The name of the Google Sheet.
        worksheet_name (str): The name of the worksheet within the Google Sheet.
        creds_path (str): Path to the JSON key file for Google Sheets API.
    """

   # Defines the OAuth2 scope, which limits what script can access.
    scope = [
        'https://spreadsheets.google.com/feeds', # feeds
        'https://www.googleapis.com/auth/spreadsheets', # google sheets
        'https://www.googleapis.com/auth/drive.file', # files in drive
        'https://www.googleapis.com/auth/drive' # google drive
    ]

    # Authenticate using service account credentials from json key
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    # Open or create the spreadsheet
    try:
        sheet = client.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        sheet = client.create(spreadsheet_name)

    # Open or create the worksheet
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=worksheet_name, rows=str(len(df)+1), cols=str(len(df.columns)))

    # Prepare data with headers
    data = [df.columns.tolist()] + df.values.tolist()

    # Upload data
    worksheet.update('A1', data)

    print(f"Uploaded to Google Sheet: {spreadsheet_name} > {worksheet_name}")
    
def reorder_columns(master_df):
    # Reorder weekly medication flags
    for week in [2, 4, 6, 8, 10]:
        bup_col = f"on_bup_week{week}"
        arp_col = f"on_arp_week{week}"
        freq2_col = f"week{week}_freq2"

        if freq2_col in master_df.columns:
            insert_pos = master_df.columns.get_loc(freq2_col) + 1
            for col in [bup_col, arp_col]:
                if col in master_df.columns:
                    col_data = master_df.pop(col)
                    master_df.insert(insert_pos, col, col_data)
                    insert_pos += 1

    # Reorder total counts
    if "on_arp_week10" in master_df.columns:
        insert_pos = master_df.columns.get_loc("on_arp_week10") + 1
        for col in ["total_on_bup", "total_on_arp"]:
            if col in master_df.columns:
                col_data = master_df.pop(col)
                master_df.insert(insert_pos, col, col_data)
                insert_pos += 1

    # Move medication_group
    if "total_on_arp" in master_df.columns and "medication_group" in master_df.columns:
        insert_pos = master_df.columns.get_loc("total_on_arp") + 1
        med_col = master_df.pop("medication_group")
        master_df.insert(insert_pos, "medication_group", med_col)

    # Move taking_bup and taking_arp
    if "medication_group" in master_df.columns:
        insert_pos = master_df.columns.get_loc("medication_group") + 1
        for col in ["taking_bup", "taking_arp"]:
            if col in master_df.columns:
                col_data = master_df.pop(col)
                master_df.insert(insert_pos, col, col_data)
                insert_pos += 1
    
    # reorder falls and injur columns
    if 'total_number_falls' in master_df.columns:
        insert_pos = master_df.columns.get_loc('total_on_arp') + 1
        total_falls_col = master_df.pop('total_number_falls')
        master_df.insert(insert_pos, 'total_number_falls', total_falls_col)


    if 'total_number_injuries' in master_df.columns:
        insert_pos = master_df.columns.get_loc('total_number_falls') + 1
        total_inj_col = master_df.pop('total_number_injuries')
        master_df.insert(insert_pos, 'total_number_injuries', total_inj_col)

    # Reorder sqrt blood marker columns to be next to their originals
    for col in list(master_df.columns):  # use list to avoid mutation during iteration
        if col.endswith("_sqrt"):
            original_col = col.replace("_sqrt", "")
            if original_col in master_df.columns:
                # remove the sqrt column and reinsert after original
                sqrt_col_data = master_df.pop(col)
                insert_pos = master_df.columns.get_loc(original_col) + 1
                master_df.insert(insert_pos, col, sqrt_col_data)

    # Reorder log blood marker columns to be next to their originals
    for col in list(master_df.columns):  # use list to avoid mutation during iteration
        if col.endswith("_log"):
            original_col = col.replace("_log", "")
            if original_col in master_df.columns:
                # remove the sqrt column and reinsert after original
                sqrt_col_data = master_df.pop(col)
                insert_pos = master_df.columns.get_loc(original_col) + 1
                master_df.insert(insert_pos, col, sqrt_col_data)

    # reorder had_fall and after total_number_falls
    if 'had_fall' in master_df.columns and 'total_number_falls' in master_df.columns:
        insert_pos = master_df.columns.get_loc('total_number_falls') + 1
        had_fall_col = master_df.pop('had_fall')
        master_df.insert(insert_pos, 'had_fall', had_fall_col)

    # reorder BMI_extreme after bmi
    if 'BMI_extreme' in master_df.columns and 'bmi' in master_df.columns:
        insert_pos = master_df.columns.get_loc('bmi') + 1
        bmi_extreme_col = master_df.pop('BMI_extreme')
        master_df.insert(insert_pos, 'BMI_extreme', bmi_extreme_col)

        # rorder years_with_depression to be after age
    if 'years_with_depression' in master_df.columns and 'age' in master_df.columns:
        insert_pos = master_df.columns.get_loc('age') + 1
        years_col_data = master_df.pop('years_with_depression')
        master_df.insert(insert_pos, 'years_with_depression', years_col_data)

    

        
    return master_df




def compute_response_delta(row):
    # Try using MADRS scores first
    madrs_baseline = row.get("baseline_madrs")
    madrs_w10 = row.get("week10_madrs")

    if pd.notna(madrs_baseline) and pd.notna(madrs_w10) and madrs_baseline != 0:
        delta = (madrs_baseline - madrs_w10) / madrs_baseline * 100
        return round(delta)

    # If MADRS data isn't available, fallback to PHQ-9 scores
    phq9_baseline = row.get("baseline_phq9")
    phq9_w10 = row.get("week10_phq9")

    if pd.notna(phq9_baseline) and pd.notna(phq9_w10) and phq9_baseline != 0:
        delta = (phq9_baseline - phq9_w10) / phq9_baseline * 100
        return round(delta)

    # If neither is available, return NaN
    return np.nan

def add_sqrt_blood_markers(df):
    """
    Applies square root transformation to all relevant numeric blood marker columns
    and adds new columns with a '_sqrt' suffix.

    Args:
        df (pd.DataFrame): The DataFrame containing blood markers.

    Returns:
        pd.DataFrame: DataFrame with new sqrt-transformed columns.
    """
    blood_marker_cols = [
        'IL-6', 'gp130', 'IL-8/CXCL8', 'uPAR', 'MIF',
        'CCL2/JE/MCP-1', 'Osteoprotegerin/TNFRSF11B', 'IL-1 beta/IL-1F2',
        'CCL20/MIP-3 alpha', 'CCL3/MIP-1 alpha', 'CCL4/MIP-1 beta',
        'CCL13/MCP-4', 'GM-CSF', 'ICAM-1/CD54', 'TNF RII/TNFRSF1B',
        'TNF RI/TNFRSF1A', 'PIGF', 'CXCL1/GRO alpha/KC/CINC-1',
        'IGFBP-2', 'TIMP-1', 'IGFBP-6', 'Angiogenin'
    ]

    for col in blood_marker_cols:
        if col in df.columns:
            numeric_series = pd.to_numeric(df[col], errors='coerce')  # force numeric, coerce errors to NaN
            df[f"{col}_sqrt"] = np.where(numeric_series >= 0, np.sqrt(numeric_series), np.nan)

    return df



def add_log_blood_markers(df):
    """
    natural log transformation to all relevant  blood marker columns
    and adds new columns with a '_log' suffix. Only non-negative and non-zero values are transformed;
    others are set to NaN.

    Args:
        df (pd.DataFrame): The DataFrame containing blood markers.

    Returns:
        pd.DataFrame: DataFrame with new log-transformed columns.
    """
    blood_marker_cols = [
        'IL-6', 'gp130', 'IL-8/CXCL8', 'uPAR', 'MIF',
        'CCL2/JE/MCP-1', 'Osteoprotegerin/TNFRSF11B', 'IL-1 beta/IL-1F2',
        'CCL20/MIP-3 alpha', 'CCL3/MIP-1 alpha', 'CCL4/MIP-1 beta',
        'CCL13/MCP-4', 'GM-CSF', 'ICAM-1/CD54', 'TNF RII/TNFRSF1B',
        'TNF RI/TNFRSF1A', 'PIGF', 'CXCL1/GRO alpha/KC/CINC-1',
        'IGFBP-2', 'TIMP-1', 'IGFBP-6', 'Angiogenin'
    ]

    for col in blood_marker_cols:
        if col in df.columns:
            numeric_series = pd.to_numeric(df[col], errors='coerce')  # force numeric, coerce errors to NaN
            df[f"{col}_log"] = np.where(numeric_series > 0, np.log(numeric_series), np.nan)

    return df

######## master sheet creation #############

# make master dataframe by adding all record_ids into one column and then drop the duplicates
def make_master_df():
    from baard import load_all_record_ids, compute_remission_status, reorder_columns 
    baard_dir = "/external/rprshnas01/netdata_kcni/dflab/data/BAARD/"

    # Load base record IDs
    master_df = load_all_record_ids(baard_dir).drop_duplicates(subset=["record_id"]).reset_index(drop=True)

    # Load CSVs
    mri_date = pd.read_csv(f"{baard_dir}/mri/smri/processed/OPT_baseline_selected_thickness.csv")[['record_id', 'mr_date']]
    madras = pd.read_csv(f"{baard_dir}/temp/processed/OPT_madrs.csv")
    phq9 = pd.read_csv(f"{baard_dir}/temp/processed/OPT_phq9.csv")
    core_variables = pd.read_csv(f"{baard_dir}/temp/processed/OPT_demographics.csv")
    opt_mini = pd.read_csv(f"{baard_dir}/temp/processed/OPT_mini.csv")
    OPT_athf = pd.read_csv(f"{baard_dir}/temp/processed/OPT_ATHF.csv")
    nih_toolbox_cog = pd.read_csv(f"{baard_dir}/temp/processed/OPT_nih_toolbox_cog.csv")
    nih_toolbox_motor = pd.read_csv(f"{baard_dir}/temp/processed/OPT_nih_toolbox_motor.csv")
    meds_df = pd.read_csv(f"{baard_dir}/temp/processed/OPT_decision_support.csv")
    neurocog_df = pd.read_csv(f"{baard_dir}/temp/processed/baseline_indexscores.csv")
    falls_df = pd.read_csv(f"{baard_dir}/temp/processed/OPT_falls.csv")
    blood_df = pd.read_csv(f"{baard_dir}/temp/processed/baseline_blood.csv")
    smri_df = pd.read_csv(f"{baard_dir}/mri/smri/processed/OPT_baseline_selected_thickness.csv").drop(columns=['mr_date'], errors='ignore')
    fmri_df = pd.read_csv(f"{baard_dir}/mri/fmri/processed/OPT_baseline_connectivity_Network_Connectivity.csv")
    dwi_df = pd.read_csv(f"{baard_dir}/mri/dwi/processed/FA_2024.csv").drop(columns=['subjects'], errors='ignore')
    baseline_date_df = pd.read_csv(f"{baard_dir}/temp/processed/OPT_baseline_date.csv")
    genetics_df = pd.read_csv(f"{baard_dir}/temp/processed/OPT_genetics.csv")

    # Merge
    master_df = (master_df
        .merge(mri_date, on="record_id", how="left")
        .merge(baseline_date_df, on="record_id", how="left")
        .merge(madras, on="record_id", how="left")
        .merge(phq9, on="record_id", how="left")
        .merge(core_variables, on="record_id", how="left")
        .merge(opt_mini, on="record_id", how="left")
        .merge(OPT_athf, on="record_id", how="left")
        .merge(meds_df, on="record_id", how="left")
        .merge(neurocog_df, on="record_id", how="left")
        .merge(nih_toolbox_cog, on="record_id", how="left")
        .merge(nih_toolbox_motor, on="record_id", how="left")
        .merge(falls_df, on="record_id", how="left")
        .merge(blood_df, on="record_id", how="left")
        .merge(genetics_df, on="record_id", how="left")
        .merge(smri_df, on="record_id", how="left")
        .merge(fmri_df, on="record_id", how="left")
        .merge(dwi_df, on="record_id", how="left")
    )

    master_df["remission_status"] = master_df.apply(compute_remission_status, axis=1)
    master_df = master_df.sort_values(by="record_id").drop_duplicates(subset=["record_id"]).reset_index(drop=True)
    master_df['site'] = master_df['record_id'].str[:2].str.upper()
    master_df['has_blood'] = master_df['IL-6'].notna().astype(int) #don't really need this

    for week in [2, 4, 6, 8, 10]:
        master_df[f"on_bup_week{week}"] = ((master_df.get(f"week{week}_med1") == "BUPROPION") | 
                                           (master_df.get(f"week{week}_med2") == "BUPROPION")).astype(int)
        master_df[f"on_arp_week{week}"] = ((master_df.get(f"week{week}_med1") == "ARIPIPRAZOLE") | 
                                           (master_df.get(f"week{week}_med2") == "ARIPIPRAZOLE")).astype(int)

    bup_cols = [f"on_bup_week{w}" for w in [2, 4, 6, 8, 10] if f"on_bup_week{w}" in master_df.columns]
    arp_cols = [f"on_arp_week{w}" for w in [2, 4, 6, 8, 10] if f"on_arp_week{w}" in master_df.columns]

    master_df["total_on_bup"] = master_df[bup_cols].sum(axis=1)
    master_df["total_on_arp"] = master_df[arp_cols].sum(axis=1)

    master_df['medication_group'] = np.where(
        (master_df['total_on_bup'] >= 1) & (master_df['total_on_arp'] == 0), 'BUPROPION',
        np.where(
            (master_df['total_on_arp'] >= 1) & (master_df['total_on_bup'] == 0), 'ARIPIPRAZOLE',
            np.nan
        )
    )

    master_df['taking_bup'] = (master_df['medication_group'] == 'BUPROPION').astype(int)
    master_df['taking_arp'] = (master_df['medication_group'] == 'ARIPIPRAZOLE').astype(int)

    # sum falls and injury info


    falls_cols = [f"number_falls_week{w}" for w in [2, 4, 6, 8, 10] if f"number_falls_week{w}" in master_df.columns]
    inj_cols = [f"fall_injury_week{w}" for w in [2, 4, 6, 8, 10] if f"fall_injury_week{w}" in master_df.columns]

    master_df["total_number_falls"] = master_df[falls_cols].sum(axis=1)
    master_df["total_number_injuries"] = master_df[inj_cols].sum(axis=1)



    # Compute percent change in symptoms from baseline to week 10 using MADRS or PHQ9
    master_df["response_delta"] = master_df.apply(compute_response_delta, axis=1)
    #make response_status flag, that captures if someone has responded more than 50%
    master_df["response_status"] = master_df["response_delta"].apply(lambda x: 1 if x >= 50 else 0)

        # add had_fall binarized variable
    master_df['had_fall'] = (master_df['total_number_falls'] > 0).astype(int)

    # add new varaible BMI_extremer, where 1 = bmi > 40 or < 20, binary variables
    master_df['BMI_extreme'] = ((master_df['bmi'] > 40) | (master_df['bmi'] < 20)).astype(int)



    master_df=add_sqrt_blood_markers(master_df)

    master_df=add_log_blood_markers(master_df)


    # compute years_with_depression using difference between age and mini_addtl_q2(age at first depression episode)
    master_df['mini_addtl_q2_numeric'] = pd.to_numeric(master_df['mini_addtl_q2'], errors='coerce')
    master_df['years_with_depression'] = master_df['age'] - master_df['mini_addtl_q2_numeric']

    # use reorder_columns to reorder the columns in the master_df
    master_df = reorder_columns(master_df)

    return master_df


