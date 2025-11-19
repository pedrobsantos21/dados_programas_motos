import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from folium.plugins import Fullscreen
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


# Configuração da página com tema escuro
st.set_page_config(
    page_title="Programa 'Piloto Consciente SP' - Diagnóstico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS para tema escuro
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título principal
st.title("Programa 'Piloto Consciente SP' - Diagnóstico")

# Preparar dados para o mapa
dados_2024 = sysdata[sysdata["ano"] == 2024].copy()

taxa_media_por_municipio = (
    sysdata[sysdata["ano"].isin([2022, 2023, 2024])]
    .groupby("cod_ibge")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_media"})
)

dados_2024 = dados_2024.merge(taxa_media_por_municipio, on="cod_ibge", how="left")
dados_2024["taxa_media_formatada"] = dados_2024["taxa_media"].round(2)

# Calcular min e max da taxa média para o colormap
min_taxa = dados_2024["taxa_media"].min()
max_taxa = dados_2024["taxa_media"].max()

# Criar colormap usando Blues do colorbrewer
colormap = cm.LinearColormap(
    colors=["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
    vmin=min_taxa,
    vmax=max_taxa,
    caption="Taxa Média de Óbitos (por 100 mil hab.)",
)


# Criar função para definir cor baseada na taxa média usando o colormap
def get_color(taxa_valor):
    """Retorna cor em formato hex baseada na taxa média usando escala Blues"""
    return colormap.rgb_hex_str(taxa_valor)


# Criar coluna de cor para o folium
dados_2024["color"] = dados_2024["taxa_media"].apply(get_color)

# Criar mapa folium (centro em São Paulo)
m = folium.Map(
    location=[-23.5505, -46.6333],
    zoom_start=7,
    tiles="CartoDB positron",  # Tema claro
)

# Adicionar plugin de fullscreen
Fullscreen().add_to(m)

# Adicionar GeoJSON ao mapa
folium.GeoJson(
    dados_2024.to_json(),
    style_function=lambda feature: {
        "fillColor": feature["properties"]["color"],
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["name_muni", "Superintendência", "taxa_media_formatada"],
        aliases=["Município:", "Superintendência:", "Taxa Média:"],
        style=("background-color: steelblue; color: white; padding: 10px;"),
    ),
).add_to(m)

# Criar legenda
# Calcular valores para a legenda
valores_legenda = [
    min_taxa,
    min_taxa + (max_taxa - min_taxa) * 0.25,
    min_taxa + (max_taxa - min_taxa) * 0.5,
    min_taxa + (max_taxa - min_taxa) * 0.75,
    max_taxa,
]

cores_legenda = [get_color(v) for v in valores_legenda]

# Criar HTML da legenda com texto mais escuro para melhor legibilidade
legenda_html = """
<div style="position: fixed; 
     bottom: 50px; right: 50px; width: 200px; height: auto; 
     background-color: white; border:2px solid grey; z-index:9999; 
     font-size:14px; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
     <p style="margin-top: 0; margin-bottom: 5px; font-weight: bold; color: #333333;">Taxa Média de Óbitos<br/>(por 100 mil hab.)</p>
"""

for i in range(len(valores_legenda) - 1):
    legenda_html += f"""
     <div style="display: flex; align-items: center; margin-bottom: 3px;">
         <div style="width: 30px; height: 20px; background-color: {cores_legenda[i]}; border: 1px solid black; margin-right: 5px;"></div>
         <span style="color: #333333;">{valores_legenda[i]:.2f} - {valores_legenda[i + 1]:.2f}</span>
     </div>
"""

legenda_html += (
    """
     <div style="display: flex; align-items: center;">
         <div style="width: 30px; height: 20px; background-color: """
    + cores_legenda[-1]
    + """; border: 1px solid black; margin-right: 5px;"></div>
         <span style="color: #333333;">"""
    + f"{valores_legenda[-1]:.2f}+"
    + """</span>
     </div>
</div>
"""
)

m.get_root().html.add_child(folium.Element(legenda_html))

# Preparar dados para o mapa de superintendências
# Agrupar geometrias dos municípios por superintendência
dados_superintendencias = sysdata[
    (sysdata["ano"] == 2024) & (sysdata["Superintendência"].notna())
].copy()

# Calcular taxa média por superintendência (já existe taxa_media_sup)
taxa_media_por_superintendencia = (
    sysdata[sysdata["ano"].isin([2022, 2023, 2024])]
    .groupby("Superintendência")["taxa_obitos"]
    .mean()
    .reset_index()
    .rename(columns={"taxa_obitos": "taxa_media"})
)

# Dissolver polígonos por superintendência
superintendencias_gdf = (
    dados_superintendencias[["Superintendência", "geometry"]]
    .dissolve(by="Superintendência")
    .reset_index()
)

# Merge com taxa média
superintendencias_gdf = superintendencias_gdf.merge(
    taxa_media_por_superintendencia, on="Superintendência", how="left"
)
superintendencias_gdf["taxa_media_formatada"] = superintendencias_gdf[
    "taxa_media"
].round(2)

# Calcular min e max da taxa média para o colormap de superintendências
min_taxa_sup = superintendencias_gdf["taxa_media"].min()
max_taxa_sup = superintendencias_gdf["taxa_media"].max()

# Criar colormap usando Blues do colorbrewer para superintendências
colormap_sup = cm.LinearColormap(
    colors=["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
    vmin=min_taxa_sup,
    vmax=max_taxa_sup,
    caption="Taxa Média de Óbitos (por 100 mil hab.)",
)


# Criar função para definir cor baseada na taxa média usando o colormap
def get_color_sup(taxa_valor):
    """Retorna cor em formato hex baseada na taxa média usando escala Blues"""
    return colormap_sup.rgb_hex_str(taxa_valor)


# Criar coluna de cor para o folium
superintendencias_gdf["color"] = superintendencias_gdf["taxa_media"].apply(
    get_color_sup
)

# Criar mapa folium para superintendências (centro em São Paulo)
m_sup = folium.Map(
    location=[-23.5505, -46.6333],
    zoom_start=7,
    tiles="CartoDB positron",  # Tema claro
)

# Adicionar plugin de fullscreen
Fullscreen().add_to(m_sup)

# Adicionar GeoJSON ao mapa
folium.GeoJson(
    superintendencias_gdf.to_json(),
    style_function=lambda feature: {
        "fillColor": feature["properties"]["color"],
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["Superintendência", "taxa_media_formatada"],
        aliases=["Superintendência:", "Taxa Média:"],
        style=("background-color: steelblue; color: white; padding: 10px;"),
    ),
).add_to(m_sup)

# Criar legenda para superintendências
valores_legenda_sup = [
    min_taxa_sup,
    min_taxa_sup + (max_taxa_sup - min_taxa_sup) * 0.25,
    min_taxa_sup + (max_taxa_sup - min_taxa_sup) * 0.5,
    min_taxa_sup + (max_taxa_sup - min_taxa_sup) * 0.75,
    max_taxa_sup,
]

cores_legenda_sup = [get_color_sup(v) for v in valores_legenda_sup]

# Criar HTML da legenda com texto mais escuro para melhor legibilidade
legenda_html_sup = """
<div style="position: fixed; 
     bottom: 50px; right: 50px; width: 200px; height: auto; 
     background-color: white; border:2px solid grey; z-index:9999; 
     font-size:14px; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
     <p style="margin-top: 0; margin-bottom: 5px; font-weight: bold; color: #333333;">Taxa Média de Óbitos<br/>(por 100 mil hab.)</p>
"""

for i in range(len(valores_legenda_sup) - 1):
    legenda_html_sup += f"""
     <div style="display: flex; align-items: center; margin-bottom: 3px;">
         <div style="width: 30px; height: 20px; background-color: {cores_legenda_sup[i]}; border: 1px solid black; margin-right: 5px;"></div>
         <span style="color: #333333;">{valores_legenda_sup[i]:.2f} - {valores_legenda_sup[i + 1]:.2f}</span>
     </div>
"""

legenda_html_sup += (
    """
     <div style="display: flex; align-items: center;">
         <div style="width: 30px; height: 20px; background-color: """
    + cores_legenda_sup[-1]
    + """; border: 1px solid black; margin-right: 5px;"></div>
         <span style="color: #333333;">"""
    + f"{valores_legenda_sup[-1]:.2f}+"
    + """</span>
     </div>
</div>
"""
)

m_sup.get_root().html.add_child(folium.Element(legenda_html_sup))

# Primeira linha: Tabela e Mapa de Municípios
col1, col2 = st.columns(2)

with col1:
    st.subheader("Tabela de Municípios")
    st.dataframe(
        tabela_municipios_display,
        width="stretch",
        hide_index=True,
    )

with col2:
    st.subheader("Municípios")
    # Mapa folium
    st_folium(m, width="stretch")

# Segunda linha: Tabela de Superintendências
col3, col4 = st.columns(2)

with col3:
    st.subheader("Tabela de Superintendências")
    st.dataframe(
        tabela_superintendencias_display,
        width="stretch",
        hide_index=True,
    )

with col4:
    st.subheader("Superintendências")
    # Mapa folium de superintendências
    st_folium(m_sup, width="stretch")
