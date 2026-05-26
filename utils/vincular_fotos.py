
import os

pasta_fotos = 'fotos'

for foto in os.listdir(pasta_fotos):
    cpf = foto.replace('.jpg', '')
    print(f'Foto vinculada ao CPF: {cpf}')
