# ui.py
import json
from datetime import datetime
import services
from validators import validar_nome_completo, validar_email, validar_senha
from config import TIPO_USUARIO_COMUM, TIPO_COLABORADOR, TIPO_ADMINISTRADOR
from database_manager import Usuario  # Usando 'Usuario' como o DAO

# --- Funções Auxiliares de UI ---


def obter_input_validado(prompt, validador, mensagem_erro):
    while True:
        valor = input(prompt).strip()
        if validador(valor):
            return valor
        print(mensagem_erro)


def input_idade(prompt, valor_atual=None):
    display_atual = f" ({valor_atual})" if valor_atual is not None else " (opcional)"
    while True:
        entrada = input(f"{prompt}{display_atual}: ").strip()
        if not entrada and valor_atual is not None:
            return valor_atual
        if not entrada and valor_atual is None:
            return None
        try:
            return int(entrada)
        except ValueError:
            print(
                "Idade inválida. Por favor, digite um número inteiro ou deixe em branco para manter/ignorar.")

# --- Lógica do Fluxo do Usuário Comum Pós-Login ---


def processar_fluxo_usuario_logado(usuario_data_completa):
    usuario_id = usuario_data_completa[0]
    nome_usuario = usuario_data_completa[1]
    respostas_q_json = usuario_data_completa[6]
    pet_sugerido_existente = usuario_data_completa[7]
    # respostas_pet_apoio_json = usuario_data_completa[8] # String JSON, será parseada em obter_dados_completos_usuario

    print(
        f"\nLogin como Usuário bem-sucedido. Bem-vindo(a), {nome_usuario.split(' ')[0]}!")
    ui_registrar_humor_diario(usuario_id, nome_usuario)

    try:
        respostas_questionario_existente = json.loads(
            respostas_q_json) if respostas_q_json else None
    except json.JSONDecodeError:
        print("Erro ao ler respostas do questionário de bem-estar.")
        respostas_questionario_existente = None

    if respostas_questionario_existente:
        print("\nPercebemos que você já preencheu nosso questionário. Vamos direto às indicações!")
        ui_exibir_indicacoes()
        ui_secao_pet_apoio(usuario_id, nome_usuario, pet_sugerido_existente)
        ui_solicitar_contato_profissional()
        ui_feedback_indicacoes()
    else:
        print("\nÉ sua primeira vez preenchendo o questionário principal ou ele não foi salvo.")
        print("Para te conhecermos melhor, por favor, responda a algumas perguntas.")
        # Retorna lista de dicts
        respostas_coletadas_lista = ui_realizar_questionario_bem_estar()
        services.processar_questionario_bem_estar(
            usuario_id, respostas_coletadas_lista)
        print("Suas respostas foram salvas!")
        ui_solicitar_contato_profissional()
        ui_exibir_indicacoes()
        ui_secao_pet_apoio(usuario_id, nome_usuario, None)
        ui_feedback_indicacoes()
    print(
        f"\nObrigado por usar o SafeSpace, {nome_usuario.split(' ')[0]}. Sessão encerrada.")

# --- Função de Login Unificado ---


def realizar_login_unificado():
    print("\n--- LOGIN SAFESPACE ---")
    email = input("Digite seu email: ").strip()
    senha = input("Digite sua senha: ").strip()
    usuario_data_completa = services.autenticar_e_obter_dados_completos(
        email, senha)
    if usuario_data_completa:
        user_type = usuario_data_completa[5]
        if user_type == TIPO_ADMINISTRADOR:
            print(
                f"\nLogin como Administrador bem-sucedido. Bem-vindo(a), {usuario_data_completa[1]}!")
            menu_administrador()
        elif user_type == TIPO_COLABORADOR:
            print(
                f"\nLogin como Colaborador bem-sucedido. Bem-vindo(a), {usuario_data_completa[1]}!")
            menu_colaborador()
        elif user_type == TIPO_USUARIO_COMUM:
            processar_fluxo_usuario_logado(usuario_data_completa)
        else:
            print("Tipo de usuário desconhecido. Por favor, contate o suporte.")
    else:
        print("Falha no login: email ou senha incorretos.")

