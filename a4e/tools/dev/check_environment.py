"""
Check environment tool.
"""

import sys
import shutil
import os
from pathlib import Path

from ...core import mcp, get_project_dir, get_configured_project_dir


@mcp.tool()
def check_environment() -> dict:
    """
    Diagnose the current environment for agent development
    """
    _PROJECT_DIR = get_configured_project_dir()
    
    results = {
        "python": {
            "version": sys.version.split()[0],
            "ok": sys.version_info >= (3, 10),
        },
        "project_root": {
            "configured_dir": str(_PROJECT_DIR) if _PROJECT_DIR else None,
            "effective_dir": str(get_project_dir()),
            "using_fallback": _PROJECT_DIR is None,
        },
        "dependencies": {"pyngrok": False, "message": "Not installed"},
        "ngrok_binary": {"found": False, "path": None},
        "ngrok_auth": {"configured": False},
        "recommendations": [],
    }

    # Check pyngrok
    try:
        import pyngrok

        results["dependencies"]["pyngrok"] = True
        results["dependencies"]["message"] = f"Installed ({pyngrok.__version__})"
    except ImportError:
        results["recommendations"].append("Install pyngrok: 'uv add pyngrok'")

    # Check ngrok binary
    ngrok_path = shutil.which("ngrok")
    if ngrok_path:
        results["ngrok_binary"]["found"] = True
        results["ngrok_binary"]["path"] = ngrok_path
    else:
        results["recommendations"].append("Install ngrok CLI and add to PATH")

    # Check auth token
    if os.environ.get("NGROK_AUTHTOKEN"):
        results["ngrok_auth"]["configured"] = True
        results["ngrok_auth"]["source"] = "env_var"
    else:
        try:
            from pyngrok import conf

            if conf.get_default().auth_token:
                results["ngrok_auth"]["configured"] = True
                results["ngrok_auth"]["source"] = "config_file"
        except ImportError:
            config_path = Path.home() / ".ngrok2" / "ngrok.yml"
            config_path_new = (
                Path.home() / "Library/Application Support/ngrok/ngrok.yml"
            )
            if config_path.exists() or config_path_new.exists():
                results["ngrok_auth"]["configured"] = True
                results["ngrok_auth"]["source"] = "config_file_detected"

    if not results["ngrok_auth"]["configured"]:
        results["recommendations"].append(
            "Configure ngrok auth: 'ngrok config add-authtoken <TOKEN>'"
        )

    return results

