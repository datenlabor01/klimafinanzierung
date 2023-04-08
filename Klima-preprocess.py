import pandas as pd
import re

#Read-in data:
df_bilateral22 = pd.read_excel("KlifiDEU2022.xlsx", sheet_name = "Annex III Table 1", header = 17)
df_multilateral22 = pd.read_excel("KlifiDEU2022.xlsx", sheet_name = "Annex III Table 2", header = 19)
df_mobilised22 = pd.read_excel("KlifiDEU2022.xlsx", sheet_name = "Annex III Table 3", header = 16)

df_bilateral21 = pd.read_excel("KlifiDEU2021.xlsx", sheet_name = "III_Table1")
df_multilateral21 = pd.read_excel("KlifiDEU2021.xlsx", sheet_name = "III_Table2")
df_mobilised21 = pd.read_excel("KlifiDEU2021.xlsx", sheet_name = "III_Table3")

#Delete empty first row and first column for all frames:
df_bilateral22 = df_bilateral22.drop(index=[0])
df_bilateral22 = df_bilateral22.iloc[:, 1:]
df_multilateral22 = df_multilateral22.drop(index=[0])
df_multilateral22= df_multilateral22.iloc[:, 1:]
df_mobilised22 = df_mobilised22.drop(index=[0])
df_mobilised22= df_mobilised22.iloc[:, 1:]

#Add year entries:
df_bilateral22["Year"] = 2022
df_multilateral22["Year"] = 2022
df_mobilised22["Year"] = 2022
df_bilateral21["Year"] = 2021
df_multilateral21["Year"] = 2021
df_mobilised21["Year"] = 2021

#Align column names to each other:
df_bilateral22.columns = df_bilateral21.columns
df_multilateral22.columns = df_multilateral21.columns
df_mobilised22.columns = df_mobilised21.columns

#Combine to one frame:
df_bilateral = pd.concat([df_bilateral21, df_bilateral22])
df_multilateral = pd.concat([df_multilateral21, df_multilateral22])
df_mobilised = pd.concat([df_mobilised22, df_mobilised21])

#Set climate finance to relevant columns:
df_bilateral["Klimafinanzierung"] = df_bilateral["CommittedAmount"]
bol = df_bilateral["AdditionalInformation"].str.contains("German Energy and Climate Fund")
df_bilateral.loc[bol == True, "Klimafinanzierung"] = df_bilateral.loc[bol == True, "ProvidedAmount"]

df_multilateral["Klimafinanzierung"] = df_multilateral["ProvidedClimateSpecific"]
df_mobilised["Klimafinanzierung"] = df_mobilised["AmountMobilised"]

#Create category for distinction between mobilised private, budgetary resources and mobilised public:
df_bilateral["Haushalt"] = "Haushaltsmittel"
df_bilateral.loc[df_bilateral["AdditionalInformation"].str.contains("project also included in") == True, "Haushalt"] = "Mobilisierte öffentliche Klimafinanzierung"
df_multilateral["Haushalt"] = "Haushaltsmittel"
df_mobilised["Haushalt"] = "Mobilisierte private Klimafinanzierung"

#Change bilateral BMU projects to provided amount instead of commited amount:
project_list =  pd.read_excel("project_list.xlsx")
projects = list(project_list.iloc[:,0])
df_bilateral.loc[df_bilateral.Title.isin(projects), "Klimafinanzierung"] = df_bilateral.loc[df_bilateral.Title.isin(projects), "ProvidedAmount"]

#Align multilateral and mobilised data to other two frames:
df_multilateral["Recipient"] = df_multilateral["MultilateralInstitution"]
df_multilateral["Ressort"] = "Multilateral"
df_mobilised["Ressort"] = df_mobilised["AdditionalInformation"]
df_mobilised["FinancialInstrument"] = df_mobilised["TypeOfPublicIntervention"]

#Add channel description:
df_multilateral["Channel"] = "Multilateral"
df_bilateral["Channel"] = "Bilateral"
df_mobilised["Channel"] = "Mobilisiert"

#Read-in mapping table for region and continent:
keys_country = pd.read_excel("Country Mapping.xlsx")
#Get German recipient name, region and continent:
keys_reg = dict(zip(keys_country["Recipient name (EN)"], keys_country["Region"]))
keys_con = dict(zip(keys_country["Recipient name (EN)"], keys_country["Continent"]))
keys_rec = dict(zip(keys_country["Recipient name (EN)"], keys_country["Recipient Name deutsch"]))
keys_con_eng = dict(zip(keys_country["Recipient name (EN)"], keys_country["CONTINENT"]))
keys_iso = dict(zip(keys_country["Recipient name (EN)"], keys_country["ISOcode"]))

#Split-up column to obtain ressort:
df_zusatz = df_bilateral["AdditionalInformation"].str.split(',', expand=True)
df_melder = df_zusatz[0].str.split('(', expand=True)

#Get optionally project number, ressort (without whitespace) and implementing organization:
df_zusatz["Projektnummer"] = df_zusatz[2]
df_melder["Ressort"] = df_melder[0]
df_melder["Ressort"] = df_melder["Ressort"].str.rstrip()
df_melder["Durchführungsorganisation"] = df_melder[1]
df_bilateral["Ressort"] = df_melder["Ressort"]

#Build main dataframe:
dat_gesamt = pd.concat([df_bilateral, df_multilateral, df_mobilised], join = "inner").reset_index()

#For German description of purpose codes:
#Read-in mapping table:
keys_codes = pd.read_excel("Purpose Codes Mapping.xlsx")
#Delete empty entries to avoid false mapping:
keys_codes = keys_codes[keys_codes['DAC 5'].notna()]
keys_purpose = dict(zip(keys_codes["DAC 5"].astype(str), keys_codes["Beschreibung"]))
#Apply mapping to purpose code between first brackets:
df_subsector = dat_gesamt["Sector"].str.extract('.*\((.*)\).*')
df_subsector["Sector"] = df_subsector[0].astype(str).map(keys_purpose)
dat_gesamt.loc[df_subsector["Sector"].isna() == False, "Sector"] = df_subsector.loc[df_subsector["Sector"].isna() == False, "Sector"]
#Delete trailing whitespace:
dat_gesamt["Sector"] = dat_gesamt["Sector"].str.rstrip()
#Align terminology:
dat_gesamt.loc[dat_gesamt["Sector"] == "not applicable", "Sector"] = "Andere"
dat_gesamt.loc[dat_gesamt["Sector"] == "Not applicable", "Sector"] = "Andere"
dat_gesamt.loc[dat_gesamt["Sector"] == "not available", "Sector"] = "Andere"
dat_gesamt.loc[dat_gesamt["Sector"].isna() == True, "Sector"] = "Andere"

#Simpliy and translate instrument categories:
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "grant", "FinancialInstrument"] = "Zuschuss"
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "Grant", "FinancialInstrument"] = "Zuschuss"
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "concessional loan", "FinancialInstrument"] = "Darlehen"
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "concessional loan from budgetary sources", "FinancialInstrument"] = "Darlehen"
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "composite loan", "FinancialInstrument"] = "Darlehen"
dat_gesamt.loc[dat_gesamt.FinancialInstrument == "grant equivalent of concessional loan", "FinancialInstrument"] = "Darlehen"

#Align ressort names to each other and shorten:
dat_gesamt.loc[dat_gesamt["Ressort"].str.contains("Deutsche Investitions- und Entwicklungsgesellschaft"), "Ressort"] = "DEG"
dat_gesamt.loc[dat_gesamt["Ressort"].str.contains("Kreditanstalt für Wiederaufbau"), "Ressort"] = "KfW"
dat_gesamt.loc[dat_gesamt["Ressort"] == "BMWi", "Ressort"] = "BMWK"
dat_gesamt.loc[dat_gesamt["Ressort"] == "BMU", "Ressort"] = "BMUV"