# --- Menu Principal ---


def menu_principal():
    while True:
        print("\n--- MENU PRINCIPAL SAFESPACE ---")
        print("1 - Login")
        print("2 - Cadastrar (Novo Usuário Comum)")
        print("3 - Sair")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == '1':
            realizar_login_unificado()
        elif opcao == '2':
            ui_cadastrar_usuario_comum()
        elif opcao == '3':
            print("Saindo do sistema. Até mais!")
            break
        else:
            print("Opção inválida. Tente novamente.")

# --- Funções de UI para Usuário Comum ---


def ui_cadastrar_usuario_comum():
    print("\n--- CADASTRO DE NOVO USUÁRIO ---")
    nome = obter_input_validado(
        "Digite o nome completo (nome e sobrenome): ", validar_nome_completo, "Nome inválido.")
    idade = input_idade("Digite a idade")
    while True:
        email = obter_input_validado(
            "Digite o email (ex: @hotmail.com, @gmail.com ou @outlook.com): ", validar_email, "Email inválido.")
        if not Usuario.buscar_usuario_por_email(email):
            break
        print("Este email já está cadastrado. Por favor, use outro.")
    senha = obter_input_validado(
        "Digite a senha (mínimo 8 caracteres, com letras e números): ", validar_senha, "Senha inválida.")
    resultado = services.registrar_novo_usuario(
        nome, email, senha, idade, TIPO_USUARIO_COMUM)
    print(resultado)


def ui_registrar_humor_diario(usuario_id, nome_usuario):
    print(
        f"\n--- Como você está se sentindo hoje, {datetime.now().strftime('%d/%m/%Y')}, {nome_usuario.split(' ')[0]}? ---")
    registro_existente = services.obter_registro_humor_hoje(usuario_id)
    if registro_existente:
        print(
            f"Você já registrou seu humor para hoje: '{registro_existente[3]}'.")
        return
    sentimento = input("Descreva em uma palavra ou curta frase: ").strip()
    resultado = services.registrar_sentimento_diario(usuario_id, sentimento)
    print(resultado)


def ui_realizar_questionario_bem_estar():
    print("\n--- QUESTIONÁRIO DE BEM-ESTAR ---")
    print("Responda com 'sim' ou 'não':")
    perguntas = [
        "1. Você se sente mais triste ou deprimido(a) na maior parte do tempo?",
        "2. Tem sentido menos interesse ou prazer em fazer as coisas que antes gostava?",
        "3. Está com dificuldades para dormir ou dormindo em excesso?",
        "4. Tem sentido ansiedade, nervosismo ou preocupação excessiva?",
        "5. Sente-se cansado(a) ou com pouca energia frequentemente?"
    ]
    respostas = []
    for pergunta_texto in perguntas:
        while True:
            resposta = input(f"{pergunta_texto} ").strip().lower()
            if resposta in ['sim', 'não', 'nao']:
                respostas.append(
                    {"pergunta": pergunta_texto, "resposta": resposta})
                break
            else:
                print("Resposta inválida. Digite 'sim' ou 'não'.")
    print("\nObrigado por suas respostas!")
    return respostas  # Retorna lista de dicts


def ui_exibir_indicacoes():
    print("\n" + "="*50)
    print("           INDICAÇÕES PARA O SEU BEM-ESTAR")
    # (Conteúdo das indicações como antes)
    print("- 'A Coragem de Ser Imperfeito' por Brené Brown")
    print("- 'Ansiedade: Como Enfrentar o Mal do Século' por Augusto Cury")
    print("\nLembre-se: Estas são apenas sugestões.")


