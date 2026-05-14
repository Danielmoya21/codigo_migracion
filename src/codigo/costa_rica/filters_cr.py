from polars import col as c
import polars as pl

exogenas = 'p + p_bajo + p_alto + C(a6)'
cols_exogenas = 'p p_bajo p_alto a6'.split()
categoricals = 'a6'

def filter_exogenas(min_skill=1):
    return (
        pl.all_horizontal(c(cols_exogenas).is_not_null())
        | c.habilidad.is_in([min_skill,10])
    )

def employment_filters(nac=1, sex=2):
    return (
    # c.nacionalidad.eq(nac),
    c.a4.eq(sex),
    c.exp.lt(40),
    c.hortotnorm.is_null() | c.hortotnorm.is_between(0,72, closed='left'),
    )

def wage_filters(nac=1, sex=2):
    return (
    c.posiemppri.is_in([11,12]), #Keep wage earners
    c.nacionalidad.eq(nac), #Keep natives
    c.a4.eq(sex), #keep men/women
    c.exp.lt(40),
    c.condact.eq(1),
    # c.hortotnorm.is_between(0,999,closed='none'),
    # c.w_real.gt(0)
    c.hortotnorm.is_between(0,72, closed='none'),
    c.w_real.is_between(0,40_000, closed='none'),
    )


