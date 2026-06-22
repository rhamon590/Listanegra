from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Colaborador
from models import db, Colaborador, ListaNegra, PreAdmissao, Usuario
from functools import wraps
import sqlite3

import pandas as pd
import os

import pandas as pd
from flask import request, redirect, flash

from werkzeug.utils import secure_filename

from models import db, Colaborador, ListaNegra

import pandas as pd
from flask import send_file
from io import BytesIO

app = Flask(__name__)
app.secret_key = '123456'

# =========================================
# CONFIG
# =========================================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///colaboradores.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================================
# CAMINHO BASE
# =========================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

# =========================================
# FLASK
# =========================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

app.secret_key = '123456'

# =========================================
# CONFIG
# =========================================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///colaboradores.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================================
# PASTAS
# =========================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    'uploads'
)

STATIC_FOLDER = os.path.join(
    BASE_DIR,
    'static'
)

FOTOS_FOLDER = os.path.join(
    STATIC_FOLDER,
    'fotos'
)

# =========================================
# CRIAR PASTAS
# =========================================

if not os.path.exists(UPLOAD_FOLDER):

    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(STATIC_FOLDER):

    os.makedirs(STATIC_FOLDER)

if not os.path.exists(FOTOS_FOLDER):

    os.makedirs(FOTOS_FOLDER)

print('UPLOAD_FOLDER:', UPLOAD_FOLDER)

print('FOTOS_FOLDER:', FOTOS_FOLDER)

# =========================================
# DATABASE
# =========================================

db.init_app(app)

with app.app_context():

    db.create_all()

    admin = Usuario.query.filter_by(
        usuario='Rhamon'
    ).first()

    if not admin:

        novo_admin = Usuario(
            usuario='Rhamon'
        )

        novo_admin.set_senha('369125')

        db.session.add(novo_admin)

        db.session.commit()

        print('USUÁRIO CRIADO')

# =========================================
# LOGIN
# =========================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario']

        senha = request.form['senha']

        user = Usuario.query.filter_by(
            usuario=usuario
        ).first()

        if user and user.check_senha(senha):

            session['usuario'] = user.usuario

            flash('Login realizado com sucesso!')

            return redirect('/')

        else:

            flash('Usuário ou senha inválidos')

            return redirect('/login')

    return render_template('login.html')

# =========================================
# PROTEGER ROTAS
# =========================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'usuario' not in session:

            return redirect('/login')

        return f(*args, **kwargs)

    return decorated_function
# =========================================
# LOGOUT
# =========================================

@app.route('/logout')
def logout():

    session.pop('usuario', None)

    flash('Logout realizado')

    return redirect('/login')
# =========================================
# HOME
# =========================================

@app.route('/')
@login_required
def index():

    # =====================================
    # VERIFICAR LOGIN
    # =====================================

    if 'usuario' not in session:

        return redirect('/login')

    colaboradores = Colaborador.query.all()

    return render_template(
        'index.html',
        colaboradores=colaboradores
    )

# =========================================
# CADASTRAR
# =========================================

@app.route('/novo', methods=['POST'])
@login_required
def novo():

    nome = request.form['nome']

    cpf = request.form['cpf']

    data_nascimento = request.form.get(
        'data_nascimento',
        ''
    )

    naturalidade = request.form.get(
        'naturalidade',
        ''
    )

    cep = request.form.get(
        'cep',
        ''
    )

    endereco = request.form.get(
        'endereco',
        ''
    )

    cidade = request.form.get(
        'cidade',
        ''
    )

    funcao = request.form['funcao']

    # LIMPAR CPF
    cpf = cpf.replace('.', '')
    cpf = cpf.replace('-', '')
    cpf = cpf.replace(' ', '')
    cpf = cpf.lstrip('0')

    # DUPLICADO
    existe = Colaborador.query.filter_by(
        cpf=cpf
    ).first()

    if existe:

        print('CPF já cadastrado')

        return redirect('/')

    colaborador = Colaborador(

        nome=nome,

        cpf=cpf,

        data_nascimento=data_nascimento,

        naturalidade=naturalidade,

        cep=cep,

        endereco=endereco,

        cidade=cidade,

        funcao=funcao

    )

    db.session.add(colaborador)

    db.session.commit()

    print('Colaborador cadastrado')

    return redirect('/')

