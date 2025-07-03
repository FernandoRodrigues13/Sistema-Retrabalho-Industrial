import sqlite3
import csv
import os

DATABASE_FILE = 'producao.db'
CSV_FILE = 'produtos_retrabalho.csv'

# --- CONFIGURAÇÕES CORRIGIDAS ---
DELIMITADOR = ';' 
# 'utf-8-sig' é a codificação especial que remove o "ï»¿" (BOM) do início do arquivo.
CODIFICACAO = 'utf-8-sig'

def importar_produtos_retrabalho():
    print("--- INICIANDO SCRIPT DE IMPORTAÇÃO FINAL ---")
    
    if not os.path.exists(CSV_FILE):
        print(f"\nERRO: Arquivo '{CSV_FILE}' não encontrado.")
        return

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print(f"Conectado ao banco de dados '{DATABASE_FILE}'.")
    except sqlite3.Error as e:
        print(f"\nERRO ao conectar ao banco de dados: {e}")
        return

    produtos_para_inserir = []
    print(f"Lendo o arquivo '{CSV_FILE}' com as configurações corretas...")
    try:
        with open(CSV_FILE, mode='r', encoding=CODIFICACAO, errors='ignore') as file:
            csv_reader = csv.reader(file, delimiter=DELIMITADOR)
            next(csv_reader, None) # Pula a linha do cabeçalho
            
            for i, row in enumerate(csv_reader, 2):
                if not any(row): continue
                
                # O script espera pelo menos 8 colunas para encontrar a 'und'
                if len(row) >= 8:
                    id_produto_str = row[0].strip()
                    cod_entrada = row[1].strip()
                    cod_saida = row[2].strip()
                    # A coluna 3 (cliente) é ignorada
                    descricao = row[4].strip()
                    beneficiamento = row[5].strip()
                    # A coluna 6 (setor) é ignorada
                    und = row[7].strip()

                    if id_produto_str and cod_entrada:
                        try:
                            id_produto_int = int(id_produto_str)
                            produtos_para_inserir.append((id_produto_int, cod_entrada, cod_saida, descricao, beneficiamento, und))
                        except ValueError:
                            print(f"AVISO: ID '{id_produto_str}' na linha {i} não é um número válido e será ignorado.")
                    else:
                        print(f"AVISO: Linha {i} ignorada por ter ID ou Cód. Entrada vazios.")
                else:
                    print(f"AVISO: Linha {i} ignorada por ter poucas colunas para extrair todos os dados.")

    except Exception as e:
        print(f"\nERRO ao ler o arquivo CSV: {e}")
        conn.close()
        return

    if not produtos_para_inserir:
        print("\nNenhum produto válido foi encontrado no CSV para importar. Verifique o arquivo e as configurações.")
        conn.close()
        return

    sql_insert = "INSERT OR REPLACE INTO produtos_retrabalho (id, cod_entrada, cod_saida, descricao, beneficiamento, und) VALUES (?, ?, ?, ?, ?, ?)"
    print(f"\nEncontrados {len(produtos_para_inserir)} produtos. Inserindo no banco de dados...")
    
    try:
        cursor.execute("DELETE FROM produtos_retrabalho")
        conn.commit()
        print("Tabela de produtos limpa antes da nova importação.")
        
        cursor.executemany(sql_insert, produtos_para_inserir)
        conn.commit()
        print(f"\nIMPORTAÇÃO CONCLUÍDA COM SUCESSO! {cursor.rowcount} linhas foram inseridas.")
        
    except sqlite3.Error as e:
        print(f"\nERRO durante a inserção no banco: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("Conexão com o banco de dados fechada.")
        print("--- FIM DO SCRIPT ---")

if __name__ == '__main__':
    importar_produtos_retrabalho()