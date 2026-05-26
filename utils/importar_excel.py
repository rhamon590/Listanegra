
import pandas as pd

arquivo = 'colaboradores.xlsx'

df = pd.read_excel(arquivo)

df['CPF'] = (
    df['CPF']
    .astype(str)
    .str.replace('.', '', regex=False)
    .str.replace('-', '', regex=False)
    .str.lstrip('0')
)

print(df.head())
