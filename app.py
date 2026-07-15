from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_file,
)
from functools import wraps
from io import BytesIO
from datetime import datetime
import os
import re

import pandas as pd
from sqlalchemy import or_, text
from werkzeug.utils import secure_filename

from models import db, Colaborador, ListaNegra, PreAdmissao, Usuario


# =========================================================
# CONFIGURAÇÃO BASE
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

app.secret_key = os.environ.get("SECRET_KEY", "123456")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///colaboradores.db",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
FOTOS_FOLDER = os.path.join(STATIC_FOLDER, "fotos")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(FOTOS_FOLDER, exist_ok=True)

db.init_app(app)


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def limpar_documento(valor):
    """Remove máscara de CPF/telefone e tira zeros à esquerda."""
    if valor is None:
        return ""

    valor = str(valor).strip()

    if valor.lower() in ["nan", "none", "nat"]:
        return ""

    valor = re.sub(r"\D", "", valor)
    return valor.lstrip("0")


def limpar_texto(valor):
    """Trata valores vazios vindos do Excel."""
    if valor is None:
        return ""

    valor = str(valor).strip()

    if valor.lower() in ["nan", "none", "nat"]:
        return ""

    return valor


def limpar_data(valor):
    """Converte datas do Excel para formato dd/mm/aaaa quando possível."""
    if valor is None:
        return ""

    if str(valor).lower() in ["nan", "none", "nat", ""]:
        return ""

    try:
        data = pd.to_datetime(valor, errors="coerce")
        if pd.isna(data):
            return limpar_texto(valor)
        return data.strftime("%d/%m/%Y")
    except Exception:
        return limpar_texto(valor)


def set_attr_if_exists(obj, campo, valor):
    """Só grava o campo se ele existir no model."""
    if hasattr(obj, campo):
        setattr(obj, campo, valor)


def get_attr(obj, campo, padrao=""):
    """Lê atributo com segurança."""
    return getattr(obj, campo, padrao) if obj else padrao


def normalizar_colunas(df):
    """Remove espaços das colunas e aceita variações simples."""
    df.columns = [str(c).strip() for c in df.columns]

    mapa = {
        "Data de nascimento": "Data nascimento",
        "Nascimento": "Data nascimento",
        "Data Nascimento": "Data nascimento",
        "Endereco": "Endereço",
        "Funcao": "Função",
        "Telefone/WhatsApp": "Telefone",
        "Whatsapp": "Telefone",
        "WhatsApp": "Telefone",
        "Pre admissão": "Pré-admissão",
        "Pre-admissão": "Pré-admissão",
        "Pre Admissão": "Pré-admissão",
        "Pre-Admissão": "Pré-admissão",
        "Data admissão": "Data Admissão",
        "Data de admissão": "Data Admissão",
        "Data Admissao": "Data Admissão",
    }

    df.rename(columns=mapa, inplace=True)
    return df


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

    cpf = limpar_documento(get_attr(colaborador, "cpf"))
    item = buscar_na_lista_negra(get_attr(colaborador, "nome"), cpf)

    if not item:
        item = ListaNegra(
            nome=get_attr(colaborador, "nome"),
            cpf=cpf,
            motivo=motivo or get_attr(colaborador, "motivo") or "Restrição manual",
            status="Restrito",
        )
        db.session.add(item)

    item.nome = get_attr(colaborador, "nome") or get_attr(item, "nome")
    item.cpf = cpf or get_attr(item, "cpf")
    item.motivo = motivo or get_attr(colaborador, "motivo") or get_attr(item, "motivo") or "Restrição manual"
    item.status = "Restrito"

    set_attr_if_exists(item, "telefone", get_attr(colaborador, "telefone"))
    set_attr_if_exists(item, "obra", get_attr(colaborador, "obra"))
    set_attr_if_exists(item, "campo", get_attr(colaborador, "campo"))

    return item


