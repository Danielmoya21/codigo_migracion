import pyreadstat
import polars as pl
from polars import col as c
import polars.selectors as cs
import argparse
from codigo import transformations as trans
from definitions import bases, codigo, root

parser = argparse.ArgumentParser()
parser.add_argument('--var', type=str, default='region')
args = parser.parse_args()

grouping = input('Do you want to group skill cells? y/n\n>')

output_name = f'chile_{args.var}_processed' if grouping!='y' else f'chile_{args.var}_grouped_processed'
output = bases.joinpath(f'chile/limpio/{output_name}.sav')
cols = 'esc edad o10 sexo educ oficio1_08 folio region zona ytrabajocor expr activ ecivil o15 asal rama1 expr anno nacionalidad'.split()

load_file = bases.joinpath('chile/limpio/chile_all.sav')
df, meta = pyreadstat.read_sav(load_file, output_format='polars', usecols=cols)
print(f'{load_file.name} has been loaded')
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels

# -----------------------------------
# IDENTIFICADOR DE HOGAR
# -----------------------------------
df = (
    df.with_columns(
        c.folio.mul(1e4).add(c.anno)
    )
)

# -----------------------------------
# GENERAL FILTERS
# -----------------------------------
edad = c.edad.is_between(15,65, closed='both') #Mantener solo personas en edad de trabajar
nivel_de_instruccion = ~c.educ.is_in([-88, 99])

df = df.filter(nivel_de_instruccion, edad) #Filtros de sexo y nacionalidad se aplican al final

# -----------------------------------
# EXPERIENCIA
# -----------------------------------
df = trans.add_experience(df, 'edad', 'esc') #De momento no se usan los filtros, al final se filtra exp>0
print('experience created')

# -----------------------------------
# LOGRO
# -----------------------------------
recode = {
    0:1,
    4:3,
    5:4,
    6:4,
    7:5,
    8:5,
    9:5,
    10:5,
    11:5,
    12:5
    }
df = trans.add_logro(df, col='educ', recode_dict=recode)
print('logro created')

# -----------------------------------
# HABILIDAD
# -----------------------------------
df = trans.add_habilidad(df)
print('habilidad created')

if grouping=='y':
    group_dict = {1:2}
    df = df.with_columns(c.habilidad.replace(group_dict)) #!!! This is grouping is different in Costa Rica
    print(f'Following recode was done to habilidad: {group_dict}')

# -----------------------------------
# NACIONALIDAD
# -----------------------------------
# nacionalidad_lbls = {0:'venezolano', 1:'chileno', 2:'otro'}
# Variable se creo en preprocesamiento

# -----------------------------------
# REAL WAGES
# -----------------------------------
ipc_values = {
    2015:70.39, 
    2017:73.93,
    2020:80.43,
    2022:97.21, 
    }
df = (
    df
    .with_columns(
        c.ytrabajocor.truediv(4)
        .truediv(c.o10)
        .alias('w_hora')
    )
)
df = trans.add_real_wages(df, 'w_hora', ipc_values=ipc_values)
print('real_wages created')

# -----------------------------------
# RECODE REGION
# -----------------------------------
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

region_lbls = {1: 'Norte', 2: 'Centro Norte', 3: 'Centro Sur', 4: 'Sur', 5: 'Austral'}
df = (
    df
    .with_columns(
        c.region.replace(recode_region)
        .replace({5:4}) # Se necesitaban menos regiones por el tamaño de muestra
        .alias('region')
    )
)

# -----------------------------------
# CARGAR MATRIZ DE PESOS
# -----------------------------------
if grouping == 'y':
    mat_group = '_grouped'
else:
    mat_group = ''

weight_matrix = root.joinpath(f'codigo/chile/pesos_{args.var}{mat_group}_chile.xlsx')
pesos = pl.read_excel(weight_matrix)
print(f'matrix : {weight_matrix.name} with shape: {pesos.shape} has been loaded')
pesos = pesos.unpivot(index='habilidad', variable_name=args.var, value_name='weight').with_columns(c(f'{args.var} weight'.split()).cast(pl.Float64))
df = df.join(pesos, on=['habilidad', args.var], how='left')
print('weights matrix loaded')

# -----------------------------------
# SAME SKILL CELLS
# -----------------------------------
#Nationals
df = trans.same_skill(df, factor='expr', nac=1, groups=f'anno {args.var} habilidad sexo'.split(), alias='chilenos')
#Nicaraguans
df = trans.same_skill(df, factor='expr', nac=0, weight=True, groups='anno habilidad sexo'.split(), alias='venezolanos')

# -----------------------------------
# LOWER SKILL CELLS
# -----------------------------------
#Nationals
df = trans.other_skills(df, factor='expr', nac=1, groups=f'anno habilidad {args.var} sexo'.split(), alias='chilenos_bajo')
#Nicaraguans
df = trans.other_skills(df, factor='expr', nac=0, weight=True, groups='anno habilidad sexo'.split(), alias='venezolanos_bajo')

# -----------------------------------
# GREATER SKILL CELLS
# -----------------------------------
#Nationals
df = trans.other_skills(df, factor='expr', nac=1, groups=f'anno habilidad {args.var} sexo'.split(), reverse=True, alias='chilenos_alto')
#Nicaraguans
df = trans.other_skills(df, factor='expr', nac=0, weight=True, groups='anno habilidad sexo'.split(), reverse=True, alias='venezolanos_alto')

print('skill cells created')

df = (
    df.with_columns(
        c.venezolanos.truediv(c.venezolanos.add(c.chilenos)).alias('p'),
        c.venezolanos_alto.truediv(c.venezolanos_alto.add(c.chilenos_alto)).alias('p_alto'),
        c.venezolanos_bajo.truediv(c.venezolanos_bajo.add(c.chilenos_bajo)).alias('p_bajo')
    )
    .with_columns(c(['p', 'p_alto', 'p_bajo']).replace({1:None})) #Remove outliers
)
#Replace edge groups with missing values for lower and greater proportions
df = (
    df
    .with_columns(
        pl.when(c.habilidad.eq(c.habilidad.max()))
        .then(None)
        .otherwise(c.p_alto)
        .alias('p_alto'),
        
        pl.when(c.habilidad.eq(c.habilidad.min()))
        .then(None)
        .otherwise(c.p_bajo)
        .alias('p_bajo')
    )
)

# -----------------------------------
# ADD SELF CREATED LABELS
# -----------------------------------
for k, v in vars(trans).items():
    if k.endswith('_lbls'):
        globals()[k] = v

zona_lbls = {1:'urbano', 2:'rural'}
for k, v in globals().items():
    if k.endswith('_lbls'):
        var_labels[k.removesuffix('_lbls')] = v


pyreadstat.write_sav(df, output, column_labels = col_labels, variable_value_labels = var_labels)
print(f'\nDataframe saved in {output}\n')

