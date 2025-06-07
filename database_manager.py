# backend/database_manager.py
import sqlite3
import json
# Garanta que config.py está acessível
from config import DATABASE_NAME, TIPO_ADMINISTRADOR, TIPO_COLABORADOR, TIPO_USUARIO_COMUM


def conectar():
    """Cria a conexão com o banco de dados SQLite."""
    return sqlite3.connect(DATABASE_NAME)


def criar_tabelas_iniciais():
    """Cria as tabelas 'usuarios' e 'humor_diario' e o usuário admin default."""
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                idade INTEGER,
                type INTEGER,
                respostas_questionario TEXT,
                pet_sugerido TEXT,
                respostas_pet_apoio TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS humor_diario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                data TEXT NOT NULL, -- Formato YYYY-MM-DD
                sentimento TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = 'admin'")
        if cursor.fetchone()[0] == 0:
            try:
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha, type) VALUES (?, ?, ?, ?)",
                    ("Admin", "admin", "1234", TIPO_ADMINISTRADOR)
                )
                conn.commit()
                print("Usuário 'admin' default criado.")
            except sqlite3.IntegrityError:
                print("Usuário 'admin' já existe ou houve um conflito.")


class Usuario:  # Sua classe DAO para usuários
    @staticmethod
    def buscar_usuario_por_email(email):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
            return cursor.fetchone()

    @staticmethod
    def buscar_usuario_por_email_senha_tipo(email, senha, tipo_usuario):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, email, senha, idade, type, respostas_questionario, pet_sugerido, respostas_pet_apoio FROM usuarios WHERE email = ? AND senha = ? AND type = ?",
                (email, senha, tipo_usuario)
            )
            return cursor.fetchone()

    @staticmethod
    def inserir_usuario(nome, email, senha, idade, user_type, respostas_questionario=None, pet_sugerido=None, respostas_pet_apoio=None):
        with conectar() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha, idade, type, respostas_questionario, pet_sugerido, respostas_pet_apoio) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (nome, email, senha, idade, user_type,
                     json.dumps(
                         respostas_questionario) if respostas_questionario else None,
                     pet_sugerido,
                     json.dumps(respostas_pet_apoio) if respostas_pet_apoio else None)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    @staticmethod
    def listar_todos_usuarios():
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, email, senha, idade, type FROM usuarios")
            return cursor.fetchall()

    @staticmethod
    def listar_usuarios_por_tipo(tipo_usuario):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, idade FROM usuarios WHERE type = ?", (tipo_usuario,))
            return cursor.fetchall()

    @staticmethod
    def atualizar_dados_usuario(id_usuario, nome, email, senha, idade):
        with conectar() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE usuarios
                    SET nome = ?, email = ?, senha = ?, idade = ?
                    WHERE id = ?
                """, (nome, email, senha, idade, id_usuario))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    @staticmethod
    def atualizar_respostas_questionario_usuario(id_usuario, respostas_json_string):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET respostas_questionario = ? WHERE id = ?",
                (respostas_json_string, id_usuario)
            )
            conn.commit()

    @staticmethod
    def atualizar_pet_usuario(id_usuario, pet_sugerido, respostas_pet_apoio_json_string):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET pet_sugerido = ?, respostas_pet_apoio = ? WHERE id = ?",
                (pet_sugerido, respostas_pet_apoio_json_string, id_usuario)
            )
            conn.commit()

    @staticmethod
    def deletar_usuario_por_id(id_usuario):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM humor_diario WHERE usuario_id = ?", (id_usuario,))
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
            conn.commit()

    @staticmethod
    def buscar_usuario_por_id(id_usuario):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM usuarios WHERE id = ?", (id_usuario,))
            return cursor.fetchone()

    # MODIFICADO: buscar_colaboradores_com_email
    @staticmethod
    def buscar_colaboradores_com_email():  # Modificado para retornar nome e email
        with conectar() as conn:
            cursor = conn.cursor()
            # Seleciona nome e email dos colaboradores
            cursor.execute(
                "SELECT nome, email FROM usuarios WHERE type = ?", (TIPO_COLABORADOR,))
            return cursor.fetchall()  # Retorna lista de tuplas (nome, email)

    @staticmethod
    def buscar_detalhes_usuario_para_colaborador(id_usuario):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome, respostas_questionario, pet_sugerido, respostas_pet_apoio FROM usuarios WHERE id = ? AND type = ?",
                (id_usuario, TIPO_USUARIO_COMUM)
            )
            return cursor.fetchone()


class HumorDiarioDAO:
    @staticmethod
    def inserir_humor_diario(usuario_id, data, sentimento):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO humor_diario (usuario_id, data, sentimento) VALUES (?, ?, ?)",
                (usuario_id, data, sentimento)
            )
            conn.commit()

    @staticmethod
    # data no formato 'YYYY-MM-DD'
    def buscar_humor_diario_usuario_data(usuario_id, data):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, usuario_id, data, sentimento FROM humor_diario WHERE usuario_id = ? AND data = ?",
                (usuario_id, data)
            )
            return cursor.fetchone()

    @staticmethod
    def buscar_historico_humor_usuario(id_usuario, limite=7):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, sentimento FROM humor_diario WHERE usuario_id = ? ORDER BY data DESC LIMIT ?",
                (id_usuario, limite)
            )
            return cursor.fetchall()

    # NOVO MÉTODO:
    @staticmethod
    def buscar_humor_mensal(usuario_id, ano, mes):
        """Busca todos os registros de humor para um usuário em um ano/mês específico.
           Retorna um dicionário {dia: sentimento}."""
        # Formata o mês para ter dois dígitos (ex: 7 -> '07')
        mes_formatado = f"{mes:02d}"
        data_inicio = f"{ano}-{mes_formatado}-01"
        # Para o fim do mês, podemos usar um truque ou calcular o último dia.
        # Aqui, vamos buscar todos que começam com 'AAAA-MM-'
        data_like = f"{ano}-{mes_formatado}-%"

        humores_do_mes = {}
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, sentimento FROM humor_diario WHERE usuario_id = ? AND data LIKE ?",
                (usuario_id, data_like)
            )
            for row in cursor.fetchall():
                # Extrai o dia da data 'YYYY-MM-DD'
                try:
                    dia = int(row[0].split('-')[2])
                    # Armazena sentimento para o dia
                    humores_do_mes[dia] = row[1]
                except (IndexError, ValueError):
                    print(
                        f"Formato de data inválido encontrado no banco: {row[0]}")
        return humores_do_mes