def criar_admin_padrao():
    """Cria usuário padrão caso ainda não exista."""
    usuario_admin = os.environ.get("ADMIN_USER", "Rhamon")
    senha_admin = os.environ.get("ADMIN_PASSWORD", "369125")

    admin = Usuario.query.filter_by(usuario=usuario_admin).first()

    if not admin:
        novo_admin = Usuario(usuario=usuario_admin)
        novo_admin.set_senha(senha_admin)

        db.session.add(novo_admin)
        db.session.commit()

        print("USUÁRIO PADRÃO CRIADO")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# BANCO DE DADOS
# =========================================================

def criar_indices_desempenho():
    """Cria índices também em bancos que já existiam antes da otimização."""
    comandos = [
        "CREATE INDEX IF NOT EXISTS ix_colaborador_nome ON colaborador (nome)",
        "CREATE INDEX IF NOT EXISTS ix_colaborador_cpf ON colaborador (cpf)",
        "CREATE INDEX IF NOT EXISTS ix_colaborador_obra ON colaborador (obra)",
        "CREATE INDEX IF NOT EXISTS ix_colaborador_funcao ON colaborador (funcao)",
        "CREATE INDEX IF NOT EXISTS ix_colaborador_restrito ON colaborador (restrito)",
        "CREATE INDEX IF NOT EXISTS ix_lista_negra_nome ON lista_negra (nome)",
        "CREATE INDEX IF NOT EXISTS ix_lista_negra_cpf ON lista_negra (cpf)",
        "CREATE INDEX IF NOT EXISTS ix_pre_admissao_cpf ON pre_admissao (cpf)",
    ]

    try:
        for comando in comandos:
            db.session.execute(text(comando))
        db.session.commit()
    except Exception as erro:
        db.session.rollback()
        print(f"Aviso ao criar índices: {erro}")


with app.app_context():
    db.create_all()
    criar_indices_desempenho()
    criar_admin_padrao()


