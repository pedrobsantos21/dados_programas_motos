import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

# ============================================================================
# CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ============================================================================


@st.cache_data
def carregar_dados():
    """Carrega e prepara os dados do GeoPackage."""
    path_sysdata = "data/sysdata.gpkg"
    sysdata = gpd.read_file(path_sysdata)
    sysdata["taxa_obitos"] = (
        (sysdata["quantidade_obitos"] / sysdata["populacao_total"]) * 100000
    ).fillna(0)
    return sysdata


sysdata = carregar_dados()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================


@st.cache_data
def calcular_obitos_por_ano(_data, group_by, anos=[2022, 2023, 2024]):
    """Calcula óbitos por ano agrupados por uma coluna."""
    obitos_por_ano = {}
    for ano in anos:
        obitos = (
            _data[_data["ano"] == ano]
            .groupby(group_by)["quantidade_obitos"]
            .sum()
            .reset_index()
            .rename(columns={"quantidade_obitos": f"obitos_{ano}"})
        )
        obitos_por_ano[ano] = obitos
    return obitos_por_ano


@st.cache_data
def calcular_taxa_media(_data, group_by, anos=[2022, 2023, 2024]):
    """Calcula taxa média de óbitos agrupada por uma coluna."""
    taxa_media = (
        _data[_data["ano"].isin(anos)]
        .groupby(group_by)["taxa_obitos"]
        .mean()
        .reset_index()
        .rename(columns={"taxa_obitos": "taxa_media"})
    )
    return taxa_media


@st.cache_data
def calcular_taxa_por_ano(_data, group_by, ano):
    """Calcula taxa de óbitos para um ano específico."""
    taxa = (
        _data[_data["ano"] == ano]
        .groupby(group_by)["taxa_obitos"]
        .mean()
        .reset_index()
        .rename(columns={"taxa_obitos": f"taxa_{ano}"})
    )
    return taxa


@st.cache_data
def preparar_tabela_display(tabela, tipo="municipios"):
    """Prepara tabela para exibição formatando colunas."""
    tabela_display = tabela.copy()

    if tipo == "municipios":
        colunas_display = [
            "cod_ibge",
            "name_muni",
            "Superintendência",
            "obitos_2022",
            "obitos_2023",
            "obitos_2024",
            "taxa_media",
            "delta_obitos_pct",
        ]
        tabela_display = tabela_display[colunas_display]
        # Formatação antes de renomear
        tabela_display["cod_ibge"] = tabela_display["cod_ibge"].astype(str)
        for ano in [2022, 2023, 2024]:
            tabela_display[f"obitos_{ano}"] = tabela_display[f"obitos_{ano}"].astype(
                int
            )
        tabela_display["taxa_media"] = tabela_display["taxa_media"].round(2)
        tabela_display["delta_obitos_pct"] = tabela_display["delta_obitos_pct"].round(2)
        # Renomear colunas
        tabela_display.columns = [
            "Código IBGE",
            "Município",
            "Superintendência",
            "Óbitos 2022",
            "Óbitos 2023",
            "Óbitos 2024",
            "Taxa Média de Óbitos",
            "Variação óbitos (%)",
        ]
    else:  # superintendencias
        colunas_display = [
            "Superintendência",
            "obitos_2022",
            "obitos_2023",
            "obitos_2024",
            "taxa_media",
            "delta_obitos_pct",
        ]
        tabela_display = tabela_display[colunas_display]
        # Formatação antes de renomear
        for ano in [2022, 2023, 2024]:
            tabela_display[f"obitos_{ano}"] = tabela_display[f"obitos_{ano}"].astype(
                int
            )
        tabela_display["taxa_media"] = tabela_display["taxa_media"].round(2)
        tabela_display["delta_obitos_pct"] = tabela_display["delta_obitos_pct"].round(2)
        # Renomear colunas
        tabela_display.columns = [
            "Superintendência",
            "Óbitos 2022",
            "Óbitos 2023",
            "Óbitos 2024",
            "Taxa Média de Óbitos",
            "Variação óbitos (%)",
        ]

    return tabela_display


