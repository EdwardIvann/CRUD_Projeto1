# backend/services.py
import json
import random
import database_manager  # Importa o módulo todo
from datetime import datetime
from database_manager import Usuario, HumorDiarioDAO  # Importa as classes DAO
from config import TIPO_USUARIO_COMUM, TIPO_COLABORADOR, TIPO_ADMINISTRADOR  # Importa config

# ... (autenticar_usuario, autenticar_e_obter_dados_completos, registrar_novo_usuario - como estavam) ...


def autenticar_usuario(email, senha, tipo_usuario):
    return Usuario.buscar_usuario_por_email_senha_tipo(email, senha, tipo_usuario)


def autenticar_e_obter_dados_completos(email, senha):
    with database_manager.conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, email, senha, idade, type, respostas_questionario, pet_sugerido, respostas_pet_apoio FROM usuarios WHERE email = ? AND senha = ?",
            (email, senha)
        )
        return cursor.fetchone()


def registrar_novo_usuario(nome, email, senha, idade, user_type):
    if Usuario.buscar_usuario_por_email(email):
        return "Email já cadastrado."
    user_id = Usuario.inserir_usuario(nome, email, senha, idade, user_type)
    return "Usuário cadastrado com sucesso." if user_id else "Erro ao cadastrar usuário."


def atualizar_info_usuario(id_usuario, nome, email, senha, idade):
    # ... (como antes)
    usuario_existente = Usuario.buscar_usuario_por_id(id_usuario)
    if not usuario_existente:
        return "Usuário não encontrado."
    if email != usuario_existente[2] and Usuario.buscar_usuario_por_email(email) and Usuario.buscar_usuario_por_email(email)[0] != id_usuario:
        return "Este email já está cadastrado para outro usuário."
    return "Usuário atualizado com sucesso." if Usuario.atualizar_dados_usuario(id_usuario, nome, email, senha, idade) else "Erro ao atualizar usuário."


def deletar_usuario_por_id(id_usuario):
    # ... (como antes)
    usuario_a_deletar = Usuario.buscar_usuario_por_id(id_usuario)
    if not usuario_a_deletar:
        return "Usuário não encontrado."
    if usuario_a_deletar[2] == "admin" and usuario_a_deletar[0] == 1:
        return "Proibido deletar o usuário 'admin' default."
    Usuario.deletar_usuario_por_id(id_usuario)
    return "Usuário e seus registros de humor excluídos com sucesso."


def processar_questionario_bem_estar(usuario_id, respostas_lista_de_dict):
    # ... (como antes)
    try:
        Usuario.atualizar_respostas_questionario_usuario(
            usuario_id, json.dumps(respostas_lista_de_dict))
    except TypeError as e:
        print(f"Erro JSON (bem-estar): {e}")


def logica_sugestao_pet(respostas_dict_para_logica):
    # ... (como antes, apenas exemplo) ...
    sugestao_pet = "Gato (sugestão padrão)"
    try:
        alergia = respostas_dict_para_logica.get(
            "5. Você tem alguma alergia a pelos de animais? (sim/não)", "não")
        if alergia == 'sim':
            sugestao_pet = "Peixe"
    except Exception:
        pass  # Evitar quebrar se a chave não existir
    return sugestao_pet


def processar_questionario_pet_e_sugerir(usuario_id, respostas_dict_para_logica, respostas_lista_para_salvar):
    # ... (como antes, já corrigido para salvar respostas_lista_para_salvar) ...
    sugestao = logica_sugestao_pet(respostas_dict_para_logica)
    try:
        Usuario.atualizar_pet_usuario(
            usuario_id, sugestao, json.dumps(respostas_lista_para_salvar))
    except Exception as e:
        print(f"Erro ao salvar pet: {e}")
        return None
    return sugestao


def registrar_sentimento_diario(usuario_id, sentimento):
    # ... (como antes) ...
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    if HumorDiarioDAO.buscar_humor_diario_usuario_data(usuario_id, data_hoje):
        return "Humor já registrado hoje."
    if sentimento:
        HumorDiarioDAO.inserir_humor_diario(usuario_id, data_hoje, sentimento)
        return "Sentimento registrado."
    return "Nenhum sentimento fornecido."


def obter_registro_humor_hoje(usuario_id):
    # ... (como antes) ...
    return HumorDiarioDAO.buscar_humor_diario_usuario_data(usuario_id, datetime.now().strftime("%Y-%m-%d"))

# MODIFICADO:


def obter_colaboradores_para_encaminhamento(quantidade=20):
    """Retorna uma lista de tuplas (nome, email) de colaboradores."""
    # Usuario.buscar_colaboradores_com_email() agora retorna (nome, email)
    # MODIFICADO para chamar o método que retorna email
    todos_colaboradores = Usuario.buscar_colaboradores_com_email()
    if not todos_colaboradores:
        return []
    if len(todos_colaboradores) <= quantidade:
        return todos_colaboradores
    return random.sample(todos_colaboradores, quantidade)

# NOVO SERVIÇO:


def obter_humor_mensal(usuario_id, ano, mes):
    """Busca os registros de humor de um usuário para um dado mês/ano."""
    return HumorDiarioDAO.buscar_humor_mensal(usuario_id, ano, mes)


def obter_dados_completos_usuario(id_usuario):
    # ... (como antes, já corrigido e sem o alerta) ...
    detalhes_usuario_tupla = Usuario.buscar_detalhes_usuario_para_colaborador(
        id_usuario)
    if not detalhes_usuario_tupla:
        return None
    nome_usuario, respostas_q_json, pet_sugerido, respostas_pa_json_str = detalhes_usuario_tupla
    respostas_questionario, respostas_pet_apoio = [], []
    if respostas_q_json:
        try:
            respostas_questionario = json.loads(respostas_q_json)
        except json.JSONDecodeError:
            print(f"Erro JSON bem-estar user {id_usuario}")
    if respostas_pa_json_str:
        try:
            parsed_data = json.loads(respostas_pa_json_str)
            if isinstance(parsed_data, list):
                respostas_pet_apoio = parsed_data
        except json.JSONDecodeError:
            print(f"Erro JSON pet user {id_usuario}")
    historico_humor = HumorDiarioDAO.buscar_historico_humor_usuario(id_usuario)
    return {"nome": nome_usuario, "respostas_questionario_bem_estar": respostas_questionario,
            "pet_sugerido": pet_sugerido, "respostas_questionario_pet_apoio": respostas_pet_apoio,
            "historico_humor": historico_humor}
