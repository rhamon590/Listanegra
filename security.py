"""Tabelas novas de controle de acesso e rastreabilidade.

Não altera o esquema das tabelas de colaboradores nem exclui contas existentes.
"""
from datetime import datetime, timedelta
import hashlib
from models import db

ROLES = ("admin", "rh", "cadastro", "visualizador")
TERMS_VERSION = "2026-10-26.1"

class UserRole(db.Model):
    __tablename__ = "sec_user_roles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    role = db.Column(db.String(30), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

class UserAcknowledgement(db.Model):
    __tablename__ = "sec_acknowledgements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    version = db.Column(db.String(30), nullable=False)
    acknowledged_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "version", name="uq_sec_ack_version"),)

class AuditEntry(db.Model):
    __tablename__ = "sec_audit"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(100), nullable=False, default="system")
    action = db.Column(db.String(70), nullable=False)
    resource = db.Column(db.String(90), nullable=False, default="")
    item_id = db.Column(db.String(45), nullable=False, default="")
    happened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

class AppSetting(db.Model):
    __tablename__ = "sec_settings"
    key = db.Column(db.String(70), primary_key=True)
    value = db.Column(db.Text, nullable=False, default="")

class FailedLogin(db.Model):
    __tablename__ = "sec_failed_login"
    key = db.Column(db.String(64), primary_key=True)
    failures = db.Column(db.Integer, nullable=False, default=0)
    blocked_until = db.Column(db.DateTime)

def get_role(user_id):
    data = UserRole.query.filter_by(user_id=user_id).first()
    return data.role if data and data.active else None

def get_setting(key):
    record = db.session.get(AppSetting, key)
    return record.value if record else ""

def set_setting(key, value):
    record = db.session.get(AppSetting, key)
    if record is None:
        record = AppSetting(key=key)
        db.session.add(record)
    record.value = str(value).strip()

def audit(action, user=None, resource="", item_id=""):
    db.session.add(AuditEntry(user_id=getattr(user,"id",None),
                              username=getattr(user,"usuario","system"),
                              action=str(action)[:70],resource=str(resource)[:90],
                              item_id=str(item_id)[:45]))
    db.session.commit()

def login_key(username, ip):
    return hashlib.sha256((username.casefold()+"|"+ip).encode()).hexdigest()

def is_blocked(key):
    record=db.session.get(FailedLogin,key)
    return bool(record and record.blocked_until and record.blocked_until > datetime.utcnow())

def mark_failed(key):
    record=db.session.get(FailedLogin,key)
    if record is None:
        record=FailedLogin(key=key)
        db.session.add(record)
    if record.blocked_until and record.blocked_until < datetime.utcnow():
        record.failures=0
        record.blocked_until=None
    record.failures += 1
    if record.failures >= 5:
        record.blocked_until=datetime.utcnow()+timedelta(minutes=15)
    db.session.commit()

def reset_failed(key):
    record=db.session.get(FailedLogin,key)
    if record:
        db.session.delete(record)
        db.session.commit()