def criar_colormap(min_val, max_val):
    """Cria colormap usando escala Blues do colorbrewer."""
    return cm.LinearColormap(
        colors=["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
        vmin=min_val,
        vmax=max_val,
        caption="Taxa Média de Óbitos (por 100 mil hab.)",
    )


def criar_legenda(min_val, max_val, get_color_func):
    """Cria HTML da legenda para o mapa."""
    valores_legenda = [
        min_val,
        min_val + (max_val - min_val) * 0.25,
        min_val + (max_val - min_val) * 0.5,
        min_val + (max_val - min_val) * 0.75,
        max_val,
    ]

    cores_legenda = [get_color_func(v) for v in valores_legenda]

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

    return legenda_html


def criar_mapa(
    gdf,
    colormap,
    tooltip_fields,
    tooltip_aliases,
    location=[-23.5505, -46.6333],
    zoom_start=7,
    weight=1,
):
    """Cria mapa folium com GeoJSON, legenda e fullscreen."""
    min_val = gdf["taxa_media"].min()
    max_val = gdf["taxa_media"].max()

    # Criar função de cor
    def get_color(taxa_valor):
        return colormap.rgb_hex_str(taxa_valor)

    # Adicionar coluna de cor
    gdf["color"] = gdf["taxa_media"].apply(get_color)
    gdf["taxa_media_formatada"] = gdf["taxa_media"].round(2)

    # Criar mapa
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles="CartoDB positron",
    )

    # Adicionar fullscreen
    Fullscreen().add_to(m)

    # Adicionar GeoJSON
    folium.GeoJson(
        gdf.to_json(),
        style_function=lambda feature: {
            "fillColor": feature["properties"]["color"],
            "color": "black",
            "weight": weight,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            style=("background-color: steelblue; color: white; padding: 10px;"),
        ),
    ).add_to(m)

    # Adicionar legenda
    legenda_html = criar_legenda(min_val, max_val, get_color)
    m.get_root().html.add_child(folium.Element(legenda_html))

    return m


@st.cache_data
def preparar_dados_mapa(_data, ano, group_by, dissolve=False):
    """Prepara dados GeoDataFrame para o mapa."""
    dados = _data[(_data["ano"] == ano) & (_data[group_by].notna())].copy()

    # Calcular taxa média
    taxa_media = calcular_taxa_media(_data, group_by)

    if dissolve:
        # Dissolver polígonos
        gdf = dados[[group_by, "geometry"]].dissolve(by=group_by).reset_index()
    else:
        # Manter polígonos individuais (um por grupo)
        gdf = (
            dados[[group_by, "geometry"]]
            .drop_duplicates(subset=group_by)
            .reset_index(drop=True)
        )

    # Merge com taxa média
    gdf = gdf.merge(taxa_media, on=group_by, how="left")

    return gdf


# ============================================================================
# PREPARAÇÃO DAS TABELAS
# ============================================================================


