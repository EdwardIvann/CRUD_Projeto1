ORIENTAÇÕES:
- Para iniciar com interface visual basta executar o programa SAFESPACE.bat:
ao iniciar o aplicativo ele criará um DataBase novo com apenas um usuario admin default, onde voce pode logar com as credenciais abaixo:
e-mail: admin
senha: 1234

- pode testar todas as opções do menu admin bem como retornar para a pagina inicial e realizar um cadastro de usuario comum e logins de usuarios criados
OBS1: usuarios do tipo colaborador e admin são incluidos apenas manualmente pelo painel admin

- Caso queira realizar um teste mais completo criamos um script para popular o banco de dados, siga os passos abaixo:
após rodar o CRUD ao menos uma vez para ele criar o DataBase, você deve executar no VScode o arquivo populate_db e confirmar sua ação (necessario executar apenas uma vez)
quando o programa de populate terminar voce já terá um banco de dados populados de usuarios para realizar diversos testes praticos do safespace_app

OBS2: Caso ocorra algum erro ao executar o arquivo .bat (algums sistemas bloqueiam), execute o safespace_app.py manualmente no VScode
OBS3: Caso queira verificar sem a interface visual pelo terminal(tela preta), só executar o main.py no VScode