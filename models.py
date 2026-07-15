from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), unique=True, nullable=False, index=True)
    senha = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha, senha)

    def __repr__(self):
        return f"<Usuario {self.usuario}>"


class Colaborador(db.Model):
    __tablename__ = "colaborador"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(200), nullable=False, index=True)
    cpf = db.Column(db.String(20), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(20))
    data_nascimento = db.Column(db.String(50))
    naturalidade = db.Column(db.String(100))
    cep = db.Column(db.String(20))
    endereco = db.Column(db.String(300))
    cidade = db.Column(db.String(100), index=True)
    estado = db.Column(db.String(100))
    funcao = db.Column(db.String(100), index=True)

    campo = db.Column(db.String(200), index=True)
    campo_isolado = db.Column(db.Boolean, default=False, index=True)
    obra = db.Column(db.String(200), index=True)
    foto = db.Column(db.String(300))

    status = db.Column(db.String(50), default="Liberado", index=True)
    pre_admissao = db.Column(db.String(100), default="Em análise")
    data_admissao = db.Column(db.String(50))

    restrito = db.Column(db.Boolean, default=False, index=True)
    motivo = db.Column(db.String(500))
    data_cadastro = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    def __repr__(self):
        return f"<Colaborador {self.nome}>"


class PreAdmissao(db.Model):
    __tablename__ = "pre_admissao"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    cpf = db.Column(db.String(20), index=True)
    telefone = db.Column(db.String(20))
    funcao = db.Column(db.String(150), index=True)
    campo = db.Column(db.String(150), index=True)
    obra = db.Column(db.String(150), index=True)
    data_admissao = db.Column(db.String(50))
    isolado = db.Column(db.Boolean, default=False, index=True)
    status = db.Column(db.String(50), default="Em análise", index=True)
    lista_negra = db.Column(db.Boolean, default=False)
    motivo_lista = db.Column(db.String(500))
    data_cadastro = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    def __repr__(self):
        return f"<PreAdmissao {self.nome}>"


class ListaNegra(db.Model):
    __tablename__ = "lista_negra"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    obra = db.Column(db.String(200), index=True)
    campo = db.Column(db.String(200), index=True)
    cpf = db.Column(db.String(20), index=True)
    telefone = db.Column(db.String(20))
    motivo = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default="Restrito", index=True)
    data_restricao = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    def __repr__(self):
        return f"<ListaNegra {self.nome}>"
