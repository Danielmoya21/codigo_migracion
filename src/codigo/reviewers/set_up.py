from polars import col as c
import polars as pl, polars.selectors as cs
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Vars:
    hourly_income:str
    work_hours:str
    path:Path


#Set up Costa Rica
cols_exogenas = 'p p_bajo p_alto a6'.split()
employment_filters = (
    c.nacionalidad.eq(1),
    c.a4.eq(2),
    # c.hortotnorm.is_null() | c.hortotnorm.lt(72),
    # c.exp.lt(40)
    )

wage_filters = (
    c.posiemppri.is_in([11,12]), #Keep wage earners
    c.nacionalidad.eq(1),
    c.a4.eq(2),
    c.exp.lt(40),
    c.condact.eq(1),
    # c.hortotnorm.lt(72),
    # c.w_real.is_between(0,40_000, closed='none'),
    )


#----------------------
#SET UP CHILE
#----------------------
cols_exogenas = 'p p_bajo p_alto ecivil'.split()
employment_filters = (
    c.nacionalidad.eq(1),   #Chilenos
    c.sexo.eq(2),   #Mujeres
    c.o10.is_null() | c.o10.is_between(0,72, closed='left'),   #eliminar horas atipicas
    c.exp.lt(40),
    )
wage_filters = (
    c.nacionalidad.eq(1),
    c.sexo.eq(2),
    c.o10.is_between(0,72, closed='none'),
    c.exp.lt(40),
    c.activ.eq(1),
    c.asal.eq(1), #Keep wage earners
    c.w_real.gt(0)
    )
