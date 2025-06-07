# safespace_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import sys
import os
import json
from datetime import datetime
import calendar  # Para o calendário de humor

# Imports diretos dos módulos backend
try:
    import services
    import config
    import validators
    # Para criar_tabelas_iniciais e acesso direto ao DAO se necessário
    import database_manager

    from config import TIPO_ADMINISTRADOR, TIPO_COLABORADOR, TIPO_USUARIO_COMUM
    from database_manager import Usuario as UsuarioDAO  # Usando Usuario como o DAO
    from database_manager import criar_tabelas_iniciais
except ImportError as e:
    critical_error_message = (
        f"ERRO CRÍTICO DE IMPORTAÇÃO: {e}\n\n"
        "Certifique-se de que os arquivos:\n"
        "  - config.py\n"
        "  - database_manager.py\n"
        "  - services.py\n"
        "  - validators.py\n"
        "estejam no MESMO DIRETÓRIO que este script (safespace_app.py).\n\n"
        "A aplicação não pode continuar."
    )
    print(critical_error_message)
    try:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror(
            "Erro Crítico de Inicialização", critical_error_message)
        root_error.destroy()
    except Exception:
        pass
    sys.exit(1)

# --- Função Utilitária Global ---


def center_window_util(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

# --- Diálogos e Janelas da Aplicação ---


class UnifiedLoginDialog(simpledialog.Dialog):
    def __init__(self, parent, title="Login SafeSpace"):
        super().__init__(parent, title)

    def body(self, master_frame):
        ttk.Label(master_frame, text="Email:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.email_entry = ttk.Entry(master_frame, width=35)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        self.email_entry.focus_set()
        ttk.Label(master_frame, text="Senha:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)
        self.senha_entry = ttk.Entry(master_frame, width=35, show="*")
        self.senha_entry.grid(row=1, column=1, padx=5, pady=5)
        return self.email_entry

    def validate(self):
        if not self.email_entry.get() or not self.senha_entry.get():
            messagebox.showwarning(
                "Entrada Inválida", "Email e senha são obrigatórios.", parent=self)
            return 0
        return 1

    def apply(self):
        email, senha = self.email_entry.get(), self.senha_entry.get()
        user_data = services.autenticar_e_obter_dados_completos(email, senha)
        if user_data:
            self.result = user_data
        else:
            messagebox.showerror(
                "Falha no Login", "Email ou senha incorretos.", parent=self)
            self.result = None


class UserFormDialog(simpledialog.Dialog):  # Usado pelo Admin
    def __init__(self, parent, title=None, user_data_to_edit=None):
        self.user_data, self.is_edit_mode = user_data_to_edit, bool(
            user_data_to_edit)
        super().__init__(parent, title)

    def body(self, mf):  # mf para master_frame
        labels = ["Nome Completo:", "Email:",
                  "Senha:" if not self.is_edit_mode else "Nova Senha (vazio p/ não alterar):", "Idade (opcional):"]
        self.entries = {}
        for i, txt in enumerate(labels):
            ttk.Label(mf, text=txt).grid(
                row=i, column=0, sticky="w", padx=5, pady=3)

        self.entries["nome"] = ttk.Entry(mf, width=35)
        self.entries["nome"].grid(row=0, column=1, padx=5, pady=3)
        self.entries["email"] = ttk.Entry(mf, width=35)
        self.entries["email"].grid(row=1, column=1, padx=5, pady=3)
        self.entries["senha"] = ttk.Entry(mf, width=35, show="*")
        self.entries["senha"].grid(row=2, column=1, padx=5, pady=3)
        self.entries["idade"] = ttk.Entry(mf, width=35)
        self.entries["idade"].grid(row=3, column=1, padx=5, pady=3)

        if self.is_edit_mode:
            self.entries["nome"].insert(0, self.user_data[1])
            self.entries["email"].insert(0, self.user_data[2])
            if self.user_data[4] is not None:
                self.entries["idade"].insert(0, str(self.user_data[4]))
            ttk.Label(mf, text="Tipo Atual:").grid(
                row=4, column=0, sticky="w", padx=5, pady=3)
            ttk.Label(mf, text=str(self.user_data[5])).grid(
                row=4, column=1, sticky="w", padx=5, pady=3)
        else:
            ttk.Label(mf, text="Tipo de Usuário:").grid(
                row=4, column=0, sticky="w", padx=5, pady=3)
            self.tipo_var = tk.IntVar(value=TIPO_USUARIO_COMUM)
            tf = ttk.Frame(mf)
            for val, txt in [(TIPO_USUARIO_COMUM, "Usuário"), (TIPO_COLABORADOR, "Colaborador"), (TIPO_ADMINISTRADOR, "Admin")]:
                ttk.Radiobutton(tf, text=txt, variable=self.tipo_var,
                                value=val).pack(side="left", padx=2)
            tf.grid(row=4, column=1, sticky="w", padx=5, pady=3)
        return self.entries["nome"]

    def validate(self):
        vals = {k: e.get() for k, e in self.entries.items()}
        if not validators.validar_nome_completo(vals["nome"]):
            messagebox.showwarning(
                "Inválido", "Nome completo inválido.", parent=self)
            return 0
        if not validators.validar_email(vals["email"]):
            messagebox.showwarning("Inválido", "Email inválido.", parent=self)
            return 0
        if (not self.is_edit_mode or vals["senha"]) and not validators.validar_senha(vals["senha"]):
            messagebox.showwarning(
                "Inválido", "Senha inválida (ou nova senha inválida).", parent=self)
            return 0
        if vals["idade"] and not vals["idade"].isdigit():
            messagebox.showwarning(
                "Inválido", "Idade deve ser número.", parent=self)
            return 0
        return 1

    def apply(self):
        nome, email, senha, idade_str = (self.entries[k].get() for k in [
                                         "nome", "email", "senha", "idade"])
        tipo = self.tipo_var.get(
        ) if not self.is_edit_mode else self.user_data[5]
        self.result = (nome, email, senha, idade_str, tipo)


class AdminWindow:
    def __init__(self, master_toplevel_window):
        self.master = master_toplevel_window
        self.master.title("SafeSpace - Admin")
        self.master.geometry("950x600")
        center_window_util(self.master, 950, 600)
        self.master.configure(bg="#e8e8e8")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Admin.TButton", padding=5)
        style.configure("Title.Admin.TLabel", font=(
            'Helvetica', 16, "bold"), background="#e8e8e8")
        mf = ttk.Frame(self.master, padding=15)
        mf.pack(expand=True, fill=tk.BOTH)
        ttk.Label(mf, text="Gerenciamento de Usuários",
                  style="Title.Admin.TLabel").pack(pady=15)
        af = ttk.Frame(mf)
        af.pack(pady=10, fill=tk.X)
        for txt, cmd in [("Adicionar", self.open_add_user_dialog), ("Atualizar", self.open_update_user_dialog), ("Deletar", self.delete_selected_user)]:
            ttk.Button(af, text=txt, style="Admin.TButton",
                       command=cmd).pack(side=tk.LEFT, padx=5)
        ttk.Button(af, text="Recarregar", style="Admin.TButton",
                   command=self.load_users).pack(side=tk.RIGHT, padx=5)
        cols = ("id", "nome", "email", "idade", "tipo")
        self.tree = ttk.Treeview(
            mf, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col.capitalize(
            ), anchor=tk.W, command=lambda c=col: self.sort_treeview(c, False))
            self.tree.column(col, width=100 if col not in [
                             "id", "idade", "tipo"] else 60, minwidth=40)
        self.tree.column("nome", width=200)
        self.tree.column("email", width=250)
        self.tree.pack(expand=True, fill=tk.BOTH, pady=10)
        sb = ttk.Scrollbar(self.tree, orient=tk.VERTICAL,
                           command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_users()

    def sort_treeview(self, col, reverse):  # Simplificado
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children('')]
        is_num = col in ['id', 'idade']
        def key_func(x): return (int(x[0]) if x[0].isdigit(
        ) else x[0].lower()) if is_num and x[0] != '-' else str(x[0]).lower()
        data.sort(key=key_func, reverse=reverse)
        for i, (_, child) in enumerate(data):
            self.tree.move(child, '', i)
        self.tree.heading(
            col, command=lambda c=col: self.sort_treeview(c, not reverse))

    def load_users(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            for id, nome, email, _, idade, tipo_n in UsuarioDAO.listar_todos_usuarios():
                tipos = {TIPO_USUARIO_COMUM: "Usuário",
                         TIPO_COLABORADOR: "Colaborador", TIPO_ADMINISTRADOR: "Admin"}
                self.tree.insert("", tk.END, values=(
                    id, nome, email, idade if idade else '-', tipos.get(tipo_n, str(tipo_n))))
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao carregar: {e}", parent=self.master)

    def get_selected_user_id(self):
        iid = self.tree.focus()
        if not iid:
            messagebox.showwarning(
                "Seleção", "Selecione um usuário.", parent=self.master)
            return None
        return int(self.tree.item(iid, "values")[0])

    def open_add_user_dialog(self):
        d = UserFormDialog(self.master, "Adicionar Usuário")
        if d.result:
            n, e, s, i_s, t = d.result
            i = int(i_s) if i_s.isdigit() else None
            if UsuarioDAO.buscar_usuario_por_email(e):
                messagebox.showerror(
                    "Erro", "Email já existe.", parent=self.master)
                return
            res = services.registrar_novo_usuario(n, e, s, i, t)
            messagebox.showinfo("Cadastro", res, parent=self.master)
            if "sucesso" in res.lower():
                self.load_users()

    def open_update_user_dialog(self):
        uid = self.get_selected_user_id()
        if uid is None:
            return
        ud = UsuarioDAO.buscar_usuario_por_id(uid)
        if not ud:
            messagebox.showerror(
                "Erro", "Usuário não encontrado.", parent=self.master)
            return
        d = UserFormDialog(
            self.master, f"Atualizar ID: {uid}", user_data_to_edit=ud)
        if d.result:
            n, e_n, s_n, i_s, _ = d.result
            i_n = int(i_s) if i_s.isdigit() else (ud[4] if i_s == '' else None)
            s_f = s_n or ud[3]
            if e_n != ud[2] and UsuarioDAO.buscar_usuario_por_email(e_n):
                messagebox.showerror(
                    "Erro", "Novo email já em uso.", parent=self.master)
                return
            res = services.atualizar_info_usuario(uid, n, e_n, s_f, i_n)
            messagebox.showinfo("Atualização", res, parent=self.master)
            if "sucesso" in res.lower():
                self.load_users()

    def delete_selected_user(self):
        uid = self.get_selected_user_id()
        if uid is None:
            return
        ud = UsuarioDAO.buscar_usuario_por_id(uid)
        nome = ud[1] if ud else f"ID {uid}"
        if messagebox.askyesno("Confirmar", f"Excluir '{nome}' (ID:{uid})?", parent=self.master):
            res = services.deletar_usuario_por_id(uid)
            messagebox.showinfo("Deleção", res, parent=self.master)
            self.load_users()


class ColaboradorMainWindow:
    def __init__(self, master_toplevel_window, nome_colaborador):
        self.master = master_toplevel_window
        self.nome_colaborador = nome_colaborador
        self.master.title(f"SafeSpace - Colaborador: {self.nome_colaborador}")
        self.master.geometry("950x700")
        center_window_util(self.master, 950, 700)
        self.master.configure(bg="#e6e6fa")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Colab.TButton", padding=5)
        style.configure("Title.Colab.TLabel", font=(
            'Helvetica', 14, "bold"), background="#e6e6fa")
        pw = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        lfc = ttk.Frame(pw, padding=10)
        pw.add(lfc, weight=1)
        ttk.Label(lfc, text="Usuários Comuns",
                  style="Title.Colab.TLabel").pack(pady=5)
        cf = ttk.Frame(lfc)
        cf.pack(fill=tk.X, pady=5)
        ttk.Button(cf, text="Recarregar", style="Colab.TButton",
                   command=self.load_common_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(cf, text="Ver Detalhes", style="Colab.TButton",
                   command=self.display_selected_user_details).pack(side=tk.LEFT, padx=2)
        cols = ("id", "nome", "idade")
        self.ut = ttk.Treeview(
            lfc, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.ut.heading(c, text=c.capitalize())
            self.ut.column(c, width=100 if c == "nome" else 50, anchor=tk.W)
        self.ut.pack(expand=True, fill=tk.BOTH, pady=5)
        scl = ttk.Scrollbar(self.ut, orient=tk.VERTICAL, command=self.ut.yview)
        self.ut.configure(yscroll=scl.set)
        scl.pack(side=tk.RIGHT, fill=tk.Y)
        dfc = ttk.Frame(pw, padding=10)
        pw.add(dfc, weight=2)
        dlf = ttk.LabelFrame(dfc, text="Detalhes do Usuário", padding=10)
        dlf.pack(expand=True, fill=tk.BOTH)
        self.dta = scrolledtext.ScrolledText(
            dlf, wrap=tk.WORD, state="disabled", font=("Arial", 10))
        self.dta.pack(expand=True, fill=tk.BOTH, pady=5)
        self._cfg_tags()
        self.load_common_users()

    def _cfg_tags(self): self.dta.tag_configure("title", font=('Arial', 12, "bold", "underline"), spacing3=10); self.dta.tag_configure("subtitle", font=('Arial', 10, "bold"),
                                                                                                                                       spacing3=3); self.dta.tag_configure("item_q", font=('Arial', 10), lmargin1=10); self.dta.tag_configure("item_r", font=('Arial', 10, "italic"), lmargin1=20, spacing3=5)

    def _clear_dta(self): self.dta.config(state="normal"); self.dta.delete(
        1.0, tk.END); self.dta.config(state="disabled")

    def load_common_users(self):
        for i in self.ut.get_children():
            self.ut.delete(i)
            self._clear_dta()
        try:
            for uid, nome, idade in UsuarioDAO.listar_usuarios_por_tipo(TIPO_USUARIO_COMUM):
                self.ut.insert("", "end", values=(
                    uid, nome, idade if idade else '-'))
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao listar: {e}", parent=self.master)

    def get_sel_uid(self):
        iid = self.ut.focus()
        if not iid:
            messagebox.showwarning(
                "Seleção", "Selecione um usuário.", parent=self.master)
            return None
        return int(self.ut.item(iid, "values")[0])

    def display_selected_user_details(self):
        uid = self.get_sel_uid()
        if uid is None:
            self._clear_dta()
            return
        self.dta.config(state="normal")
        self.dta.delete(1.0, tk.END)
        try:
            d = services.obter_dados_completos_usuario(uid)
            if not d:
                self.dta.insert(
                    tk.END, "Usuário não encontrado.\n", ("item_q",))
                return
            self.dta.insert(
                tk.END, f"Detalhes de {d['nome']} (ID: {uid})\n", ("title",))
            for title, content in [("Quest. Bem-Estar:", d.get('respostas_questionario_bem_estar')), ("Pet Sugerido:", d.get('pet_sugerido')), ("Quest. Pet:", d.get('respostas_questionario_pet_apoio')), ("Hist. Humor (7d):", d.get('historico_humor'))]:
                self.dta.insert(tk.END, f"{title}\n", ("subtitle",))
                if not content:
                    self.dta.insert(tk.END, "  (N/A)\n", ("item_q",))
                elif isinstance(content, list) and title != "Hist. Humor (7d):":
                    for item in content:
                        self.dta.insert(tk.END, f"  {item.get('pergunta', '?')}: {item.get('resposta', '-').upper() if title.startswith('Quest. Bem') else item.get('resposta', '-')}\n",
                                        ("item_q" if title.startswith("Pet Sug") else "item_r"))
                elif title == "Pet Sugerido:":
                    self.dta.insert(tk.END, f"  {content}\n", ("item_q",))
                elif title == "Hist. Humor (7d):":
                    for dt, snt in content:
                        self.dta.insert(
                            tk.END, f"  {dt}: {snt}\n", ("item_q",))
                elif isinstance(content, (dict, str)):
                    self.dta.insert(tk.END, f"  {str(content)}\n", ("item_q",))
                self.dta.insert(tk.END, "\n")
        except Exception as e:
            messagebox.showerror(
                "Erro Detalhes", f"Erro: {e}", parent=self.master)
            self.dta.insert(tk.END, f"Erro: {e}\n")
        finally:
            self.dta.config(state="disabled")

# --- Classes de Diálogo e Janela do Usuário ---


# Mesma lógica do UserFormDialog, mas para TIPO_USUARIO_COMUM
class UsuarioCadastroDialog(simpledialog.Dialog):
    def __init__(self, parent, title="Cadastrar Novo Usuário"):
        self.parent_for_messagebox = parent
        super().__init__(parent, title)

    def body(self, mf):
        labels = ["Nome Completo:", "Email:", "Senha:", "Idade (opcional):"]
        self.entries = {}
        for i, txt in enumerate(labels):
            ttk.Label(mf, text=txt).grid(
                row=i, column=0, sticky="w", padx=5, pady=3)
        self.entries["nome"] = ttk.Entry(mf, width=35)
        self.entries["nome"].grid(row=0, column=1, padx=5, pady=3)
        self.entries["email"] = ttk.Entry(mf, width=35)
        self.entries["email"].grid(row=1, column=1, padx=5, pady=3)
        self.entries["senha"] = ttk.Entry(mf, width=35, show="*")
        self.entries["senha"].grid(row=2, column=1, padx=5, pady=3)
        self.entries["idade"] = ttk.Entry(mf, width=35)
        self.entries["idade"].grid(row=3, column=1, padx=5, pady=3)
        return self.entries["nome"]

    def validate(self):
        v = {k: e.get() for k, e in self.entries.items()}
        if not validators.validar_nome_completo(v["nome"]):
            messagebox.showwarning("Inválido", "Nome.", parent=self)
            return 0
        if not validators.validar_email(v["email"]):
            messagebox.showwarning("Inválido", "Email.", parent=self)
            return 0
        if UsuarioDAO.buscar_usuario_por_email(v["email"]):
            messagebox.showwarning("Inválido", "Email já existe.", parent=self)
            return 0
        if not validators.validar_senha(v["senha"]):
            messagebox.showwarning("Inválido", "Senha.", parent=self)
            return 0
        if v["idade"] and not v["idade"].isdigit():
            messagebox.showwarning("Inválido", "Idade num.", parent=self)
            return 0
        return 1

    def apply(self):
        n, e, s, i_s = (self.entries[k].get()
                        for k in ["nome", "email", "senha", "idade"])
        i = int(i_s) if i_s.isdigit() else None
        res = services.registrar_novo_usuario(n, e, s, i, TIPO_USUARIO_COMUM)
        messagebox.showinfo("Cadastro", res, parent=self.parent_for_messagebox)
        self.result = "sucesso" in res.lower()


class QuestionarioBemEstarDialog(simpledialog.Dialog):
    # ... (código como na sua última versão funcional, sem alterações aqui) ...
    def __init__(
        self, parent, title="Questionário de Bem-Estar"): super().__init__(parent, title)

    def body(self, master_frame):
        ttk.Label(master_frame, text="Responda 'Sim' ou 'Não':",
                  font=("Arial", 10, "bold")).pack(pady=5, anchor="w")
        self.perguntas_textos = ["1. Sente-se mais triste/deprimido(a) na maior parte do tempo?", "2. Menos interesse/prazer em atividades que gostava?",
                                 "3. Dificuldades para dormir ou dormindo em excesso?", "4. Ansiedade, nervosismo ou preocupação excessiva?", "5. Cansaço ou pouca energia frequentemente?"]
        self.respostas_vars = []
        for i, p_texto in enumerate(self.perguntas_textos):
            q_f = ttk.Frame(master_frame, padding=(0, 2))
            q_f.pack(fill="x", anchor="w")
            ttk.Label(q_f, text=p_texto, wraplength=380, justify="left").pack(
                side="top", anchor="w", pady=2)
            var = tk.StringVar(value="")
            rb_f = ttk.Frame(q_f)
            rb_f.pack(side="top", anchor="w")
            ttk.Radiobutton(rb_f, text="Sim", variable=var,
                            value="sim").pack(side="left", padx=10)
            ttk.Radiobutton(rb_f, text="Não", variable=var,
                            value="não").pack(side="left", padx=10)
            self.respostas_vars.append(var)
        return None

    def validate(self):
        for i, var in enumerate(self.respostas_vars):
            if not var.get():
                messagebox.showwarning(
                    "Incompleto", f"Responda à pergunta {i+1}.", parent=self)
                return 0
        return 1

    def apply(self): self.result = [{"pergunta": self.perguntas_textos[i], "resposta": var.get(
    )} for i, var in enumerate(self.respostas_vars)]


class QuestionarioPetDialog(simpledialog.Dialog):
    # ... (código como na sua última versão funcional, sem alterações aqui) ...
    def __init__(self, parent, title="Preferências Pet"): super().__init__(
        parent, title)

    def body(self, mf):
        ttk.Label(mf, text="Descobrindo seu pet ideal!", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, pady=5, sticky="w")
        self.p_cfg = [{"key": "1. Nível atividade (1-baixa, 2-mod, 3-alta)", "label": "Atividade (1-B, 2-M, 3-A):", "type": "scale", "min": 1, "max": 3}, {"key": "2. Tempo diário pet (1-pouco, 2-mod, 3-muito)", "label": "Tempo Pet (1-P, 2-M, 3-M):", "type": "scale", "min": 1, "max": 3}, {"key": "3. Moradia (casa/apartamento)", "label": "Moradia:", "type": "radio", "options": ["casa", "apartamento"]}, {
            "key": "4. Atenção do pet (independente/muita atencao)", "label": "Atenção Pet:", "type": "radio", "options": ["independente", "muita atencao"]}, {"key": "5. Alergia a pelos (sim/não)", "label": "Alergia Pelos:", "type": "radio", "options": ["sim", "não"]}, {"key": "6. Porte preferido (grande/medio/pequeno)", "label": "Porte Preferido:", "type": "radio", "options": ["grande", "medio", "pequeno"]}]
        self.eVars = {}
        r = 1
        for pc in self.p_cfg:
            ttk.Label(mf, text=pc["label"], wraplength=180, justify="left").grid(
                row=r, column=0, sticky="w", padx=5, pady=3)
            if pc["type"] == "scale":
                var = tk.IntVar(value=pc["min"])
                ttk.Scale(mf, from_=pc["min"], to=pc["max"], orient=tk.HORIZONTAL, variable=var, length=180).grid(
                    row=r, column=1, sticky="ew", padx=5, pady=3)
            elif pc["type"] == "radio":
                var = tk.StringVar(value=pc["options"][0])
                rbf = ttk.Frame(mf)
                [ttk.Radiobutton(rbf, text=o.capitalize(), variable=var, value=o).pack(
                    side="left", padx=3) for o in pc["options"]]
                rbf.grid(row=r, column=1, sticky="w", padx=5, pady=3)
            self.eVars[pc["key"]] = var
            r += 1
        return None

    def validate(self): return 1
    def apply(self): self.result_dict_logica = {pc["key"]: self.eVars[pc["key"]].get() for pc in self.p_cfg}; self.result_lista_db = [
        {"pergunta": pc["key"], "resposta": self.eVars[pc["key"]].get()} for pc in self.p_cfg]


# ##############################################
# ##          CLASSE MODIFICADA ABAIXO        ##
# ##############################################
class UsuarioMainWindow:
    def __init__(self, master_toplevel_window, user_data_dict):
        self.master = master_toplevel_window
        self.user_data = user_data_dict
        self.master.title(
            f"SafeSpace - {self.user_data['nome'].split(' ')[0]}")
        self.master.geometry("750x780")  # Aumentada altura para calendário
        center_window_util(self.master, 750, 780)
        self.master.configure(bg="#f0fff0")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("User.TButton", padding=6,
                        font=('Helvetica', 10, 'bold'))
        style.configure("User.TLabel", background="#f0fff0",
                        font=('Helvetica', 10))
        style.configure("Title.User.TLabel", font=(
            'Helvetica', 16, "bold"), background="#f0fff0")
        style.configure("Subtitle.User.TLabel", font=(
            'Helvetica', 12, "bold"), background="#f0fff0")
        style.configure("TNotebook.Tab", padding=(
            12, 6), font=('Helvetica', 10, 'bold'))
        style.configure("CalendarDay.TFrame", background="white",
                        relief="solid", borderwidth=1)
        style.configure("CalendarDayNum.TLabel", font=(
            'Arial', 9, 'bold'), background="white", anchor="nw", padding=(2, 1))
        style.configure("CalendarMood.TLabel", font=('Arial', 7), background="white",
                        # wraplength para humor
                        anchor="sw", padding=(2, 1), wraplength=50)
        style.configure("CalendarHeader.TLabel", padding=3, font=(
            'Arial', 9, 'bold'), anchor="center", background="#d0d0d0")

        self.prompt_registrar_humor_diario()

        self.notebook = ttk.Notebook(self.master, padding=10)
        self.tab_bem_estar = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_bem_estar, text=' Meu Bem-Estar ')
        self._criar_aba_bem_estar(self.tab_bem_estar)
        self.tab_pet = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_pet, text=' Pet de Apoio ')
        self._criar_aba_pet_apoio(self.tab_pet)
        self.tab_apoio = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_apoio, text=' Apoio e Feedback ')
        self._criar_aba_apoio_feedback(self.tab_apoio)
        self.notebook.pack(expand=True, fill="both")
        self._atualizar_ui_baseado_em_dados_usuario()

    def prompt_registrar_humor_diario(self):
        # (como na sua última versão funcional, mas atualiza calendário)
        reg_exist = services.obter_registro_humor_hoje(self.user_data["id"])
        if reg_exist:
            messagebox.showinfo(
                "Humor", f"Humor de hoje: '{reg_exist[3]}'.", parent=self.master)
            return
        sent = simpledialog.askstring(
            "Humor Diário", f"Olá {self.user_data['nome'].split(' ')[0]}! Como se sente?", parent=self.master)
        if sent is not None and sent.strip():
            res = services.registrar_sentimento_diario(
                self.user_data["id"], sent.strip())
            if "sucesso" in res.lower() and hasattr(self, 'calendar_frame_actual'):
                self._desenhar_calendario_humor()
            messagebox.showinfo("Humor", res, parent=self.master)
        elif sent is not None:
            messagebox.showinfo(
                "Humor", "Nenhum sentimento registrado.", parent=self.master)

    def _criar_aba_bem_estar(self, parent_frame):
        ttk.Label(parent_frame, text="Recursos e Monitoramento",
                  style="Subtitle.User.TLabel").pack(pady=5, anchor="center")

        self.btn_q_bem_estar = ttk.Button(
            parent_frame, text="Questionário Bem-Estar", style="User.TButton", command=self.abrir_questionario_bem_estar)
        self.btn_q_bem_estar.pack(pady=5, fill=tk.X, padx=50, ipady=4)

        self.btn_ver_indicacoes = ttk.Button(
            parent_frame, text="Ver Indicações", style="User.TButton", command=self.abrir_janela_indicacoes)
        self.btn_ver_indicacoes.pack(pady=5, fill=tk.X, padx=50, ipady=4)

        # Botão de registrar humor foi removido daqui

        calendar_container = ttk.LabelFrame(
            parent_frame, text="Calendário de Humor Mensal", padding=10)
        calendar_container.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        nav_frame = ttk.Frame(calendar_container)
        nav_frame.pack(fill=tk.X, pady=2)
        self.current_calendar_date = datetime.now()
        self.prev_month_button = ttk.Button(
            nav_frame, text="<< Ant.", command=lambda: self._change_month(-1))
        self.prev_month_button.pack(side=tk.LEFT, padx=3)
        self.month_year_label = ttk.Label(nav_frame, text="", font=(
            'Helvetica', 12, 'bold'), anchor="center")
        self.month_year_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.next_month_button = ttk.Button(
            nav_frame, text="Próx. >>", command=lambda: self._change_month(1))
        self.next_month_button.pack(side=tk.RIGHT, padx=3)
        self.calendar_frame_actual = ttk.Frame(calendar_container)
        self.calendar_frame_actual.pack(fill=tk.BOTH, expand=True, pady=5)
        self._desenhar_calendario_humor()

    def _change_month(self, delta):
        y, m = self.current_calendar_date.year, self.current_calendar_date.month + delta
        if m > 12:
            y += 1
            m = 1
        elif m < 1:
            y -= 1
            m = 12
        self.current_calendar_date = datetime(y, m, 1)
        self._desenhar_calendario_humor()

    def _desenhar_calendario_humor(self):
        for w in self.calendar_frame_actual.winfo_children():
            w.destroy()
        y, m = self.current_calendar_date.year, self.current_calendar_date.month
        nomes_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        self.month_year_label.config(text=f"{nomes_meses[m-1]} {y}")

        humores = services.obter_humor_mensal(self.user_data["id"], y, m)
        cal_list = calendar.monthcalendar(y, m)
        dias_semana_nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for c, nome_dia in enumerate(dias_semana_nomes):
            ttk.Label(self.calendar_frame_actual, text=nome_dia, style="CalendarHeader.TLabel").grid(
                row=0, column=c, sticky="nsew", padx=1, pady=1)
            self.calendar_frame_actual.grid_columnconfigure(c, weight=1)

        for r, semana in enumerate(cal_list, start=1):
            self.calendar_frame_actual.grid_rowconfigure(r, weight=1)
            for c, dia_num in enumerate(semana):
                day_f = ttk.Frame(self.calendar_frame_actual, style="CalendarDay.TFrame",
                                  borderwidth=1, relief="solid")  # Use TFrame
                day_f.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                if dia_num != 0:
                    ttk.Label(day_f, text=str(dia_num), style="CalendarDayNum.TLabel").pack(
                        anchor="nw", padx=2, pady=1)
                    sentimento = humores.get(dia_num)
                    if sentimento:
                        # Limita o texto
                        display_s = (
                            sentimento[:8]+"..") if len(sentimento) > 10 else sentimento
                        lbl_s = ttk.Label(
                            day_f, text=display_s, style="CalendarMood.TLabel")
                        lbl_s.pack(expand=True, fill=tk.BOTH, padx=2, pady=1)
                        # Add tooltip (requer classe externa ou lógica simples)
                        # ToolTip(lbl_s, text=sentimento)

    def _criar_aba_pet_apoio(self, parent_frame):
        # ... (como na sua última versão funcional)
        ttk.Label(parent_frame, text="Seu Amigo de Quatro Patas",
                  style="Subtitle.User.TLabel").pack(pady=10)
        self.pet_info_label = ttk.Label(parent_frame, text="", font=(
            "Arial", 11), wraplength=500, justify="center", background="#f0fff0")
        self.pet_info_label.pack(pady=15, padx=10)
        self.btn_q_pet = ttk.Button(parent_frame, text="Descobrir/Reavaliar Pet Ideal",
                                    style="User.TButton", command=self.abrir_questionario_pet)
        self.btn_q_pet.pack(pady=7, fill=tk.X, padx=50, ipady=5)

    def _criar_aba_apoio_feedback(self, parent_frame):
        # ... (como na sua última versão funcional)
        ttk.Label(parent_frame, text="Conecte-se e Compartilhe",
                  style="Subtitle.User.TLabel").pack(pady=10)
        ttk.Button(parent_frame, text="Falar com um Profissional", style="User.TButton",
                   command=self.abrir_janela_contato_colaborador).pack(pady=7, fill=tk.X, padx=50, ipady=5)
        ttk.Button(parent_frame, text="Dar Feedback sobre Indicações", style="User.TButton",
                   command=self.dar_feedback_indicacoes).pack(pady=7, fill=tk.X, padx=50, ipady=5)

    def _atualizar_ui_baseado_em_dados_usuario(self):
        q_bem_estar_feito = bool(
            self.user_data.get("respostas_questionario_json"))
        if q_bem_estar_feito:
            self.btn_q_bem_estar.config(
                text="Questionário Bem-Estar (Respondido)", state=tk.DISABLED)
            self.btn_ver_indicacoes.config(state=tk.NORMAL)
        else:
            self.btn_q_bem_estar.config(
                text="Responder Questionário Bem-Estar", state=tk.NORMAL)
            self.btn_ver_indicacoes.config(state=tk.DISABLED)
        self.btn_q_pet.config(
            state=tk.NORMAL if q_bem_estar_feito else tk.DISABLED)
        self._atualizar_info_pet_label()

    def _atualizar_info_pet_label(self):
        # ... (como na sua última versão funcional) ...
        q_bem_estar_feito = bool(
            self.user_data.get("respostas_questionario_json"))
        if self.user_data.get("pet_sugerido"):
            self.pet_info_label.config(
                text=f"Pet sugerido: {self.user_data['pet_sugerido']}!")
        elif q_bem_estar_feito:
            self.pet_info_label.config(text="Descubra seu pet ideal.")
        else:
            self.pet_info_label.config(
                text="Responda ao Questionário de Bem-Estar primeiro.")

    def abrir_janela_indicacoes(self):
        if not self.user_data.get("respostas_questionario_json"):
            messagebox.showinfo(
                "Atenção", "Responda ao Questionário de Bem-Estar para ver indicações.", parent=self.master)
            return
        # ... (conteúdo completo das indicações como na sua última versão funcional) ...
        win = tk.Toplevel(self.master)
        win.title("Indicações")
        win.geometry("650x550")
        center_window_util(win, 650, 550)
        win.grab_set()
        win.configure(bg="#f0fff0")
        txt_area = scrolledtext.ScrolledText(
            win, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 10))
        txt_area.pack(expand=True, fill="both")
        conteudo_indicacoes = """**Indicação de Livros:**\n- 'A Coragem de Ser Imperfeito' por Brené Brown\n- 'Ansiedade: Como Enfrentar o Mal do Século' por Augusto Cury\n- 'O Poder do Hábito' por Charles Duhigg\n\n**Indicação de Esportes:**\n- Caminhada/Corrida ao ar livre\n- Yoga ou Pilates\n- Natação\n- Dança\n\n**Indicação de Lazer/Atividades Extras:**\n- Meditação e Mindfulness\n- Jardinagem ou contato com a natureza\n- Desenho, pintura ou outras atividades artísticas\n- Cozinhar novas receitas\n- Passar tempo com animais de estimação\n\n**Indicação de Podcasts:**\n- 'Mente Ativa'\n- 'Calm'\n- 'Ted Talks Daily'\n- 'Prazer, Feminino'\n\n**Indicação de Músicas/Filmes/Séries:**\nFilmes:\n- 'Divertida Mente'\n- 'À Procura da Felicidade'\n- 'O Discurso do Rei'\nSéries:\n- 'Modern Family'\n- 'Anne with an E'\n- Documentários sobre natureza\n\nLembre-se: Estas são apenas sugestões. Encontre o que funciona melhor para você e não hesite em procurar ajuda profissional."""
        txt_area.insert(tk.END, conteudo_indicacoes)
        txt_area.config(state="disabled")
        ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=10)

    def abrir_questionario_bem_estar(self):
        if self.user_data.get("respostas_questionario_json"):
            messagebox.showinfo(
                "Completo", "Questionário de Bem-Estar já respondido.", parent=self.master)
            return
        # ... (restante da lógica como na sua última versão funcional) ...
        dialog = QuestionarioBemEstarDialog(self.master)
        if dialog.result:
            services.processar_questionario_bem_estar(
                self.user_data["id"], dialog.result)
            self.user_data["respostas_questionario_json"] = json.dumps(
                dialog.result)  # Atualiza local
            messagebox.showinfo(
                "Salvo", "Respostas salvas!", parent=self.master)
            self._atualizar_ui_baseado_em_dados_usuario()
            if hasattr(self, 'calendar_frame_actual'):
                self._desenhar_calendario_humor()  # Atualiza calendário

    def abrir_questionario_pet(self):
        # ... (como na sua última versão funcional) ...
        if not self.user_data.get("respostas_questionario_json"):
            messagebox.showwarning(
                "Atenção", "Responda ao Questionário de Bem-Estar primeiro.", parent=self.master)
            return
        dialog = QuestionarioPetDialog(self.master)
        if hasattr(dialog, 'result_dict_logica') and dialog.result_dict_logica:
            sugestao = services.processar_questionario_pet_e_sugerir(
                self.user_data["id"], dialog.result_dict_logica, dialog.result_lista_db)
            if sugestao:
                self.user_data["pet_sugerido"] = sugestao
                self.user_data["respostas_pet_apoio_json"] = json.dumps(
                    dialog.result_lista_db)
                messagebox.showinfo(
                    "Pet Sugerido", f"Seu pet ideal: {sugestao}", parent=self.master)
            else:
                messagebox.showinfo(
                    "Pet", "Não foi possível gerar sugestão.", parent=self.master)
            self._atualizar_ui_baseado_em_dados_usuario()

    def abrir_janela_contato_colaborador(self):
        # MODIFICADO para exibir nome e email
        # Espera-se [(nome, email), ...]
        colaboradores_info = services.obter_colaboradores_para_encaminhamento()

        win = tk.Toplevel(self.master)
        win.title("Contato Profissional")
        win.geometry("500x400")
        center_window_util(win, 500, 400)
        win.grab_set()
        win.configure(bg="#f0fff0")
        txt_area = scrolledtext.ScrolledText(
            win, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 10))
        txt_area.pack(expand=True, fill="both")

        if not colaboradores_info:
            txt_area.insert(
                tk.END, "Desculpe, não há colaboradores disponíveis no momento.")
        else:
            txt_area.insert(
                tk.END, "Nossos colaboradores disponíveis para você:\n\n")
            for nome, email in colaboradores_info:  # Desempacota nome e email
                txt_area.insert(
                    tk.END, f"- Nome: {nome}\n   Email: {email}\n\n")
            txt_area.insert(
                tk.END, "\nVocê pode entrar em contato com um deles para um apoio mais próximo.")

        txt_area.config(state="disabled")
        ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=10)

    def dar_feedback_indicacoes(self):
        # ... (como na sua última versão funcional, com a verificação adicionada) ...
        if not self.user_data.get("respostas_questionario_json"):
            messagebox.showinfo(
                "Atenção", "Responda ao Questionário e veja as indicações antes de dar feedback.", parent=self.master)
            return
        if not messagebox.askokcancel("Feedback", "Realizou ao menos duas indicações?", parent=self.master):
            return
        melhora = messagebox.askyesno(
            "Humor", "Sentiu melhora no humor?", parent=self.master, icon=messagebox.QUESTION)
        if melhora is not None:
            msg = "Que ótimo!" if melhora else "Entendido. O cuidado é contínuo."
            messagebox.showinfo("Feedback", msg, parent=self.master)
            messagebox.showinfo(
                "Feedback", "Agradecemos seu feedback!", parent=self.master)