# =========================================
# IMPORTAR EXCEL
# =========================================

# =========================================
# IMPORTAR EXCEL
# =========================================

# =========================================
# IMPORTAR EXCEL
# =========================================

@app.route('/importar', methods=['POST'])
@login_required
def importar():

    if 'arquivo' not in request.files:

        flash('Nenhum arquivo enviado', 'error')

        return redirect('/')

    arquivo = request.files['arquivo']

    if arquivo.filename == '':

        flash('Arquivo inválido', 'error')

        return redirect('/')

    nome_arquivo = secure_filename(
        arquivo.filename
    )

    caminho = os.path.join(
        UPLOAD_FOLDER,
        nome_arquivo
    )

    # =========================================
    # SALVAR EXCEL
    # =========================================

    try:

        arquivo.save(caminho)

    except Exception as erro:

        return f'Erro ao salvar Excel: {erro}'

    # =========================================
    # LER EXCEL
    # =========================================

    try:

        df = pd.read_excel(caminho)

    except Exception as erro:

        return f'Erro ao ler Excel: {erro}'

    total_importados = 0
    total_atualizados = 0

    # =========================================
    # LOOP
    # =========================================

    for _, row in df.iterrows():

        try:

            # =====================================
            # PEGAR DADOS
            # =====================================

            nome = str(
                row.get('Nome', '')
            ).strip()

            cpf = str(
                row.get('CPF', '')
            ).strip()

            telefone = str(
                row.get('Telefone', '')
            ).strip()

            data_nascimento = str(
                row.get('Data nascimento', '')
            ).strip()

            naturalidade = str(
                row.get('Naturalidade', '')
            ).strip()

            cep = str(
                row.get('CEP', '')
            ).strip()

            endereco = str(
                row.get('Endereço', '')
            ).strip()

            cidade = str(
                row.get('Cidade', '')
            ).strip()

            funcao = str(
                row.get('Função', '')
            ).strip()

            obra = str(
                row.get('Obra', '')
            ).strip()

            # =====================================
            # LIMPAR NAN
            # =====================================

            campos = [
                nome,
                cpf,
                telefone,
                data_nascimento,
                naturalidade,
                cep,
                endereco,
                cidade,
                funcao,
                obra
            ]

            campos = [
                '' if c == 'nan' else c
                for c in campos
            ]

            nome = campos[0]
            cpf = campos[1]
            telefone = campos[2]
            data_nascimento = campos[3]
            naturalidade = campos[4]
            cep = campos[5]
            endereco = campos[6]
            cidade = campos[7]
            funcao = campos[8]
            obra = campos[9]

            # =====================================
            # LIMPAR CPF
            # =====================================

            cpf = cpf.replace('.', '')
            cpf = cpf.replace('-', '')
            cpf = cpf.replace(' ', '')
            cpf = cpf.replace('/', '')
            cpf = cpf.lstrip('0')

            # =====================================
            # LIMPAR TELEFONE
            # =====================================

            telefone = telefone.replace('(', '')
            telefone = telefone.replace(')', '')
            telefone = telefone.replace('-', '')
            telefone = telefone.replace(' ', '')

            # =====================================
            # CPF VAZIO
            # =====================================

            if cpf == '':

                print('CPF vazio')

                continue

            # =====================================
            # VERIFICAR EXISTENTE
            # =====================================

            colaborador = Colaborador.query.filter_by(
                cpf=cpf
            ).first()

            # =====================================
            # ATUALIZAR
            # =====================================

            if colaborador:

                colaborador.nome = nome
                colaborador.telefone = telefone
                colaborador.data_nascimento = data_nascimento
                colaborador.naturalidade = naturalidade
                colaborador.cep = cep
                colaborador.endereco = endereco
                colaborador.cidade = cidade
                colaborador.funcao = funcao
                colaborador.obra = obra

                total_atualizados += 1

                print(f'Atualizado: {cpf}')

            # =====================================
            # NOVO
            # =====================================

            else:

                novo_colaborador = Colaborador(

                    nome=nome,

                    cpf=cpf,

                    telefone=telefone,

                    data_nascimento=data_nascimento,

                    naturalidade=naturalidade,

                    cep=cep,

                    endereco=endereco,

                    cidade=cidade,

                    funcao=funcao,

                    obra=obra
                )

                db.session.add(
                    novo_colaborador
                )

                total_importados += 1

                print(f'Importado: {cpf}')

        except Exception as erro:

            print('ERRO LINHA:', erro)

    # =========================================
    # SALVAR
    # =========================================

    db.session.commit()

    flash(
        f'''
        Importação concluída!
        Novos: {total_importados}
        Atualizados: {total_atualizados}
        ''',
        'success'
    )

    return redirect('/')