# =========================================================
# LOGIN / LOGOUT
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        user = Usuario.query.filter_by(usuario=usuario).first()

        if user and user.check_senha(senha):
            session["usuario"] = user.usuario
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))

        flash("Usuário ou senha inválidos.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    flash("Logout realizado.", "success")
    return redirect(url_for("login"))


# =========================================================
# HOME / COLABORADORES
# =========================================================

@app.route("/")
@login_required
def index():
    pagina = request.args.get("page", 1, type=int)
    busca = request.args.get("busca", "").strip()
    obra = request.args.get("obra", "").strip()
    funcao = request.args.get("funcao", "").strip()
    por_pagina = 30

    consulta = Colaborador.query

    if busca:
        cpf_limpo = limpar_documento(busca)
        filtros_busca = [Colaborador.nome.ilike(f"%{busca}%")]
        if cpf_limpo:
            filtros_busca.append(Colaborador.cpf == cpf_limpo)
        consulta = consulta.filter(or_(*filtros_busca))

    if obra:
        consulta = consulta.filter(Colaborador.obra == obra)

    if funcao:
        consulta = consulta.filter(Colaborador.funcao == funcao)

    colaboradores = (
        consulta
        .order_by(Colaborador.nome.asc())
        .paginate(page=pagina, per_page=por_pagina, error_out=False)
    )

    total_colaboradores = Colaborador.query.count()
    total_liberados = Colaborador.query.filter(Colaborador.restrito.is_(False)).count()
    total_restritos = Colaborador.query.filter(Colaborador.restrito.is_(True)).count()

    obras = [
        item[0] for item in
        db.session.query(Colaborador.obra)
        .filter(Colaborador.obra.isnot(None), Colaborador.obra != "")
        .distinct()
        .order_by(Colaborador.obra.asc())
        .all()
    ]

    funcoes = [
        item[0] for item in
        db.session.query(Colaborador.funcao)
        .filter(Colaborador.funcao.isnot(None), Colaborador.funcao != "")
        .distinct()
        .order_by(Colaborador.funcao.asc())
        .all()
    ]

    return render_template(
        "index.html",
        colaboradores=colaboradores,
        total_colaboradores=total_colaboradores,
        total_liberados=total_liberados,
        total_restritos=total_restritos,
        busca=busca,
        obra_selecionada=obra,
        funcao_selecionada=funcao,
        obras=obras,
        funcoes=funcoes,
    )


@app.route("/novo", methods=["POST"])
@login_required
def novo():
    nome = request.form.get("nome", "").strip()
    cpf = limpar_documento(request.form.get("cpf", ""))
    telefone = limpar_documento(request.form.get("telefone", ""))

    if not nome or not cpf:
        flash("Nome e CPF são obrigatórios.", "danger")
        return redirect(url_for("index"))

    existe = Colaborador.query.filter_by(cpf=cpf).first()

    if existe:
        flash("CPF já cadastrado.", "warning")
        return redirect(url_for("index"))

    colaborador = Colaborador(
        nome=nome,
        cpf=cpf,
        data_nascimento=request.form.get("data_nascimento", ""),
        naturalidade=request.form.get("naturalidade", ""),
        cep=request.form.get("cep", ""),
        endereco=request.form.get("endereco", ""),
        cidade=request.form.get("cidade", ""),
        funcao=request.form.get("funcao", ""),
    )

    set_attr_if_exists(colaborador, "telefone", telefone)
    set_attr_if_exists(colaborador, "obra", request.form.get("obra", ""))
    set_attr_if_exists(colaborador, "estado", request.form.get("estado", ""))
    set_attr_if_exists(colaborador, "campo", request.form.get("campo", ""))
    set_attr_if_exists(colaborador, "data_admissao", request.form.get("data_admissao", ""))

    db.session.add(colaborador)
    db.session.commit()

    flash("Colaborador cadastrado com sucesso!", "success")
    return redirect(url_for("index"))


@app.route("/colaborador/<int:id>")
@login_required
def ver_colaborador(id):
    colaborador = Colaborador.query.get(id)

    if not colaborador:
        flash("Colaborador não encontrado.", "danger")
        return redirect(url_for("index"))

    return render_template("colaborador.html", c=colaborador)


@app.route("/excluir_varios", methods=["POST"])
@login_required
def excluir_varios():
    dados = request.get_json(silent=True) or {}
    ids = dados.get("ids", [])

    ids_validos = []
    for id_colab in ids:
        try:
            ids_validos.append(int(id_colab))
        except (TypeError, ValueError):
            continue

    if ids_validos:
        Colaborador.query.filter(Colaborador.id.in_(ids_validos)).delete(
            synchronize_session=False
        )

    db.session.commit()

    return jsonify({"mensagem": "Colaboradores excluídos com sucesso."})


# =========================================================
# IMPORTAR / EXPORTAR COLABORADORES
# =========================================================

@app.route("/importar", methods=["POST"])
@login_required
def importar():
    if "arquivo" not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for("index"))

    arquivo = request.files["arquivo"]

    if arquivo.filename == "":
        flash("Arquivo inválido.", "danger")
        return redirect(url_for("index"))

    nome_arquivo = secure_filename(arquivo.filename)
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)

    try:
        arquivo.save(caminho)
        df = pd.read_excel(caminho)
        df = normalizar_colunas(df)
    except Exception as erro:
        flash(f"Erro ao ler Excel: {erro}", "danger")
        return redirect(url_for("index"))

    total_importados = 0
    total_atualizados = 0
    total_ignorados = 0

    for _, row in df.iterrows():
        nome = limpar_texto(row.get("Nome", ""))
        cpf = limpar_documento(row.get("CPF", ""))

        if not nome or not cpf:
            total_ignorados += 1
            continue

        telefone = limpar_documento(row.get("Telefone", ""))
        data_nascimento = limpar_data(row.get("Data nascimento", ""))
        naturalidade = limpar_texto(row.get("Naturalidade", ""))
        cep = limpar_documento(row.get("CEP", ""))
        endereco = limpar_texto(row.get("Endereço", ""))
        cidade = limpar_texto(row.get("Cidade", ""))
        estado = limpar_texto(row.get("Estado", ""))
        funcao = limpar_texto(row.get("Função", ""))
        obra = limpar_texto(row.get("Obra", ""))
        campo = limpar_texto(row.get("Campo", ""))
        data_admissao = limpar_data(row.get("Data Admissão", ""))
        status = limpar_texto(row.get("Status", "")) or "Liberado"
        pre_admissao = limpar_texto(row.get("Pré-admissão", "")) or "Em análise"
        motivo = limpar_texto(row.get("Motivo da Restrição", ""))
        foto = limpar_texto(row.get("Foto", ""))

        colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        if colaborador:
            total_atualizados += 1
        else:
            colaborador = Colaborador(cpf=cpf)
            db.session.add(colaborador)
            total_importados += 1

        colaborador.nome = nome
        colaborador.data_nascimento = data_nascimento
        colaborador.naturalidade = naturalidade
        colaborador.cep = cep
        colaborador.endereco = endereco
        colaborador.cidade = cidade
        colaborador.funcao = funcao

        set_attr_if_exists(colaborador, "telefone", telefone)
        set_attr_if_exists(colaborador, "estado", estado)
        set_attr_if_exists(colaborador, "obra", obra)
        set_attr_if_exists(colaborador, "campo", campo)
        set_attr_if_exists(colaborador, "data_admissao", data_admissao)
        set_attr_if_exists(colaborador, "status", status)
        set_attr_if_exists(colaborador, "pre_admissao", pre_admissao)
        set_attr_if_exists(colaborador, "motivo", motivo)
        set_attr_if_exists(colaborador, "foto", foto)

        if status.lower() in ["restrito", "bloqueado", "lista negra"]:
            set_attr_if_exists(colaborador, "restrito", True)
            sincronizar_lista_negra(colaborador, motivo or "Restrição importada")

    db.session.commit()

    flash(
        f"Importação concluída! Novos: {total_importados} | Atualizados: {total_atualizados} | Ignorados: {total_ignorados}",
        "success",
    )

    return redirect(url_for("index"))


