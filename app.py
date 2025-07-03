from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import sqlite3, os, math, traceback, io, csv
from datetime import datetime, date, time, timedelta

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
DATABASE_FILE = 'producao.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS operadores (matricula TEXT PRIMARY KEY, nome TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS setores (codigo TEXT PRIMARY KEY, nome TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS motivos_retrabalho (id INTEGER PRIMARY KEY, motivo TEXT NOT NULL UNIQUE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS produtos_retrabalho (id INTEGER PRIMARY KEY, cod_entrada TEXT UNIQUE, cod_saida TEXT, descricao TEXT, beneficiamento TEXT, und TEXT)")
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
    conn.commit()
    if cursor.execute("SELECT COUNT(*) FROM operadores").fetchone()[0] == 0: cursor.executemany("INSERT INTO operadores (matricula, nome) VALUES (?, ?)", [('101', 'João Silva'), ('102', 'Maria Oliveira')])
    if cursor.execute("SELECT COUNT(*) FROM setores").fetchone()[0] == 0: cursor.executemany("INSERT INTO setores (codigo, nome) VALUES (?, ?)", [(f"S{i:02}", f"Setor de Teste {i}") for i in range(1, 11)])
    if cursor.execute("SELECT COUNT(*) FROM motivos_retrabalho").fetchone()[0] == 0: cursor.executemany("INSERT INTO motivos_retrabalho (id, motivo) VALUES (?, ?)", [(i, f"Motivo Exemplo {i}") for i in range(1, 16)])
    conn.commit()
    conn.close()

with app.app_context(): init_db(); print(f"Banco de dados inicializado: {DATABASE_FILE}")

def format_date_for_display(date_str):
    if not date_str: return ''
    try: return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError: return date_str
def calcular_turno(hora_str):
    if not hora_str: return "Não Especificado"
    try: h = time.fromisoformat(hora_str)
    except ValueError: return "Indefinido"
    if time(6, 0, 0) <= h <= time(13, 59, 59, 999999): return "Manhã"
    elif time(14, 0, 0) <= h <= time(21, 59, 59, 999999): return "Tarde"
    else: return "Noite"

@app.route('/')
def rota_raiz(): return send_from_directory(app.static_folder, 'apontamentos.html')
@app.route('/apontamentos')
def pagina_apontamentos(): return send_from_directory(app.static_folder, 'apontamentos.html')
@app.route('/cadastros')
def pagina_cadastros(): return send_from_directory(app.static_folder, 'cadastros.html')
@app.route('/dashboard')
def pagina_dashboard(): return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/api/operador/<string:matricula>', methods=['GET'])
def get_operador_lookup(matricula):
    conn = get_db_connection(); row = conn.execute("SELECT nome FROM operadores WHERE matricula = ?", (matricula,)).fetchone(); conn.close()
    if row: return jsonify({"nome": row['nome']})
    else: return jsonify({"erro": "Operador não encontrado"}), 404
@app.route('/api/produto/<int:produto_id>', methods=['GET'])
def get_produto_by_id(produto_id):
    conn = get_db_connection(); row = conn.execute("SELECT * FROM produtos_retrabalho WHERE id = ?", (produto_id,)).fetchone(); conn.close()
    if row: return jsonify(dict(row))
    else: return jsonify({"erro": f"Produto com ID {produto_id} não encontrado"}), 404
@app.route('/api/setor/<string:codigo>', methods=['GET'])
def get_setor_by_codigo(codigo):
    conn = get_db_connection(); row = conn.execute("SELECT nome FROM setores WHERE codigo = ?", (codigo.upper(),)).fetchone(); conn.close()
    if row: return jsonify({"nome": row['nome']})
    else: return jsonify({"erro": f"Setor com código '{codigo}' não encontrado"}), 404
@app.route('/api/motivo/<int:motivo_id>', methods=['GET'])
def get_motivo_by_id(motivo_id):
    conn = get_db_connection(); row = conn.execute("SELECT motivo FROM motivos_retrabalho WHERE id = ?", (motivo_id,)).fetchone(); conn.close()
    if row: return jsonify({"motivo": row['motivo']})
    else: return jsonify({"erro": f"Motivo com ID {motivo_id} não encontrado"}), 404

@app.route('/api/operadores', methods=['GET'])
def get_operadores():
    c=get_db_connection(); r=c.execute('SELECT * FROM operadores ORDER BY nome').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/operadores', methods=['POST'])