from flask import jsonify
from sqlalchemy import or_


def limpar_documento(valor):
    """Remove máscara de CPF/telefone e tira zeros à esquerda."""
    if valor is None:
        return ""
    valor = str(valor).strip()
    for ch in [".", "-", "/", " ", "(", ")"]:
        valor = valor.replace(ch, "")
    return valor.lstrip("0")


def buscar_na_lista_negra(nome="", cpf=""):
    nome = (nome or "").strip()
    cpf = limpar_documento(cpf)

    filtros = []

    if cpf:
        filtros.append(ListaNegra.cpf == cpf)

    if nome:
        filtros.append(ListaNegra.nome.ilike(f"%{nome}%"))

    if not filtros:
        return None

    return ListaNegra.query.filter(or_(*filtros)).first()


def sincronizar_lista_negra(colaborador, motivo="Restrição manual"):
    """Quando restringe na ficha normal, cria/atualiza também na Lista Negra."""
    if not colaborador:
        return None

    cpf = limpar_documento(colaborador.cpf)

    item = buscar_na_lista_negra(colaborador.nome, cpf)

    if not item:
        item = ListaNegra(
            nome=colaborador.nome,
            cpf=cpf,
            telefone=colaborador.telefone or "",
            obra=colaborador.obra or "",
            campo=colaborador.campo or "",
            motivo=motivo or colaborador.motivo or "Restrição manual",
            status="Restrito"
        )
        db.session.add(item)
    else:
        item.nome = colaborador.nome or item.nome
        item.cpf = cpf or item.cpf
        item.telefone = colaborador.telefone or item.telefone
        item.obra = colaborador.obra or item.obra
        item.campo = colaborador.campo or item.campo
        item.motivo = motivo or colaborador.motivo or item.motivo or "Restrição manual"
        item.status = "Restrito"

    return item


@app.route("/buscar_colaborador_pre_admissao")
@login_required
def buscar_colaborador_pre_admissao():

    termo = request.args.get("termo", "").strip()

    if not termo:
        return jsonify({"encontrado": False})

    cpf_limpo = limpar_documento(termo)

    colaborador = Colaborador.query.filter(
        or_(
            Colaborador.nome.ilike(f"%{termo}%"),
            Colaborador.cpf == cpf_limpo
        )
    ).first()

    item_lista = buscar_na_lista_negra(termo, cpf_limpo)

    if not colaborador and not item_lista:
        return jsonify({"encontrado": False})

    nome = colaborador.nome if colaborador else item_lista.nome
    cpf = colaborador.cpf if colaborador else item_lista.cpf
    telefone = colaborador.telefone if colaborador else item_lista.telefone
    funcao = colaborador.funcao if colaborador else ""
    obra = colaborador.obra if colaborador else item_lista.obra
    campo = colaborador.campo if colaborador else item_lista.campo
    motivo = item_lista.motivo if item_lista else colaborador.motivo

    return jsonify({
        "encontrado": True,
        "id": colaborador.id if colaborador else None,
        "nome": nome or "",
        "cpf": cpf or "",
        "telefone": telefone or "",
        "funcao": funcao or "",
        "obra": obra or "",
        "campo": campo or "",
        "foto": (colaborador.foto if colaborador and colaborador.foto else "https://cdn-icons-png.flaticon.com/512/149/149071.png"),
        "restrito": True if item_lista else bool(colaborador.restrito if colaborador else False),
        "na_lista_negra": True if item_lista else False,
        "motivo": motivo or "",
        "status": "Restrito" if item_lista else (colaborador.status or "Liberado"),
        "pre_admissao": colaborador.pre_admissao if colaborador else "Não cadastrado na lista normal",
        "origem": "lista_negra" if item_lista and not colaborador else "normal_e_lista_negra" if item_lista and colaborador else "normal"
    })


