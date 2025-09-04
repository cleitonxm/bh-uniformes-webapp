import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- URL do banco ---
db_url = os.getenv("DATABASE_URL", "sqlite:///clientes.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

db = SQLAlchemy(app)

# --- Modelo ---
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))      # validaremos unicidade na aplicação
    telefone = db.Column(db.String(50))

with app.app_context():
    db.create_all()

# --- Validações auxiliares ---
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))

def email_exists(email: str) -> bool:
    # Busca case-insensitive
    return (
        Cliente.query.filter(db.func.lower(Cliente.email) == email.lower()).first()
        is not None
    )

# --- Rotas ---
@app.route("/")
def home():
    return redirect(url_for("clientes"))

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()

        errors = []

        # Nome obrigatório
        if not nome:
            errors.append("O nome é obrigatório.")

        # E-mail: opcional, mas se vier precisa ser válido
        if email and not is_valid_email(email):
            errors.append("Informe um e-mail válido.")

        # E-mail: não pode repetir (se informado)
        if email and email_exists(email):
            errors.append("Esse e-mail já está cadastrado.")

        if errors:
            # Renderiza a página com os erros e mantém os dados do formulário
            for e in errors:
                flash(e, "error")
            lista = Cliente.query.order_by(Cliente.id.desc()).all()
            form_backup = {"nome": nome, "email": email, "telefone": telefone}
            return render_template("clientes.html", clientes=lista, form=form_backup)

        # Sucesso -> salva e redireciona (PRG)
        c = Cliente(nome=nome, email=email or None, telefone=telefone or None)
        db.session.add(c)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for("clientes"))

    lista = Cliente.query.order_by(Cliente.id.desc()).all()
    return render_template("clientes.html", clientes=lista, form={})

@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    db.session.delete(c)
    db.session.commit()
    flash("Cliente excluído.", "success")
    return redirect(url_for("clientes"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
