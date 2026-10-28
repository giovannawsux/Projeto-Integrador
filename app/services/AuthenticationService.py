from app.models.usuario import Usuario
from app import db
from flask_login import login_user, logout_user

class AuthenticationService():
    def login(form):
        print(f"O usuario {form.username.data} fez o login, lembrar={form.remember_me.data}")
        return True

    def logout():
        return logout_user()


    def login_suap(dados):
        username = str(dados.get('matricula') or dados.get('username') or dados.get('email'))
        email = dados.get('email') or f'{username}@suap.local'
        user = Usuario.query.filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first()

        if not user:
            user = Usuario(username=username, email=email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return user