def ui_realizar_questionario_pet():
    print("\n--- DESCOBRINDO SEU PET IDEAL ---")
    respostas_dict_para_logica = {}
    respostas_lista_para_db = []
    perguntas_pet = [
        {"key": "1. Qual é o seu nível de atividade física diária? (1-baixa, 2-moderada, 3-alta)",
         "pergunta": "1. Nível de atividade (1-baixa, 2-mod, 3-alta):", "tipo": "int", "min": 1, "max": 3},
        {"key": "2. Quanto tempo você pode dedicar diariamente para cuidar de um pet? (1-pouco, 2-moderado, 3-muito)",
         "pergunta": "2. Tempo diário para pet (1-pouco, 2-mod, 3-muito):", "tipo": "int", "min": 1, "max": 3},
        {"key": "3. Você mora em uma casa com quintal ou apartamento? (casa/apartamento)",
         "pergunta": "3. Moradia (casa/apartamento):", "tipo": "str", "opcoes": ["casa", "apartamento"]},
        {"key": "4. Você prefere um pet que seja mais independente ou que precise de muita atenção? (independente/muita atencao)",
         "pergunta": "4. Atenção do pet (independente/muita atencao):", "tipo": "str", "opcoes": ["independente", "muita atencao"]},
        {"key": "5. Você tem alguma alergia a pelos de animais? (sim/não)",
         "pergunta": "5. Alergia a pelos (sim/não):", "tipo": "str", "opcoes": ["sim", "não", "nao"]},
        {"key": "6. Você prefere pets de grande, médio ou pequeno porte? (grande/medio/pequeno)",
         "pergunta": "6. Porte preferido (grande/medio/pequeno):", "tipo": "str", "opcoes": ["grande", "medio", "pequeno"]}
    ]
    for item_config in perguntas_pet:
        while True:
            resposta_str = input(f"{item_config['pergunta']} ").strip().lower()
            valido = False
            valor_resposta = None
            if item_config["tipo"] == "int":
                try:
                    num_resposta = int(resposta_str)
                    if item_config["min"] <= num_resposta <= item_config["max"]:
                        valido = True
                        valor_resposta = num_resposta
                except ValueError:
                    print(
                        f"Inválido. Número entre {item_config['min']}-{item_config['max']}.")
            elif item_config["tipo"] == "str":
                if resposta_str in item_config["opcoes"]:
                    valido = True
                    valor_resposta = resposta_str
                else:
                    print(
                        f"Inválido. Opções: {', '.join(item_config['opcoes'])}.")
            if valido:
                # Chave completa para lógica
                respostas_dict_para_logica[item_config["key"]] = valor_resposta
                respostas_lista_para_db.append(
                    # Salva chave completa
                    {"pergunta": item_config["key"], "resposta": valor_resposta})
                break
    return respostas_dict_para_logica, respostas_lista_para_db


def ui_secao_pet_apoio(usuario_id, nome_usuario, pet_sugerido_existente):
    print("\n" + "="*50 +
          f"\n           PETS DE APOIO EMOCIONAL PARA {nome_usuario.split(' ')[0]}\n" + "="*50)
    if pet_sugerido_existente:
        print(
            f"\nLembramos: seu pet de apoio sugerido foi: **{pet_sugerido_existente}**!")
        if input("Responder novamente para nova sugestão? (sim/não): ").lower() != 'sim':
            print("Ok, mantendo sugestão anterior.")
            return
    else:
        print("\nPets podem ser incríveis aliados para a saúde mental.")

    if input("Gostaria de preencher um formulário para encontrar seu pet ideal? (sim/não): ").lower() == 'sim':
        respostas_dict_logica, respostas_lista_para_db = ui_realizar_questionario_pet()
        sugestao_nova = services.processar_questionario_pet_e_sugerir(
            usuario_id,
            respostas_dict_logica,
            respostas_lista_para_db  # Passando a lista correta
        )
        if sugestao_nova:
            print(
                f"\nSeu pet ideal é: **{sugestao_nova}**! Ele combina com você.")
        else:
            print("\nNão foi possível gerar uma sugestão ou houve erro ao salvar.")
        print("\nLembre-se: ter um pet é uma decisão séria. Pesquise e considere adoção!")
    else:
        print("\nEntendido. O apoio emocional pode vir de diversas formas!")


