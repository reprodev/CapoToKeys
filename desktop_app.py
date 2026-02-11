import os
import socket
import threading
import time
from pathlib import Path

from webui import create_app


def _wait_for_server(host: str, port: int, timeout_s: float = 10.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    return False


def _run_server(host: str, port: int):
    app = create_app()
    app.run(host=host, port=port, debug=False, use_reloader=False)


def main():
    if "DATA_DIR" not in os.environ:
        repo_root = Path(__file__).resolve().parent
        os.environ["DATA_DIR"] = str(repo_root / "appdata" / "config" / "capotokeys")

    host = "127.0.0.1"
    port = int(os.getenv("DESKTOP_PORT", "4506"))

    server_thread = threading.Thread(target=_run_server, args=(host, port), daemon=True)
    server_thread.start()

    if not _wait_for_server(host, port):
        raise SystemExit("Could not start embedded web server for desktop app.")

    try:
        import webview
    except ImportError as exc:
        raise SystemExit("Desktop mode needs pywebview. Install requirements-desktop.txt") from exc

    # Let links with target=_blank open in the system browser.`r`n    # This ensures file downloads work in desktop executable mode.`r`n    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True`r`n    webview.create_window("CapoToKeys", f"http://{host}:{port}", min_size=(960, 700))
    webview.start()


if __name__ == "__main__":
    main()