#Split recipients to retain country name/organization name in one column:
string = dat_gesamt["Recipient"].str.split('(', expand=True)
dat_gesamt["Recipient"] = string[0]
#Delete trailing whitespace:
dat_gesamt["Recipient"] = dat_gesamt["Recipient"].str.rstrip()

#Align country name to OECD coding:
dat_gesamt.loc[dat_gesamt["Recipient"] == "West Bank and Gaza Strip / Palestinian Territory", "Recipient"] = "West Bank and Gaza Strip"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Turkey", "Recipient"] = "Türkiye"
dat_gesamt.loc[dat_gesamt["Recipient"] == "United Republic of Tanzania", "Recipient"] = "Tanzania"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Cote d'Ivoire / Ivory Coast", "Recipient"] = "Côte d'Ivoire"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Côte d'Ivoire / Ivory Coast", "Recipient"] = "Côte d'Ivoire"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Syria", "Recipient"] = "Syrian Arab Republic"
dat_gesamt.loc[dat_gesamt["Recipient"] == "East Timor", "Recipient"] = "Timor-Leste"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Swaziland", "Recipient"] = "Eswatini"
dat_gesamt.loc[dat_gesamt["Recipient"] == "China", "Recipient"] = "China (People's Republic of)"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Republic of North Macedonia", "Recipient"] = "North Macedonia"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Republic of Korea", "Recipient"] = "Democratic People's Republic of Korea"

#Align entry names:
dat_gesamt.loc[dat_gesamt["Recipient"] == "global", "Recipient"] = "Developing countries, unspecified"
dat_gesamt.loc[dat_gesamt["Recipient"] == "regional", "Recipient"] = "Developing countries, unspecified"
dat_gesamt.loc[dat_gesamt["Recipient"] == "developing country, not specified", "Recipient"] = "Developing countries, unspecified"
dat_gesamt.loc[dat_gesamt["Recipient"] == "developing countries, unspecified", "Recipient"] = "Developing countries, unspecified"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Region Asia /Middle East / South East Europe", "Recipient"] = "Developing countries, unspecified"

dat_gesamt.loc[dat_gesamt["Recipient"] == "Afrika na", "Recipient"] = "Africa, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Africa na", "Recipient"] = "Africa, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Region Africa", "Recipient"] = "Africa, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Latin America and the Caribbean supra-regional", "Recipient"] = "South America, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Latin America", "Recipient"] = "South America, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Region Latin America and the Caribbean", "Recipient"] = "South America, regional"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Americas, regional", "Recipient"] = "South America, regional"

#Apply OECD-country mapping to get region and continent:
dat_gesamt["Recipient Deutsch"] = dat_gesamt["Recipient"].map(keys_rec)
dat_gesamt["Region"] = dat_gesamt["Recipient"].map(keys_reg)
dat_gesamt["Kontinent"] = dat_gesamt["Recipient"].map(keys_con)
dat_gesamt["CONTINENT"] = dat_gesamt["Recipient"].map(keys_con_eng)
dat_gesamt["ISOCode"] = dat_gesamt["Recipient"].map(keys_iso)

dat_gesamt.loc[dat_gesamt["Recipient Deutsch"].isna() == True, "Recipient Deutsch"] = dat_gesamt.loc[dat_gesamt["Recipient Deutsch"].isna() == True, "Recipient"]

#Add region and continent for Israel and Chile as they are not on OECD list:
dat_gesamt.loc[dat_gesamt["Recipient"] == "Israel", "Region"] = "Naher- und Mittlerer Osten"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Israel", "Kontinent"] = "Asien"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Chile", "Region"] = "Südamerika"
dat_gesamt.loc[dat_gesamt["Recipient"] == "Chile", "Kontinent"] = "Amerika"

#Add "nicht aufteilbar" for recipients without assigned region and continent: 
dat_gesamt.loc[dat_gesamt["Region"].isna() == True, ["Region", "Kontinent"]] = "Nicht aufteilbar"

dat_gesamt.to_csv('klifi_deu.csv', sep = ";", index = False) 
