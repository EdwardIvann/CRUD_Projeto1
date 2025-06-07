# populate_db.py
import sqlite3
import json
import random
from datetime import datetime, timedelta

# Imports dos seus módulos
try:
    from database_manager import criar_tabelas_iniciais, Usuario, HumorDiarioDAO, conectar
    from config import TIPO_COLABORADOR, TIPO_USUARIO_COMUM
    from services import logica_sugestao_pet  # Para gerar sugestão de pet coerente
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Certifique-se de que populate_db.py está no mesmo diretório que os outros módulos backend,")
    print("ou que o PYTHONPATH está configurado corretamente.")
    exit()

# --- Dados de Amostra (como antes) ---
FIRST_NAMES = ["Alice", "Bruno", "Clara", "Davi", "Elisa", "Felipe", "Gabriela", "Heitor", "Isabela", "João",
               "Laura", "Miguel", "Natália", "Otávio", "Patrícia", "Rodrigo", "Sofia", "Thiago", "Valentina", "William"]
LAST_NAMES = ["Alves", "Barros", "Cardoso", "Dias", "Esteves", "Freitas", "Gomes", "Henriques", "Iglesias", "Jesus",
              "Klein", "Lopes", "Martins", "Nogueira", "Oliveira"]
DOMAINS = ["example.com", "test.org", "sample.net", "demo.co"]
SIMPLE_PASSWORD = "Password@123"  # Senha um pouco mais forte

BEM_ESTAR_PERGUNTAS = [
    "1. Você se sente mais triste ou deprimido(a) na maior parte do tempo?",
    "2. Tem sentido menos interesse ou prazer em fazer as coisas que antes gostava?",
    "3. Está com dificuldades para dormir ou dormindo em excesso?",
    "4. Tem sentido ansiedade, nervosismo ou preocupação excessiva?",
    "5. Sente-se cansado(a) ou com pouca energia frequentemente?"
]

PET_PERGUNTAS_CONFIG = [
    {"key": "1. Qual é o seu nível de atividade física diária? (1-baixa, 2-moderada, 3-alta)",
     "tipo": "int", "min": 1, "max": 3},
    {"key": "2. Quanto tempo você pode dedicar diariamente para cuidar de um pet? (1-pouco, 2-moderado, 3-muito)",
     "tipo": "int", "min": 1, "max": 3},
    {"key": "3. Você mora em uma casa com quintal ou apartamento? (casa/apartamento)", "tipo": "str", "opcoes": [
        "casa", "apartamento"]},
    {"key": "4. Você prefere um pet que seja mais independente ou que precise de muita atenção? (independente/muita atencao)", "tipo": "str", "opcoes": [
        "independente", "muita atencao"]},
    {"key": "5. Você tem alguma alergia a pelos de animais? (sim/não)", "tipo": "str", "opcoes": [
        "sim", "não"]},
    {"key": "6. Você prefere pets de grande, médio ou pequeno porte? (grande/medio/pequeno)", "tipo": "str", "opcoes": [
        "grande", "medio", "pequeno"]}
]

HUMOR_SENTIMENTOS = ["Feliz", "Triste", "Normal",
                     "Ansioso(a)", "Cansado(a)", "Estressado(a)", "Contente", "Animado(a)", "Irritado(a)", "Relaxado(a)"]

# --- Funções Geradoras de Dados (como antes, com pequenas melhorias) ---


def generate_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_random_email(name, existing_emails):
    name_parts = name.lower().split(" ")
    base_email = f"{name_parts[0]}.{name_parts[-1]}"  # Ex: ana.oliveira
    email = f"{base_email}@{random.choice(DOMAINS)}"
    count = 0
    while email in existing_emails:
        count += 1
        email = f"{base_email}{count}@{random.choice(DOMAINS)}"
    existing_emails.add(email)
    return email


def generate_random_age(min_age=18, max_age=65):
    return random.randint(min_age, max_age)


def generate_bem_estar_respostas():
    respostas = []
    for pergunta_texto in BEM_ESTAR_PERGUNTAS:
        respostas.append({"pergunta": pergunta_texto,
                         "resposta": random.choice(["sim", "não"])})
    return respostas


def generate_pet_respostas():
    respostas_dict_para_logica = {}
    respostas_lista_para_db = []
    for p_config in PET_PERGUNTAS_CONFIG:
        if p_config["tipo"] == "int":
            valor = random.randint(p_config["min"], p_config["max"])
        else:  # str
            valor = random.choice(p_config["opcoes"])
        respostas_dict_para_logica[p_config["key"]] = valor
        # Salva a chave completa da pergunta para facilitar a leitura humana no JSON se necessário
        respostas_lista_para_db.append(
            {"pergunta": p_config["key"], "resposta": valor})
    return respostas_dict_para_logica, respostas_lista_para_db


