import flet as ft
import requests

# URL base de la API de GitHub
GITHUB_API_URL = "https://api.github.com"

# --- Lógica para interactuar con la API de GitHub ---

def get_user_repos(token):
    """
    Obtiene TODOS los repositorios (personales, de colaborador y de organización)
    manejando la paginación de la API de GitHub.
    """
    headers = {"Authorization": f"token {token}"}
    all_repos_data = []
    # Empezamos con la URL de la primera página
    url = f"{GITHUB_API_URL}/user/repos?affiliation=owner,collaborator,organization_member&per_page=100"

    # Bucle para manejar la paginación
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza un error si la petición falla
        all_repos_data.extend(response.json())

        # Verificamos si hay una página 'siguiente' en los encabezados de la respuesta
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            url = None # Si no hay 'next', terminamos el bucle

    return all_repos_data

# --- Componentes y Lógica de la Interfaz Gráfica (Flet) ---

def main(page: ft.Page):
    page.title = "Buscador de Repositorios de GitHub"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Lista que almacenará todos los repositorios encontrados
    all_repos = []

    def fetch_all_repos(e):
        """Función que se activa al hacer clic en 'Conectar'."""
        token = token_input.value
        if not token:
            show_error("Por favor, ingresa un token de acceso.")
            return

        # Actualizar UI para mostrar estado de carga
        connect_button.disabled = True
        progress_ring.visible = True
        page.update()

        try:
            repos_data = get_user_repos(token)

            all_repos.clear()
            for repo in repos_data:
                all_repos.append({
                    "full_name": repo["full_name"],
                    "html_url": repo["html_url"]
                })

            all_repos.sort(key=lambda x: x["full_name"].lower())

            connect_view.visible = False
            search_view.visible = True

            update_repo_list("")

        except requests.exceptions.HTTPError as ex:
            show_error(f"Error de API: {ex.response.status_code}. Revisa tu token y permisos.")
        except Exception as ex:
            show_error(f"Ocurrió un error inesperado: {ex}")
        finally:
            connect_button.disabled = False
            progress_ring.visible = False
            page.update()

    def update_repo_list(search_term: str):
        """Filtra y actualiza la lista de repositorios en la UI."""
        search_term = search_term.lower()
        visible_repos = [repo for repo in all_repos if search_term in repo["full_name"].lower()]

        repo_list_view.controls.clear()
        if not visible_repos:
            repo_list_view.controls.append(ft.Text("No se encontraron repositorios con ese filtro."))
        else:
            for repo in visible_repos:
                repo_list_view.controls.append(
                    ft.ListTile(
                        title=ft.Text(repo["full_name"]),
                        trailing=ft.IconButton(
                            icon=ft.Icons.OPEN_IN_BROWSER,
                            tooltip="Abrir en GitHub",
                            data=repo["html_url"],
                            on_click=lambda e: page.launch_url(e.control.data)
                        )
                    )
                )
        results_count.value = f"Mostrando {len(visible_repos)} de {len(all_repos)} repositorios"
        page.update()

    def search_on_change(e):
        update_repo_list(e.control.value)

    def show_error(message):
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.colors.ERROR)
        page.snack_bar.open = True
        page.update()

    # --- Definición de Vistas ---

    token_input = ft.TextField(
        label="GitHub Personal Access Token",
        password=True,
        # 💡 CORRECCIÓN: 'can_reveal_password' es una mejora útil de las versiones modernas
        can_reveal_password=True,
    )
    connect_button = ft.ElevatedButton("Conectar y Cargar Repositorios", on_click=fetch_all_repos)
    progress_ring = ft.ProgressRing(visible=False)

    connect_view = ft.Column(
        [
            ft.Text("Ingresa tu Token de Acceso Personal de GitHub.", size=18),
            ft.Text("La aplicación necesita permisos 'repo' y 'read:org'."),
            token_input,
            connect_button,
            progress_ring
        ],
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    search_input = ft.TextField(
        label="Buscar repositorio (ej: 'owner/nombre-repo')",
        on_change=search_on_change,
        prefix_icon=ft.Icons.SEARCH
    )
    results_count = ft.Text()
    repo_list_view = ft.ListView(expand=True, spacing=10)

    search_view = ft.Column(
        [
            search_input,
            results_count,
            ft.Divider(),
            repo_list_view
        ],
        visible=False,
        expand=True
    )

    page.add(
        ft.Container(
            content=ft.Column([connect_view, search_view]),
            padding=20,
            expand=True,
            alignment=ft.alignment.center
        )
    )

# --- Iniciar la aplicación ---
if __name__ == "__main__":
    # 💡 CORRECCIÓN: ft.run() es la forma moderna y correcta de iniciar una app Flet.
    ft.app(target=main)
