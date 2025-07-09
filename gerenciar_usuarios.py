# Arquivo: gerenciar_usuarios.py
import sqlite3
import bcrypt

DATABASE_FILE = 'producao.db'

def atualizar_usuario():
    print("--- Ferramenta de Gestão de Usuários ---")
    matricula = input("Digite a matrícula do operador a ser atualizado: ").strip()
    senha = input(f"Digite a NOVA senha para '{matricula}' (deixe em branco para não alterar): ").strip()
    permissao = input(f"Digite o nível de permissão ('adm' ou 'operador') (deixe em branco para não alterar): ").strip().lower()

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    updates = []
    params = []

    if senha:
        senha_hashed = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        updates.append("senha = ?")
        params.append(senha_hashed)
    
    if permissao in ['adm', 'operador']:
        updates.append("permissao = ?")
        params.append(permissao)
    
    if not updates:
        print("Nenhuma alteração a ser feita.")
        return

    params.append(matricula)
    query = f"UPDATE operadores SET {', '.join(updates)} WHERE matricula = ?"
    
    try:
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0:
            print(f"ERRO: Nenhum operador com a matrícula '{matricula}' foi encontrado.")
        else:
            conn.commit()
            print(f"\nSUCESSO: Usuário '{matricula}' atualizado.")
    except sqlite3.Error as e:
        print(f"ERRO de banco de dados: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    atualizar_usuario()