@app.route("/buscar_status_colaborador")
@login_required
def buscar_status_colaborador():

    termo = request.args.get("termo", "").strip()

    if not termo:
        return jsonify({"encontrado": False})

    cpf_limpo = limpar_documento(termo)

    colaborador = Colaborador.query.filter(
        or_(
            Colaborador.nome.ilike(f"%{termo}%"),
            Colaborador.cpf == cpf_limpo
        )
    ).first()

    item_lista = buscar_na_lista_negra(termo, cpf_limpo)

    if not colaborador and not item_lista:
        return jsonify({
            "encontrado": False,
            "mensagem": "Nenhum cadastro encontrado na lista normal nem na lista negra."
        })

    return jsonify({
        "encontrado": True,
        "nome": (colaborador.nome if colaborador else item_lista.nome) or "",
        "cpf": (colaborador.cpf if colaborador else item_lista.cpf) or "",
        "na_lista_normal": True if colaborador else False,
        "na_lista_negra": True if item_lista else False,
        "restrito": True if item_lista else bool(colaborador.restrito if colaborador else False),
        "motivo": (item_lista.motivo if item_lista else colaborador.motivo) or "",
        "url_ficha": url_for("ver_colaborador", id=colaborador.id) if colaborador else "",
        "url_lista_negra": url_for("lista_negra")
    })


@app.route("/exportar_pre_admissoes_excel")
@login_required
def exportar_pre_admissoes_excel():

    pre_admissoes = PreAdmissao.query.all()

    dados = []

    for p in pre_admissoes:
        dados.append({
            "Nome": p.nome,
            "CPF": p.cpf,
            "Telefone": p.telefone,
            "Função": p.funcao,
            "Campo": p.campo,
            "Obra": p.obra,
            "Status": p.status,
            "Isolado": "SIM" if p.isolado else "NÃO"
        })

    df = pd.DataFrame(dados)

    arquivo = BytesIO()

    with pd.ExcelWriter(
        arquivo,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Pré-Admissões"
        )

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="pre_admissoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
from flask import request, jsonify

@app.route('/excluir_varios', methods=['POST'])
def excluir_varios():

    dados = request.get_json()

    ids = dados.get('ids', [])

    for id_colab in ids:

        colaborador = Colaborador.query.get(id_colab)

        if colaborador:
            db.session.delete(colaborador)

    db.session.commit()

    return jsonify({
        'mensagem':'Colaboradores excluídos com sucesso'
    })
# =========================================
# IMPORTAR FOTOS
# =========================================

@app.route('/importar_fotos', methods=['POST'])
@login_required
def importar_fotos():

    arquivos = request.files.getlist('fotos')

    for arquivo in arquivos:

        if arquivo.filename == '':
            continue

        nome_arquivo = secure_filename(
            arquivo.filename
        )

        caminho = os.path.join(
            FOTOS_FOLDER,
            nome_arquivo
        )

        try:

            arquivo.save(caminho)

        except Exception as erro:

            print('Erro salvar foto:', erro)

            continue

        # CPF PELO NOME
        cpf = nome_arquivo.replace('.jpg', '')
        cpf = cpf.replace('.png', '')
        cpf = cpf.replace('.jpeg', '')

        cpf = cpf.replace('.', '')
        cpf = cpf.replace('-', '')
        cpf = cpf.replace(' ', '')
        cpf = cpf.lstrip('0')

        colaborador = Colaborador.query.filter_by(
            cpf=cpf
        ).first()

        if colaborador:

            colaborador.foto = (
                f'/static/fotos/{nome_arquivo}'
            )

            db.session.commit()

            print(f'Foto vinculada: {cpf}')

        else:

            print(f'CPF não encontrado: {cpf}')

    return redirect('/')

# =========================================
# RESTRINGIR
# =========================================

@app.route('/restringir/<int:id>')
@login_required
def restringir(id):

    colaborador = Colaborador.query.get(id)

    if colaborador:

        colaborador.restrito = True
        colaborador.motivo = 'Restrição manual'

        sincronizar_lista_negra(
            colaborador,
            colaborador.motivo
        )

        db.session.commit()

        flash('Colaborador restrito e enviado para a Lista Negra!', 'success')

    return redirect('/')

