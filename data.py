import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import os
import re

def limpar_nome(nome):
    return re.sub(r'[<>:"/\\|?*]', '_', nome)

def gerar_nome_ofertas(nome_original):
    # Divide o nome em partes e insere "_Ofertas" antes do ano (se detectado)
    partes = nome_original.split()
    for i, parte in enumerate(partes):
        if parte.isdigit() and len(parte) == 4:  # Detecta ano com 4 dígitos
            return ' '.join(partes[:i]) + '_Ofertas ' + ' '.join(partes[i:])
    return nome_original + '_Ofertas'  # Caso não tenha ano, adiciona no final

Tk().withdraw()
arquivos = askopenfilenames(title="Selecione os arquivos CSV", filetypes=[("CSV files", "*.csv")])

if arquivos:
    try:
        for arquivo in arquivos:
            nome_base = os.path.splitext(os.path.basename(arquivo))[0]
            nome_pasta = gerar_nome_ofertas(nome_base)
            pasta_saida = os.path.join("planilhas_por_curso", limpar_nome(nome_pasta))
            os.makedirs(pasta_saida, exist_ok=True)

            df = pd.read_csv(arquivo)
            df.columns = df.columns.str.strip()
            df['course'] = df['course'].astype(str).str.strip()

            df['username'] = df['username'].astype(str).str.zfill(11)  # ou o tamanho fixo correto

            for course_code in df['course'].unique():
                df_filtrado = df[df['course'] == course_code]
                nome_limpo = limpar_nome(course_code)
                caminho_arquivo = os.path.join(pasta_saida, f"{nome_limpo}.csv")
                df_filtrado.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
                print(f"Arquivo gerado: {caminho_arquivo}")

        print("\nConcluído! As planilhas foram salvas na pasta 'planilhas_por_curso'.")
    except Exception as e:
        print("Erro ao processar os arquivos:", e)
else:
    print("Nenhum arquivo foi selecionado.")
