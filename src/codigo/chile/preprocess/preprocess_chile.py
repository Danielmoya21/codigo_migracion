import pyreadstat
import polars as pl
from polars import col as c
import polars.selectors as cs
from pathlib import Path
import ucr_tools.core.data_analysis as da
import numpy as np
import os
from itertools import combinations
os.chdir(Path(__file__).parent)

years = [2015,2017,2020,2022]

for year in years:
    globals()[f'df_{year}'], meta= pyreadstat.read_sav(f'casen_{year}.sav', output_format='polars')
    globals()[f'df_{year}'] = globals()[f'df_{year}'].rename(str.casefold)
    globals()[f'var_labels_{year}'] = {k.casefold():v for k,v in meta.variable_value_labels.items()}
    globals()[f'col_labels_{year}'] = {k.casefold():v for k,v in meta.column_names_to_labels.items()}
    
# --------------------------------
# HORAS DE TRABAJO
# --------------------------------
# 2020 no traia la variable horas de trabajo por semana solo por mes
df_2020 = (
    df_2020
    .with_columns(
        c.y2_hrs.truediv(4).alias('o10')
    )
)

# --------------------------------
# NACIONALIDAD
# --------------------------------
# Cada año trae variables diferentes para el codigo del pais
year_country_var = {
    2015:'r1bespp_cod',  #513 Venezuela - 504 Chile
    2017: 'r1b_p_cod', #513 Venezuela - 504 Chile
    2020: 'r1b_p_cod', #513 Venezuela - Chile no sale
    2022: 'r1b_pais_esp_cod' #513 Venezuela - 504 Chile
}
cols = ['r1bespp_cod', 'r1b_p_cod', 'r1b_p_cod', 'r1b_pais_esp_cod']
nacionalidad_lbls = {0:'venezolano', 1:'chileno', 2:'otro'}

for year in years:
    globals()[f'var_labels_{year}']['nacionalidad'] = nacionalidad_lbls
#Aqui se añade la nacionalidad
df_2015, df_2017, df_2020, df_2022 = [
    df.with_columns(
        pl.when(c.r1b.is_in([1,2]))
        .then(1)
        .when(c(col).eq(513))
        .then(0)
        .otherwise(2)
        .alias('nacionalidad')
    )
    for df, col in zip([df_2015, df_2017, df_2020, df_2022], cols)
]

# --------------------------------
# Rename Country Codes and labels
# --------------------------------
for i in years:
    globals()[f'df_{i}'] = globals()[f'df_{i}'].rename({year_country_var.get(i):'country_code'}) 
    
for i in years:
    globals()[f'var_labels_{i}']['country_code'] = globals()[f'var_labels_{i}'][year_country_var.get(i)]

# --------------------------------
# ASALARIADOS
# --------------------------------
# 1, 2 y 9 de la variable o15 se consideran no asalariados - venia definida solo para 2022
df_2015, df_2017, df_2020, df_2022 = [
    df.with_columns(
        pl.when(c.o15.is_in([1,2,9]))
        .then(0)
        .when(c.o15.is_in(np.arange(3,9)))
        .then(1)
        .otherwise(None)
        .alias('asal')
    )
    for df in [df_2015, df_2017, df_2020, df_2022]
]

for year in years:
    globals()[f'var_labels_{year}']['asal'] = {0:'no asalariado', 1:'asalariado'}

# --------------------------------  
# RENOMBRAR VARIABLES ENTRE BASES
# --------------------------------
df_2015, df_2017 =  [
    df.rename({'oficio1': 'oficio1_08'})
    for df in [df_2015, df_2017]
]

df_2022 = df_2022.rename({'area':'zona'})


# --------------------------------  
# VERIFICAR COLUMNAS
# --------------------------------
cols = 'esc edad o10 sexo educ oficio1_08 folio region ytrabajocor expr activ ecivil o15 asal rama1 expr nacionalidad'.split()
for year in years:
    print(year)
    print([i for i in cols if i not in globals()[f'df_{year}']])
    print('-'*10)


for year in years:
    pyreadstat.write_sav(globals()[f'df_{year}'], f'casen_cleaned_{year}.sav', column_labels=globals()[f'col_labels_{year}'], variable_value_labels=globals()[f'var_labels_{year}'])
    
print('all dfs were saved :)')