# =========================================
# LIBERAR
# =========================================

@app.route('/liberar/<int:id>')
@login_required
def liberar(id):

    colaborador = Colaborador.query.get(id)

    if colaborador:

        colaborador.restrito = False

        colaborador.motivo = ''

        db.session.commit()

    return redirect('/')

# =========================================
# VER COLABORADOR
# =========================================

@app.route('/colaborador/<int:id>')
@login_required
def ver_colaborador(id):

    colaborador = Colaborador.query.get(id)

    if not colaborador:

        return 'Colaborador não encontrado'

    return render_template(
        'colaborador.html',
        c=colaborador
    )

@app.route('/nova_restricao', methods=['GET', 'POST'])
@login_required
def nova_restricao():

    if request.method == 'POST':

        cpf = limpar_documento(request.form.get('cpf'))
        nome = request.form.get('nome', '').strip()
        obra = request.form.get('obra', '').strip()
        motivo = request.form.get('motivo', '').strip() or 'Restrição manual'

        colaborador = None

        if cpf:
            colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        if not colaborador and nome:
            colaborador = Colaborador.query.filter(
                Colaborador.nome.ilike(f"%{nome}%")
            ).first()

        if colaborador:
            colaborador.restrito = True
            colaborador.motivo = motivo
            if obra:
                colaborador.obra = obra
        else:
            colaborador = Colaborador(
                nome=nome,
                cpf=cpf or f"SEMCPF{ListaNegra.query.count() + 1}",
                obra=obra,
                restrito=True,
                motivo=motivo
            )
            db.session.add(colaborador)
            db.session.flush()

        item = sincronizar_lista_negra(colaborador, motivo)
        if item and obra:
            item.obra = obra

        db.session.commit()

        flash('Restrição salva e sincronizada com a Lista Negra!', 'success')

        return redirect(url_for('lista_negra'))

    return render_template('nova_restricao.html')


@app.route("/liberar_lista/<int:id>")
@login_required
def liberar_lista(id):

    item = ListaNegra.query.get(id)

    if item:

        if item.cpf:
            colaborador = Colaborador.query.filter_by(cpf=item.cpf).first()
        else:
            colaborador = Colaborador.query.filter(
                Colaborador.nome.ilike(f"%{item.nome}%")
            ).first()

        if colaborador:
            colaborador.restrito = False
            colaborador.motivo = ""

        db.session.delete(item)
        db.session.commit()

        flash('Colaborador liberado e removido da Lista Negra!', 'success')

    return redirect("/lista_negra")


@app.route('/lista_negra')
@login_required
def lista_negra():

    lista_negra = ListaNegra.query.all()

    return render_template(
        'lista_negra.html',
        lista_negra=lista_negra
    )

@app.route('/importar_lista_negra', methods=['POST'])
@login_required
def importar_lista_negra():

    arquivo = request.files['arquivo_excel']

    if arquivo:

        df = pd.read_excel(arquivo)
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():

            nome = str(row.get('Nome', '')).strip()
            obra = str(row.get('Obra', '')).strip()
            cpf = limpar_documento(row.get('CPF', ''))
            motivo = str(row.get('Motivo', '')).strip() or 'Restrição importada'

            if not nome:
                continue

            item = buscar_na_lista_negra(nome, cpf)

            if not item:
                item = ListaNegra(
                    nome=nome,
                    obra=obra,
                    cpf=cpf,
                    motivo=motivo,
                    status='Restrito'
                )
                db.session.add(item)
            else:
                item.nome = nome
                item.obra = obra or item.obra
                item.cpf = cpf or item.cpf
                item.motivo = motivo
                item.status = 'Restrito'

            colaborador = None
            if cpf:
                colaborador = Colaborador.query.filter_by(cpf=cpf).first()
            if not colaborador:
                colaborador = Colaborador.query.filter(
                    Colaborador.nome.ilike(f"%{nome}%")
                ).first()

            if colaborador:
                colaborador.restrito = True
                colaborador.motivo = motivo

        db.session.commit()

        flash('Lista negra importada e sincronizada com colaboradores!', 'success')

    return redirect('/lista_negra')


