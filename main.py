import flet as ft
import requests
import threading
import time

# --- CONFIGURAÇÃO ---
URL_SERVER = "https://auth-predator.onrender.com"
SENHA_ADMIN = "Matheusconde222!"

def main(page: ft.Page):
    page.title = "PREDATOR MANAGER MOBILE"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "adaptive"
    page.bgcolor = "#121212"

    # --- Elementos da Interface ---
    lbl_status = ft.Text("Conectando...", color="orange", size=12)
    
    # Elementos Aba Gerador
    dd_tempo = ft.Dropdown(
        label="Tempo",
        width=200,
        options=[
            ft.dropdown.Option("1 Dia"),
            ft.dropdown.Option("7 Dias"),
            ft.dropdown.Option("30 Dias"),
            ft.dropdown.Option("Vitalício"),
        ],
        value="30 Dias"
    )
    
    slider_qtd = ft.Slider(min=1, max=10, divisions=9, label="{value}", value=1)
    txt_resultado = ft.TextField(multiline=True, min_lines=5, read_only=True, label="Keys Geradas")
    
    # Elementos Aba Clientes
    lista_clientes = ft.Column(scroll="auto", expand=True)

    # --- Funções Lógicas ---

    def verificar_status():
        try:
            requests.get(URL_SERVER, timeout=5)
            lbl_status.value = "Sistema Online ✅"
            lbl_status.color = "green"
        except:
            lbl_status.value = "Servidor Offline ❌"
            lbl_status.color = "red"
        page.update()

    def acao_gerar(e):
        btn_gerar.disabled = True
        btn_gerar.text = "Gerando..."
        page.update()

        mapa = {"1 Dia": 86400, "7 Dias": 604800, "30 Dias": 2592000, "Vitalício": 315360000}
        segundos = mapa.get(dd_tempo.value, 2592000)
        qtd = int(slider_qtd.value)

        def thread_gerar():
            try:
                payload = {"senha": SENHA_ADMIN, "qtd": qtd, "segundos": segundos}
                resp = requests.post(f"{URL_SERVER}/api/admin/gerar", json=payload, timeout=30)
                dados = resp.json()
                
                if dados.get("success"):
                    chaves = "\n".join(dados["keys"])
                    txt_resultado.value = chaves
                    page.snack_bar = ft.SnackBar(ft.Text(f"{qtd} Keys Geradas!"))
                    page.snack_bar.open = True
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {dados.get('message')}"))
                    page.snack_bar.open = True
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro Conexão: {ex}"))
                page.snack_bar.open = True
            finally:
                btn_gerar.disabled = False
                btn_gerar.text = "GERAR KEYS"
                page.update()

        threading.Thread(target=thread_gerar).start()

    def copiar_texto(e):
        page.set_clipboard(txt_resultado.value)
        page.snack_bar = ft.SnackBar(ft.Text("Copiado para área de transferência!"))
        page.snack_bar.open = True
        page.update()

    def carregar_clientes(e=None):
        lista_clientes.controls.clear()
        btn_refresh.disabled = True
        btn_refresh.text = "Buscando..."
        page.update()

        def thread_listar():
            try:
                resp = requests.post(f"{URL_SERVER}/api/admin/listar_usuarios", json={"senha": SENHA_ADMIN}, timeout=30)
                dados = resp.json()
                
                if dados.get("success"):
                    users = dados.get("users", [])
                    if not users:
                        lista_clientes.controls.append(ft.Text("Nenhum usuário encontrado."))
                    
                    for u in users:
                        cor = "green" if u['status'] == "Ativo" else "red" if u['status'] == "Banido" else "grey"
                        
                        card = ft.Container(
                            padding=10,
                            bgcolor="#1e1e1e",
                            border_radius=5,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(u['user'], weight="bold", size=16, expand=True),
                                    ft.Container(
                                        content=ft.Text(u['status'], size=10, color="black"),
                                        bgcolor=cor, padding=5, border_radius=3
                                    )
                                ]),
                                ft.Text(f"Tempo: {u.get('tempo', '--')}", size=12, color="blue"),
                                ft.Row([
                                    ft.ElevatedButton("Reset HWID", on_click=lambda e, user=u['user']: acao_usuario(user, "resetar"), height=30),
                                    ft.ElevatedButton("Banir" if not u.get('banned') else "Desbanir", 
                                                      on_click=lambda e, user=u['user']: acao_usuario(user, "banir" if not u.get('banned') else "desbanir"),
                                                      height=30, color="red" if not u.get('banned') else "green")
                                ], alignment="end")
                            ])
                        )
                        lista_clientes.controls.append(card)
                else:
                    lista_clientes.controls.append(ft.Text(f"Erro: {dados.get('message')}", color="red"))

            except Exception as ex:
                lista_clientes.controls.append(ft.Text(f"Erro de conexão: {ex}", color="red"))
            finally:
                btn_refresh.disabled = False
                btn_refresh.text = "Atualizar Lista"
                page.update()
        
        threading.Thread(target=thread_listar).start()

    def acao_usuario(usuario, acao):
        def thread_acao():
            try:
                payload = {"senha": SENHA_ADMIN, "usuario": usuario, "acao": acao}
                requests.post(f"{URL_SERVER}/api/admin/acao_usuario", json=payload, timeout=10)
                page.snack_bar = ft.SnackBar(ft.Text(f"Ação '{acao}' realizada em {usuario}!"))
                page.snack_bar.open = True
                carregar_clientes()
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Falha na conexão."))
                page.snack_bar.open = True
            page.update()
        threading.Thread(target=thread_acao).start()

    # --- Montagem da Tela ---
    btn_gerar = ft.ElevatedButton("GERAR KEYS", on_click=acao_gerar, bgcolor="#00aa00", color="white", height=50, width=200)
    
    # ÍCONE EM TEXTO "copy" (UNIVERSAL)
    btn_copy = ft.IconButton(icon="copy", on_click=copiar_texto, tooltip="Copiar")
    
    btn_refresh = ft.ElevatedButton("Atualizar Lista", on_click=carregar_clientes, bgcolor="#0055aa", color="white")

    # Layout das Abas
    tab_gerador = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Gerador de Licenças", size=20, weight="bold"),
            dd_tempo,
            ft.Text("Quantidade:"),
            slider_qtd,
            ft.Divider(),
            btn_gerar,
            ft.Row([txt_resultado, btn_copy], alignment="center"),
        ], horizontal_alignment="center")
    )

    tab_clientes = ft.Container(
        padding=10,
        content=ft.Column([
            btn_refresh,
            ft.Divider(),
            lista_clientes
        ])
    )

    # ABA PADRÃO (Funciona na v0.23.2)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Gerador", icon="key", content=tab_gerador),
            ft.Tab(text="Clientes", icon="people", content=tab_clientes),
        ],
        expand=1,
    )

    # Adiciona tudo na página
    page.add(
        ft.Row([ft.Text("PREDATOR ADMIN", size=25, weight="bold", color="#00ff00")], alignment="center"),
        ft.Row([lbl_status], alignment="center"),
        tabs
    )

    threading.Thread(target=verificar_status).start()

ft.app(target=main)
