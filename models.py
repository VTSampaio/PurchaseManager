from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Purchase Request Model
class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_requests'
    id = db.Column(db.Integer, primary_key=True)
    numero_solicitacao = db.Column(db.String(20), unique=True, nullable=False)  # Número único da solicitação
    requester_name = db.Column(db.String(100), nullable=False)
    requester_email = db.Column(db.String(120), nullable=True)  # Office 365 integration
    obra_id = db.Column(db.String(50), nullable=True)
    responsavel = db.Column(db.String(100), nullable=True)
    tipo_entrega = db.Column(db.String(50), nullable=True)
    endereco_entrega = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pendente', nullable=False)  # Pendente, Em Análise, Atendida, Cancelada
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with items
    items = db.relationship('RequestItem', backref='request', lazy=True, cascade='all, delete-orphan')
    
    def generate_numero_solicitacao(self):
        """Generate a unique request number"""
        from datetime import datetime
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        
        # Count existing requests for this month/year to get sequential number
        count = db.session.query(PurchaseRequest).filter(
            PurchaseRequest.created_at >= datetime(now.year, now.month, 1)
        ).count() + 1
        
        # Format: SOL-YYYY-MM-NNNN (e.g., SOL-2024-05-0001)
        return f"SOL-{year}-{month}-{count:04d}"

# Purchase Request Item Model
class RequestItem(db.Model):
    __tablename__ = 'request_items'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), nullable=False)
    descricao_insumos = db.Column(db.String(500), nullable=False)
    qtd = db.Column(db.Float, nullable=False)
    und = db.Column(db.String(20), nullable=False)
    periodo_locacao = db.Column(db.String(100), nullable=True)
    demanda = db.Column(db.String(100), nullable=True)
    data_entrega = db.Column(db.Date, nullable=True)
    servico_cpu = db.Column(db.String(100), nullable=True)
    cod_insumo = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    status_item = db.Column(db.String(20), default='Pendente', nullable=False)  # Pendente, Atendido, Cancelado