@app.route("/admissao", methods=["GET", "POST"])
@login_required
def admissao():

    if request.method == "POST":

        nome = request.form.get("nome")

        cpf = request.form.get("cpf")

        campo = request.form.get("campo")

        telefone = request.form.get("telefone")

        funcao = request.form.get("funcao")

        obra = request.form.get("obra")

        status = request.form.get("status") or "Aguardando"

        data_admissao = request.form.get(
            "data_admissao"
        )

        isolado = True if request.form.get(
            "campo_isolado"
        ) else False

        # =====================================
        # LIMPAR CPF
        # =====================================

        cpf = cpf.replace(".", "")
        cpf = cpf.replace("-", "")
        cpf = cpf.replace("/", "")
        cpf = cpf.replace(" ", "")
        cpf = cpf.lstrip("0")

        # =====================================
        # CONSULTAR LISTA NEGRA
        # =====================================

        lista_negra = buscar_na_lista_negra(nome, cpf)

        if lista_negra:

            flash(
                f"⚠️ {nome} ESTÁ NA LISTA NEGRA!",
                "danger"
            )

            return redirect(
                url_for("admissao")
            )

        # =====================================
        # SALVAR PRÉ-ADMISSÃO
        # =====================================

        nova_pre = PreAdmissao(

            nome=nome,

            cpf=cpf,

            telefone=telefone,

            funcao=funcao,

            campo=campo,

            obra=obra,

            data_admissao=data_admissao,

            isolado=isolado,

            status=status
        )

        db.session.add(nova_pre)

        db.session.commit()

        flash(
            "✅ Pré-admissão salva!",
            "success"
        )

        return redirect(
            url_for("admissao")
        )

    filtro_status = request.args.get("status", "Todos").strip()

    consulta = PreAdmissao.query

    if filtro_status and filtro_status != "Todos":
        consulta = consulta.filter(
            PreAdmissao.status == filtro_status
        )

    pre_admissoes = consulta.order_by(
        PreAdmissao.id.desc()
    ).all()

    return render_template(
        "admissao.html",
        pre_admissoes=pre_admissoes,
        filtro_status=filtro_status
    )


@app.route('/zerar_pre_admissao')
@login_required
def zerar_pre_admissao():

    try:

        PreAdmissao.query.delete()

        db.session.commit()

        return 'Tabela de pré-admissão limpa com sucesso'

    except Exception as e:

        db.session.rollback()

        return str(e)

from models import db, PreAdmissao

@app.route('/limpar-pre-admissoes')
@login_required
def limpar_pre_admissoes():

    PreAdmissao.query.delete()

    db.session.commit()

    return 'Pré-admissões apagadas com sucesso'
# =========================================
# APROVAR ADMISSÃO
# =========================================

@app.route("/aprovar_admissao/<int:id>")
@login_required
def aprovar_admissao(id):

    colaborador = Colaborador.query.get(id)

    if colaborador:

        colaborador.pre_admissao = "Liberado"

        db.session.commit()

        flash(
            "✅ Pré-admissão aprovada!",
            "success"
        )

    return redirect(url_for("admissao"))


# =========================================
# REPROVAR ADMISSÃO
# =========================================

@app.route("/reprovar_admissao/<int:id>")
@login_required
def reprovar_admissao(id):

    colaborador = Colaborador.query.get(id)

    if colaborador:

        colaborador.pre_admissao = "Reprovado"

        db.session.commit()

        flash(
            "❌ Pré-admissão reprovada!",
            "danger"
        )

    return redirect(url_for("admissao"))

@app.route("/alterar_status_pre_admissao/<int:id>/<novo_status>")
@login_required
def alterar_status_pre_admissao(id, novo_status):

    status_map = {
        "aguardando": "Aguardando",
        "admitido": "Admitido",
        "recusado": "Recusado"
    }

    if novo_status not in status_map:
        flash("Status inválido.", "danger")
        return redirect(url_for("admissao"))

    pre = PreAdmissao.query.get(id)

    if not pre:
        flash("Pré-admissão não encontrada.", "danger")
        return redirect(url_for("admissao"))

    pre.status = status_map[novo_status]

    db.session.commit()

    flash("Status atualizado com sucesso!", "success")
    return redirect(url_for("admissao"))
# =========================================
# START
# =========================================

if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
