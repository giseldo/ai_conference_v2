from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from supabase import create_client
import os
from dotenv import load_dotenv
from functools import wraps
import uuid
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "123")

# Configuração do Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Decorator para verificar se o usuário está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        
        # Verificar se o usuário é admin consultando a tabela de usuários
        user_id = session['user']['id']
        try:
            response = supabase.table('profiles').select('is_admin').eq('id', user_id).execute()
            if response.data and response.data[0].get('is_admin') == True:
                return f(*args, **kwargs)
            else:
                flash('Acesso negado. Você precisa ser administrador para acessar esta página.', 'danger')
                return redirect(url_for('index'))
        except Exception as e:
            flash(f'Erro ao verificar permissões: {str(e)}', 'danger')
            return redirect(url_for('index'))
            
    return decorated_function

# Função para obter conferências do Supabase
def get_conferences_from_db():
    try:
        response = supabase.table('conferences').select('*').execute()
        return response.data
    except Exception as e:
        print(f"Erro ao obter conferências: {str(e)}")
        return []

# Função para obter uma conferência específica pelo ID
def get_conference_by_id(conference_id):
    try:
        response = supabase.table('conferences').select('*').eq('id', conference_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Erro ao obter conferência: {str(e)}")
        return None

# Rota principal
@app.route('/')
def index():
    conferences = get_conferences_from_db()
    return render_template('index.html', conferences=conferences)

# Rota para exibir detalhes de uma conferência específica
@app.route('/conference/<conference_id>')
def conference_details(conference_id):
    conference = get_conference_by_id(conference_id)
    if conference:
        return render_template('conference_details.html', conference=conference)
    else:
        return render_template('404.html'), 404

# Rota para a página de signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Criar usuário no Supabase
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user = response.user
            
            if user:
                return redirect(url_for('login'))
            else:
                return render_template('signup.html', error="Ocorreu um erro durante o registro")
        
        except Exception as e:
            return render_template('signup.html', error=str(e))
    
    return render_template('signup.html')

# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Autenticar usuário no Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            session['user'] = {
                'id': response.user.id,
                'email': response.user.email,
                'access_token': response.session.access_token
            }
            
            return redirect(url_for('configuracao'))
        
        except Exception as e:
            return render_template('login.html', error=str(e))
    
    return render_template('login.html')

# Rota para o painel do usuário (protegida)
@app.route('/configuracao')
@login_required
def configuracao():
    user = session.get('user')
    # Verificar se o usuário é admin
    try:
        response = supabase.table('profiles').select('is_admin').eq('id', user['id']).execute()
        is_admin = response.data and response.data[0].get('is_admin') == True
    except:
        is_admin = False
    
    is_admin = True
    
    return render_template('configuracao.html', user=user, is_admin=is_admin)

# Rota para logout
@app.route('/logout')
def logout():
    # Realizar logout no Supabase
    supabase.auth.sign_out()
    
    # Limpar sessão
    session.pop('user', None)
    
    return redirect(url_for('index'))

# Rota para listar conferências (admin)
@app.route('/admin/conferences')
#@admin_required
def admin_conferences():
    conferences = get_conferences_from_db()
    return render_template('admin/conferences.html', conferences=conferences)

# Rota para adicionar nova conferência
@app.route('/admin/conferences/new', methods=['GET', 'POST'])
#@admin_required
def add_conference():
    print("entrou aqui")
    if request.method == 'POST':
        try:
            # Preparar dados da conferência
            conference_data = {
                'name': request.form.get('name'),
                'full_name': request.form.get('full_name'),
                'dates': request.form.get('dates'),
                'location': request.form.get('location'),
                'deadline': request.form.get('deadline'),
                'website': request.form.get('website'),
                'description': request.form.get('description'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Inserir no Supabase
            response = supabase.table('conferences').insert(conference_data).execute()
            
            flash('Conferência adicionada com sucesso!', 'success')
            return redirect(url_for('admin_conferences'))
            
        except Exception as e:
            flash(f'Erro ao adicionar conferência: {str(e)}', 'danger')
            return render_template('admin/conference_form.html', conference=None, action='add')
    
    return render_template('admin/conference_form.html', conference=None, action='add')

# Rota para editar conferência
@app.route('/admin/conferences/edit/<conference_id>', methods=['GET', 'POST'])
#@admin_required
def edit_conference(conference_id):
    # Obter a conferência pelo ID
    conference = get_conference_by_id(conference_id)
    
    if not conference:
        flash('Conferência não encontrada', 'danger')
        return redirect(url_for('admin_conferences'))
    
    if request.method == 'POST':
        try:
            # Preparar dados atualizados
            updated_data = {
                'name': request.form.get('name'),
                'full_name': request.form.get('full_name'),
                'dates': request.form.get('dates'),
                'location': request.form.get('location'),
                'deadline': request.form.get('deadline'),
                'website': request.form.get('website'),
                'description': request.form.get('description'),
                'updated_at': datetime.now().isoformat()
            }
            
            # Atualizar no Supabase
            supabase.table('conferences').update(updated_data).eq('id', conference_id).execute()
            
            flash('Conferência atualizada com sucesso!', 'success')
            return redirect(url_for('admin_conferences'))
            
        except Exception as e:
            flash(f'Erro ao atualizar conferência: {str(e)}', 'danger')
            return render_template('admin/conference_form.html', conference=conference, action='edit')
    
    return render_template('admin/conference_form.html', conference=conference, action='edit')

# Rota para excluir conferência
@app.route('/admin/conferences/delete/<conference_id>', methods=['POST'])
#@admin_required
def delete_conference(conference_id):
    try:
        # Excluir do Supabase
        supabase.table('conferences').delete().eq('id', conference_id).execute()
        flash('Conferência excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir conferência: {str(e)}', 'danger')
    
    return redirect(url_for('admin_conferences'))

# Rota para a página "sobre"
@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# Rota para a página de contato
@app.route('/contato')
def contato():
    return render_template('contato.html')

# Rota para a página de perfil do usuário
@app.route('/perfil')
@login_required
def perfil():
    user = session.get('user')
    return render_template('perfil.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)