# Arquivo: gerenciar_usuarios.py (Versão Completa)
import sqlite3
import bcrypt
import getpass # Para esconder a senha ao digitar

DATABASE_FILE = 'producao.db'

def gerenciar_usuario():
    print("--- Ferramenta de Gestão de Usuários ---")
    
    matricula = input("Digite a matrícula do operador para criar/atualizar a senha: ").strip()
    if not matricula:
        print("Matrícula não pode ser vazia.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Verifica se o operador existe
        cursor.execute("SELECT matricula, nome FROM operadores WHERE matricula = ?", (matricula,))
        operador = cursor.fetchone()

        if not operador:
            print(f"\nERRO: Operador com matrícula '{matricula}' não encontrado no banco de dados.")
            print("Cadastre o operador no sistema primeiro (pela tela de Cadastros).")
            return
            
        print(f"\nAtualizando usuário: {operador['nome']} (Matrícula: {operador['matricula']})")
        
        # Usando getpass para não exibir a senha no terminal
        senha = getpass.getpass("Digite a NOVA senha para este operador: ")
        senha_confirma = getpass.getpass("Confirme a NOVA senha: ")

        if senha != senha_confirma:
            print("\nERRO: As senhas não coincidem!")
            return

        if not senha:
            print("\nERRO: A senha não pode ser vazia.")
            return

        # Criptografa a senha
        senha_hashed = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        
        # Pede a permissão
        permissao = ''
        while permissao not in ['adm', 'operador']:
            permissao = input("Digite o nível de permissão ('adm' ou 'operador'): ").strip().lower()
            if permissao not in ['adm', 'operador']:
                print("Opção inválida. Por favor, digite 'adm' ou 'operador'.")
                
        cursor.execute("UPDATE operadores SET senha = ?, permissao = ? WHERE matricula = ?", (senha_hashed, permissao, matricula))
        conn.commit()
        print(f"\nSUCESSO: Senha e permissão para o operador '{matricula}' foram atualizadas!")

    except sqlite3.Error as e:
        print(f"\nERRO de banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    gerenciar_usuario()