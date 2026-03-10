import time
import requests
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Herramientas CLI internas para CRAutos Market Intelligence")
console = Console()

API_BASE_URL = "http://localhost:8000/api"

@app.command()
def run_scraper(
    poll_interval: int = typer.Option(5, help="Intervalo de polling en segundos para ver el estado del scraper.")
):
    """
    Activa el scraper del backend mediante la API REST y hace polling hasta que finalice.
    """
    console.print("[bold blue]Iniciando proceso de scraping en el backend...[/bold blue]")

    # 1. Trigger the scraper
    try:
        response = requests.post(f"{API_BASE_URL}/scraper/run")
        response.raise_for_status()
        data = response.json()
        console.print(f"[green]✔[/green] {data.get('message', 'Scraping iniciado exitosamente.')}")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]✖ Error al intentar iniciar el scraper:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 2. Polling loop
    console.print("\n[bold yellow]Monitoreando el estado del scraper...[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task = progress.add_task(description="Obteniendo estado inicial...", total=None)

        while True:
            try:
                status_response = requests.get(f"{API_BASE_URL}/scraper/status")
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get('status', 'unknown').lower()
                cars = status_data.get('cars_scraped', 0)
                pages = status_data.get('pages_processed', 0)
                errors = status_data.get('errors_count', 0)
                duration = status_data.get('duration_seconds', 0)

                # Update progress description
                desc = f"Estado: [bold cyan]{status.upper()}[/bold cyan] | Autos: [green]{cars}[/green] | Páginas: {pages} | Errores: [red]{errors}[/red] | Tiempo: {duration}s"
                progress.update(task, description=desc)

                if status in ['completed', 'failed']:
                    # Exit loop if finished
                    progress.update(task, description=f"[bold {'green' if status == 'completed' else 'red'}]{desc}[/bold {'green' if status == 'completed' else 'red'}]")
                    break

            except requests.exceptions.RequestException as e:
                progress.update(task, description=f"[bold red]Error al obtener el estado:[/bold red] {e}")
                # We don't exit immediately on connection error during polling, we might just retry
                # but we'll print it to let the user know.

            time.sleep(poll_interval)

    # Final summary outside of progress bar
    console.print("\n[bold]Resumen Final:[/bold]")
    if status == 'completed':
        console.print(f"[bold green]✔ El scraper finalizó exitosamente en {duration} segundos.[/bold green]")
        console.print(f"Total autos scrapeados: [bold]{cars}[/bold]")
        console.print(f"Páginas procesadas: [bold]{pages}[/bold]")
    else:
        console.print(f"[bold red]✖ El scraper finalizó con estado: {status}[/bold red]")
        console.print("Revisa los logs del backend para más detalles.")

if __name__ == "__main__":
    app()