def add_operador():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO operadores(matricula, nome) VALUES(?,?)',(d['matricula'],d['nome'])); c.commit(); return jsonify({'mensagem':'Operador adicionado!'}),201
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/operadores/<string:mat>', methods=['PUT'])
def update_operador(mat):
    d=request.get_json(); c=get_db_connection(); c.execute('UPDATE operadores SET nome=? WHERE matricula=?',(d['nome'],mat)); c.commit(); c.close(); return jsonify({'mensagem':'Operador atualizado!'})
@app.route('/api/operadores/<string:mat>', methods=['DELETE'])
def delete_operador(mat):
    c=get_db_connection();
    try: c.execute('DELETE FROM operadores WHERE matricula=?',(mat,)); c.commit(); return jsonify({'mensagem':'Operador excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()

@app.route('/api/produtos', methods=['GET'])
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
def get_setores():
    c=get_db_connection(); r=c.execute('SELECT * FROM setores ORDER BY codigo').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/setores', methods=['POST'])
def add_setor():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO setores(codigo, nome) VALUES(?,?)',(d['codigo'].upper(), d['nome'])); c.commit(); return jsonify({'mensagem':'Setor adicionado!'}), 201
    except Exception as e: return jsonify({'erro':str(e)}), 400
    finally: c.close()
@app.route('/api/setores/<string:codigo>', methods=['PUT'])
def update_setor(codigo):
    d=request.get_json(); c=get_db_connection(); c.execute('UPDATE setores SET nome=? WHERE codigo=?', (d['nome'], codigo.upper())); c.commit(); c.close(); return jsonify({'mensagem':'Setor atualizado!'})
@app.route('/api/setores/<string:codigo>', methods=['DELETE'])
def delete_setor(codigo):
    c=get_db_connection()
    try: c.execute('DELETE FROM setores WHERE codigo=?', (codigo.upper(),)); c.commit(); return jsonify({'mensagem':'Setor excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}), 400
    finally: c.close()

@app.route('/api/motivos', methods=['GET'])
def get_motivos():
    c=get_db_connection(); r=c.execute('SELECT * FROM motivos_retrabalho ORDER BY id').fetchall(); c.close(); return jsonify([dict(i) for i in r])
@app.route('/api/motivos', methods=['POST'])
def add_motivo():
    d=request.get_json(); c=get_db_connection()
    try: c.execute('INSERT INTO motivos_retrabalho(id,motivo) VALUES(?,?)',(d['id'],d['motivo'])); c.commit(); return jsonify({'mensagem':'Motivo adicionado!'}),201
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/motivos/<int:id>', methods=['PUT'])
def update_motivo(id):
    d=request.get_json(); c=get_db_connection()
    try: c.execute('UPDATE motivos_retrabalho SET id=?,motivo=? WHERE id=?',(d['id_novo'],d['motivo'],id)); c.commit(); return jsonify({'mensagem':'Motivo atualizado!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()
@app.route('/api/motivos/<int:id>', methods=['DELETE'])
def delete_motivo(id):
    c=get_db_connection()
    try: c.execute('DELETE FROM motivos_retrabalho WHERE id=?',(id,)); c.commit(); return jsonify({'mensagem':'Motivo excluído!'})
    except Exception as e: return jsonify({'erro':str(e)}),400
    finally: c.close()

@app.route('/api/apontamentos/retrabalho', methods=['POST'])
def registrar_apontamento_retrabalho():
    d=request.get_json(); c=get_db_connection()
    try:
        h=datetime.now().strftime('%H:%M:%S')
        c.execute('INSERT INTO apontamentos_retrabalho(data,hora,turno,matricula_operador,cod_entrada,setor_codigo,motivo_retrabalho_id,quantidade) VALUES(?,?,?,?,?,?,?,?)',(date.today().strftime('%Y-%m-%d'),h,calcular_turno(h),d['matriculaOperador'],d['codEntrada'],d['setorId'].upper(),int(d['motivoId']),float(d['quantidade']))); c.commit(); return jsonify({'mensagem':'Apontamento registrado com sucesso!'}),201
    except Exception as e: print(e); return jsonify({'erro':str(e)}),500
    finally: c.close()
@app.route('/api/apontamentos/retrabalho', methods=['GET'])
def get_apontamentos_retrabalho():
    c=get_db_connection(); p={}; cs=[]
    try:
        pg=request.args.get('page',1,type=int); pp=20; offset=(pg-1)*pp
        if request.args.get('dataDe'): cs.append("ar.data >= :dataDe"); p['dataDe']=request.args.get('dataDe')
        if request.args.get('dataAte'): cs.append("ar.data <= :dataAte"); p['dataAte']=request.args.get('dataAte')
        if request.args.get('idProduto'): cs.append("pr.id = :idProduto"); p['idProduto']=request.args.get('idProduto')
        bq="FROM apontamentos_retrabalho ar LEFT JOIN operadores o ON ar.matricula_operador=o.matricula LEFT JOIN produtos_retrabalho pr ON ar.cod_entrada=pr.cod_entrada LEFT JOIN setores s ON ar.setor_codigo=s.codigo LEFT JOIN motivos_retrabalho mr ON ar.motivo_retrabalho_id=mr.id"
        wc=" WHERE "+ " AND ".join(cs) if cs else ""
        t_row=c.execute(f"SELECT COUNT(ar.id) as t {bq}{wc}",p).fetchone()
        t = t_row['t'] if t_row else 0
        tp=math.ceil(t/pp) if t>0 else 1
        sf="ar.id,ar.data,ar.hora,ar.turno,ar.quantidade,o.nome as nome_operador,o.matricula as matricula_operador,pr.cod_entrada,pr.descricao as descricao_produto,s.nome as nome_setor,mr.motivo as motivo_retrabalho"
        rows=c.execute(f"SELECT {sf} {bq}{wc} ORDER BY ar.data DESC,ar.hora DESC LIMIT :l OFFSET :o",{**p,'l':pp,'o':offset}).fetchall()
        items=[{**row,'data':format_date_for_display(row['data'])} for row in rows]
        return jsonify({"items":items,"total_pages":tp,"current_page":pg, "has_next": pg < tp, "has_prev": pg > 1})
    except Exception as e:
        print(f"ERRO EM GET /api/apontamentos/retrabalho: {e}"); traceback.print_exc()
        return jsonify({"erro": "Erro interno ao buscar o histórico."}), 500
    finally: c.close()
@app.route('/api/apontamento/retrabalho/<int:id>', methods=['GET'])
def get_apontamento_by_id(id):
    c=get_db_connection(); r=c.execute("SELECT ar.*,o.nome as nome_operador,pr.id as produto_id,pr.descricao as descricao_produto,pr.cod_saida,pr.beneficiamento,pr.und,s.nome as nome_setor,mr.motivo as motivo_retrabalho FROM apontamentos_retrabalho ar LEFT JOIN operadores o ON ar.matricula_operador=o.matricula LEFT JOIN produtos_retrabalho pr ON ar.cod_entrada=pr.cod_entrada LEFT JOIN setores s ON ar.setor_codigo=s.codigo LEFT JOIN motivos_retrabalho mr ON ar.motivo_retrabalho_id=mr.id WHERE ar.id=?",(id,)).fetchone(); c.close()
    return jsonify(dict(r)) if r else (jsonify({'erro':'Not Found'}),404)
@app.route('/api/apontamentos/retrabalho/<int:id>', methods=['PUT'])
def update_apontamento(id):
    d=request.get_json(); c=get_db_connection()
    try: c.execute('UPDATE apontamentos_retrabalho SET matricula_operador=?,cod_entrada=?,setor_codigo=?,motivo_retrabalho_id=?,quantidade=? WHERE id=?',(d['matriculaOperador'],d['codEntrada'],d['setorId'].upper(),int(d['motivoId']),float(d['quantidade']),id)); c.commit(); return jsonify({'mensagem':'Apontamento atualizado com sucesso!'})
    except Exception as e: c.rollback(); return jsonify({'erro': str(e)}), 500
    finally: c.close()
@app.route('/api/apontamentos/retrabalho/<int:id>', methods=['DELETE'])
def deletar_apontamento(id):
    c=get_db_connection(); c.execute('DELETE FROM apontamentos_retrabalho WHERE id=?',(id,)); c.commit(); c.close(); return jsonify({'mensagem':'Apontamento excluído com sucesso!'})
@app.route('/api/apontamentos/exportar', methods=['GET'])
def exportar_apontamentos_csv():
    c=get_db_connection(); p={}; cs=[]
    if request.args.get('dataDe'): cs.append("ar.data >= :dataDe"); p['dataDe']=request.args.get('dataDe')
    if request.args.get('dataAte'): cs.append("ar.data <= :dataAte"); p['dataAte']=request.args.get('dataAte')
    if request.args.get('idProduto'): cs.append("pr.id = :idProduto"); p['idProduto']=request.args.get('idProduto')
    wc=" WHERE "+ " AND ".join(cs) if cs else ""
    q=f"SELECT ar.data,ar.hora,ar.turno,ar.matricula_operador,o.nome,pr.cod_entrada,pr.descricao,ar.setor_codigo,s.nome,ar.motivo_retrabalho_id,mr.motivo,ar.quantidade FROM apontamentos_retrabalho ar LEFT JOIN operadores o ON ar.matricula_operador=o.matricula LEFT JOIN produtos_retrabalho pr ON ar.cod_entrada=pr.cod_entrada LEFT JOIN setores s ON ar.setor_codigo=s.codigo LEFT JOIN motivos_retrabalho mr ON ar.motivo_retrabalho_id=mr.id {wc} ORDER BY ar.data DESC,ar.hora DESC"
    d=c.execute(q,p).fetchall(); c.close(); o=io.StringIO(); w=csv.writer(o,delimiter=';'); w.writerow(['Data','Hora','Turno','Matricula_Operador','Nome_Operador','Cod_Entrada_Produto','Descricao_Produto','Cod_Setor','Nome_Setor','ID_Motivo','Descricao_Motivo','Quantidade']); w.writerows(d); o.seek(0)
    return Response(o,mimetype="text/csv",headers={"Content-Disposition":f"attachment;filename=apontamentos_{date.today()}.csv"})

# --- NOVA ROTA PARA O DASHBOARD ---
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    conn = get_db_connection()
    try:
        data_de_str = request.args.get('dataDe')
        data_ate_str = request.args.get('dataAte')
        params = {}
        where_clause = ""
        if data_de_str and data_ate_str:
            where_clause = "WHERE data BETWEEN :dataDe AND :dataAte"
            params = {'dataDe': data_de_str, 'dataAte': data_ate_str}

        kpis_query = f"SELECT COUNT(id) as total_apontamentos, SUM(quantidade) as quantidade_total, COUNT(DISTINCT matricula_operador) as operadores_ativos FROM apontamentos_retrabalho {where_clause}"
        kpis = conn.execute(kpis_query, params).fetchone()

        setor_query = f"SELECT s.nome, SUM(ar.quantidade) as total FROM apontamentos_retrabalho ar JOIN setores s ON ar.setor_codigo = s.codigo {where_clause} GROUP BY s.nome ORDER BY total DESC"
        prod_por_setor = conn.execute(setor_query, params).fetchall()

        produto_query = f"SELECT pr.descricao, SUM(ar.quantidade) as total FROM apontamentos_retrabalho ar JOIN produtos_retrabalho pr ON ar.cod_entrada = pr.cod_entrada {where_clause} GROUP BY pr.descricao ORDER BY total DESC LIMIT 5"
        top_produtos = conn.execute(produto_query, params).fetchall()

        turno_query = f"SELECT turno, SUM(quantidade) as total FROM apontamentos_retrabalho {where_clause} GROUP BY turno HAVING turno IS NOT NULL ORDER BY turno"
        prod_por_turno = conn.execute(turno_query, params).fetchall()
        
        diaria_query = f"SELECT data, SUM(quantidade) as total FROM apontamentos_retrabalho {where_clause} GROUP BY data ORDER BY data ASC"
        prod_diaria = conn.execute(diaria_query, params).fetchall()

        dashboard_data = {
            "kpis": dict(kpis) if kpis and kpis['total_apontamentos'] is not None else {"total_apontamentos": 0, "quantidade_total": 0, "operadores_ativos": 0},
            "producao_por_setor": [dict(row) for row in prod_por_setor],
            "top_produtos": [dict(row) for row in top_produtos],
            "producao_por_turno": [dict(row) for row in prod_por_turno],
            "producao_diaria": [{"data": format_date_for_display(row['data']), "total": row['total']} for row in prod_diaria]
        }
        return jsonify(dashboard_data)
    except Exception as e:
        print(f"ERRO /api/dashboard: {e}"); traceback.print_exc()
        return jsonify({"erro": "Erro ao carregar dados do dashboard"}), 500
    finally:
        if conn: conn.close()
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)