def ui_solicitar_contato_profissional():
    if input("\nDeseja falar com um profissional agora? (sim/não): ").lower() == 'sim':
        ui_encaminhar_para_colaborador()
    else:
        print("\nEntendido. Estamos aqui se precisar.")


def ui_encaminhar_para_colaborador():
    colaboradores = services.obter_colaboradores_para_encaminhamento()
    if not colaboradores:
        print("\nDesculpe, não há colaboradores disponíveis.")
        return
    print("\n--- NOSSOS COLABORADORES DISPONÍVEIS ---")
    for i, nome in enumerate(colaboradores):
        print(f"{i+1}. {nome}")
    print("\nVocê pode contatá-los para apoio.")


def ui_feedback_indicacoes():
    print("\n--- SEU FEEDBACK É IMPORTANTE ---")
    input("Pressione Enter após realizar ao menos duas indicações para dar seu feedback.")
    if input("Sentiu melhora no humor após as indicações? (sim/não): ").lower() == 'sim':
        print("Que ótimo! Ficamos felizes em ajudar.")
    else:
        print("Entendido. O processo de cuidado é contínuo.")
    print("Agradecemos seu feedback!")

# --- Menus de Colaborador e Administrador (Pós-Login) ---


def menu_colaborador():
    while True:
        print("\n--- MENU COLABORADOR ---")
        print("1. Listar usuários comuns\n2. Visualizar detalhes do usuário\n3. Logout")
        op = input("Opção: ").strip()
        if op == '1':
            ui_listar_usuarios_comuns()
        elif op == '2':
            ui_visualizar_detalhes_usuario_colab()
        elif op == '3':
            print("Saindo do menu colaborador.")
            break
        else:
            print("Opção inválida.")


def ui_listar_usuarios_comuns():
    print("\n--- USUÁRIOS COMUNS ---")
    usuarios = Usuario.listar_usuarios_por_tipo(TIPO_USUARIO_COMUM)
    if not usuarios:
        print("Nenhum usuário comum.")
        return
    print(f"{'ID':<5}{'Nome':<20}{'Idade':<10}\n" + "-" * 37)
    for uid, nome, idade in usuarios:
        print(f"{uid:<5}{nome:<20}{idade if idade is not None else '-':<10}")


def ui_visualizar_detalhes_usuario_colab():
    ui_listar_usuarios_comuns()
    try:
        user_id = int(input("\nID do usuário para ver detalhes: "))
    except ValueError:
        print("ID inválido.")
        return

    dados = services.obter_dados_completos_usuario(user_id)
    if not dados:
        print("Usuário não encontrado ou não é comum.")
        return

    print(f"\n--- DETALHES DE {dados['nome']} (ID: {user_id}) ---")
    print("\n**Questionário de Bem-Estar:**")
    if dados['respostas_questionario_bem_estar']:
        for item in dados['respostas_questionario_bem_estar']:
            print(
                f"- {item.get('pergunta', 'N/A')}: **{item.get('resposta', 'N/A').upper()}**")
    else:
        print("  (Não respondido)")

    print(
        f"\n**Pet Sugerido:**\n  {dados['pet_sugerido'] if dados['pet_sugerido'] else '(Nenhum)'}")

    print("\n**Questionário de Preferências de Pet:**")
    pet_q_data = dados['respostas_questionario_pet_apoio']
    if pet_q_data and isinstance(pet_q_data, list):
        for item in pet_q_data:
            if isinstance(item, dict):
                print(
                    f"- {item.get('pergunta', 'N/A')}: **{item.get('resposta', 'N/A')}**")
            else:
                print(f"  - Item malformado: {item}")
    elif pet_q_data:  # Existe mas não é lista
        print(
            f"  Dados de questionário de pet em formato inesperado (Tipo: {type(pet_q_data)}): {pet_q_data}")
    else:
        print("  (Não respondido)")

    print("\n**Histórico de Humor (Últimos 7):**")
    if dados['historico_humor']:
        print(f"{'Data':<12}{'Sentimento':<25}\n" + "-" * 37)
        for data, sentimento in dados['historico_humor']:
            print(f"{data:<12}{sentimento:<25}")
    else:
        print("  (Nenhum registro)")


