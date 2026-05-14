import polars as pl
from polars import col as c
from definitions import bases
import seaborn as sns
import matplotlib.pyplot as plt
from ucr_tools.core import data_analysis as da

sns.set_theme('paper')
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 12

df:pl.DataFrame
df, var_labels, col_labels = da.read_file(bases.joinpath('cr/limpio/cr_region_processed_inc_2020_2022.sav'))

totals = (
    df.filter(c.nacionalidad.eq(0))
    .group_by('anno nacionalidad'.split())
    .agg(c.factor.sum())
)

dpi=300
fig, ax = plt.subplots(figsize=(6,3))
ax.set_ylim(260_000,350_000)
ax.set_yticklabels(f'{x:2,.0f}' for x in ax.get_yticks())
sns.lineplot(
    data=totals.with_columns(pl.lit('Nicaraguans').alias('Nationality')),
    x='anno', 
    y='factor', 
    ax=ax, 
    hue='Nationality',
    marker='o',
    linestyle='--',
    )
ax.set_ylabel('')
ax.set_xlabel('')
ax.legend().remove()
plt.tight_layout()
plt.savefig('line_graph_migration.png', dpi=dpi, bbox_inches='tight')