@app.route("/exportar_colaboradores_excel")
@login_required
def exportar_colaboradores_excel():
    colaboradores = Colaborador.query.order_by(Colaborador.nome.asc()).all()

    dados = []

    for c in colaboradores:
        dados.append(
            {
                "Nome": get_attr(c, "nome"),
                "CPF": get_attr(c, "cpf"),
                "Telefone": get_attr(c, "telefone"),
                "Data nascimento": get_attr(c, "data_nascimento"),
                "Naturalidade": get_attr(c, "naturalidade"),
                "CEP": get_attr(c, "cep"),
                "Endereço": get_attr(c, "endereco"),
                "Cidade": get_attr(c, "cidade"),
                "Estado": get_attr(c, "estado"),
                "Função": get_attr(c, "funcao"),
                "Obra": get_attr(c, "obra"),
                "Campo": get_attr(c, "campo"),
                "Data Admissão": get_attr(c, "data_admissao"),
                "Status": get_attr(c, "status", "Liberado"),
                "Pré-admissão": get_attr(c, "pre_admissao", "Em análise"),
                "Restrito": "SIM" if get_attr(c, "restrito", False) else "NÃO",
                "Motivo da Restrição": get_attr(c, "motivo"),
                "Foto": get_attr(c, "foto"),
                "Data Cadastro": get_attr(c, "data_cadastro"),
            }
        )

    df = pd.DataFrame(dados)

    arquivo = BytesIO()

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Colaboradores")

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="colaboradores.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/modelo_colaboradores_excel")
@login_required
def modelo_colaboradores_excel():
    colunas = [
        "Nome",
        "CPF",
        "Telefone",
        "Data nascimento",
        "Naturalidade",
        "CEP",
        "Endereço",
        "Cidade",
        "Estado",
        "Função",
        "Obra",
        "Campo",
        "Data Admissão",
        "Status",
        "Pré-admissão",
        "Motivo da Restrição",
        "Foto",
    ]

    exemplo = [
        {
            "Nome": "JOÃO SILVA",
            "CPF": "12345678901",
            "Telefone": "16999999999",
            "Data nascimento": "10/05/1995",
            "Naturalidade": "SERTÃOZINHO/SP",
            "CEP": "14160000",
            "Endereço": "RUA A, 100",
            "Cidade": "SERTÃOZINHO",
            "Estado": "SP",
            "Função": "SOLDADOR",
            "Obra": "CERRADINHO",
            "Campo": "CAMPO 01",
            "Data Admissão": "25/06/2026",
            "Status": "Liberado",
            "Pré-admissão": "Em análise",
            "Motivo da Restrição": "",
            "Foto": "",
        }
    ]

    df = pd.DataFrame(exemplo, columns=colunas)

    arquivo = BytesIO()

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Modelo")

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="modelo_importacao_colaboradores.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =========================================================
# IMPORTAR FOTOS
# =========================================================

