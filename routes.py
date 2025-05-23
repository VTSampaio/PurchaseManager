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
        # Get requester name
        requester_name = request.form.get('requester_name', '').strip()
        
        if not requester_name:
            flash('Nome do solicitante é obrigatório', 'error')
            return redirect(url_for('request_form'))
        
        # Create new purchase request
        purchase_request = PurchaseRequest(requester_name=requester_name)
        db.session.add(purchase_request)
        db.session.flush()  # Get the ID without committing
        
        # Process items
        item_names = request.form.getlist('item_name[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_descriptions = request.form.getlist('item_description[]')
        
        # Validate that we have at least one item
        valid_items = []
        for i in range(len(item_names)):
            if i < len(item_names) and i < len(item_quantities):
                name = item_names[i].strip()
                try:
                    quantity = int(item_quantities[i])
                except (ValueError, IndexError):
                    quantity = 0
                
                if name and quantity > 0:
                    description = item_descriptions[i].strip() if i < len(item_descriptions) else ''
                    valid_items.append({
                        'name': name,
                        'quantity': quantity,
                        'description': description
                    })
        
        if not valid_items:
            flash('Pelo menos um item válido é obrigatório', 'error')
            db.session.rollback()
            return redirect(url_for('request_form'))
        
        # Add valid items to the request
        for item_data in valid_items:
            item = RequestItem(
                request_id=purchase_request.id,
                item_name=item_data['name'],
                quantity=item_data['quantity'],
                description=item_data['description']
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