@st.cache_data
def preparar_tabela_municipios(_data):
    """Prepara tabela completa de municípios."""
    obitos_municipios = calcular_obitos_por_ano(_data, "cod_ibge")
    taxa_media_municipios = calcular_taxa_media(_data, "cod_ibge")
    taxa_2022_municipios = calcular_taxa_por_ano(_data, "cod_ibge", 2022)
    taxa_2024_municipios = calcular_taxa_por_ano(_data, "cod_ibge", 2024)

    todos_municipios = _data["cod_ibge"].unique()
    tabela_base_municipios = pd.DataFrame({"cod_ibge": todos_municipios})

    tabela_municipios = (
        tabela_base_municipios.merge(obitos_municipios[2022], on="cod_ibge", how="left")
        .merge(obitos_municipios[2023], on="cod_ibge", how="left")
        .merge(obitos_municipios[2024], on="cod_ibge", how="left")
        .merge(taxa_2022_municipios, on="cod_ibge", how="left")
        .merge(taxa_2024_municipios, on="cod_ibge", how="left")
        .merge(taxa_media_municipios, on="cod_ibge", how="left")
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

    info_municipios = _data[
        ["cod_ibge", "name_muni", "Superintendência"]
    ].drop_duplicates(subset="cod_ibge")

    tabela_municipios = tabela_municipios.merge(
        info_municipios, on="cod_ibge", how="left"
    )
    tabela_municipios_display = preparar_tabela_display(
        tabela_municipios, tipo="municipios"
    )

    return tabela_municipios_display


@st.cache_data
def preparar_tabela_superintendencias(_data):
    """Prepara tabela completa de superintendências."""
    obitos_superintendencias = calcular_obitos_por_ano(_data, "Superintendência")
    taxa_media_superintendencias = calcular_taxa_media(_data, "Superintendência")

    todos_superintendencias = _data["Superintendência"].dropna().unique()
    tabela_base_superintendencias = pd.DataFrame(
        {"Superintendência": todos_superintendencias}
    )

    tabela_superintendencias = (
        tabela_base_superintendencias.merge(
            obitos_superintendencias[2022], on="Superintendência", how="left"
        )
        .merge(obitos_superintendencias[2023], on="Superintendência", how="left")
        .merge(obitos_superintendencias[2024], on="Superintendência", how="left")
        .merge(taxa_media_superintendencias, on="Superintendência", how="left")
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

    tabela_superintendencias_display = preparar_tabela_display(
        tabela_superintendencias, tipo="superintendencias"
    )

    return tabela_superintendencias_display


tabela_municipios_display = preparar_tabela_municipios(sysdata)
tabela_superintendencias_display = preparar_tabela_superintendencias(sysdata)

# ============================================================================
# PREPARAÇÃO DOS MAPAS
# ============================================================================


@st.cache_data
def preparar_dados_mapa_municipios(_data):
    """Prepara dados completos do mapa de municípios."""
    dados_municipios = preparar_dados_mapa(_data, 2024, "cod_ibge", dissolve=False)
    info_municipios = _data[
        ["cod_ibge", "name_muni", "Superintendência"]
    ].drop_duplicates(subset="cod_ibge")
    dados_municipios = dados_municipios.merge(
        info_municipios[["cod_ibge", "name_muni", "Superintendência"]],
        on="cod_ibge",
        how="left",
    )
    return dados_municipios


@st.cache_data
def preparar_dados_mapa_superintendencias(_data):
    """Prepara dados completos do mapa de superintendências."""
    dados_superintendencias = preparar_dados_mapa(
        _data, 2024, "Superintendência", dissolve=True
    )
    return dados_superintendencias


# Preparar dados dos mapas
dados_municipios = preparar_dados_mapa_municipios(sysdata)
dados_superintendencias = preparar_dados_mapa_superintendencias(sysdata)

# Criar mapas (não cached pois folium.Map não é serializável)
min_taxa_municipios = dados_municipios["taxa_media"].min()
max_taxa_municipios = dados_municipios["taxa_media"].max()
colormap_municipios = criar_colormap(min_taxa_municipios, max_taxa_municipios)

m_municipios = criar_mapa(
    dados_municipios,
    colormap_municipios,
    tooltip_fields=["name_muni", "Superintendência", "taxa_media_formatada"],
    tooltip_aliases=["Município:", "Superintendência:", "Taxa Média:"],
    weight=1,
)

min_taxa_superintendencias = dados_superintendencias["taxa_media"].min()
max_taxa_superintendencias = dados_superintendencias["taxa_media"].max()
colormap_superintendencias = criar_colormap(
    min_taxa_superintendencias, max_taxa_superintendencias
)

m_superintendencias = criar_mapa(
    dados_superintendencias,
    colormap_superintendencias,
    tooltip_fields=["Superintendência", "taxa_media_formatada"],
    tooltip_aliases=["Superintendência:", "Taxa Média:"],
    weight=2,
)

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

# Configuração da página com tema escuro
st.set_page_config(
    page_title="Programa 'Piloto Consciente SP' - Diagnóstico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS para tema escuro
# st.markdown(
#     """
#     <style>
#     .stApp {
#         background-color: #0e1117;
#     }
#     .main .block-container {
#         padding-top: 2rem;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# Título principal
st.title("Programa 'Piloto Consciente SP' - Diagnóstico")

# Tabela de Municípios
st.subheader("Tabela de Municípios")
st.dataframe(
    tabela_municipios_display,
    width="stretch",
    hide_index=True,
)

# Mapa de Municípios
st.subheader("Municípios")
st_folium(m_municipios, width="stretch")

# Tabela de Superintendências
st.subheader("Tabela de Superintendências")
st.dataframe(
    tabela_superintendencias_display,
    width="stretch",
    hide_index=True,
)

# Mapa de Superintendências
st.subheader("Superintendências")
st_folium(m_superintendencias, width="stretch")
