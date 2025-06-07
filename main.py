# main.py (Ponto de entrada para a estrutura modularizada)

# Importa as funções necessárias dos seus módulos
from database_manager import criar_tabelas_iniciais
from ui import menu_principal  # menu_principal do seu ui.py modularizado e corrigido

if __name__ == "__main__":
    print("Inicializando SafeSpace...")
    try:
        criar_tabelas_iniciais()  # Garante que as tabelas e o admin default existam
        # print("Banco de dados verificado/inicializado.")
    except Exception as e:
        print(f"ERRO CRÍTICO ao inicializar o banco de dados: {e}")
        print("A aplicação não pode continuar.")
    else:
        menu_principal()          # Inicia a interface do usuário do console

    print("SafeSpace finalizado.")
