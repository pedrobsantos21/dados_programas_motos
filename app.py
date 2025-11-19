import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
import unicodedata
import os

# ============================================================================
# CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ============================================================================


def _normalize_value(value: str) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.lower().strip()


def normalize_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).apply(_normalize_value)


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
sysdata["superintendencia_norm"] = normalize_series(sysdata["Superintendência"])

# Tentar diferentes nomes possíveis para o arquivo de superintendências
path_superintendencias_geo = None
possible_paths = [
    "data/superintendencias_detran.gpkg",
    "data/Superintendencias_DETRAN.gpkg",
    "data/Superintendencias_detran.gpkg",
]

for path in possible_paths:
    if os.path.exists(path):
        path_superintendencias_geo = path
        break

if path_superintendencias_geo is None:
    raise FileNotFoundError(
        f"Arquivo de superintendências não encontrado. Procurou em: {possible_paths}"
    )

geo_superintendencias = gpd.read_file(path_superintendencias_geo)
geo_superintendencias["superintendencia_norm"] = normalize_series(
    geo_superintendencias["superinten"]
)

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
def calcular_populacao_2024(_data, group_by):
    """Calcula população de 2024 agrupada por uma coluna."""
    # Para municípios, usar first() pois cada município tem uma única população
    # Para superintendências, usar sum() para somar populações de todos os municípios
    if group_by == "cod_ibge":
        populacao = (
            _data[_data["ano"] == 2024]
            .groupby(group_by)["populacao_total"]
            .first()
            .reset_index()
            .rename(columns={"populacao_total": "populacao_2024"})
        )
    else:
        # Para superintendências, somar populações de todos os municípios
        populacao = (
            _data[_data["ano"] == 2024]
            .groupby(group_by)["populacao_total"]
            .sum()
            .reset_index()
            .rename(columns={"populacao_total": "populacao_2024"})
        )
    return populacao


