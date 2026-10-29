"""Local finfreedom setup and diagnostic commands."""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(prog="finfreedom")
    commands = parser.add_subparsers(dest="command", required=True)
    db = commands.add_parser("db")
    db_commands = db.add_subparsers(dest="db_command", required=True)
    db_commands.add_parser("status")
    db_commands.add_parser("use-sqlite")
    mysql = db_commands.add_parser("configure-mysql")
    mysql.add_argument("--host", required=True)
    mysql.add_argument("--port", type=int, default=3306)
    mysql.add_argument("--database", required=True)
    mysql.add_argument("--user", required=True)
    mysql.add_argument("--no-tls", action="store_true")
    install = commands.add_parser("install")
    install.add_argument("--profile", action="append", dest="profiles",
                         help="DSH profile to install into; repeat for multiple profiles")
    legacy = commands.add_parser("import-legacy", help="Import old holdings, watchlist and market cache into SQLite")
    legacy.add_argument("--container", required=True, help="Existing Financial Freedom web container")
    args = parser.parse_args()
    if args.command == "install":
        install_plugin(args.profiles)
    elif args.command == "import-legacy":
        from finfreedom.legacy_import import import_from_container
        import json
        print(json.dumps(import_from_container(args.container), ensure_ascii=False, indent=2))
    elif args.db_command == "status":
        from finfreedom.database import status
        print(status())
    elif args.db_command == "use-sqlite":
        from finfreedom.database import status, use_sqlite
        use_sqlite()
        print(status())
    elif args.db_command == "configure-mysql":
        from finfreedom.database import configure_mysql, status
        password = getpass.getpass("MySQL password (input hidden): ")
        configure_mysql(args.host, args.port, args.database, args.user, password, tls=not args.no_tls)
        print(status())


def install_plugin(profiles: list[str] | None) -> None:
    """Install Python runtime, packaged Skill files, and the DSH bundle."""
    repo_root = Path(__file__).resolve().parents[1]
    dsh_home = Path(os.environ.get("DSH_HOME", "~/.dsh")).expanduser()
    dsh = shutil.which("dsh")
    if not dsh:
        raise SystemExit("未找到 dsh 命令；请先安装 DeepSeek Harness。")
    venv = dsh_home / "finfreedom" / "venv"
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        configured = os.environ.get("FINFREEDOM_PYTHON")
        candidates = [configured] if configured else []
        candidates.extend(shutil.which(name) for name in ("python3.13", "python3.12", "python3.11", "python3"))
        candidates.append(sys.executable)
        created = False
        for candidate in dict.fromkeys(item for item in candidates if item):
            compatible = subprocess.run(
                [candidate, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode == 0
            if not compatible:
                continue
            try:
                subprocess.run([candidate, "-m", "venv", str(venv)], check=True)
                created = True
                break
            except subprocess.CalledProcessError:
                shutil.rmtree(venv, ignore_errors=True)
        if not created:
            raise SystemExit("未找到可用的 Python 3.11+；可设置 FINFREEDOM_PYTHON 指向解释器。")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", str(repo_root)], check=True)
    source_skills = repo_root / "skills"
    target_skills = dsh_home / "skills"
    target_skills.mkdir(mode=0o700, parents=True, exist_ok=True)
    for skill in source_skills.iterdir():
        destination = target_skills / skill.name
        if destination.exists():
            print(f"保留现有 Skill（避免覆盖用户内容）: {skill.name}")
            continue
        shutil.copytree(skill, destination)
    if profiles is None:
        profile_root = dsh_home / "profiles"
        profiles = sorted(item.name for item in profile_root.iterdir() if item.is_dir()) if profile_root.exists() else []
    if not profiles:
        profiles = ["web"]
    for profile in profiles:
        if not profile or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in profile):
            raise SystemExit(f"profile 名无效：{profile!r}")
        subprocess.run([dsh, "plugin", "--profile", profile, "add", str(repo_root)], check=True)
        print(f"已安装到 DSH profile: {profile}")


if __name__ == "__main__":
    main()
