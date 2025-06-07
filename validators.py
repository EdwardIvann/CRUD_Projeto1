# validators.py
import re


def validar_nome_completo(nome):
    """Verifica se o nome contém pelo menos duas palavras (nome e sobrenome)."""
    partes_nome = nome.strip().split(' ')
    return len(partes_nome) >= 2 and all(len(parte) > 0 for parte in partes_nome)


def validar_email(email):
    """Valida o formato do email para ter letras, números e domínios específicos."""
    padrao_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(padrao_email, email) is not None


def validar_senha(senha):
    """Valida a senha para ter letras, números e no mínimo 8 caracteres."""
    if len(senha) < 8:
        return False
    tem_letra = re.search(r'[a-zA-Z]', senha)
    tem_numero = re.search(r'[0-9]', senha)
    return tem_letra is not None and tem_numero is not None
