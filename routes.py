from flask import render_template, request, redirect, url_for, flash, session, send_file, make_response
from flask_login import current_user
from werkzeug.utils import secure_filename
import pandas as pd
import os
from io import BytesIO
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
    try:
        # Get statistics for dashboard
        total_requests = PurchaseRequest.query.count()
        pending_requests = PurchaseRequest.query.filter_by(status='Pendente').count()
        completed_requests = PurchaseRequest.query.filter_by(status='Atendida').count()
        cancelled_requests = PurchaseRequest.query.filter_by(status='Cancelada').count()
        
        stats = {
            'total': total_requests,
            'pending': pending_requests,
            'completed': completed_requests,
            'cancelled': cancelled_requests
        }
        return render_template('index.html', stats=stats)
    except Exception as e:
        return render_template('index.html', stats=None)

@app.route('/request')
def request_form():
    """Purchase request form for users"""
    # Get Excel items from session if available
    excel_items = session.get('excel_items', [])
    # Clear items from session after retrieving
    if 'excel_items' in session:
        del session['excel_items']
    
    return render_template('request_form.html', excel_items=excel_items)

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
        purchase_request = PurchaseRequest()
        purchase_request.requester_name = requester_name
        purchase_request.requester_email = requester_email if requester_email else None
        purchase_request.obra_id = obra_id if obra_id else None
        purchase_request.responsavel = responsavel if responsavel else None
        purchase_request.tipo_entrega = tipo_entrega if tipo_entrega else None
        purchase_request.endereco_entrega = endereco_entrega if endereco_entrega else None
        
        # Generate unique request number
        purchase_request.numero_solicitacao = purchase_request.generate_numero_solicitacao()
        
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
            item = RequestItem()
            item.request_id = purchase_request.id
            item.descricao_insumos = item_data['descricao_insumos']
            item.qtd = item_data['qtd']
            item.und = item_data['und']
            item.periodo_locacao = item_data['periodo_locacao'] if item_data['periodo_locacao'] else None
            item.demanda = item_data['demanda'] if item_data['demanda'] else None
            item.data_entrega = item_data['data_entrega']
            item.servico_cpu = item_data['servico_cpu'] if item_data['servico_cpu'] else None
            item.cod_insumo = item_data['cod_insumo'] if item_data['cod_insumo'] else None
            item.observacoes = item_data['observacoes'] if item_data['observacoes'] else None
            db.session.add(item)
        
        db.session.commit()
        flash(f'Solicitação enviada com sucesso! Número: {purchase_request.numero_solicitacao}', 'success')
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

@app.route('/minhas-solicitacoes')
def minhas_solicitacoes():
    """Lista todas as solicitações para usuários verificarem status"""
    try:
        # Get all purchase requests ordered by date
        requests = PurchaseRequest.query.order_by(PurchaseRequest.created_at.desc()).all()
        return render_template('minhas_solicitacoes.html', requests=requests)
    except Exception as e:
        flash(f'Erro ao carregar solicitações: {str(e)}', 'error')
        return render_template('minhas_solicitacoes.html', requests=[])

