from app import app
from flask import current_app, render_template, redirect, flash, request, url_for, session

from app.forms.login_form import LoginForm
from app.forms.usuario_form import UsuarioForm
from app.services.AuthenticationService import AuthenticationService
from app.services.UsuarioService import UsuarioService
from app.services.SuapAuthenticationService import SuapAuthenticationService
from flask_login import login_required
from secrets import token_urlsafe
from hmac import compare_digest
from urllib.parse import urljoin


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template("login.html")



@app.route("/professor")
def professor():
    return render_template("professor.html")

@app.route('/aluno')
def aluno():
    return render_template('aluno.html')


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/endereco')
def endereco():
    return render_template('endereco.html')


@app.route('/inserir', methods=['GET', 'POST'])
def inserir_usuario():
    formulario = UsuarioForm()
    if formulario.validate_on_submit():
        if UsuarioService.salvar(formulario):
            flash("Usuario cadastrado com sucesso!", category="success")
            return redirect("/")
        else:
            flash("Usuário não cadastrado.", category="warning")
            return redirect("/inserir")
    return render_template('cadastro_usuario.html', 
                            title='Cadastro de Usuário', 
                            form=formulario)
    

@app.route('/buscar_usuario', methods=['GET', 'POST'])
def buscar_usuario():
    if request.method == 'GET':
        return render_template('buscar_usuario.html')
    elif request.method == 'POST':
        email_a_buscar = request.form.get("email")
        if email_a_buscar:
            usuario = UsuarioService.buscar_por_email(email_a_buscar)
            print(usuario.username)
            print(usuario.email)
            UsuarioService.atualizar(usuario)
        return render_template("index.html")


@app.route('/listar_usuario')
def listar_usuario():
    usuarios = UsuarioService.listar()
    return render_template('listar_usuario.html', title='Listagem de Usuário', usuarios = usuarios)


@app.route('/logout')
def logout():
    AuthenticationService.logout()
    session.clear()
    return redirect(url_for('index'))
    
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario = UsuarioService.buscar_por_id(id)

    form = UsuarioForm(obj=usuario)
    if form.validate_on_submit():
        sucesso = UsuarioService.atualizar(usuario, form)
        if sucesso:
            flash("Usuário atualizado com sucesso!", category='success')
            return render_template('index.html')
        else:
            flash("Usuário não atualizado. Tente novamente mais tarde.", category='warning')
            return render_template("cadastro_usuario.html", form=form, editar=True)

    return render_template("cadastro_usuario.html", form=form, editar=True)    

@app.route('/login-suap')
def login_suap():
    state = token_urlsafe(32)
    redirect_uri = request.host_url.rstrip('/') + url_for('suap_callback')
    session['suap_oauth_state'] = state
    session['suap_redirect_uri'] = redirect_uri
    return redirect(SuapAuthenticationService.authorization_url(state, redirect_uri))


@app.route('/suap/callback')
def suap_callback():
    if request.args.get('error'):
        flash('Autenticação no SUAP cancelada.', 'error')
        return redirect(url_for('login'))

    state = session.pop('suap_oauth_state', None)
    if not state or not compare_digest(state, request.args.get('state', '')):
        flash('Callback do SUAP inválido.', 'error')
        return redirect(url_for('login'))

    code = request.args.get('code')
    if not code:
        flash('Código de autorização do SUAP não recebido.', 'error')
        return redirect(url_for('login'))

    redirect_uri = session.pop('suap_redirect_uri', None)
    if not redirect_uri:
        flash('URL de callback do SUAP não encontrada.', 'error')
        return redirect(url_for('login'))

    tokens = SuapAuthenticationService.exchange_code(code, redirect_uri)
    if not tokens:
        flash('Não foi possível obter o token do SUAP.', 'error')
        return redirect(url_for('login'))

    session['suap_access_token'] = tokens['access_token']
    return redirect(url_for('suap_eu'))


@app.route('/suap/eu')
def suap_eu():
    access_token = session.get('suap_access_token')
    if not access_token:
        return redirect(url_for('login_suap'))
    dados = SuapAuthenticationService.eu(access_token)
    if dados is None:
        session.pop('suap_access_token', None)
        flash('Não foi possível consultar os dados do SUAP.', 'error')
        return redirect(url_for('login_suap'))
    AuthenticationService.login_suap(dados)
    foto = dados.get('url_foto_75x100') or dados.get('url_foto') or dados.get('foto')
    foto_url = urljoin(current_app.config['SUAP_URL'] + '/', foto) if foto else None
    #return render_template('suap_eu.html', title='Perfil SUAP', dados=dados, foto_url=foto_url)
    print(dados)

    if dados.get('tipo_vinculo') == 'Aluno':
        return redirect(url_for('aluno'))

    elif "Servidor" in dados.get('tipo_vinculo'):
        if "Portuguesa" in dados.get('vinculo').get('disciplina_ingresso'):
            print('Deu certo')
            return redirect(url_for('professor'))
        else:
            return redirect(url_for('login_suap'))