@app.route("/importar_fotos", methods=["POST"])
@login_required
def importar_fotos():
    arquivos = request.files.getlist("fotos")
    vinculadas = 0
    nao_encontradas = 0

    for arquivo in arquivos:
        if arquivo.filename == "":
            continue

        nome_arquivo = secure_filename(arquivo.filename)
        caminho = os.path.join(FOTOS_FOLDER, nome_arquivo)

        try:
            arquivo.save(caminho)
        except Exception as erro:
            print("Erro salvar foto:", erro)
            continue

        cpf = limpar_documento(os.path.splitext(nome_arquivo)[0])

        colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        if colaborador:
            set_attr_if_exists(colaborador, "foto", f"/static/fotos/{nome_arquivo}")
            vinculadas += 1
        else:
            nao_encontradas += 1
            print(f"CPF não encontrado para foto: {cpf}")

    db.session.commit()

    flash(f"Fotos processadas! Vinculadas: {vinculadas} | Não encontradas: {nao_encontradas}", "success")
    return redirect(url_for("index"))


# =========================================================
# RESTRIÇÃO / LISTA NEGRA
# =========================================================

@app.route("/restringir/<int:id>")
@login_required
def restringir(id):
    colaborador = Colaborador.query.get(id)

    if colaborador:
        set_attr_if_exists(colaborador, "restrito", True)
        set_attr_if_exists(colaborador, "motivo", "Restrição manual")

        sincronizar_lista_negra(colaborador, "Restrição manual")
        db.session.commit()

        flash("Colaborador restrito e enviado para a Lista Negra!", "success")

    return redirect(url_for("index"))


@app.route("/liberar/<int:id>")
@login_required
def liberar(id):
    colaborador = Colaborador.query.get(id)

    if colaborador:
        set_attr_if_exists(colaborador, "restrito", False)
        set_attr_if_exists(colaborador, "motivo", "")
        db.session.commit()

        flash("Colaborador liberado.", "success")

    return redirect(url_for("index"))


@app.route("/nova_restricao", methods=["GET", "POST"])
@login_required
def nova_restricao():
    if request.method == "POST":
        cpf = limpar_documento(request.form.get("cpf"))
        nome = request.form.get("nome", "").strip()
        telefone = limpar_documento(request.form.get("telefone"))
        obra = request.form.get("obra", "").strip()
        campo = request.form.get("campo", "").strip()
        motivo = request.form.get("motivo", "").strip() or "Restrição manual"

        if not nome and not cpf:
            flash("Informe nome ou CPF.", "danger")
            return redirect(url_for("nova_restricao"))

        colaborador = None

        if cpf:
            colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        if not colaborador and nome:
            colaborador = Colaborador.query.filter(
                Colaborador.nome.ilike(f"%{nome}%")
            ).first()

        if not colaborador:
            colaborador = Colaborador(
                nome=nome,
                cpf=cpf or f"SEMCPF{ListaNegra.query.count() + 1}",
                obra=obra,
                restrito=True,
                motivo=motivo,
            )
            db.session.add(colaborador)
            db.session.flush()

        colaborador.nome = nome or get_attr(colaborador, "nome")
        set_attr_if_exists(colaborador, "cpf", cpf or get_attr(colaborador, "cpf"))
        set_attr_if_exists(colaborador, "telefone", telefone)
        set_attr_if_exists(colaborador, "obra", obra)
        set_attr_if_exists(colaborador, "campo", campo)
        set_attr_if_exists(colaborador, "restrito", True)
        set_attr_if_exists(colaborador, "motivo", motivo)

        item = sincronizar_lista_negra(colaborador, motivo)
        set_attr_if_exists(item, "telefone", telefone)
        set_attr_if_exists(item, "obra", obra)
        set_attr_if_exists(item, "campo", campo)

        db.session.commit()

        flash("Restrição salva e sincronizada com a Lista Negra!", "success")
        return redirect(url_for("lista_negra"))

    return render_template("nova_restricao.html")


