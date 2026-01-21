import subprocess
import shutil
import time
import sys
import re
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode

HUB_URL = "https://dev-a4e.global.simetrik.com"
IS_WINDOWS = platform.system() == "Windows"


class DevManager:
    """Manages the development server and ngrok tunnel lifecycle."""

    @staticmethod
    def stop_dev_server(port: int = 5000) -> Dict[str, Any]:
        """
        Stop development server and cleanup tunnels.

        Args:
            port: Port to cleanup.

        Returns:
            Dictionary with cleanup status.
        """
        try:
            DevManager._cleanup_port(port)
            return {
                "success": True,
                "message": f"Dev server stopped and port {port} cleaned up.",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to stop dev server: {str(e)}"}

    @staticmethod
    def _cleanup_port(port: int):
        """Kill any process using the specified port and any ngrok process."""
        try:
            if IS_WINDOWS:
                # Windows: Use netstat and taskkill
                # Find PID using port
                try:
                    result = subprocess.run(
                        f'netstat -ano | findstr :{port}',
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        # Parse PID from netstat output (last column)
                        for line in result.stdout.strip().split('\n'):
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                if pid.isdigit():
                                    print(f"Killing process {pid} on port {port}")
                                    subprocess.run(
                                        f'taskkill /F /PID {pid}',
                                        shell=True,
                                        capture_output=True
                                    )
                except Exception:
                    pass  # No process found or error parsing

                # Kill ngrok processes on Windows
                try:
                    subprocess.run(
                        'taskkill /F /IM ngrok.exe',
                        shell=True,
                        capture_output=True
                    )
                except Exception:
                    pass
            else:
                # Unix (macOS/Linux): Use lsof and kill
                cmd = f"lsof -t -i:{port}"
                try:
                    pid = subprocess.check_output(cmd, shell=True).decode().strip()
                    if pid:
                        print(f"Killing process {pid} on port {port}")
                        subprocess.run(f"kill -9 {pid}", shell=True)
                except subprocess.CalledProcessError:
                    pass  # No process found

                # Kill orphan ngrok processes
                try:
                    subprocess.run("pkill -f ngrok", shell=True)
                except Exception:
                    pass

        except Exception as e:
            print(f"Warning during cleanup: {e}")

    @staticmethod
    def start_dev_server(
        project_dir: Path, port: int = 5000, auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start the agent runner and ngrok tunnel.

        Args:
            project_dir: Path to the agent project directory.
            port: Port to run the server on.
            auth_token: Optional ngrok auth token.

        Returns:
            Dictionary with success status and connection details.
        """
        if not project_dir.exists():
            return {
                "success": False,
                "error": f"Project directory {project_dir} does not exist",
            }

        # Perform cleanup before starting
        DevManager._cleanup_port(port)

        # 1. Start the Agent Server (Dev Runner)
        # We assume dev_runner.py is in the parent directory of this file's parent (a4e/dev_runner.py)
        # utils/dev_manager.py -> a4e/utils/dev_manager.py
        # We need a4e/dev_runner.py

        # Get the package root (a4e)
        package_root = Path(__file__).parent.parent
        runner_script = package_root / "dev_runner.py"

        if not runner_script.exists():
            return {
                "success": False,
                "error": f"Runner script not found at {runner_script}",
            }

        print(f"Starting agent server on port {port}...")

        # On Windows, using PIPE without reading causes the process to hang
        # when the buffer fills up. Use DEVNULL or files instead.
        if IS_WINDOWS:
            # Create detached process on Windows to avoid blocking
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            server_process = subprocess.Popen(
                [
                    sys.executable,
                    str(runner_script),
                    "--agent-path",
                    str(project_dir),
                    "--port",
                    str(port),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        else:
            server_process = subprocess.Popen(
                [
                    sys.executable,
                    str(runner_script),
                    "--agent-path",
                    str(project_dir),
                    "--port",
                    str(port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        # Give it a moment to start
        time.sleep(2)
        if server_process.poll() is not None:
            error_details = "No output captured (Windows uses DEVNULL)" if IS_WINDOWS else ""
            if not IS_WINDOWS:
                stdout, stderr = server_process.communicate()
                if stdout:
                    error_details += f"STDOUT:\n{stdout}\n"
                if stderr:
                    error_details += f"STDERR:\n{stderr}\n"

            return {
                "success": False,
                "error": "Agent server failed to start (likely port already in use)",
                "details": error_details or "No output captured",
            }

        agent_id = project_dir.name

        # 2. Start ngrok Tunnel
        return DevManager._start_ngrok(agent_id, port, auth_token, server_process)

    @staticmethod
    def _start_ngrok(
        agent_id: str,
        port: int,
        auth_token: Optional[str],
        server_process: subprocess.Popen,
    ) -> Dict[str, Any]:
        """Internal helper to start ngrok via library or CLI."""
        import concurrent.futures

        public_url = None
        method = "unknown"

        def _connect_pyngrok(port: int, auth_token: Optional[str]) -> str:
            """Helper to run pyngrok connection with timeout support."""
            from pyngrok import ngrok, conf  # type: ignore

            if auth_token:
                conf.get_default().auth_token = auth_token

            # Smartly manage tunnels instead of killing all
            try:
                tunnels = ngrok.get_tunnels()
                for t in tunnels:
                    addr = str(t.config.get("addr", ""))
                    if addr.endswith(f":{port}") or addr == str(port):
                        print(f"Disconnecting existing tunnel for port {port}: {t.public_url}")
                        ngrok.disconnect(t.public_url)
            except Exception as e:
                print(f"Warning: Failed to enumerate/disconnect tunnels: {e}")

            tunnel = ngrok.connect(port)
            return tunnel.public_url

        # Try pyngrok first with timeout
        try:
            from pyngrok import ngrok  # type: ignore - just to check if installed

            # Use ThreadPoolExecutor to add timeout to pyngrok operations
            timeout_seconds = 30 if IS_WINDOWS else 15
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_connect_pyngrok, port, auth_token)
                try:
                    public_url = future.result(timeout=timeout_seconds)
                    method = "pyngrok"
                except concurrent.futures.TimeoutError:
                    print(f"pyngrok timed out after {timeout_seconds}s, falling back to CLI")
                    raise ImportError("pyngrok timeout")  # Fall through to CLI

        except ImportError:
            # Fallback to ngrok CLI
            ngrok_path = shutil.which("ngrok")
            if not ngrok_path:
                server_process.kill()
                return {
                    "success": False,
                    "error": "Neither 'pyngrok' library nor 'ngrok' CLI found.",
                    "fix": "Run 'uv add pyngrok' OR install ngrok CLI.",
                }

            # Start ngrok CLI process
            try:
                if auth_token:
                    subprocess.run(
                        [ngrok_path, "config", "add-authtoken", auth_token], check=True
                    )

                ngrok_process = subprocess.Popen(
                    [ngrok_path, "http", str(port), "--log=stdout"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # Read stdout to find the URL
                start_time = time.time()
                while time.time() - start_time < 10:
                    line = ngrok_process.stdout.readline()  # type: ignore
                    if not line:
                        break

                    # Look for "url=https://..." with support for all ngrok domains
                    match = re.search(
                        r"url=(https://[a-zA-Z0-9-]+\.(?:ngrok\.app|ngrok\.dev|ngrok\.pizza|ngrok-free\.app|ngrok-free\.dev|ngrok-free\.pizza|ngrok\.io|ngrok-free\.io))",
                        line,
                    )
                    if match:
                        public_url = match.group(1)
                        method = "ngrok_cli"
                        break

                if not public_url:
                    server_process.kill()
                    ngrok_process.kill()
                    return {
                        "success": False,
                        "error": "Failed to get public URL from ngrok CLI",
                        "details": "Timeout waiting for URL",
                    }

            except Exception as e:
                server_process.kill()
                return {
                    "success": False,
                    "error": f"Failed to start ngrok CLI: {str(e)}",
                }

        except Exception as e:
            server_process.kill()
            return {"success": False, "error": f"Failed to start tunnel: {str(e)}"}

        if public_url:

            return {
                "success": True,
                "message": f"Dev mode started successfully via {method}",
                "public_url": public_url,
                "hub_url": f"{HUB_URL}/builder/playground?{urlencode({'url': public_url, 'agent': agent_id} )}",
                "instructions": [
                    "1. Copy the Hub URL above",
                    "2. Open it in your browser",
                    "3. Your local agent is now connected to the Hub!",
                    "4. Press Ctrl+C to stop the server",
                ],
                "pid": server_process.pid,
            }

        server_process.kill()
        return {"success": False, "error": "Unknown error starting tunnel"}