def populate():
    print("Iniciando a população do banco de dados com dados de teste...")

    try:
        criar_tabelas_iniciais()
        print("Tabelas verificadas/criadas.")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        return

    existing_emails = set()
    admin_default = Usuario.buscar_usuario_por_email("admin")
    if admin_default:
        existing_emails.add(admin_default[2])

    # --- Adicionar 10 Colaboradores ---
    print("\nAdicionando Colaboradores...")
    for i in range(10):
        nome = generate_random_name()
        email = generate_random_email(nome, existing_emails)
        senha = SIMPLE_PASSWORD
        idade = generate_random_age(25, 55)
        user_type = TIPO_COLABORADOR

        # Colaboradores não têm questionários ou pets respondidos
        user_id = Usuario.inserir_usuario(
            nome, email, senha, idade, user_type,
            respostas_questionario=None,
            pet_sugerido=None,
            respostas_pet_apoio=None
        )
        if user_id:
            print(
                f"  Colaborador '{nome}' (ID: {user_id}, Email: {email}) adicionado.")
        else:
            print(
                f"  Falha ao adicionar colaborador '{nome}' (email: {email}).")

    # --- Adicionar 20 Usuários Comuns ---
    print("\nAdicionando Usuários Comuns...")
    for i in range(20):
        nome = generate_random_name()
        email = generate_random_email(nome, existing_emails)
        senha = SIMPLE_PASSWORD
        idade = generate_random_age(18, 60)
        user_type = TIPO_USUARIO_COMUM

        respostas_q_bem_estar_lista = None
        pet_respostas_lista_db = None
        pet_sugerido = None

        # Chance de ter respondido ao questionário de bem-estar (ex: 70%)
        if random.random() < 0.7:
            respostas_q_bem_estar_lista = generate_bem_estar_respostas()

            # Desses, chance de ter respondido ao questionário de pet (ex: 60%)
            if random.random() < 0.6:
                pet_respostas_dict_logica, pet_respostas_lista_db_temp = generate_pet_respostas()
                pet_respostas_lista_db = pet_respostas_lista_db_temp  # Atribui a lista correta
                pet_sugerido = logica_sugestao_pet(pet_respostas_dict_logica)

        user_id = Usuario.inserir_usuario(
            nome, email, senha, idade, user_type,
            respostas_questionario=respostas_q_bem_estar_lista,
            pet_sugerido=pet_sugerido,
            respostas_pet_apoio=pet_respostas_lista_db  # Passa a lista de dicts ou None
        )

        if user_id:
            print(
                f"  Usuário Comum '{nome}' (ID: {user_id}, Email: {email}) adicionado.")

            # Adicionar histórico de humor para dias anteriores para alguns usuários (ex: 80% de chance)
            if random.random() < 0.8:
                # Mais entradas para simular uso
                num_humor_entries = random.randint(5, 20)
                print(
                    f"    Adicionando {num_humor_entries} entradas de humor para {nome}...")
                for _ in range(num_humor_entries):
                    # Humor nos últimos 2 meses
                    dias_atras = random.randint(1, 60)
                    data_humor_dt = datetime.now() - timedelta(days=dias_atras)
                    data_humor_str = data_humor_dt.strftime("%Y-%m-%d")
                    sentimento = random.choice(HUMOR_SENTIMENTOS)

                    # Evita duplicar humor para o mesmo dia (improvável com datas aleatórias, mas bom ter)
                    if not HumorDiarioDAO.buscar_humor_diario_usuario_data(user_id, data_humor_str):
                        try:
                            HumorDiarioDAO.inserir_humor_diario(
                                user_id, data_humor_str, sentimento)
                        except Exception as e_humor:
                            print(
                                f"      Erro ao inserir humor para usuário {user_id} na data {data_humor_str}: {e_humor}")
        else:
            print(
                f"  Falha ao adicionar usuário comum '{nome}' (email: {email}).")

    print("\nPopulação do banco de dados com dados de teste concluída!")
    print("IMPORTANTE: Execute este script idealmente apenas uma vez em um banco de dados novo.")


if __name__ == "__main__":
    confirm = input(
        "ATENÇÃO: Este script irá adicionar dados de teste ao banco.\n"
        "Se já existem dados, pode haver conflitos de email ou duplicação de histórico de humor.\n"
        "É recomendado executar em um banco de dados limpo ou após backup.\n"
        "Deseja continuar? (s/N): "
    ).strip().lower()
    if confirm == 's':
        populate()
    else:
        print("Operação cancelada pelo usuário.")
