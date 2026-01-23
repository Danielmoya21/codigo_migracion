import polars as pl, polars.selectors as cs
from polars import col as c
import pyreadstat
from pathlib import Path


folder_path = r'C:\Users\dmoya\Downloads\ece'
years = [2015,2016,2017,2018,2019,2022,2023]
survey='III Trimestre'
country = 'cr'

#Chile

output = f'bases/ece_{country}_final.dta'

dfs = []
for year in years:
    df, meta = pyreadstat.read_sav(Path(folder_path).joinpath(f'{survey} {year}.sav'), output_format='polars', encoding='utf-8')
    df:pl.DataFrame
    df = df.with_columns(anno=year)
    dfs.append(df.rename(str.casefold))

final_df = pl.concat(dfs, how='diagonal_relaxed')

meta.column_names_to_labels = {k.casefold():v for k, v in meta.column_names_to_labels.items()}
meta.variable_value_labels = {k.casefold():v for k, v in meta.variable_value_labels.items()}

pyreadstat.write_dta(final_df, output, column_labels=meta.column_names_to_labels, variable_value_labels=meta.variable_value_labels)