@app.route("/lista_negra")
@login_required
def lista_negra():
    lista = ListaNegra.query.order_by(ListaNegra.nome.asc()).all()

    return render_template(
        "lista_negra.html",
        lista_negra=lista,
    )


@app.route("/liberar_lista/<int:id>")
@login_required
def liberar_lista(id):
    item = ListaNegra.query.get(id)

    if item:
        colaborador = None

        if get_attr(item, "cpf"):
            colaborador = Colaborador.query.filter_by(cpf=item.cpf).first()

        if not colaborador and get_attr(item, "nome"):
            colaborador = Colaborador.query.filter(
                Colaborador.nome.ilike(f"%{item.nome}%")
            ).first()

        if colaborador:
            set_attr_if_exists(colaborador, "restrito", False)
            set_attr_if_exists(colaborador, "motivo", "")

        db.session.delete(item)
        db.session.commit()

        flash("Colaborador liberado e removido da Lista Negra!", "success")

    return redirect(url_for("lista_negra"))


@app.route("/importar_lista_negra", methods=["POST"])
@login_required
def importar_lista_negra():
    if "arquivo_excel" not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for("lista_negra"))

    arquivo = request.files["arquivo_excel"]

    try:
        df = pd.read_excel(arquivo)
        df = normalizar_colunas(df)
    except Exception as erro:
        flash(f"Erro ao ler Excel: {erro}", "danger")
        return redirect(url_for("lista_negra"))

    total = 0

    for _, row in df.iterrows():
        nome = limpar_texto(row.get("Nome", ""))
        cpf = limpar_documento(row.get("CPF", ""))
        telefone = limpar_documento(row.get("Telefone", ""))
        obra = limpar_texto(row.get("Obra", ""))
        campo = limpar_texto(row.get("Campo", ""))
        motivo = limpar_texto(row.get("Motivo", "")) or "Restrição importada"

        if not nome and not cpf:
            continue

        item = buscar_na_lista_negra(nome, cpf)

        if not item:
            item = ListaNegra(
                nome=nome,
                cpf=cpf,
                motivo=motivo,
                status="Restrito",
            )
            db.session.add(item)

        item.nome = nome or get_attr(item, "nome")
        item.cpf = cpf or get_attr(item, "cpf")
        item.motivo = motivo
        item.status = "Restrito"

        set_attr_if_exists(item, "telefone", telefone)
        set_attr_if_exists(item, "obra", obra)
        set_attr_if_exists(item, "campo", campo)

        colaborador = None

        if cpf:
            colaborador = Colaborador.query.filter_by(cpf=cpf).first()

        if not colaborador and nome:
            colaborador = Colaborador.query.filter(
                Colaborador.nome.ilike(f"%{nome}%")
            ).first()

        if colaborador:
            set_attr_if_exists(colaborador, "restrito", True)
            set_attr_if_exists(colaborador, "motivo", motivo)

        total += 1

    db.session.commit()

    flash(f"Lista negra importada e sincronizada! Registros: {total}", "success")
    return redirect(url_for("lista_negra"))


