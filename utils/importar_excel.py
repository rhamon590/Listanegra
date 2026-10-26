
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

print(f"Planilha carregada: {len(df)} linha(s). Os dados pessoais não serão exibidos no console.")
