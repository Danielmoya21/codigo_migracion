import polars as pl
from polars import col as c

# ------------------------------------------------------------------------------
# EXPERIENCIA
# ------------------------------------------------------------------------------
def add_experience(df, edad:str, escolari:str):
    return (
        df
        .with_columns(
            c(edad).add(-c(escolari)).add(-6)
            .alias('exp')
            )
        .filter(
            c.exp.ge(0)
            )
        .with_columns(
            pl.when(c.exp.gt(15))
            .then(1)
            .otherwise(0)
            .alias('exp_cat')
            )
    )

# ------------------------------------------------------------------------------
# LOGRO ACADÉMICO
# ------------------------------------------------------------------------------
logro_lbls = {
    1: "Primaria Incompleta",
    2: "Primaria Completa",
    3: "Secundaria Incompleta",
    4: "Secundaria Completa",
    5: "Educacion Terciaria"
}

def add_logro(df: pl.DataFrame, col, recode_dict:dict) -> pl.DataFrame:
    return (
        df
        .with_columns(
        c(col)
        .replace(recode_dict)
        .alias('logro')
        )
    )

# ------------------------------------------------------------------------------
# HABILIDAD
# ------------------------------------------------------------------------------
habilidad_lbls = {
    1: "P Inc -15", 
    2: "P Inc +15",
    3: "P Comp -15",
    4: "P Comp +15",
    5: "S Inc -15",
    6: "S Inc+15",
    7: "S Comp -15",
    8: "S Comp +15",
    9: "Ter -15",
    10: "Ter +15",
}
def add_habilidad(df:pl.DataFrame):
    return (
        df
        .sort(by=['logro', 'exp_cat'])
        .with_row_index()
        .with_columns(
            pl.first('index')
            .over("logro", "exp_cat")
            .rank("dense")
            .alias('habilidad')
        ).drop('index')
    )

# ------------------------------------------------------------------------------
# REAL WAGES
# ------------------------------------------------------------------------------
def add_real_wages(df: pl.DataFrame, col:str, ipc_values:dict) -> pl.DataFrame:
    return (
        df
        .with_columns(
            c.anno.replace_strict(ipc_values, default=None).truediv(100).alias("ipc")
        )
        .with_columns(
            c(col).truediv(c.ipc).alias("w_real")
        )
        .with_columns(
            c.w_real.log().alias("w_real_log")
        )
    )

# ------------------------------------------------------------------------------
# PEOPLE COUNTS
# ------------------------------------------------------------------------------
def weighting(weight):
    weight = c.weight if weight else 1
    return weight

def same_skill(df:pl.DataFrame, factor:str, nac:int, alias:str, groups:list, weight:bool=False):
    weight = weighting(weight)
    return (
        df
        .with_columns(
            c(factor).filter(c.nacionalidad.eq(nac))   # 1 Costarricenses
            .sum().over(groups)
            .mul(weight)
            .alias(alias)
            )
        )
    
# Higher Skill cell
def other_skills(df:pl.DataFrame, factor:str, nac:int, alias:str, groups:list, weight:bool=False, reverse:bool=False):
    groups_cum_sum = groups.copy()
    groups_cum_sum.remove('habilidad')
    
    weight = weighting(weight)
    
    grid = df.select(c(groups)).unique().sort(groups)
    totales = (
        df
        .filter(c.nacionalidad.eq(nac))
        .group_by(groups)
        .agg(c(factor).sum().alias('N'))
        .sort(groups)
    )
    
    totales = grid.join(totales, on=groups, how="left").with_columns(c.N.fill_null(0))
    
    if reverse:
        totales = totales.reverse()
        
    totales=(
        totales
        .with_columns(
            c.N
            .cum_sum()
            .over(groups_cum_sum)
            .add(-c.N)
            .alias(alias)
        )
    )
    return df.join(totales.drop('N'), on=groups, how='left').with_columns(c(alias).mul(weight))

# ------------------------------------------------------------------------------
# RECODE REGION CHILE
# ------------------------------------------------------------------------------
recode_region = {
    **{k: 1 for k in range(1, 4)},
    **{k: 2 for k in range(4, 7)},
    **{k: 3 for k in range(7, 10)},
    10:4,
    **{k: 5 for k in range(11, 13)},
    13:2,
    14:4,
    15:1,
    16:3
}
region_lbls_chile = {1: 'Norte', 2: 'Centro Norte', 3: 'Centro Sur', 4: 'Sur', 5: 'Austral'}