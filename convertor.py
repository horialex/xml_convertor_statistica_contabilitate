import pandas as pd
import datetime
import xml.etree.ElementTree as ET
from check_code import format_no_decimals, get_nomenclator, get_su, map_country, save_incorrect_codes

# luna pt care extragem datele
luna = 'decembrie'

# Date statice
month = "12"
year = "2025" 
ref_period = f"{year}-{month}"
nr_tva=  "0022064919"
nume_firma = "SC UNITED TIM SRL"
first_name = "RUS"
last_name = "ALINA IONELA"
email = "rusalinaionela29@yahoo.com"
phone = "0755345573"
position = "CONTABIL"
ns = "http://www.intrastat.ro/xml/InsSchema"
create_dt = datetime.datetime.now().astimezone().isoformat(timespec='milliseconds')

# Alte date
delivery_terms_code = "DAP"
nature_of_transaction_A_code = "1"
nature_of_transaction_B_code = "1.1"
mode_of_transport_code = "3"
supply_unit_code = "p/st"

nomenclator_path = "ins/nomenclator.xls"


df = pd.read_excel(f"date/{luna}.xlsx", header=1, dtype=str)
df_nomenclator = get_nomenclator(nomenclator_path)

# Drop fully empty rows (like your first row)
df = df.dropna(how="all")
df = df.reset_index(drop=True)
df.columns = [
    "furnizor",
    "denumire_produs_romana",
    "cod_nc8",
    "cantitate",
    "masa_neta_kg",
    "valoare_factura_fara_tva_fara_voucher",
    "tara_origine_produs",
    "tara_expediere"
]

# df = df.fillna("")
# df = df.iloc[:-1].reset_index(drop=True) // Sterge ultimul rand
df = df.reset_index(drop=True)
df = format_no_decimals(df, ["valoare_factura_fara_tva_fara_voucher", "masa_neta_kg"])

# ------------------    FIX
df["cod_nc8"] = df["cod_nc8"].astype(str).str.strip()

