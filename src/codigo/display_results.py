import polars as pl, polars.selectors as cs
from polars import col as c
import pandas as pd
import pypandoc
import pyfixest as pf
from pathlib import Path
import openpyxl
import re
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif

table_args = {
    'type':'gt',
    'keep':'p|p_bajo|p_alto',
    'fe_present':'YES', 
    'fe_absent':'NO', 
    'thousands_sep':True,
    # 'signif_code': [0.01, 0.05,0.1]
    }

def create_xl_wb(path:Path):
    if not path.exists():
        book = openpyxl.Workbook()
        book.save(path)
        book.close()
        
def cross_tab(df:pd.DataFrame, cols:list, args=None):
    col1, col2 = cols
    args = args or {}
    return (
        pd.crosstab(df[col1], df[col2], **args) # margins=True
        .rename(var_labels[col1], axis=0)
        .rename(var_labels[col2], axis=1)
        .reset_index()
    )

def fmt_low_people_cells(df:pd.DataFrame, treshold:int=20):
    cols_format = df.select_dtypes(include=['number']).columns
    return (
        df.style
        .highlight_between(subset=cols_format, left=0, right=treshold)
    )

def great_table_to_word(table:pf.etable, output_path:Path):
    temp_file = Path(__file__).parent.joinpath('temp.html')
    temp_file.touch()
    output_path
    with temp_file.open('wt') as f:
        f.write(table.as_raw_html())
    pypandoc.convert_file(source_file=temp_file, to='docx', outputfile=output_path.as_posix())
    temp_file.unlink()
    
def clean_exogenas(str):
    match = re.match(r'^C\((.*)\)$', str)
    return match.group(1) if match else str

def compute_vif(df:pd.DataFrame|pl.DataFrame, vars:list[str], cat:list[str]=None):
    df = df.to_pandas() if isinstance(df, pl.DataFrame) else df
    df = df[vars]
    df = df[df.notnull().all(axis=1)]
    if cat:
        cat = [cat] if isinstance(cat, str) else cat
        df = pd.get_dummies(df, columns=cat, drop_first=True, dtype=int)
    vif_data = pd.DataFrame()
    vif_data['variable'] = df.columns.to_list()
    vif_data['VIF'] = [vif(df.values, i) for i in range(len(df.columns))]
    return vif_data

def write_df_txt(df:pd.DataFrame, df_name:str):
    return f'\n\n{df_name}\n{df.to_string(index=False)}'

def generate_observations_tables(dfs:list[pl.DataFrame], paths:list[Path], variable:str='region'):
    for _df, path in zip(dfs, paths):
        create_xl_wb(path)
        cross_tab(_df.to_pandas(), cols=f'habilidad {variable}'.split(), args={'dropna':False}).to_excel(path, sheet_name='all_years', index=False)
        
        with pd.ExcelWriter(path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            row=1
            for year, gp in _df.sort('anno').group_by('anno', maintain_order=True):
                year=year[0]
                gp = gp.to_pandas().reset_index()
                gp = cross_tab(gp, ['habilidad', f'{variable}'], args={'dropna':False})
                fmt_low_people_cells(gp).to_excel(writer, sheet_name='years', startrow=row, index=False)
                writer.book['years'].cell(row, column=1, value=year)
                row += gp.shape[0] + 3
                
def wrap_word(col):
    return pl.lit('('), c(col), pl.lit(')')