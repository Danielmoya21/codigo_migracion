import pyreadstat
import polars as pl
from polars import col as c
import polars.selectors as cs
from pathlib import Path
from functools import reduce
from definitions import bases

country = 'chile'
bases = bases.joinpath(country)
encoding='utf-8'

# Costa Rica
if country=='cr':
    years = [2015,2016,2017,2018,2019,2022,2023]
    survey='ENAHO'
    ext='.sav'
#Chile
elif country=='chile':
    years = [2015,2017,2020,2022]
    survey = 'casen_cleaned'
    ext='.sav'
    
output = bases.joinpath(f'limpio/{country}_all').with_suffix(ext)

dfs = []
for year in years:
    df, meta = pyreadstat.read_sav(bases.joinpath(f'{survey}_{year}').with_suffix(ext), output_format='polars')
    print(f'{year} db loaded\n')
    df:pl.DataFrame
    df = df.with_columns(anno=year)
    dfs.append(df.rename(str.casefold))

common_cols = list(
    reduce(
        set.intersection,
        (set(df.columns) for df in dfs)
    )
)

final_df = pl.concat([df.select(common_cols) for df in dfs], how='diagonal_relaxed')

meta.column_names_to_labels = {k.casefold():v for k, v in meta.column_names_to_labels.items()}
meta.variable_value_labels = {k.casefold():v for k, v in meta.variable_value_labels.items()}

pyreadstat.write_sav(final_df, output, column_labels=meta.column_names_to_labels, variable_value_labels=meta.variable_value_labels)
print(f'saved all dbs in {output}')