@st.cache_data
def preparar_tabela_display(tabela, tipo="municipios"):
    """Prepara tabela para exibição formatando colunas."""
    tabela_display = tabela.copy()

    if tipo == "municipios":
        colunas_display = [
            "cod_ibge",
            "name_muni",
            "Superintendência",
            "obitos_total",
            "populacao_2024",
            "taxa_media",
            "delta_obitos_pct",
        ]
        tabela_display = tabela_display[colunas_display]
        # Formatação antes de renomear
        tabela_display["cod_ibge"] = tabela_display["cod_ibge"].astype(str)
        tabela_display["obitos_total"] = tabela_display["obitos_total"].astype(int)
        tabela_display["populacao_2024"] = tabela_display["populacao_2024"].astype(int)
        tabela_display["taxa_media"] = tabela_display["taxa_media"].round(2)
        tabela_display["delta_obitos_pct"] = tabela_display["delta_obitos_pct"].round(2)
        # Renomear colunas
        tabela_display.columns = [
            "Código IBGE",
            "Município",
            "Superintendência",
            "Óbitos Total (2022-2024)",
            "População 2024",
            "Taxa Média de Óbitos",
            "Variação óbitos (%)",
        ]
    else:  # superintendencias
        colunas_display = [
            "Superintendência",
            "obitos_total",
            "populacao_2024",
            "taxa_media",
            "delta_obitos_pct",
        ]
        tabela_display = tabela_display[colunas_display]
        # Formatação antes de renomear
        tabela_display["obitos_total"] = tabela_display["obitos_total"].astype(int)
        tabela_display["populacao_2024"] = tabela_display["populacao_2024"].astype(int)
        tabela_display["taxa_media"] = tabela_display["taxa_media"].round(2)
        tabela_display["delta_obitos_pct"] = tabela_display["delta_obitos_pct"].round(2)
        # Renomear colunas
        tabela_display.columns = [
            "Superintendência",
            "Óbitos Total (2022-2024)",
            "População 2024",
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
    # Garantir que não há NaN e calcular min/max
    gdf["taxa_media"] = gdf["taxa_media"].fillna(0)
    min_val = gdf["taxa_media"].min()
    max_val = gdf["taxa_media"].max()

    # Garantir que min < max (caso todos os valores sejam iguais)
    if min_val >= max_val:
        max_val = min_val + 1 if min_val == max_val else min_val + 0.01

    # Criar função de cor
    def get_color(taxa_valor):
        # Garantir que o valor está dentro dos limites do colormap
        taxa_valor = max(min_val, min(max_val, taxa_valor))
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
    populacao_2024_municipios = calcular_populacao_2024(_data, "cod_ibge")

    todos_municipios = _data["cod_ibge"].unique()
    tabela_base_municipios = pd.DataFrame({"cod_ibge": todos_municipios})

    tabela_municipios = (
        tabela_base_municipios.merge(obitos_municipios[2022], on="cod_ibge", how="left")
        .merge(obitos_municipios[2023], on="cod_ibge", how="left")
        .merge(obitos_municipios[2024], on="cod_ibge", how="left")
        .merge(taxa_media_municipios, on="cod_ibge", how="left")
        .merge(populacao_2024_municipios, on="cod_ibge", how="left")
        .fillna(0)
    )

    # Calcular total de óbitos (soma dos três anos)
    tabela_municipios["obitos_total"] = (
        tabela_municipios["obitos_2022"]
        + tabela_municipios["obitos_2023"]
        + tabela_municipios["obitos_2024"]
    )

    # Calcular variação de óbitos (%)
    tabela_municipios["delta_obitos_pct"] = (
        (
            (tabela_municipios["obitos_2024"] - tabela_municipios["obitos_2022"])
            / tabela_municipios["obitos_2022"].replace(0, 1)
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
    populacao_2024_superintendencias = calcular_populacao_2024(
        _data, "Superintendência"
    )

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
        .merge(populacao_2024_superintendencias, on="Superintendência", how="left")
        .fillna(0)
    )

    # Calcular total de óbitos (soma dos três anos)
    tabela_superintendencias["obitos_total"] = (
        tabela_superintendencias["obitos_2022"]
        + tabela_superintendencias["obitos_2023"]
        + tabela_superintendencias["obitos_2024"]
    )

    # Calcular variação de óbitos (%)
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
def preparar_dados_mapa_superintendencias(_data, _geo_superintendencias):
    """Prepara dados completos do mapa de superintendências usando shapes oficiais."""
    taxa_media = calcular_taxa_media(_data, "Superintendência").copy()
    taxa_media["superintendencia_norm"] = normalize_series(
        taxa_media["Superintendência"]
    )

    geo = _geo_superintendencias.copy()
    if "superintendencia_norm" not in geo.columns:
        geo["superintendencia_norm"] = normalize_series(geo["superinten"])

    # Mapeamento manual para corrigir diferenças de grafia e casos especiais
    # Formato: {nome_normalizado_no_geo: nome_normalizado_no_sysdata}
    mapeamento_manual = {
        "sao bernardo do campo": "sao bernado do campo",  # Corrige grafia "BERNADO" vs "BERNARDO"
        "botucatu": "piracicaba",  # Botucatu no geo corresponde a PIRACICABA no sysdata
    }

    # Mapeamento de nomes para exibição (quando o nome no geo difere do nome no sysdata)
    mapeamento_nomes = {
        "botucatu": "PIRACICABA",  # Exibir como PIRACICABA mesmo que o shape seja Botucatu
    }

    # Aplicar mapeamento manual no geo
    geo["superintendencia_norm_mapped"] = geo["superintendencia_norm"].map(
        lambda x: mapeamento_manual.get(x, x)
    )

    # Fazer merge usando o nome mapeado
    gdf = geo.merge(
        taxa_media[["superintendencia_norm", "Superintendência", "taxa_media"]],
        left_on="superintendencia_norm_mapped",
        right_on="superintendencia_norm",
        how="left",
    )

    # Preencher Superintendência: usar nome do sysdata quando disponível,
    # caso contrário usar mapeamento de nomes, senão usar nome original do geo
    # Criar série auxiliar para mapeamento
    for idx in gdf.index:
        if pd.isna(gdf.loc[idx, "Superintendência"]):
            geo_norm_val = geo.loc[idx, "superintendencia_norm"]
            if geo_norm_val in mapeamento_nomes:
                gdf.loc[idx, "Superintendência"] = mapeamento_nomes[geo_norm_val]
            else:
                gdf.loc[idx, "Superintendência"] = geo.loc[idx, "superinten"]
    gdf["taxa_media"] = gdf["taxa_media"].fillna(0)

    # Remover colunas auxiliares apenas se existirem
    colunas_para_remover = []
    if "superintendencia_norm" in gdf.columns:
        colunas_para_remover.append("superintendencia_norm")
    if "superintendencia_norm_mapped" in gdf.columns:
        colunas_para_remover.append("superintendencia_norm_mapped")
    if colunas_para_remover:
        gdf = gdf.drop(columns=colunas_para_remover)

    return gdf


# Preparar dados dos mapas
dados_municipios = preparar_dados_mapa_municipios(sysdata)
dados_superintendencias = preparar_dados_mapa_superintendencias(
    sysdata, geo_superintendencias
)

# Criar mapas (não cached pois folium.Map não é serializável)
# Garantir que não há NaN antes de calcular min/max
dados_municipios["taxa_media"] = dados_municipios["taxa_media"].fillna(0)
dados_superintendencias["taxa_media"] = dados_superintendencias["taxa_media"].fillna(0)

min_taxa_municipios = dados_municipios["taxa_media"].min()
max_taxa_municipios = dados_municipios["taxa_media"].max()
# Garantir que min < max
if min_taxa_municipios >= max_taxa_municipios:
    max_taxa_municipios = (
        min_taxa_municipios + 1
        if min_taxa_municipios == max_taxa_municipios
        else min_taxa_municipios + 0.01
    )
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
# Garantir que min < max
if min_taxa_superintendencias >= max_taxa_superintendencias:
    max_taxa_superintendencias = (
        min_taxa_superintendencias + 1
        if min_taxa_superintendencias == max_taxa_superintendencias
        else min_taxa_superintendencias + 0.01
    )
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

# Configuração da página seguindo padrões DETRAN-SP
st.set_page_config(
    page_title="Programa 'Piloto Consciente SP' - Diagnóstico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS seguindo padrões visuais do DETRAN-SP
st.markdown(
    """
    <style>
    /* Importar fonte Open Sans do Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    /* Aplicar fonte Open Sans globalmente */
    * {
        font-family: 'Open Sans', sans-serif !important;
    }
    
    /* Cor de fundo principal */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Container principal */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Títulos seguindo padrão DETRAN-SP */
    h1 {
        color: #111414;
        font-weight: 400;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    h2, h3 {
        color: #111414;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Texto padrão */
    p, div, span {
        color: #3A3F51;
    }
    
    /* DataFrames - estilo limpo */
    .stDataFrame {
        border: 1px solid #D3D8DB;
        border-radius: 4px;
    }
    
    /* Tabelas */
    .stDataFrame table {
        border-collapse: collapse;
    }
    
    .stDataFrame th {
        background-color: #F5F5F5;
        color: #111414;
        font-weight: 600;
        border-bottom: 2px solid #D3D8DB;
    }
    
    .stDataFrame td {
        border-bottom: 1px solid #D3D8DB;
    }
    
    /* Botões */
    .stButton > button {
        background-color: #111414;
        color: #FFFFFF;
        border-radius: 4px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2A2D2D;
    }
    
    /* Links */
    a {
        color: #111414;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F5F5F5;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #D3D8DB;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #B8BEC2;
    }
    
    /* Espaçamento entre seções */
    .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* Cabeçalho com logo */
    .header-container {
        display: flex;
        align-items: center;
        padding: 1.5rem 0;
        border-bottom: 2px solid #D3D8DB;
        margin-bottom: 2rem;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        padding-right: 2rem;
    }
    
    .logo-container img {
        max-width: 180px;
        height: auto;
    }
    
    .title-container {
        flex: 1;
        display: flex;
        align-items: center;
    }
    
    .title-container h1 {
        margin: 0;
        padding: 0;
        font-size: 2rem;
        font-weight: 400;
        color: #111414;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Logo e cabeçalho DETRAN-SP
st.markdown(
    """
    <div class="header-container">
        <div class="logo-container">
            <img src="https://www.detran.sp.gov.br/702a783633529610cd8381ac4f5c7b5b.iix" 
                 alt="DETRAN-SP Logo">
        </div>
        <div class="title-container">
            <h1>Programa 'Piloto Consciente SP' - Diagnóstico</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Sobre")
st.markdown(
    """
    - Quantidade de óbitos envolvendo ocupantes de motocicleta: Infosiga, out-2025
    - Estimativa de população por município: SEADE, out-2025
    - Taxa média de óbitos envolvendo ocupantes de motocicleta por 100.000 habitantes calculada com base na média dos anos de 2022, 2023 e 2024
    - Variação de óbitos envolvendo ocupantes de motocicleta calculada considerando os anos de 2022 e 2024

    v0.1 - 2025-11-19
    """
)

# Tabela de Municípios
st.subheader("Tabela de Municípios")
st.dataframe(
    tabela_municipios_display,
    width="stretch",
    hide_index=True,
)

# Mapa de Municípios
st.subheader("Mapa de Municípios")
st_folium(m_municipios, width="stretch")

# Tabela de Superintendências
st.subheader("Tabela de Superintendências")
st.dataframe(
    tabela_superintendencias_display,
    width="stretch",
    hide_index=True,
)

# Mapa de Superintendências
st.subheader("Mapa de Superintendências")
st_folium(m_superintendencias, width="stretch")