@app.route('/update_request_status/<int:request_id>', methods=['POST'])
@require_login
def update_request_status(request_id):
    """Update request status - requires authentication"""
    try:
        purchase_request = PurchaseRequest.query.get_or_404(request_id)
        new_status = request.form.get('status')
        
        if new_status in ['Pendente', 'Em Análise', 'Atendida', 'Cancelada']:
            purchase_request.status = new_status
            db.session.commit()
            flash(f'Status da solicitação atualizado para: {new_status}', 'success')
        else:
            flash('Status inválido', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/update_item_status/<int:item_id>', methods=['POST'])
@require_login
def update_item_status(item_id):
    """Update item status - requires authentication"""
    try:
        item = RequestItem.query.get_or_404(item_id)
        new_status = request.form.get('status_item')
        
        if new_status in ['Pendente', 'Atendido', 'Cancelado']:
            item.status_item = new_status
            db.session.commit()
            flash(f'Status do item atualizado para: {new_status}', 'success')
        else:
            flash('Status inválido', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status do item: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/download-template')
def download_template():
    """Download Excel template for bulk item upload"""
    try:
        # Create template data
        template_data = {
            'Descrição de Insumos': ['Exemplo: Cimento Portland CP II-E-32', 'Exemplo: Brita nº 1'],
            'QTD': [50, 10],
            'UND': ['SACO', 'M³'],
            'Período de Locação': ['30 dias', ''],
            'Demanda': ['Urgente', 'Normal'],
            'Data de Entrega': ['2024-06-01', '2024-06-15'],
            'Serviço/CPU': ['Entrega no canteiro', 'Instalação'],
            'Cód. Insumo': ['CIM001', 'BRI002'],
            'Observações': ['Entrega pela manhã', 'Verificar qualidade']
        }
        
        # Create DataFrame
        df = pd.DataFrame(template_data)
        
        # Create Excel file in memory using ExcelWriter
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False, sheet_name='Itens')
        
        output.seek(0)
        
        # Send file
        return send_file(
            output,
            as_attachment=True,
            download_name='template_itens_solicitacao.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar template: {str(e)}', 'error')
        return redirect(url_for('request_form'))

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    """Process Excel file upload with items"""
    try:
        if 'excel_file' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('request_form'))
        
        file = request.files['excel_file']
        if file.filename == '' or file.filename is None:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('request_form'))
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            flash('Por favor, envie um arquivo Excel (.xlsx ou .xls)', 'error')
            return redirect(url_for('request_form'))
        
        # Read Excel file
        df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['Descrição de Insumos', 'QTD', 'UND']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('request_form'))
        
        # Process and validate data
        valid_items = []
        for index, row in df.iterrows():
            try:
                descricao_val = row.get('Descrição de Insumos')
                qtd_val = row.get('QTD')
                und_val = row.get('UND')
                
                if pd.notna(descricao_val) and pd.notna(qtd_val) and pd.notna(und_val):
                    descricao = str(descricao_val).strip()
                    qtd = float(qtd_val)
                    und = str(und_val).strip()
                    
                    if descricao and qtd > 0 and und:
                        item_data = {
                            'descricao_insumos': descricao,
                            'qtd': qtd,
                            'und': und,
                            'periodo_locacao': str(row.get('Período de Locação', '')).strip() if pd.notna(row.get('Período de Locação')) else '',
                            'demanda': str(row.get('Demanda', '')).strip() if pd.notna(row.get('Demanda')) else '',
                            'data_entrega': None,
                            'servico_cpu': str(row.get('Serviço/CPU', '')).strip() if pd.notna(row.get('Serviço/CPU')) else '',
                            'cod_insumo': str(row.get('Cód. Insumo', '')).strip() if pd.notna(row.get('Cód. Insumo')) else '',
                            'observacoes': str(row.get('Observações', '')).strip() if pd.notna(row.get('Observações')) else ''
                        }
                        
                        # Process data de entrega
                        data_entrega_val = row.get('Data de Entrega')
                        if pd.notna(data_entrega_val):
                            try:
                                from datetime import datetime
                                if isinstance(data_entrega_val, str):
                                    item_data['data_entrega'] = datetime.strptime(data_entrega_val, '%Y-%m-%d').date()
                                elif hasattr(data_entrega_val, 'date'):
                                    item_data['data_entrega'] = data_entrega_val.date()
                            except:
                                pass
                        
                        valid_items.append(item_data)
            except Exception as e:
                continue
        
        if not valid_items:
            flash('Nenhum item válido encontrado no arquivo Excel', 'error')
            return redirect(url_for('request_form'))
        
        # Store items in session to be used in form
        session['excel_items'] = valid_items
        flash(f'{len(valid_items)} itens carregados do Excel com sucesso!', 'success')
        return redirect(url_for('request_form'))
        
    except Exception as e:
        flash(f'Erro ao processar arquivo Excel: {str(e)}', 'error')
        return redirect(url_for('request_form'))

@app.errorhandler(404)
def not_found(error):
    return render_template('403.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('403.html'), 500
