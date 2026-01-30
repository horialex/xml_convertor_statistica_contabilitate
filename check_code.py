import pandas as pd

nomenclator_path = "ins/nomenclator.xls"

country_map = {
    "China": "CN",
}

def get_nomenclator(path):
    df = pd.read_excel(path, dtype=str)
    df["SU"] = df["SU"].fillna("")
    df["CN"] = df["CN"].astype(str)
    filtered_df = df[df["CN"].str.len() >= 7]
    result = filtered_df[["CN", "SU"]]
    return result


def is_code_valid(cn_code, set):
    return cn_code in set

def get_su(cn_code, df):
    row = df[df["CN"] == cn_code]
    if not row.empty:
        return row["SU"].iloc[0]
    return None

def save_incorrect_codes(df, cn_set, luna):
    df_not_in_nomenclator = df[~df["cod_nc8"].isin(cn_set)]
    result = df_not_in_nomenclator[["cod_nc8"]]
    
    result.index = result.index + 2
    result.index.name = "row_number"
    
    output_path = f"coduri_gresite/coduri_gresite_{luna}.csv"
    result.to_csv(output_path, index=True)


def format_decimal(value):
    if value is None or value == "" or pd.isna(value):
        return ""
    try:
        return f"{float(value):.3f}"   # always 3 decimals
    except:
        return str(value)
    
def format_no_decimals(df, columns):
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(0).astype("Int64")
    return df    


def map_country(value):
    if pd.isna(value) or value == "":
        return ""
    return country_map.get(value, value)  
