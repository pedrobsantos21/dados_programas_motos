import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium import Choropleth
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium

path_sysdata = "data/sysdata.gpkg"
sysdata = gpd.read_file(path_sysdata)

sysdata["taxa_obitos"] = (
    (sysdata["quantidade_obitos"] / sysdata["populacao_total"]) * 100000
).fillna(0)

taxa_por_superintendencia = (
    sysdata.groupby(["Superintendência", "ano"])
    .agg(
        quantidade_obitos=("quantidade_obitos", "sum"),
        populacao_total=("populacao_total", "sum"),
    )
    .reset_index()
)

taxa_por_superintendencia["taxa_obitos"] = (
    (
        taxa_por_superintendencia["quantidade_obitos"]
        / taxa_por_superintendencia["populacao_total"]
    )
    * 100000
).fillna(0)

obitos_2022 = (
    sysdata[sysdata["ano"] == 2022]
    .groupby("cod_ibge")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2022"})
)

obitos_2023 = (
    sysdata[sysdata["ano"] == 2023]
    .groupby("cod_ibge")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2023"})
)

obitos_2024 = (
    sysdata[sysdata["ano"] == 2024]
    .groupby("cod_ibge")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2024"})
)

taxa_media = (
    sysdata[sysdata["ano"].isin([2022, 2023, 2024])]
    .groupby("cod_ibge")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_media"})
)

taxa_2022 = (
    sysdata[sysdata["ano"] == 2022]
    .groupby("cod_ibge")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_2022"})
)

taxa_2024 = (
    sysdata[sysdata["ano"] == 2024]
    .groupby("cod_ibge")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_2024"})
)

todos_municipios = sysdata["cod_ibge"].unique()
tabela_base = pd.DataFrame({"cod_ibge": todos_municipios})

tabela_municipios = (
    tabela_base.merge(obitos_2022, on="cod_ibge", how="left")
    .merge(obitos_2023, on="cod_ibge", how="left")
    .merge(obitos_2024, on="cod_ibge", how="left")
    .merge(taxa_2022, on="cod_ibge", how="left")
    .merge(taxa_2024, on="cod_ibge", how="left")
    .merge(taxa_media, on="cod_ibge", how="left")
    .fillna(0)
)

tabela_municipios["delta_obitos_pct"] = (
    (
        (tabela_municipios["obitos_2024"] - tabela_municipios["obitos_2022"])
        / tabela_municipios["obitos_2022"].replace(0, 1)
    )
    * 100
).fillna(0)

tabela_municipios["delta_taxa_pct"] = (
    (
        (tabela_municipios["taxa_2024"] - tabela_municipios["taxa_2022"])
        / tabela_municipios["taxa_2022"].replace(0, 1)
    )
    * 100
).fillna(0)

info_municipios = sysdata[
    ["cod_ibge", "name_muni", "Superintendência"]
].drop_duplicates(subset="cod_ibge")

tabela_municipios = tabela_municipios.merge(info_municipios, on="cod_ibge", how="left")

tabela_municipios_display = tabela_municipios[
    [
        "cod_ibge",
        "name_muni",
        "Superintendência",
        "obitos_2022",
        "obitos_2023",
        "obitos_2024",
        "taxa_media",
        "delta_obitos_pct",
    ]
].copy()

tabela_municipios_display["cod_ibge"] = tabela_municipios_display["cod_ibge"].astype(
    str
)
tabela_municipios_display["obitos_2022"] = tabela_municipios_display[
    "obitos_2022"
].astype(int)
tabela_municipios_display["obitos_2023"] = tabela_municipios_display[
    "obitos_2023"
].astype(int)
tabela_municipios_display["obitos_2024"] = tabela_municipios_display[
    "obitos_2024"
].astype(int)
tabela_municipios_display["taxa_media"] = tabela_municipios_display["taxa_media"].round(
    2
)
tabela_municipios_display["delta_obitos_pct"] = tabela_municipios_display[
    "delta_obitos_pct"
].round(2)

tabela_municipios_display.columns = [
    "Código IBGE",
    "Município",
    "Superintendência",
    "Óbitos 2022",
    "Óbitos 2023",
    "Óbitos 2024",
    "Taxa Média de Óbitos",
    "Variação óbitos (%)",
]

obitos_sup_2022 = (
    sysdata[sysdata["ano"] == 2022]
    .groupby("Superintendência")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2022"})
)

obitos_sup_2023 = (
    sysdata[sysdata["ano"] == 2023]
    .groupby("Superintendência")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2023"})
)

obitos_sup_2024 = (
    sysdata[sysdata["ano"] == 2024]
    .groupby("Superintendência")["quantidade_obitos"]
    .sum()
    .reset_index()
    .rename(columns={"quantidade_obitos": "obitos_2024"})
)

