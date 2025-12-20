"""CLI for the self-correcting coding swarm."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax

from coding_swarm.models import SwarmConfig, create_config
from coding_swarm.swarm import CodingSwarm, create_swarm

app = typer.Typer(
    name="swarm",
    help="Self-correcting coding swarm with LibCST, Docker, and Gemini AI",
    add_completion=False,
)
console = Console()


def get_config(api_key: str | None = None, mock: bool = False) -> SwarmConfig:
    """Get configuration with optional overrides."""
    kwargs = {"enable_mock_mode": mock}
    if api_key:
        kwargs["gemini_api_key"] = api_key
    return create_config(**kwargs)


@app.command()
def generate(
    description: str = typer.Argument(..., help="Project description"),
    output: str = typer.Option("./output", "--output", "-o", help="Output directory"),
    requirements: list[str] = typer.Option(None, "--req", "-r", help="Requirements"),
    api_key: str = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY"),
    max_retries: int = typer.Option(3, "--retries", help="Maximum retry attempts"),
    mock: bool = typer.Option(False, "--mock", help="Use mock mode for testing"),
) -> None:
    """Generate a complete project from a description."""
    config = get_config(api_key, mock)
    config.output_dir = output

    swarm = create_swarm(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Generating project...", total=None)

        try:
            session = swarm.generate_project(
                description=description,
                requirements=requirements,
                max_retries=max_retries,
            )

            # Save to disk
            project_path = swarm.save_project(session, output)

            # Display results
            console.print()
            console.print(Panel(f"[green]Project generated successfully![/green]"))

            if session.project:
                table = Table(title="Project Summary")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Name", session.project.name)
                table.add_row("Files", str(len(session.generated_files)))
                table.add_row("Dependencies", ", ".join(session.project.dependencies) or "None")
                table.add_row("Retries", str(session.total_retries))
                table.add_row("Output", str(project_path))

                console.print(table)

            # Show test results
            if session.test_results:
                result = session.test_results[-1]
                status = "[green]PASSED[/green]" if result.success else "[red]FAILED[/red]"
                console.print(f"\nTests: {status}")
                console.print(f"  Passed: {result.tests_passed}")
                console.print(f"  Failed: {result.tests_failed}")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        finally:
            swarm.cleanup()


@app.command()
def generate_file(
    file_path: str = typer.Argument(..., help="Target file path"),
    description: str = typer.Argument(..., help="What the code should do"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    api_key: str = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY"),
    mock: bool = typer.Option(False, "--mock", help="Use mock mode"),
) -> None:
    """Generate a single file."""
    config = get_config(api_key, mock)
    swarm = create_swarm(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Generating file...", total=None)

        try:
            code_file = swarm.generate_file(file_path, description)

            # Save or display
            if output:
                out_path = Path(output)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(code_file.content)
                console.print(f"[green]File saved to: {output}[/green]")
            else:
                console.print()
                syntax = Syntax(code_file.content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=file_path))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        finally:
            swarm.cleanup()


@app.command()
def refactor(
    file_path: str = typer.Argument(..., help="File to refactor"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    api_key: str = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY"),
    mock: bool = typer.Option(False, "--mock", help="Use mock mode"),
) -> None:
    """Refactor a Python file using LibCST."""
    config = get_config(api_key, mock)
    swarm = create_swarm(config)

    try:
        # Read input file
        input_path = Path(file_path)
        if not input_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        code = input_path.read_text()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Refactoring...", total=None)
            refactored = swarm.refactor_code(code, file_path)

        # Save or display
        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(refactored)
            console.print(f"[green]Refactored file saved to: {output}[/green]")
        else:
            console.print()
            syntax = Syntax(refactored, "python", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title=f"Refactored: {file_path}"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        swarm.cleanup()


@app.command()
def review(
    file_path: str = typer.Argument(..., help="File to review"),
    api_key: str = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY"),
    mock: bool = typer.Option(False, "--mock", help="Use mock mode"),
) -> None:
    """Review a Python file for issues."""
    config = get_config(api_key, mock)
    swarm = create_swarm(config)

    try:
        # Read input file
        input_path = Path(file_path)
        if not input_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        code = input_path.read_text()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Reviewing code...", total=None)
            review_result = swarm.review_code(code, file_path)

        # Display results
        console.print()

        status = (
            "[green]APPROVED[/green]" if review_result["approved"] else "[red]NOT APPROVED[/red]"
        )
        console.print(Panel(f"Review Status: {status}", title="Code Review"))

        if review_result["issues"]:
            console.print("\n[red]Issues:[/red]")
            for issue in review_result["issues"]:
                console.print(f"  - {issue}")

        if review_result["suggestions"]:
            console.print("\n[yellow]Suggestions:[/yellow]")
            for suggestion in review_result["suggestions"]:
                console.print(f"  - {suggestion}")

        console.print(f"\nSeverity: {review_result['severity']}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        swarm.cleanup()


@app.command()
def validate(
    file_path: str = typer.Argument(..., help="File to validate"),
) -> None:
    """Validate Python syntax using LibCST."""
    from coding_swarm.refactorer import create_refactorer

    refactorer = create_refactorer()

    try:
        input_path = Path(file_path)
        if not input_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        code = input_path.read_text()
        is_valid, error = refactorer.validate_syntax(code)

        if is_valid:
            console.print(f"[green]✓ Syntax is valid: {file_path}[/green]")
        else:
            console.print(f"[red]✗ Syntax error in {file_path}[/red]")
            console.print(f"  {error}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def demo() -> None:
    """Run a demo project generation in mock mode."""
    console.print(Panel("[cyan]Running demo in mock mode...[/cyan]"))

    config = get_config(mock=True)
    swarm = create_swarm(config)

    try:
        session = swarm.generate_project(
            description="A simple calculator with add, subtract, multiply, divide functions",
            requirements=["Support error handling for division by zero"],
        )

        console.print("\n[green]Demo completed successfully![/green]")

        if session.project:
            console.print(f"\nProject: {session.project.name}")
            console.print(f"Files generated: {len(session.generated_files)}")

            for code_file in session.generated_files[:3]:
                console.print(f"\n[cyan]{code_file.path}[/cyan]")
                syntax = Syntax(
                    code_file.content[:500] + "..."
                    if len(code_file.content) > 500
                    else code_file.content,
                    "python",
                    theme="monokai",
                    line_numbers=True,
                )
                console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        swarm.cleanup()


@app.command()
def info() -> None:
    """Display system information and status."""
    from coding_swarm.refactorer import create_refactorer
    from coding_swarm.sandbox import create_sandbox

    console.print(Panel("[cyan]Self-Correcting Coding Swarm[/cyan]", title="System Info"))

    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Check LibCST
    try:
        refactorer = create_refactorer()
        refactorer.parse("x = 1")
        table.add_row("LibCST", "[green]Available[/green]")
    except Exception:
        table.add_row("LibCST", "[red]Not Available[/red]")

    # Check Docker
    config = SwarmConfig(enable_mock_mode=False)
    try:
        sandbox = create_sandbox(config)
        if sandbox.is_available():
            table.add_row("Docker", "[green]Available[/green]")
        else:
            table.add_row("Docker", "[yellow]Not Running[/yellow]")
    except Exception:
        table.add_row("Docker", "[red]Not Available[/red]")

    # Check Gemini
    import os

    if os.environ.get("GEMINI_API_KEY"):
        table.add_row("Gemini API Key", "[green]Configured[/green]")
    else:
        table.add_row("Gemini API Key", "[yellow]Not Set[/yellow]")

    console.print(table)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
