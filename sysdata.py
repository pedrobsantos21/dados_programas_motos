import pandas as pd
import os
from rich.console import Console
from geobr import read_municipality

console = Console()

path_pessoas = "data/infosiga/pessoas_2022-2025.csv"
path_populacao = "data/estimativa_pop_idade_sexo_esp.csv"
path_cetran = "data/base_cetran.csv"
path_sysdata = "data/sysdata.gpkg"

console.print(f"Carregando dados de pessoas de {path_pessoas}")
pessoas_df = pd.read_csv(path_pessoas, encoding="latin-1", sep=";")

pessoas_fatais_moto = pessoas_df[
    (pessoas_df["gravidade_lesao"] == "FATAL")
    & (pessoas_df["tipo_veiculo_vitima"] == "MOTOCICLETA")
    & (pessoas_df["ano_obito"].isin([2022, 2023, 2024]))
]

console.print("Calculando óbitos por ano e município")

obitos_por_ano_municipio = (
    pessoas_fatais_moto.groupby(["ano_obito", "cod_ibge"])
    .size()
    .reset_index(name="quantidade_obitos")
    .reset_index(drop=True)
)

populacao_df = pd.read_csv(
    path_populacao,
    encoding="latin-1",
    sep=";",
)

console.print("Calculando população por ano e município")

populacao_2022_2024_por_municipio = (
    populacao_df[populacao_df["ano"].isin([2022, 2023, 2024])]
    .groupby(["ano", "cod_ibge"])["populacao"]
    .sum()
    .reset_index(name="populacao_total")
    .reset_index(drop=True)
)

cetran_df = pd.read_csv(
    path_cetran,
    encoding="utf-8",
    sep=";",
)

cetran_superintendencia_ibge = cetran_df[["Superintendência", "CD_MUN"]].reset_index(
    drop=True
)

console.print("Juntando dados")

dados_completos = (
    populacao_2022_2024_por_municipio.merge(
        obitos_por_ano_municipio,
        left_on=["ano", "cod_ibge"],
        right_on=["ano_obito", "cod_ibge"],
        how="left",
    )
    .merge(
        cetran_superintendencia_ibge,
        left_on="cod_ibge",
        right_on="CD_MUN",
        how="left",
    )
    .drop(columns=["ano_obito", "CD_MUN"])
    .fillna({"quantidade_obitos": 0})
    .reset_index(drop=True)
)

console.print("Carregando os dados espaciais de São Paulo")

sp_gdf = read_municipality(code_muni=35, year=2022)

console.print("Criando os dados finais")

dados_completos_geo = sp_gdf.merge(
    dados_completos,
    left_on="code_muni",
    right_on="cod_ibge",
    how="right",
)

dados_completos_geo.to_file(path_sysdata, driver="GPKG")

console.print(f"Dados salvos em {path_sysdata}")