def menu_administrador():
    while True:
        print("\n--- MENU ADMINISTRADOR ---")
        print("1. Inserir usuário\n2. Listar todos\n3. Atualizar usuário\n4. Deletar usuário\n5. Logout")
        op = input("Opção: ").strip()
        if op == '1':
            ui_cadastro_geral_usuario_admin()
        elif op == '2':
            ui_listar_todos_usuarios_admin()
        elif op == '3':
            ui_atualizar_usuario_admin()
        elif op == '4':
            ui_deletar_usuario_admin()
        elif op == '5':
            print("Saindo do menu administrador.")
            break
        else:
            print("Opção inválida.")


def ui_cadastro_geral_usuario_admin():
    print("\n--- CADASTRO (ADMIN) ---")
    nome = obter_input_validado(
        "Nome completo: ", validar_nome_completo, "Inválido.")
    idade = input_idade("Idade")
    while True:
        email = obter_input_validado("Email: ", validar_email, "Inválido.")
        if not Usuario.buscar_usuario_por_email(email):
            break
        print("Email já cadastrado.")
    senha = obter_input_validado("Senha: ", validar_senha, "Inválida.")
    while True:
        try:
            tipo = int(input("Tipo (1-Usuário, 2-Colab, 3-Admin): ").strip())
            if tipo in [1, 2, 3]:
                break
            else:
                print("Tipo 1, 2 ou 3.")
        except ValueError:
            print("Inválido.")
    print(services.registrar_novo_usuario(nome, email, senha, idade, tipo))


def ui_listar_todos_usuarios_admin():
    print("\n--- TODOS OS USUÁRIOS ---")
    users = Usuario.listar_todos_usuarios()
    if not users:
        print("Nenhum usuário.")
        return
    print(f"{'ID':<5}{'Nome':<20}{'Email':<30}{'Senha':<15}{'Idade':<7}{'Tipo':<6}\n" + "-"*90)
    for uid, nome, email, pwd, idade, tipo in users:
        print(
            f"{uid:<5}{nome:<20}{email:<30}{pwd:<15}{idade if idade is not None else '-':<7}{tipo:<6}")


def ui_atualizar_usuario_admin():
    print("\n--- ATUALIZAR USUÁRIO (ADMIN) ---")
    try:
        user_id = int(input("ID do usuário a atualizar: "))
    except ValueError:
        print("ID inválido.")
        return

    user_data = Usuario.buscar_usuario_por_id(user_id)
    if not user_data:
        print("Usuário não encontrado.")
        return

    _, nome_at, email_at, senha_at, idade_at, _ = user_data[:6]
    print(f"Editando: {nome_at} (ID: {user_id})")
    nome_n = input(f"Novo nome ({nome_at}): ").strip() or nome_at
    # ... (validação e lógica de atualização como antes)
    idade_n = input_idade(
        f"Nova idade ({idade_at if idade_at is not None else '-'})", idade_at)
    email_n = input(f"Novo email ({email_at}): ").strip() or email_at
    senha_n = input(f"Nova senha (vazio para não mudar): ").strip() or senha_at

    print(services.atualizar_info_usuario(
        user_id, nome_n, email_n, senha_n, idade_n))


def ui_deletar_usuario_admin():
    print("\n--- DELETAR USUÁRIO (ADMIN) ---")
    try:
        user_id = int(input("ID do usuário a deletar: "))
    except ValueError:
        print("ID inválido.")
        return
    print(services.deletar_usuario_por_id(user_id))

# As funções de login específico como ui_login_usuario, ui_login_colaborador,
# ui_login_administrador e menu_usuario_principal foram removidas pois
# o fluxo de login agora é centralizado em realizar_login_unificado()
# e o menu principal foi simplificado.
