"""
seed.py — Cria o banco de dados e popula os dados iniciais.
Execute uma vez antes de subir o servidor pela primeira vez.

Uso:
    python seed.py
"""

import getpass
import sys

from app.database import Base, engine, SessionLocal
from app.models import Categoria, Usuario, Produto, Movimentacao  # garante que os models são registrados
from app import auth


def criar_tabelas():
    Base.metadata.create_all(bind=engine)
    print("✓ Tabelas verificadas/criadas.")


def seed_categorias(db):
    categorias = [
        {"nome": "LIMPEZA",    "descricao": "Produtos de higiene e limpeza geral"},
        {"nome": "COZINHA",    "descricao": "Itens de copa e cozinha"},
        {"nome": "ESCRITÓRIO", "descricao": "Materiais de expediente e papelaria"},
    ]
    criadas = 0
    for dados in categorias:
        if not db.query(Categoria).filter_by(nome=dados["nome"]).first():
            db.add(Categoria(**dados))
            criadas += 1
    db.commit()
    print(f"✓ Categorias: {criadas} criada(s) ({len(categorias) - criadas} já existia(m)).")


def seed_admin(db):
    if db.query(Usuario).filter_by(login="admin").first():
        print("✓ Usuário 'admin' já existe — nenhuma alteração feita.")
        return

    print("\nCrie a senha para o usuário administrador (login: admin):")
    while True:
        senha = getpass.getpass("  Senha (mín. 8 caracteres): ")
        if len(senha) < 8:
            print("  Senha muito curta. Tente novamente.")
            continue
        confirmacao = getpass.getpass("  Confirme a senha: ")
        if senha != confirmacao:
            print("  As senhas não coincidem. Tente novamente.")
            continue
        break

    admin = Usuario(
        nome="Administrador",
        login="admin",
        senhaHash=auth.criar_hash(senha),
        perfil="ADMINISTRADOR",
    )
    db.add(admin)
    db.commit()
    print("✓ Usuário 'admin' criado com sucesso.")


def main():
    print("=== ASAC — Seed do banco de dados ===\n")
    criar_tabelas()

    db = SessionLocal()
    try:
        seed_categorias(db)
        seed_admin(db)
    finally:
        db.close()

    print("\nPronto! Suba o servidor com:")
    print("  uvicorn app.main:app --reload")
    print("  Acesse: http://localhost:8000/ui/login.html")


if __name__ == "__main__":
    main()
