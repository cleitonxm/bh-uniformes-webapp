import os
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# -----------------------------------------------------------
# Configuração de banco (Render usa DATABASE_URL)
# -----------------------------------------------------------
db_url = os.getenv("DATABASE_URL", "sqlite:///clientes.db")
# Compatibilidade: alguns providers entregam "postgres://" (antigo)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Opções de engine para responder mais rápido/estável no Render
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 0,
    "pool_recycle": 300,
}

db = SQLAlchemy(app)


# -----------------------------------------------------------
# Modelo
# -----------------------------------------------------------
class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Cliente {self.id} - {self.nome}>"


# -----------------------------------------------------------
# Inicializa tabelas no primeiro boot do app
# (mais seguro do que criar na importação quando usamos gunicorn --preload)
# -----------------------------------------------------------
@app.before_first_request
def init_db():
    with app.app_context():
        db.create_all()


# -----------------------------------------------------------
# Health check (Render vai bater aqui pra saber se está ok)
# -----------------------------------------------------------
@app.get("/health")
def health():
    return "ok", 200


# -----------------------------------------------------------
# Rotas
# -----------------------------------------------------------
@app.get("/")
def index():
    return redirect(url_for("lista_clientes"))

@app.get("/clientes")
def lista_clientes():
    clientes = Cliente.query.order_by(Cliente.id.desc()).all()
    return render_template("clientes.html", clientes=clientes)

# Se seu template usa: action="{{ url_for('adicionar') }}"
@app.post("/adicionar")
def adicionar():
    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip()
    telefone = (request.form.get("telefone") or "").strip()

    if not nome:
        # Nome é obrigatório
        return redirect(url_for("lista_clientes"))

    novo = Cliente(nome=nome, email=email or None, telefone=telefone or None)
    db.session.add(novo)
    db.session.commit()
    return redirect(url_for("lista_clientes"))

# Botão "Excluir" pode estar como link (GET) ou form (POST); aceitamos os dois
@app.route("/excluir/<int:cliente_id>", methods=["POST", "GET"])
def excluir(cliente_id: int):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        abort(404)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for("lista_clientes"))


# -----------------------------------------------------------
# Execução local (opcional)
# -----------------------------------------------------------
if __name__ == "__main__":
    # Para rodar localmente: python app.py
    # Depois acesse http://127.0.0.1:5000/clientes
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
