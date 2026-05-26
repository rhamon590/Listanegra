from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# =========================================================
# LOGIN
# =========================================================

class Usuario(db.Model):

    __tablename__ = 'usuarios'

    # =====================================
    # ID
    # =====================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================
    # USUÁRIO
    # =====================================

    usuario = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    # =====================================
    # SENHA
    # =====================================

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    # =====================================
    # GERAR SENHA
    # =====================================

    def set_senha(self, senha):

        self.senha = generate_password_hash(
            senha
        )

    # =====================================
    # VERIFICAR SENHA
    # =====================================

    def check_senha(self, senha):

        return check_password_hash(
            self.senha,
            senha
        )

    # =====================================
    # REPRESENTAÇÃO
    # =====================================

    def __repr__(self):

        return f'<Usuario {self.usuario}>'

# =========================================================
# COLABORADORES
# =========================================================

class Colaborador(db.Model):

    __tablename__ = 'colaborador'

    # =====================================
    # ID
    # =====================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================
    # DADOS PESSOAIS
    # =====================================

    nome = db.Column(
        db.String(200),
        nullable=False
    )

    cpf = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    telefone = db.Column(
        db.String(20)
    )

    data_nascimento = db.Column(
        db.String(50)
    )

    naturalidade = db.Column(
        db.String(100)
    )

    cep = db.Column(
        db.String(20)
    )

    endereco = db.Column(
        db.String(300)
    )

    cidade = db.Column(
        db.String(100)
    )

    estado = db.Column(
        db.String(100)
    )

    funcao = db.Column(
        db.String(100)
    )

    # =====================================
    # CAMPO / EMPRESA
    # =====================================

    campo = db.Column(
        db.String(200)
    )

    # =====================================
    # CAMPO ISOLADO
    # =====================================

    campo_isolado = db.Column(
        db.Boolean,
        default=False
    )

    # =====================================
    # OBRA
    # =====================================

    obra = db.Column(
        db.String(200)
    )

    # =====================================
    # FOTO
    # =====================================

    foto = db.Column(
        db.String(300)
    )

    # =====================================
    # STATUS
    # =====================================

    status = db.Column(
        db.String(50),
        default='Liberado'
    )

    # =====================================
    # PRÉ-ADMISSÃO
    # =====================================

    pre_admissao = db.Column(
        db.String(100),
        default='Em análise'
    )

    data_admissao = db.Column(
        db.String(50)
    )

    # =====================================
    # RESTRIÇÃO
    # =====================================

    restrito = db.Column(
        db.Boolean,
        default=False
    )

    motivo = db.Column(
        db.String(500)
    )

    # =====================================
    # DATA CADASTRO
    # =====================================

    data_cadastro = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # =====================================
    # REPRESENTAÇÃO
    # =====================================

    def __repr__(self):

        return f'<Colaborador {self.nome}>'


# =========================================================
# PRÉ-ADMISSÃO
# =========================================================

class PreAdmissao(db.Model):

    __tablename__ = 'pre_admissao'

    # =====================================
    # ID
    # =====================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================
    # DADOS
    # =====================================

    nome = db.Column(
        db.String(200),
        nullable=False
    )

    cpf = db.Column(
        db.String(20)
    )

    telefone = db.Column(
        db.String(20)
    )

    funcao = db.Column(
        db.String(150)
    )

    campo = db.Column(
        db.String(150)
    )

    obra = db.Column(
        db.String(150)
    )

    data_admissao = db.Column(
        db.String(50)
    )

    # =====================================
    # CAMPO ISOLADO
    # =====================================

    isolado = db.Column(
        db.Boolean,
        default=False
    )

    # =====================================
    # STATUS
    # =====================================

    status = db.Column(
        db.String(50),
        default='Em análise'
    )

    # =====================================
    # ALERTA LISTA NEGRA
    # =====================================

    lista_negra = db.Column(
        db.Boolean,
        default=False
    )

    motivo_lista = db.Column(
        db.String(500)
    )

    # =====================================
    # DATA
    # =====================================

    data_cadastro = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # =====================================
    # REPRESENTAÇÃO
    # =====================================

    def __repr__(self):

        return f'<PreAdmissao {self.nome}>'


# =========================================================
# LISTA NEGRA
# =========================================================

class ListaNegra(db.Model):

    __tablename__ = 'lista_negra'

    # =====================================
    # ID
    # =====================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================
    # DADOS
    # =====================================

    nome = db.Column(
        db.String(200),
        nullable=False
    )

    obra = db.Column(
        db.String(200)
    )

    campo = db.Column(
        db.String(200)
    )

    cpf = db.Column(
        db.String(20)
    )

    telefone = db.Column(
        db.String(20)
    )

    motivo = db.Column(
        db.String(500),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default='Restrito'
    )

    # =====================================
    # DATA RESTRIÇÃO
    # =====================================

    data_restricao = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # =====================================
    # REPRESENTAÇÃO
    # =====================================

    def __repr__(self):

        return f'<ListaNegra {self.nome}>'