@app.route("/exportar_lista_negra_excel")
@login_required
def exportar_lista_negra_excel():
    lista = ListaNegra.query.order_by(ListaNegra.nome.asc()).all()

    dados = []

    for item in lista:
        dados.append(
            {
                "Nome": get_attr(item, "nome"),
                "CPF": get_attr(item, "cpf"),
                "Telefone": get_attr(item, "telefone"),
                "Obra": get_attr(item, "obra"),
                "Campo": get_attr(item, "campo"),
                "Motivo": get_attr(item, "motivo"),
                "Status": get_attr(item, "status", "Restrito"),
            }
        )

    df = pd.DataFrame(dados)

    arquivo = BytesIO()

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Lista Negra")

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="lista_negra.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =========================================================
# BUSCAS AJAX
# =========================================================

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
            Colaborador.cpf == cpf_limpo,
        )
    ).first()

    item_lista = buscar_na_lista_negra(termo, cpf_limpo)

    if not colaborador and not item_lista:
        return jsonify({"encontrado": False})

    nome = get_attr(colaborador, "nome") or get_attr(item_lista, "nome")
    cpf = get_attr(colaborador, "cpf") or get_attr(item_lista, "cpf")

    return jsonify(
        {
            "encontrado": True,
            "id": get_attr(colaborador, "id", None),
            "nome": nome or "",
            "cpf": cpf or "",
            "telefone": get_attr(colaborador, "telefone") or get_attr(item_lista, "telefone"),
            "funcao": get_attr(colaborador, "funcao"),
            "obra": get_attr(colaborador, "obra") or get_attr(item_lista, "obra"),
            "campo": get_attr(colaborador, "campo") or get_attr(item_lista, "campo"),
            "foto": get_attr(colaborador, "foto", "https://cdn-icons-png.flaticon.com/512/149/149071.png"),
            "restrito": True if item_lista else bool(get_attr(colaborador, "restrito", False)),
            "na_lista_negra": True if item_lista else False,
            "motivo": get_attr(item_lista, "motivo") or get_attr(colaborador, "motivo"),
            "status": "Restrito" if item_lista else get_attr(colaborador, "status", "Liberado"),
            "pre_admissao": get_attr(colaborador, "pre_admissao", "Não cadastrado na lista normal"),
            "origem": "lista_negra" if item_lista and not colaborador else "normal_e_lista_negra" if item_lista and colaborador else "normal",
        }
    )


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
            Colaborador.cpf == cpf_limpo,
        )
    ).first()

    item_lista = buscar_na_lista_negra(termo, cpf_limpo)

    if not colaborador and not item_lista:
        return jsonify(
            {
                "encontrado": False,
                "mensagem": "Nenhum cadastro encontrado na lista normal nem na lista negra.",
            }
        )

    return jsonify(
        {
            "encontrado": True,
            "nome": get_attr(colaborador, "nome") or get_attr(item_lista, "nome"),
            "cpf": get_attr(colaborador, "cpf") or get_attr(item_lista, "cpf"),
            "na_lista_normal": True if colaborador else False,
            "na_lista_negra": True if item_lista else False,
            "restrito": True if item_lista else bool(get_attr(colaborador, "restrito", False)),
            "motivo": get_attr(item_lista, "motivo") or get_attr(colaborador, "motivo"),
            "url_ficha": url_for("ver_colaborador", id=colaborador.id) if colaborador else "",
            "url_lista_negra": url_for("lista_negra"),
        }
    )


# =========================================================
# PRÉ-ADMISSÃO / ADMISSÃO
# =========================================================

@app.route("/admissao", methods=["GET", "POST"])
@login_required
def admissao():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = limpar_documento(request.form.get("cpf", ""))
        campo = request.form.get("campo", "").strip()
        telefone = limpar_documento(request.form.get("telefone", ""))
        funcao = request.form.get("funcao", "").strip()
        obra = request.form.get("obra", "").strip()
        status = request.form.get("status", "Aguardando").strip() or "Aguardando"
        data_admissao = request.form.get("data_admissao", "").strip()
        isolado = True if request.form.get("campo_isolado") else False

        if not nome or not cpf:
            flash("Nome e CPF são obrigatórios.", "danger")
            return redirect(url_for("admissao"))

        lista_negra = buscar_na_lista_negra(nome, cpf)

        if lista_negra:
            flash(f"⚠️ {nome} ESTÁ NA LISTA NEGRA!", "danger")
            return redirect(url_for("admissao"))

        pre_existente = PreAdmissao.query.filter_by(cpf=cpf).first()

        if pre_existente:
            pre = pre_existente
            flash("Pré-admissão já existia. Os dados foram atualizados.", "warning")
        else:
            pre = PreAdmissao(cpf=cpf)
            db.session.add(pre)
            flash("Pré-admissão salva!", "success")

        pre.nome = nome
        pre.telefone = telefone
        pre.funcao = funcao
        pre.campo = campo
        pre.obra = obra
        pre.status = status

        set_attr_if_exists(pre, "data_admissao", data_admissao)
        set_attr_if_exists(pre, "isolado", isolado)

        db.session.commit()

        return redirect(url_for("admissao"))

    filtro_status = request.args.get("status", "Todos").strip()

    consulta = PreAdmissao.query

    if filtro_status and filtro_status != "Todos":
        consulta = consulta.filter(PreAdmissao.status == filtro_status)

    pre_admissoes = consulta.order_by(PreAdmissao.id.desc()).all()

    return render_template(
        "admissao.html",
        pre_admissoes=pre_admissoes,
        filtro_status=filtro_status,
    )


