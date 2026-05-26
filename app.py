from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Colaborador
from models import db, Colaborador, ListaNegra, PreAdmissao, Usuario
from functools import wraps

import pandas as pd
import os

import pandas as pd
from flask import request, redirect, flash

from werkzeug.utils import secure_filename

from models import db, Colaborador, ListaNegra

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

        db.session.commit()

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

        cpf = request.form.get('cpf')
        nome = request.form.get('nome')
        motivo = request.form.get('motivo')

        colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        # ==========================================
        # SE JÁ EXISTIR
        # ==========================================

        if colaborador:

            colaborador.restrito = True
            colaborador.motivo = motivo

        # ==========================================
        # SE NÃO EXISTIR
        # ==========================================

        else:

            colaborador = Colaborador(
                nome=nome,
                cpf=cpf,
                restrito=True,
                motivo=motivo
            )

            db.session.add(colaborador)

        db.session.commit()

        flash('Restrição salva com sucesso!', 'success')

        return redirect(url_for('index'))

    return render_template('nova_restricao.html')

@app.route("/liberar_lista/<int:id>")
@login_required
def liberar_lista(id):

    colaborador = Colaborador.query.get(id)

    if colaborador:

        colaborador.restrito = False

        db.session.commit()

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

        import pandas as pd

        df = pd.read_excel(arquivo)

        # remove espaços escondidos
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():

            novo = ListaNegra(

                nome=str(row.get('Nome', '')),
                obra=str(row.get('Obra', '')),
                cpf='',
                motivo=str(row.get('Motivo', '')),
                status='Restrito'

            )

            db.session.add(novo)

        db.session.commit()

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

        status = request.form.get("status")

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

        lista_negra = ListaNegra.query.filter(
            ListaNegra.nome.ilike(nome)
        ).first()

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

    pre_admissoes = PreAdmissao.query.order_by(
        PreAdmissao.id.desc()
    ).all()

    return render_template(
        "admissao.html",
        pre_admissoes=pre_admissoes
    )

from models import db, PreAdmissao

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
# =========================================
# START
# =========================================

if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )