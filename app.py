import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Usa Postgres do Render se disponível, senão cai para SQLite (para testes locais)
db_url = os.getenv("DATABASE_URL", "sqlite:///clientes.db")
db_url = db_url.replace("postgres://", "postgresql://")  # compatibilidade
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Modelo Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(50))

# Cria tabelas no primeiro start
with app.app_context():
    db.create_all()

# Página inicial: lista de clientes
@app.route("/")
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.id.desc()).all()
    return render_template("clientes.html", clientes=clientes)

# Adicionar cliente
@app.route("/adicionar", methods=["POST"])
def adicionar():
    nome = request.form["nome"].strip()
    if not nome:
        return redirect(url_for("listar_clientes"))
    email = request.form.get("email", "").strip()
    telefone = request.form.get("telefone", "").strip()
    db.session.add(Cliente(nome=nome, email=email, telefone=telefone))
    db.session.commit()
    return redirect(url_for("listar_clientes"))

# Apagar cliente
@app.route("/deletar/<int:id>")
def deletar(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for("listar_clientes"))

if __name__ == "__main__":
    app.run(debug=True)