@app.route("/alterar_status_pre_admissao/<int:id>/<novo_status>")
@login_required
def alterar_status_pre_admissao(id, novo_status):
    status_map = {
        "aguardando": "Aguardando",
        "admitido": "Admitido",
        "recusado": "Recusado",
        "cancelado": "Cancelado",
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


@app.route("/exportar_pre_admissoes_excel")
@login_required
def exportar_pre_admissoes_excel():
    pre_admissoes = PreAdmissao.query.order_by(PreAdmissao.nome.asc()).all()

    dados = []

    for p in pre_admissoes:
        dados.append(
            {
                "Nome": get_attr(p, "nome"),
                "CPF": get_attr(p, "cpf"),
                "Telefone": get_attr(p, "telefone"),
                "Função": get_attr(p, "funcao"),
                "Campo": get_attr(p, "campo"),
                "Obra": get_attr(p, "obra"),
                "Data Admissão": get_attr(p, "data_admissao"),
                "Status": get_attr(p, "status"),
                "Isolado": "SIM" if get_attr(p, "isolado", False) else "NÃO",
            }
        )

    df = pd.DataFrame(dados)

    arquivo = BytesIO()

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pré-Admissões")

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="pre_admissoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/zerar_pre_admissao")
@login_required
def zerar_pre_admissao():
    try:
        PreAdmissao.query.delete()
        db.session.commit()
        flash("Tabela de pré-admissão limpa com sucesso.", "success")
    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao limpar pré-admissões: {erro}", "danger")

    return redirect(url_for("admissao"))


@app.route("/limpar-pre-admissoes")
@login_required
def limpar_pre_admissoes():
    return zerar_pre_admissao()


@app.route("/aprovar_admissao/<int:id>")
@login_required
def aprovar_admissao(id):
    pre = PreAdmissao.query.get(id)

    if not pre:
        flash("Pré-admissão não encontrada.", "danger")
        return redirect(url_for("admissao"))

    pre.status = "Admitido"

    colaborador = Colaborador.query.filter_by(cpf=pre.cpf).first()

    if not colaborador:
        colaborador = Colaborador(cpf=pre.cpf)
        db.session.add(colaborador)

    colaborador.nome = pre.nome
    colaborador.funcao = pre.funcao
    set_attr_if_exists(colaborador, "telefone", pre.telefone)
    set_attr_if_exists(colaborador, "obra", pre.obra)
    set_attr_if_exists(colaborador, "campo", pre.campo)
    set_attr_if_exists(colaborador, "data_admissao", get_attr(pre, "data_admissao"))
    set_attr_if_exists(colaborador, "status", "Admitido")
    set_attr_if_exists(colaborador, "pre_admissao", "Liberado")

    db.session.commit()

    flash("Pré-admissão aprovada e colaborador atualizado!", "success")
    return redirect(url_for("admissao"))


@app.route("/reprovar_admissao/<int:id>")
@login_required
def reprovar_admissao(id):
    pre = PreAdmissao.query.get(id)

    if pre:
        pre.status = "Recusado"
        db.session.commit()
        flash("Pré-admissão reprovada.", "danger")

    return redirect(url_for("admissao"))

@app.route("/excluir_lista_negra_tudo", methods=["POST"])
@login_required
def excluir_lista_negra_tudo():

    try:

        colaboradores = Colaborador.query.filter_by(
            restrito=True
        ).all()

        for colaborador in colaboradores:

            colaborador.restrito = False
            colaborador.motivo = ""

        ListaNegra.query.delete()

        db.session.commit()

        return "Lista Negra excluída com sucesso.", 200

    except Exception as erro:

        db.session.rollback()

        return f"Erro ao excluir: {erro}", 500

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )
