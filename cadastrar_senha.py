# Arquivo: app.py (Versão Completa com Níveis de Permissão)

from flask import Flask, jsonify, request, send_from_directory, Response, session, redirect, url_for, flash
from flask_cors import CORS
import sqlite3, os, math, traceback, io, csv, bcrypt
from datetime import datetime, date, time
from functools import wraps

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
DATABASE_FILE = 'producao.db'
app.secret_key = 'sua-chave-secreta-muito-segura-e-aleatoria-12345' 

# --- Função de Conexão com o BD ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# --- Inicialização do BD (sem alterações na lógica) ---
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS operadores (matricula TEXT PRIMARY KEY, nome TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS setores (codigo TEXT PRIMARY KEY, nome TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS motivos_retrabalho (id INTEGER PRIMARY KEY, motivo TEXT NOT NULL UNIQUE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS produtos_retrabalho (id INTEGER PRIMARY KEY, cod_entrada TEXT UNIQUE, cod_saida TEXT, descricao TEXT, beneficiamento TEXT, und TEXT, valor REAL DEFAULT 0)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apontamentos_retrabalho (
            id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL, hora TEXT NOT NULL,
            turno TEXT, matricula_operador TEXT, cod_entrada TEXT, setor_codigo TEXT, motivo_retrabalho_id INTEGER, 
            quantidade REAL NOT NULL,
            FOREIGN KEY (matricula_operador) REFERENCES operadores (matricula) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (cod_entrada) REFERENCES produtos_retrabalho (cod_entrada) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (setor_codigo) REFERENCES setores(codigo) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (motivo_retrabalho_id) REFERENCES motivos_retrabalho(id) ON UPDATE CASCADE ON DELETE SET NULL
        )
    """)
    try: cursor.execute("ALTER TABLE produtos_retrabalho ADD COLUMN valor REAL DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE operadores ADD COLUMN senha BLOB")
    except: pass
    try: cursor.execute("ALTER TABLE operadores ADD COLUMN permissao TEXT NOT NULL DEFAULT 'operador'")
    except: pass
    conn.commit()
    conn.close()

with app.app_context():
    init_db()
    print(f"Banco de dados inicializado e verificado: {DATABASE_FILE}")

# --- DECORATORS DE SEGURANÇA ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'matricula' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Autenticação necessária'}), 401
            return redirect(url_for('pagina_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'matricula' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Autenticação necessária'}), 401
            return redirect(url_for('pagina_login'))
        if session.get('permissao') != 'adm':
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Acesso negado. Requer permissão de administrador.'}), 403
            flash('Você não tem permissão para acessar esta página.', 'erro')
            return redirect(url_for('pagina_apontamentos'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE PÁGINAS (HTML) ---
@app.route('/login', methods=['GET'])
def pagina_login():
    if 'matricula' in session: return redirect(url_for('pagina_apontamentos'))
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/')
@login_required
def rota_raiz():
    return redirect(url_for('pagina_apontamentos'))

@app.route('/apontamentos')
@login_required
def pagina_apontamentos():
    return send_from_directory(app.static_folder, 'apontamentos.html')

@app.route('/cadastros')
@admin_required
def pagina_cadastros():
    return send_from_directory(app.static_folder, 'cadastros.html')

@app.route('/dashboard')
@admin_required
def pagina_dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['POST'])
def processa_login():
    matricula = request.form.get('matricula')
    senha = request.form.get('senha')
    if not matricula or not senha: return redirect(url_for('pagina_login', erro='campos_vazios'))
    conn = get_db_connection()
    operador = conn.execute('SELECT * FROM operadores WHERE matricula = ?', (matricula,)).fetchone()
    conn.close()
    if operador and operador['senha'] and bcrypt.checkpw(senha.encode('utf-8'), operador['senha']):
        session.clear()
        session['matricula'] = operador['matricula']
        session['nome'] = operador['nome']
        session['permissao'] = operador['permissao']
        return redirect(url_for('pagina_apontamentos'))
    else:
        return redirect(url_for('pagina_login', erro='invalido'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('pagina_login'))

# --- ROTAS DE API (COM PROTEÇÃO REFINADA) ---
@app.route('/api/user/info', methods=['GET'])
@login_required
def get_user_info():
    return jsonify({'matricula': session.get('matricula'),'nome': session.get('nome'),'permissao': session.get('permissao')})
def format_date_for_display(date_str):
    if not date_str: return ''
    try: return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError: return date_str
def calcular_turno(hora_str):
    if not hora_str: return "Não Especificado"
    try: h = time.fromisoformat(hora_str)
    except ValueError: return "Indefinido"
    if time(6, 0) <= h < time(14, 0): return "1º Turno"
    elif time(14, 0) <= h < time(22, 0): return "2º Turno"
    else: return "3º Turno"
@app.route('/api/operador/<string:matricula>', methods=['GET'])
@login_required
def get_operador_lookup(matricula):
    conn = get_db_connection(); row = conn.execute("SELECT nome FROM operadores WHERE matricula = ?", (matricula,)).fetchone(); conn.close()
    return jsonify({"nome": row['nome']}) if row else (jsonify({"erro": "Operador não encontrado"}), 404)
@app.route('/api/produto/<int:produto_id>', methods=['GET'])
@login_required
def get_produto_by_id(produto_id):
    conn = get_db_connection(); row = conn.execute("SELECT * FROM produtos_retrabalho WHERE id = ?", (produto_id,)).fetchone(); conn.close()
    return jsonify(dict(row)) if row else (jsonify({"erro": f"Produto com ID {produto_id} não encontrado"}), 404)
@app.route('/api/setor/<string:codigo>', methods=['GET'])
@login_required
def get_setor_by_codigo(codigo):
    conn = get_db_connection(); row = conn.execute("SELECT nome FROM setores WHERE codigo = ?", (codigo.upper(),)).fetchone(); conn.close()
    return jsonify({"nome": row['nome']}) if row else (jsonify({"erro": f"Setor com código '{codigo}' não encontrado"}), 404)
@app.route('/api/motivo/<int:motivo_id>', methods=['GET'])
@login_required
def get_motivo_by_id(motivo_id):
    conn = get_db_connection(); row = conn.execute("SELECT motivo FROM motivos_retrabalho WHERE id = ?", (motivo_id,)).fetchone(); conn.close()
    return jsonify({"motivo": row['motivo']}) if row else (jsonify({"erro": f"Motivo com ID {motivo_id} não encontrado"}), 404)
@app.route('/api/apontamentos/retrabalho', methods=['POST'])
@login_required
def registrar_apontamento_retrabalho():
    d=request.get_json(); c=get_db_connection()
    try:
        h=datetime.now().strftime('%H:%M:%S'); turno = calcular_turno(h)
        c.execute('INSERT INTO apontamentos_retrabalho(data,hora,turno,matricula_operador,cod_entrada,setor_codigo,motivo_retrabalho_id,quantidade) VALUES(?,?,?,?,?,?,?,?)',(date.today().strftime('%Y-%m-%d'),h,turno,d['matriculaOperador'],d['codEntrada'],d['setorId'].upper(),int(d['motivoId']),float(d['quantidade']))); c.commit(); return jsonify({'mensagem':'Apontamento registrado com sucesso!'}),201
    except Exception as e: print(e); return jsonify({'erro':str(e)}),500
    finally: c.close()

# APIs que precisam de permissão de ADMIN
@app.route('/api/operadores', methods=['GET'])
@admin_required
def get_operadores():
    c=get_db_connection(); r=c.execute('SELECT matricula, nome, permissao FROM operadores ORDER BY nome').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/operadores', methods=['POST'])
@admin_required
def add_operador():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO operadores(matricula, nome) VALUES(?,?)',(d['matricula'],d['nome'])); c.commit(); return jsonify({'mensagem':'Operador adicionado!'}),201
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/operadores/<string:mat>', methods=['PUT'])
@admin_required
def update_operador(mat):
    d=request.get_json(); c=get_db_connection(); c.execute('UPDATE operadores SET nome=? WHERE matricula=?',(d['nome'],mat)); c.commit(); c.close(); return jsonify({'mensagem':'Operador atualizado!'})
@app.route('/api/operadores/<string:mat>', methods=['DELETE'])
@admin_required
def delete_operador(mat):
    c=get_db_connection()
    try: c.execute('DELETE FROM operadores WHERE matricula=?',(mat,)); c.commit(); return jsonify({'mensagem':'Operador excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/produtos', methods=['GET'])
@admin_required
def get_produtos():
    conn = get_db_connection();
    try:
        page = request.args.get('page', 1, type=int); per_page = 50; offset = (page - 1) * per_page
        total_produtos_row = conn.execute('SELECT COUNT(id) as total FROM produtos_retrabalho').fetchone()
        total_produtos = total_produtos_row['total'] if total_produtos_row else 0
        total_pages = math.ceil(total_produtos / per_page) if total_produtos > 0 else 1
        produtos = conn.execute('SELECT * FROM produtos_retrabalho ORDER BY id LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
        return jsonify({ "items": [dict(p) for p in produtos], "total_pages": total_pages, "current_page": page, "has_next": page < total_pages, "has_prev": page > 1 })
    finally: conn.close()
@app.route('/api/setores', methods=['GET'])
@admin_required
def get_setores():
    c=get_db_connection(); r=c.execute('SELECT * FROM setores ORDER BY codigo').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/setores', methods=['POST'])
@admin_required
def add_setor():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO setores(codigo, nome) VALUES(?,?)',(d['codigo'].upper(), d['nome'])); c.commit(); return jsonify({'mensagem':'Setor adicionado!'}), 201
    except Exception as e: return jsonify({'erro':str(e)}), 400
    finally: c.close()
@app.route('/api/setores/<string:codigo>', methods=['PUT'])
@admin_required
def update_setor(codigo):
    d=request.get_json(); c=get_db_connection(); c.execute('UPDATE setores SET nome=? WHERE codigo=?', (d['nome'], codigo.upper())); c.commit(); c.close(); return jsonify({'mensagem':'Setor atualizado!'})
@app.route('/api/setores/<string:codigo>', methods=['DELETE'])
@admin_required
def delete_setor(codigo):
    c=get_db_connection()
    try: c.execute('DELETE FROM setores WHERE codigo=?', (codigo.upper(),)); c.commit(); return jsonify({'mensagem':'Setor excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}), 400
    finally: c.close()
@app.route('/api/motivos', methods=['GET'])
@admin_required
def get_motivos():
    c=get_db_connection(); r=c.execute('SELECT * FROM motivos_retrabalho ORDER BY id').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/motivos', methods=['POST'])
@admin_required
def add_motivo():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO motivos_retrabalho(id,motivo) VALUES(?,?)',(d['id'],d['motivo'])); c.commit(); return jsonify({'mensagem':'Motivo adicionado!'}),201
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/motivos/<int:id>', methods=['PUT'])
@admin_required
def update_motivo(id):
    d=request.get_json(); c=get_db_connection()
    try: c.execute('UPDATE motivos_retrabalho SET id=?,motivo=? WHERE id=?',(d['id_novo'],d['motivo'],id)); c.commit(); return jsonify({'mensagem':'Motivo atualizado!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/motivos/<int:id>', methods=['DELETE'])
@admin_required
def delete_motivo(id):
    c=get_db_connection()
    try: c.execute('DELETE FROM motivos_retrabalho WHERE id=?',(id,)); c.commit(); return jsonify({'mensagem':'Motivo excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/dashboard', methods=['GET'])
@admin_required
def get_dashboard_data():
    conn = get_db_connection()
    try:
        data_de_str = request.args.get('dataDe'); data_ate_str = request.args.get('dataAte')
        params = {}; where_clause = ""
        if data_de_str and data_ate_str:
            where_clause = "WHERE ar.data BETWEEN :dataDe AND :dataAte"
            params = {'dataDe': data_de_str, 'dataAte': data_ate_str}
        
        base_query = f"SELECT ar.quantidade, ar.turno, pr.valor, s.nome as nome_setor, m.motivo, pr.cod_entrada FROM apontamentos_retrabalho ar LEFT JOIN produtos_retrabalho pr ON ar.cod_entrada = pr.cod_entrada LEFT JOIN setores s ON ar.setor_codigo = s.codigo LEFT JOIN motivos_retrabalho m ON ar.motivo_retrabalho_id = m.id {where_clause}"
        all_apontamentos = conn.execute(base_query, params).fetchall()
        quantidade_total = sum(item['quantidade'] for item in all_apontamentos)
        valor_total = sum(item['quantidade'] * (item['valor'] or 0) for item in all_apontamentos)
        kpis_turno = {'1º Turno': 0, '2º Turno': 0, '3º Turno': 0}
        prod_por_setor_dict = {}; top_produtos_dict = {}; top_motivos_dict = {}; valor_por_setor_dict = {}
        for item in all_apontamentos:
            if item['turno'] in kpis_turno: kpis_turno[item['turno']] += item['quantidade']
            setor = item['nome_setor'] or "N/E"; prod_por_setor_dict[setor] = prod_por_setor_dict.get(setor, 0) + item['quantidade']
            motivo = item['motivo'] or "N/E"; top_motivos_dict[motivo] = top_motivos_dict.get(motivo, 0) + item['quantidade']
            produto = item['cod_entrada'] or "N/E"; top_produtos_dict[produto] = top_produtos_dict.get(produto, 0) + item['quantidade']
            valor_item = item['quantidade'] * (item['valor'] or 0); valor_por_setor_dict[setor] = valor_por_setor_dict.get(setor, 0) + valor_item
        prod_por_setor = sorted([{'nome': k, 'total': v} for k, v in prod_por_setor_dict.items()], key=lambda x: x['total'], reverse=True)
        top_produtos = sorted([{'cod_entrada': k, 'total': v} for k, v in top_produtos_dict.items()], key=lambda x: x['total'], reverse=True)[:5]
        top_motivos = sorted([{'motivo': k, 'total': v} for k, v in top_motivos_dict.items()], key=lambda x: x['total'], reverse=True)[:5]
        valor_por_setor = sorted([{'nome': k, 'total_valor': v} for k, v in valor_por_setor_dict.items()], key=lambda x: x['total_valor'], reverse=True)
        dashboard_data = {
            "kpis": { "quantidade_pecas": quantidade_total, "quantidade_kg": 0, "valor_total": valor_total, "turno1_total": kpis_turno.get('1º Turno', 0), "turno2_total": kpis_turno.get('2º Turno', 0), "turno3_total": kpis_turno.get('3º Turno', 0), },
            "producao_por_setor": prod_por_setor, "top_produtos": top_produtos, "top_motivos": top_motivos, "valor_por_setor": valor_por_setor
        }
        return jsonify(dashboard_data)
    except Exception as e:
        print(f"ERRO /api/dashboard: {e}"); traceback.print_exc()
        return jsonify({"erro": "Erro ao carregar dados do dashboard"}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)