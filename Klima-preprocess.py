import pandas as pd
import plotly.express as px
keys_country = pd.read_excel("Country Mapping.xlsx")

#Bilden von Mapping für deutsche Regionen und Kontinente:
keys_reg = dict(zip(keys_country["Recipient name (EN)"], keys_country["Region"]))
keys_con = dict(zip(keys_country["Recipient name (EN)"], keys_country["Continent"]))

df_bilateral22 = pd.read_excel("KliFi Bilateral 2022.xlsx")
df_bilateral22["Jahr"] = "2022"
df_bilateral21 = pd.read_excel("KliFi Bilateral 2021.xlsx")
df_bilateral21["Jahr"] = "2021"
df_bilateral = pd.concat([df_bilateral21, df_bilateral22])

#Offen: BMU Projekte mit Bemessung nach Provided statt Committed Amount
df_bilateral["Klimafinanzierung in USD"] = df_bilateral["CommittedAmount"]

df_multilateral22 = pd.read_excel("KliFi Multilateral 2022.xlsx")
df_multilateral22["Jahr"] = "2022"
df_multilateral21 = pd.read_excel("KliFi Multilateral 2021.xlsx")
df_multilateral21["Jahr"] = "2021"

df_multilateral = pd.concat([df_multilateral21, df_multilateral22])

df_multilateral["Recipient"] = df_multilateral["MultilateralInstitution"]
df_multilateral["Ressort"] = "Multilateral"
df_multilateral["Klimafinanzierung in USD"] = df_multilateral["ProvidedClimateSpecific"]

#Aufsplitten für Ressort, DO und Projektnummer:
df_zusatz = df_bilateral["AdditionalInformation"].str.split(',', expand=True)
df_melder = df_zusatz[0].str.split('(', expand=True)

#Erhalten von Projektnummer, Ressort (ohne Leerzeichen am Ende) und DOs:
df_zusatz["Projektnummer"] = df_zusatz[2]
df_melder["Ressort"] = df_melder[0]
df_melder["Ressort"] = df_melder["Ressort"].str.rstrip()
df_melder["Durchführungsorganisation"] = df_melder[1]

#Für Erhalten der  FBS (drei-ziffrig) für Mappen auf deutsche Bezeichnung:
#df_subsector = df_bilateral["Sector"].str.split('(', expand=True)
#df_subsector[1] = df_subsector[1].str.replace(r')', '')
#df_subsector["FBS Code"] = df_subsector[1]

#Zusammenstellen der neuen Datei:
df_bilateral_sort = pd.concat([df_bilateral["Channel"], df_bilateral["Recipient"], df_bilateral["Title"],
                               df_bilateral["TypeOfSupport"], df_bilateral["FinancialInstrument"], 
                               df_bilateral["Sector"], df_melder["Ressort"], df_bilateral["Jahr"], df_bilateral["Klimafinanzierung in USD"],
                               df_melder["Durchführungsorganisation"], df_zusatz["Projektnummer"]],
                              axis = 1)

#df_bilateral_sort["FBS Sektorcode"] = df_bilateral_sort["FBS Code"].astype(str).str[:3]

#Zusammenführen bilateral und multilaterale Tabellen:
dat_gesamt = pd.concat([df_bilateral_sort, df_multilateral], join = "inner")

#Kürzen der Ressortbezeichnung und Vereinheitlichen:
dat_gesamt["Ressort"].loc[dat_gesamt["Ressort"] == "DEG - Deutsche Investitions- und Entwicklungsgesellschaft mbH"] = "DEG"
dat_gesamt["Ressort"].loc[dat_gesamt["Ressort"] == "Kreditanstalt für Wiederaufbau"] = "KfW"

#Vereinfachen der Kategorien für Finanzinstrumente:
dat_gesamt.loc[dat_gesamt["FinancialInstrument"] == "grant", "FinancialInstrument"] = "Grant"
dat_gesamt.loc[dat_gesamt["FinancialInstrument"] == "Direct investment in companies/SPVs (mezzanine/senior debt)", "FinancialInstrument"] = "Direct investment in companies/SPVs"
dat_gesamt.loc[dat_gesamt["FinancialInstrument"] == "Direct investment in companies/SPVs (equity)", "FinancialInstrument"] = "Direct investment in companies/SPVs"
dat_gesamt.loc[dat_gesamt["FinancialInstrument"] == "Syndicated loan", "FinancialInstrument"] = "Syndicated/composite loan"
dat_gesamt.loc[dat_gesamt["FinancialInstrument"] == "composite loan", "FinancialInstrument"] = "Syndicated/composite loan"

string = dat_gesamt["Recipient"].str.split('(', expand=True)
dat_gesamt["Recipient"] = string[0]
dat_gesamt["Recipient"] = dat_gesamt["Recipient"].str.rstrip()

dat_gesamt["Region"] = dat_gesamt["Recipient"].map(keys_reg)
dat_gesamt["Kontinent"] = dat_gesamt["Recipient"].map(keys_con)

#Noch offen: Regionen, Kontinente und Organisationen als Empfänger noch keine Lösung und Länder mit anderen Namen 
dat_gesamt.loc[dat_gesamt["Region"].isna() == True, ["Region", "Kontinent"]] = "Andere/nicht aufteilbar"

dat_gesamt.to_csv('data.csv', index = False) 