# --- MainApplicationGUI (como estava antes) ---


class MainApplicationGUI:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("SafeSpace - Bem-vindo(a)!")
        self.root.geometry("450x300")
        center_window_util(self.root, 450, 300)
        self.root.configure(bg="#f0f8ff")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat",
                        font=('Helvetica', 10, 'bold'))
        style.configure("TLabel", background="#f0f8ff", font=('Helvetica', 10))
        style.configure("Title.TLabel", font=(
            'Helvetica', 16, "bold"), foreground="#333")
        style.configure("Main.TFrame", background="#f0f8ff")
        style.map("Exit.TButton", background=[
                  ('active', '#ff8a8a'), ('!active', '#ffc0c0')], foreground=[('active', 'black')])
        try:
            criar_tabelas_iniciais()
        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha DB: {e}")
            self.root.destroy()
            return
        mf = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        mf.pack(expand=True, fill=tk.BOTH)
        ttk.Label(mf, text="Bem-vindo(a) ao SafeSpace!",
                  style="Title.TLabel").pack(pady=(10, 25))
        ttk.Button(mf, text="Login", command=self.open_unified_login_dialog,
                   width=30).pack(pady=8, ipady=6)
        ttk.Button(mf, text="Cadastre-se (Novo Usuário)",
                   command=self.open_user_registration_dialog, width=30).pack(pady=8, ipady=6)
        ttk.Button(mf, text="Sair", command=self.root.quit, width=30,
                   style="Exit.TButton").pack(pady=(20, 10), ipady=6)

    def open_unified_login_dialog(self):
        d = UnifiedLoginDialog(self.root)
        user_data = d.result
        if user_data:
            self.root.withdraw()
            self.redirect_to_profile(user_data)

    def open_user_registration_dialog(self): UsuarioCadastroDialog(self.root)

    def redirect_to_profile(self, user_data_completa):
        uid, nome, email, _, idade, u_type, rq_json, pet_sug, rpet_json = user_data_completa
        profile_win = tk.Toplevel(self.root)
        profile_win.protocol("WM_DELETE_WINDOW",
                             lambda: self._on_profile_close(profile_win))
        if u_type == TIPO_ADMINISTRADOR:
            AdminWindow(profile_win)
        elif u_type == TIPO_COLABORADOR:
            ColaboradorMainWindow(profile_win, nome)
        elif u_type == TIPO_USUARIO_COMUM:
            current_user_dict = {"id": uid, "nome": nome, "email": email, "idade": idade,
                                 "respostas_questionario_json": rq_json, "pet_sugerido": pet_sug, "respostas_pet_apoio_json": rpet_json}
            UsuarioMainWindow(profile_win, current_user_dict)
        else:
            messagebox.showerror(
                "Erro", f"Tipo usuário {u_type} desconhecido.", parent=self.root)
            self._on_profile_close(profile_win)
            return
        profile_win.grab_set()

    def _on_profile_close(self, profile_window_ref):
        profile_window_ref.destroy()
        try:
            if self.root.winfo_exists():
                self.root.deiconify()
        except tk.TclError:
            pass


# --- Bloco Principal de Execução ---
if __name__ == "__main__":
    all_classes_defined = True
    required_classes = [AdminWindow, ColaboradorMainWindow, UsuarioMainWindow, UsuarioCadastroDialog,
                        UnifiedLoginDialog, MainApplicationGUI, QuestionarioBemEstarDialog, QuestionarioPetDialog]
    for cls in required_classes:
        if cls.__name__ not in globals():
            print(f"ERRO FATAL: Classe {cls.__name__} não definida.")
            all_classes_defined = False
    if not all_classes_defined:
        sys.exit(1)
    root = tk.Tk()
    app = MainApplicationGUI(root)
    root.mainloop()
