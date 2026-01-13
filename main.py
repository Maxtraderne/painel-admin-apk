import flet as ft
import requests
import threading

# --- CONFIGURAÇÃO ---
URL_SERVER = "https://auth-predator.onrender.com"
SENHA_ADMIN = "Matheusconde222!"

def main(page: ft.Page):
    page.title = "PREDATOR MANAGER"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.bgcolor = "#121212"
    page.scroll = "adaptive"

    # Elementos Visuais
    lbl_status = ft.Text("Conectando...", color="orange")
    
    # --- GERADOR ---
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
    txt_result = ft.TextField(label="Keys", multiline=True, read_only=True)

    # --- CLIENTES ---
    col_clientes = ft.Column()

    # --- LÓGICA ---
    def check_status():
        try:
            requests.get(URL_SERVER, timeout=5)
            lbl_status.value = "Online ✅"
            lbl_status.color = "green"
        except:
            lbl_status.value = "Offline ❌"
            lbl_status.color = "red"
        page.update()

    def gerar(e):
        btn_gerar.disabled = True
        btn_gerar.text = "..."
        page.update()
        
        tempo_map = {"1 Dia": 86400, "7 Dias": 604800, "30 Dias": 2592000, "Vitalício": 315360000}
        segundos = tempo_map.get(dd_tempo.value)
        qtd = int(slider_qtd.value)

        def task():
            try:
                resp = requests.post(f"{URL_SERVER}/api/admin/gerar", json={"senha": SENHA_ADMIN, "qtd": qtd, "segundos": segundos}, timeout=20)
                data = resp.json()
                if data.get("success"):
                    txt_result.value = "\n".join(data["keys"])
                    page.snack_bar = ft.SnackBar(ft.Text(f"{qtd} Keys geradas!"))
                    page.snack_bar.open = True
                else:
                    txt_result.value = f"Erro: {data.get('message')}"
            except Exception as ex:
                txt_result.value = f"Erro: {ex}"
            btn_gerar.disabled = False
            btn_gerar.text = "GERAR"
            page.update()
        threading.Thread(target=task).start()

    def listar(e=None):
        col_clientes.controls.clear()
        col_clientes.controls.append(ft.Text("Buscando..."))
        page.update()

        def task():
            try:
                resp = requests.post(f"{URL_SERVER}/api/admin/listar_usuarios", json={"senha": SENHA_ADMIN}, timeout=20)
                data = resp.json()
                col_clientes.controls.clear()
                
                if data.get("success"):
                    for u in data.get("users", []):
                        cor = "green" if u['status'] == "Ativo" else "red"
                        card = ft.Container(
                            padding=10, bgcolor="#222", border_radius=5,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(u['user'], weight="bold", size=16),
                                    ft.Container(bgcolor=cor, padding=5, border_radius=3, content=ft.Text(u['status'], size=10, color="black"))
                                ], alignment="spaceBetween"),
                                ft.Text(f"Tempo: {u.get('tempo')}", size=12, color="blue"),
                                ft.Row([
                                    ft.ElevatedButton("Reset", on_click=lambda _, x=u['user']: acao(x, "resetar"), height=30),
                                    ft.ElevatedButton("Ban/Desban", on_click=lambda _, x=u['user']: acao(x, "banir" if not u.get('banned') else "desbanir"), height=30, color="red")
                                ])
                            ])
                        )
                        col_clientes.controls.append(card)
                else:
                    col_clientes.controls.append(ft.Text(f"Erro: {data.get('message')}"))
            except Exception as ex:
                col_clientes.controls.append(ft.Text(f"Erro: {ex}"))
            page.update()
        threading.Thread(target=task).start()

    def acao(user, tipo):
        def task():
            requests.post(f"{URL_SERVER}/api/admin/acao_usuario", json={"senha": SENHA_ADMIN, "usuario": user, "acao": tipo})
            listar()
        threading.Thread(target=task).start()

    # --- MONTAGEM ---
    btn_gerar = ft.ElevatedButton("GERAR", on_click=gerar, bgcolor="green", color="white", height=50)
    btn_copy = ft.IconButton(icon="copy", on_click=lambda e: page.set_clipboard(txt_result.value)) # Ícone seguro

    tab_gerador = ft.Column([
        ft.Text("Gerador", size=20, weight="bold"),
        dd_tempo, slider_qtd, btn_gerar,
        ft.Row([txt_result, btn_copy])
    ])

    tab_clientes = ft.Column([
        ft.ElevatedButton("Atualizar", on_click=listar),
        col_clientes
    ])

    # Abas Simples (Sem ícones complexos para evitar erro)
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Gerador", content=tab_gerador),
            ft.Tab(text="Clientes", content=tab_clientes),
        ]
    )

    page.add(ft.Text("PREDATOR ADMIN", size=25, color="#00ff00"), lbl_status, tabs)
    threading.Thread(target=check_status).start()

ft.app(target=main)
