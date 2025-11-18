from shiny import App, render, ui
import pandas as pd
import geopandas as gpd
import folium
from folium import Choropleth
from folium.features import GeoJsonTooltip

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


app_ui = ui.page_sidebar(
    ui.sidebar(open="closed"),
    ui.layout_columns(
        ui.card(
            ui.card_header("Tabela de Municípios"),
            ui.output_data_frame("tabela_municipios"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Municípios"),
            ui.div(
                ui.output_ui("mapa_municipios"),
                style="height: 600px; width: 100%; overflow: hidden;",
            ),
            full_screen=True,
        ),
        col_widths=[6, 6],
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Tabela de Superintendências"),
            ui.output_data_frame("tabela_superintendencias"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Superintendências"),
            full_screen=True,
        ),
        col_widths=[6, 6],
    ),
    title="Programa 'Piloto Consciente SP' - Diagnóstico",
)


def server(input, output, session):
    @render.data_frame
    def tabela_municipios():
        return render.DataGrid(
            tabela_municipios_display,
            width="100%",
            filters=True,
        )

    @render.data_frame
    def tabela_superintendencias():
        return render.DataGrid(
            tabela_superintendencias_display,
            width="100%",
            filters=True,
        )

    @render.ui
    def mapa_municipios():
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

        html_map = m._repr_html_()

        html_map = html_map.replace(
            '<div class="folium-map"',
            '<div class="folium-map" style="width: 100%; height: 300px; position: relative;"',
        )

        html_map = html_map.replace(
            'width="100%"',
            'width="100%" style="width: 100%; height: 300px; border: none;"',
        )

        html_map = html_map.replace(
            "<style>",
            "<style>\n.leaflet-bottom.leaflet-right { position: absolute; bottom: 0; right: 0; }\n.leaflet-control { margin-right: 10px; margin-bottom: 10px; }\n.info.legend { bottom: 30px; right: 10px; }\n",
        )

        return ui.HTML(html_map)


app = App(app_ui, server)
