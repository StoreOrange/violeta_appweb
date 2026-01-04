from flask import Blueprint, render_template, redirect, url_for, session, flash
repositorios_bp = Blueprint('repositorios', __name__, url_prefix='/repositorios')

def _require_login():
    if not session.get('user_id'):
        flash('Debes iniciar sesion para continuar.')
        return redirect(url_for('usuario.login'))
    return None


@repositorios_bp.route('/')
def vista_repositorios():
    guard = _require_login()
    if guard:
        return guard
    return render_template('repositorios/repositorios_view.html')