for col in [
    "valoare_factura_fara_tva_fara_voucher",
    "cantitate",
    "masa_neta_kg"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    
# ------------------    

# Convert numeric columns
# df["valoare_factura_fara_tva_fara_voucher"] = df["valoare_factura_fara_tva_fara_voucher"].astype(float)
# df["cantitate"] = df["cantitate"].astype(float)
# df["masa_neta_kg"] = df["masa_neta_kg"].astype(float)


# --- AGGREGATION WITH PRESERVED COLUMNS ---
df_agg = df.groupby("cod_nc8", as_index=False).agg({
    "furnizor": "first",
    "denumire_produs_romana": lambda x: ", ".join(sorted(set(map(str, x)))),
    "tara_origine_produs": "first",
    "tara_expediere": "first",
    "valoare_factura_fara_tva_fara_voucher": "sum",
    "cantitate": "sum",
    "masa_neta_kg": "sum"
})

# Filter rows that are not in nomenclator code - incorrect rows basically
cn_set = set(df_nomenclator["CN"])
df_not_in_nomenclator = df_agg[~df_agg["cod_nc8"].isin(cn_set)]
if not df_not_in_nomenclator.empty:
    save_incorrect_codes(df_agg, cn_set, luna)
    print("Incorrect CN codes found. Program stopped.")
    exit()


# XML namespace
ET.register_namespace("", ns)

# Root
root = ET.Element(f"{{{ns}}}InsNewArrival", {"SchemaVersion": "1.0"})

# ---- InsCodeVersions ----
code_versions = ET.SubElement(root, "InsCodeVersions")
versions = {
    "CountryVer": "2022",
    "EuCountryVer": "2021",
    "CnVer": "2025",
    "ModeOfTransportVer": "2005",
    "DeliveryTermsVer": "2021",
    "NatureOfTransactionAVer": "2022",
    "NatureOfTransactionBVer": "2022",
    "CountyVer": "1",
    "LocalityVer": "06/2006",
    "UnitVer": "1",
}

for tag, value in versions.items():
    ET.SubElement(code_versions, tag).text = value

# ---- InsDeclarationHeader ----
header = ET.SubElement(root, "InsDeclarationHeader")

ET.SubElement(header, "VatNr").text = nr_tva
ET.SubElement(header, "FirmName").text = nume_firma
ET.SubElement(header, "RefPeriod").text = ref_period
ET.SubElement(header, "CreateDt").text = create_dt

# Contact person
contact = ET.SubElement(header, "ContactPerson")
ET.SubElement(contact, "LastName").text = last_name
ET.SubElement(contact, "FirstName").text = first_name
ET.SubElement(contact, "Email").text = email
ET.SubElement(contact, "Phone").text = phone
ET.SubElement(contact, "Position").text = position

for idx, row in df_agg.iterrows():
    
    # Stop if any NaN detected
    for col, val in row.items():
        if pd.isna(val):
            print(f"⚠️ NaN found at row {idx}, column '{col}'")
            print("Row content:", row)
            raise SystemExit("Stopping due to NaN value")

    item = ET.SubElement(root, "InsArrivalItem", {"OrderNr": str(idx + 1)})

    ET.SubElement(item, "Cn8Code").text = str(row["cod_nc8"])
    ET.SubElement(item, "InvoiceValue").text = str(int(row["valoare_factura_fara_tva_fara_voucher"]))
    ET.SubElement(item, "StatisticalValue").text = str(int(row["valoare_factura_fara_tva_fara_voucher"]))
    ET.SubElement(item, "NetMass").text = str(row["masa_neta_kg"])

    ET.SubElement(item, "NatureOfTransactionACode").text = nature_of_transaction_A_code
    ET.SubElement(item, "NatureOfTransactionBCode").text = nature_of_transaction_B_code
    ET.SubElement(item, "DeliveryTermsCode").text = delivery_terms_code
    ET.SubElement(item, "ModeOfTransportCode").text = mode_of_transport_code

    ET.SubElement(item, "CountryOfOrigin").text = map_country(row["tara_origine_produs"])

    # Add InsSupplUnitsInfo node only if the code can do this
    cn_su = get_su(row["cod_nc8"], df_nomenclator)
    if cn_su == supply_unit_code:
        suppl = ET.SubElement(item, "InsSupplUnitsInfo")
        ET.SubElement(suppl, "SupplUnitCode").text = supply_unit_code
        ET.SubElement(suppl, "QtyInSupplUnits").text = str(row["cantitate"])
    
    ET.SubElement(item, "CountryOfConsignment").text = row["tara_expediere"]


# ---- Write to file ----
tree = ET.ElementTree(root)
tree.write(f"xml_result/intrastat_{luna}.xml", encoding="utf-8", xml_declaration=True)

total_cantitate = df_agg["cantitate"].sum()
print(total_cantitate)

# row = pd.read_excel(f"date/{luna}.xlsx", header=1, dtype=str)
# row = row.iloc[:-1].reset_index(drop=True)

# print(len(row))
# print(row.iloc[-1])

# df_agg.to_csv("aggregated.csv", index=False)
# # df.to_csv("original.csv", index=False)
# print(df.groupby("cod_nc8").size().sort_values(ascending=False).head(10))

# print(df[df["cod_nc8"] == "21069092"])

# for val in df["cod_nc8"]:
#     if "21069092" in str(val):
#         print(repr(val))
        
# raw = pd.read_excel(f"date/{luna}.xlsx", header=1, dtype=str)

# print("In Excel:", (raw["cod nc8"].astype(str).str.strip() == "21069092").sum())
# print("In DF:", (df["cod_nc8"] == "21069092").sum())

# for i, val in enumerate(raw["cod nc8"]):
#     if "21069092" in str(val):
#         print(i, val, list(str(val)))
        
        
# print(raw.iloc[160:170][["cod nc8", "denumire produs romana"]])

# print(raw.head())

# # print(df.loc[df["cod_nc8"].astype(str).str.contains("21069092", na=False), "cod_nc8"])