taxa_media_sup = (
    sysdata[sysdata["ano"].isin([2022, 2023, 2024])]
    .groupby("Superintendência")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_media"})
)

todos_superintendencias = sysdata["Superintendência"].dropna().unique()
tabela_base_sup = pd.DataFrame({"Superintendência": todos_superintendencias})

tabela_superintendencias = (
    tabela_base_sup.merge(obitos_sup_2022, on="Superintendência", how="left")
    .merge(obitos_sup_2023, on="Superintendência", how="left")
    .merge(obitos_sup_2024, on="Superintendência", how="left")
    .merge(taxa_media_sup, on="Superintendência", how="left")
    .fillna(0)
)

tabela_superintendencias["delta_obitos_pct"] = (
    (
        (
            tabela_superintendencias["obitos_2024"]
            - tabela_superintendencias["obitos_2022"]
        )
        / tabela_superintendencias["obitos_2022"].replace(0, 1)
    )
    * 100
).fillna(0)

tabela_superintendencias_display = tabela_superintendencias[
    [
        "Superintendência",
        "obitos_2022",
        "obitos_2023",
        "obitos_2024",
        "taxa_media",
        "delta_obitos_pct",
    ]
].copy()

tabela_superintendencias_display["obitos_2022"] = tabela_superintendencias_display[
    "obitos_2022"
].astype(int)
tabela_superintendencias_display["obitos_2023"] = tabela_superintendencias_display[
    "obitos_2023"
].astype(int)
tabela_superintendencias_display["obitos_2024"] = tabela_superintendencias_display[
    "obitos_2024"
].astype(int)
tabela_superintendencias_display["taxa_media"] = tabela_superintendencias_display[
    "taxa_media"
].round(2)
tabela_superintendencias_display["delta_obitos_pct"] = tabela_superintendencias_display[
    "delta_obitos_pct"
].round(2)

tabela_superintendencias_display.columns = [
    "Superintendência",
    "Óbitos 2022",
    "Óbitos 2023",
    "Óbitos 2024",
    "Taxa Média de Óbitos",
    "Variação óbitos (%)",
]


# Configuração da página
st.set_page_config(
    page_title="Programa 'Piloto Consciente SP' - Diagnóstico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Título principal
st.title("Programa 'Piloto Consciente SP' - Diagnóstico")

# Primeira linha: Tabela e Mapa de Municípios
col1, col2 = st.columns(2)

with col1:
    st.subheader("Tabela de Municípios")
    st.dataframe(
        tabela_municipios_display,
        use_container_width=True,
        hide_index=True,
    )

with col2:
    st.subheader("Municípios")
    # Preparar dados para o mapa
    dados_2024 = sysdata[sysdata["ano"] == 2024].copy()

    taxa_media_por_municipio = (
        sysdata[sysdata["ano"].isin([2022, 2023, 2024])]
        .groupby("cod_ibge")["taxa_obitos"]
        .mean()
        .reset_index()
        .rename(columns={"taxa_obitos": "taxa_media"})
    )

    dados_2024 = dados_2024.merge(
        taxa_media_por_municipio, on="cod_ibge", how="left"
    )
    dados_2024["taxa_media_formatada"] = dados_2024["taxa_media"].round(2)

    # Criar mapa Folium
    m = folium.Map(
        location=[-23.5505, -46.6333],
        zoom_start=7,
        tiles="OpenStreetMap",
    )

    Choropleth(
        geo_data=dados_2024.to_json(),
        data=dados_2024,
        columns=["cod_ibge", "taxa_obitos"],
        key_on="feature.properties.cod_ibge",
        fill_color="Blues",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Taxa de Óbitos por 100 mil habitantes",
    ).add_to(m)

    folium.GeoJson(
        dados_2024.to_json(),
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "transparent",
            "weight": 0,
        },
        tooltip=GeoJsonTooltip(
            fields=["name_muni", "Superintendência", "taxa_media_formatada"],
            aliases=["Município:", "Superintendência:", "Taxa Média:"],
            localize=True,
        ),
    ).add_to(m)

    # Exibir mapa usando streamlit-folium
    st_folium(m, width=None, height=600, returned_objects=[])

# Segunda linha: Tabela de Superintendências
col3, col4 = st.columns(2)

with col3:
    st.subheader("Tabela de Superintendências")
    st.dataframe(
        tabela_superintendencias_display,
        use_container_width=True,
        hide_index=True,
    )

with col4:
    st.subheader("Superintendências")
    # Espaço reservado para futuro mapa de superintendências se necessário
