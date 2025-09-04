import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Config do banco ---
# Pega a URL do banco do Render (DATABASE_URL) e cai para SQLite local se não existir.
db_url = os.getenv("DATABASE_URL", "sqlite:///clientes.db")

# Render costuma fornecer "postgres://" — o SQLAlchemy moderno precisa do driver explícito.
# Forçamos o driver do psycopg (v3): "postgresql+psycopg://"
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
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(50))

# Cria as tabelas na primeira execução
with app.app_context():
    db.create_all()

# --- Rotas ---
@app.route("/")
def home():
    return redirect(url_for("clientes"))

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()

        if nome:
            c = Cliente(nome=nome, email=email, telefone=telefone)
            db.session.add(c)
            db.session.commit()
        return redirect(url_for("clientes"))

    # GET
    lista = Cliente.query.order_by(Cliente.id.desc()).all()
    return render_template("clientes.html", clientes=lista)

@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("clientes"))

if __name__ == "__main__":
    # Para rodar localmente: python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
