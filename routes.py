from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from app import app, db
from models import PurchaseRequest, RequestItem
from replit_auth import require_login, make_replit_blueprint

# Register the Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Main landing page - shows different content based on auth status"""
    return render_template('index.html')

@app.route('/request')
def request_form():
    """Purchase request form for users"""
    return render_template('request_form.html')

@app.route('/submit_request', methods=['POST'])
def submit_request():
    """Handle purchase request submission"""
    try:
        # Get requester information
        requester_name = request.form.get('requester_name', '').strip()
        requester_email = request.form.get('requester_email', '').strip()
        obra_id = request.form.get('obra_id', '').strip()
        responsavel = request.form.get('responsavel', '').strip()
        tipo_entrega = request.form.get('tipo_entrega', '').strip()
        endereco_entrega = request.form.get('endereco_entrega', '').strip()
        
        if not requester_name:
            flash('Nome do solicitante é obrigatório', 'error')
            return redirect(url_for('request_form'))
        
        # Create new purchase request with all fields
        purchase_request = PurchaseRequest(
            requester_name=requester_name,
            requester_email=requester_email if requester_email else None,
            obra_id=obra_id if obra_id else None,
            responsavel=responsavel if responsavel else None,
            tipo_entrega=tipo_entrega if tipo_entrega else None,
            endereco_entrega=endereco_entrega if endereco_entrega else None
        )
        db.session.add(purchase_request)
        db.session.flush()  # Get the ID without committing
        
        # Process items with new detailed fields
        descricao_insumos_list = request.form.getlist('descricao_insumos[]')
        qtd_list = request.form.getlist('qtd[]')
        und_list = request.form.getlist('und[]')
        periodo_locacao_list = request.form.getlist('periodo_locacao[]')
        demanda_list = request.form.getlist('demanda[]')
        data_entrega_list = request.form.getlist('data_entrega[]')
        servico_cpu_list = request.form.getlist('servico_cpu[]')
        cod_insumo_list = request.form.getlist('cod_insumo[]')
        observacoes_list = request.form.getlist('observacoes[]')
        
        # Validate that we have at least one item
        valid_items = []
        for i in range(len(descricao_insumos_list)):
            if i < len(descricao_insumos_list) and i < len(qtd_list) and i < len(und_list):
                descricao = descricao_insumos_list[i].strip()
                try:
                    quantidade = float(qtd_list[i])
                except (ValueError, IndexError):
                    quantidade = 0
                
                unidade = und_list[i].strip()
                
                if descricao and quantidade > 0 and unidade:
                    from datetime import datetime
                    data_entrega = None
                    if i < len(data_entrega_list) and data_entrega_list[i]:
                        try:
                            data_entrega = datetime.strptime(data_entrega_list[i], '%Y-%m-%d').date()
                        except ValueError:
                            data_entrega = None
                    
                    valid_items.append({
                        'descricao_insumos': descricao,
                        'qtd': quantidade,
                        'und': unidade,
                        'periodo_locacao': periodo_locacao_list[i].strip() if i < len(periodo_locacao_list) else '',
                        'demanda': demanda_list[i].strip() if i < len(demanda_list) else '',
                        'data_entrega': data_entrega,
                        'servico_cpu': servico_cpu_list[i].strip() if i < len(servico_cpu_list) else '',
                        'cod_insumo': cod_insumo_list[i].strip() if i < len(cod_insumo_list) else '',
                        'observacoes': observacoes_list[i].strip() if i < len(observacoes_list) else ''
                    })
        
        if not valid_items:
            flash('Pelo menos um item válido é obrigatório', 'error')
            db.session.rollback()
            return redirect(url_for('request_form'))
        
        # Add valid items to the request
        for item_data in valid_items:
            item = RequestItem(
                request_id=purchase_request.id,
                descricao_insumos=item_data['descricao_insumos'],
                qtd=item_data['qtd'],
                und=item_data['und'],
                periodo_locacao=item_data['periodo_locacao'] if item_data['periodo_locacao'] else None,
                demanda=item_data['demanda'] if item_data['demanda'] else None,
                data_entrega=item_data['data_entrega'],
                servico_cpu=item_data['servico_cpu'] if item_data['servico_cpu'] else None,
                cod_insumo=item_data['cod_insumo'] if item_data['cod_insumo'] else None,
                observacoes=item_data['observacoes'] if item_data['observacoes'] else None
            )
            db.session.add(item)
        
        db.session.commit()
        flash('Solicitação enviada com sucesso!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao enviar solicitação: {str(e)}', 'error')
        return redirect(url_for('request_form'))

@app.route('/admin')
@require_login
def admin():
    """Admin panel - requires authentication"""
    try:
        # Get all purchase requests with their items
        requests = PurchaseRequest.query.order_by(PurchaseRequest.created_at.desc()).all()
        return render_template('admin.html', requests=requests)
    except Exception as e:
        flash(f'Erro ao carregar solicitações: {str(e)}', 'error')
        return render_template('admin.html', requests=[])

@app.route('/delete_request/<int:request_id>', methods=['POST'])
@require_login
def delete_request(request_id):
    """Delete a purchase request - requires authentication"""
    try:
        purchase_request = PurchaseRequest.query.get_or_404(request_id)
        db.session.delete(purchase_request)
        db.session.commit()
        flash('Solicitação excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir solicitação: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.errorhandler(404)
def not_found(error):
    return render_template('403.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('403.html'), 500
