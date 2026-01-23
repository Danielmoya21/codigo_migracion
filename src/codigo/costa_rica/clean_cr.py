import pyreadstat
import polars as pl
from polars import col as c
from codigo import transformations as trans
import argparse
from definitions import codigo, root, bases


parser = argparse.ArgumentParser()
parser.add_argument('--var', type=str, default='region')
args = parser.parse_args()

skill_groups = input('Do you want to group skill cells? y/n\n>')
if skill_groups == 'y':
    skill_gp = '_grouped'
else:
    skill_gp = ''
    
group_regions = input('Do you want to group region cells? y/n\n>')
if group_regions == 'y':
    region_gp = '_v2'
else:
    region_gp = ''
    
output_name = f'cr_{args.var}{region_gp}{skill_gp}_processed'
output = bases.joinpath(f'cr/limpio/{output_name}.sav')

df, meta = pyreadstat.read_sav(bases.joinpath('cr/limpio/cr_all.sav'), output_format='polars')
df:pl.DataFrame
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels

idh_formula_1 = pl.concat_str(c.anno, c.upm, c.cuestionario, c.hogar)
idh_formula_2 = pl.concat_str(c.anno, c.nro_vivienda, c.hogar)

# -----------------------------------
# IDENTIFICADOR DE HOGAR
# -----------------------------------
df = (
    df
    .with_columns(
        pl.when(c.anno.ne(2023))
        .then(idh_formula_1)
        .otherwise(idh_formula_2)
        .alias('iddh')
        )
    )

# -----------------------------------
# DEPENDIENTES HOGAR
# -----------------------------------
df = (
    df
    .with_columns(
        ((c.a5.lt(6) | c.a5.gt(65)) & (~c.a5.is_in([98,99]))).sum().over('iddh') #98,99 edad ignorada
        .alias('dependientes')
    )
    .with_columns(
        pl.when(c.dependientes.gt(0)).then(1).otherwise(0)
        .alias('id_dependientes')
    )
)

# -----------------------------------
# GENERAL FILTERS
# -----------------------------------
edad = c.a5.is_between(15,65, closed='both') #Mantener solo personas en edad de trabajar
nivel_de_instruccion = c.nivinst.ne(99)

df = df.filter(nivel_de_instruccion, edad) #Filtros de sexo y nacionalidad se aplican al final

# -----------------------------------
# EXPERIENCIA
# -----------------------------------
df = trans.add_experience(df, 'a5', 'escolari') #De momento no se usan los filtros, al final se filtra exp>0
print('experience created')

# -----------------------------------
# LOGRO
# -----------------------------------
recode = {0:1, 5:3, 6:4, 7:5, 8:5, 99:None}
df = trans.add_logro(df, col='nivinst', recode_dict=recode)
print('logro created')

# -----------------------------------
# HABILIDAD
# -----------------------------------
df = trans.add_habilidad(df)
print('habilidad created')

if skill_groups=='y':
    df = df.with_columns(c.habilidad.replace({1:3, 2:3, 3:4})) #!!! Use only if merging skill groups
    
# -----------------------------------
# NACIONALIDAD
# -----------------------------------
nacionalidad_lbls = {0:'nicaraguense', 1:'costarricense', 2:'otro'}
df = df.with_columns(
    pl.when(c.lugnac.is_in([0,1]))
    .then(1)
    .when(c.lugnac.eq(2))
    .then(0)
    .otherwise(2)
    .alias('nacionalidad')
)
print('nationality created')

# -----------------------------------
# REAL WAGES
# -----------------------------------
ipc_values = {
    2015:93.00390934, 
    2016:93.44616814, 
    2017:94.53304812, 
    2018:96.50343843, 
    2019:99.29164281, 
    2022:112.0987, 
    2023:109.537132
    }
df = (
    df
    .with_columns(
        c.itrbt.truediv(4)
        .truediv(c.hortotnorm)
        .alias('w_hora')
    )
)
df = trans.add_real_wages(df, 'w_hora', ipc_values=ipc_values)
print('real_wages created')

if group_regions=='y':
    region_lbls = {1:'Central', 2:'Cerca_Nic', 3:'Lejos_Nic'}
    df = df.with_columns(c.region.replace({5:2, 6:2, 4:3}))

# -----------------------------------
# CARGAR MATRIZ DE PESOS
# -----------------------------------

pesos = pl.read_excel(codigo.joinpath(f'costa_rica/pesos_{args.var}{region_gp}{skill_gp}_cr.xlsx'))
pesos = pesos.unpivot(index='habilidad', variable_name=args.var, value_name='weight').with_columns(c([args.var, 'weight']).cast(pl.Float64))
df = df.join(pesos, on=['habilidad', args.var], how='left')
print('weights matrix loaded')

# -----------------------------------
# SAME SKILL CELLS
# -----------------------------------
#Nationals
df = trans.same_skill(df, factor='factor', nac=1, groups=f'anno {args.var} habilidad a4'.split(), alias='CR')
#Nicaraguans
df = trans.same_skill(df, factor='factor', nac=0, weight=True, groups='anno habilidad a4'.split(), alias='NIC')

# -----------------------------------
# LOWER SKILL CELLS
# -----------------------------------
#Nationals
df = trans.other_skills(df, factor='factor', nac=1, groups=f'anno habilidad {args.var} a4'.split(), alias='CR_bajo')
#Nicaraguans
df = trans.other_skills(df, factor='factor', nac=0, weight=True, groups='anno habilidad a4'.split(), alias='NIC_bajo')

# -----------------------------------
# GREATER SKILL CELLS
# -----------------------------------
#Nationals
df = trans.other_skills(df, factor='factor', nac=1, groups=f'anno habilidad {args.var} a4'.split(), reverse=True, alias='CR_alto')
#Nicaraguans
df = trans.other_skills(df, factor='factor', nac=0, weight=True, groups='anno habilidad a4'.split(), reverse=True, alias='NIC_alto')

print('skill cells created')

df = (
    df.with_columns(
        c.NIC.truediv(c.NIC.add(c.CR)).alias('p'),
        c.NIC_alto.truediv(c.NIC_alto.add(c.CR_alto)).alias('p_alto'),
        c.NIC_bajo.truediv(c.NIC_bajo.add(c.CR_bajo)).alias('p_bajo')
    )
    .with_columns(c(['p', 'p_alto', 'p_bajo']).replace({1:None}))
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
        
for k, v in globals().items():
    if k.endswith('_lbls'):
        var_labels[k.removesuffix('_lbls')] = v
        
pyreadstat.write_sav(df, output.as_posix(), column_labels = col_labels, variable_value_labels = var_labels)
print('dataframe saved')

