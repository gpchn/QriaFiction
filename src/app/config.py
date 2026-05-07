import json
import shutil
import toml
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GAMES_DIR = DATA_DIR / "games"
GAMES_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"


class ConfigStore:
    _defaults = {
        "theme": "dark",
        "language": "zh-CN",
        "window_width": 1000,
        "window_height": 700,
        "default_ai_provider": "keyword",
        "ai_models": [],
    }

    def __init__(self):
        self._path = CONFIG_FILE

    def _read(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return dict(self._defaults)

    def _write(self, data: dict):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        cfg = self._read()
        keys = key.split(".")
        val = cfg
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, default)
            else:
                return default
        return val if val is not None else default

    def get_all(self) -> dict:
        cfg = self._read()
        return {**self._defaults, **cfg}

    def set(self, key: str, value):
        cfg = self._read()
        keys = key.split(".")
        target = cfg
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self._write(cfg)

    def add_ai_model(self, model: dict):
        cfg = self._read()
        models = cfg.setdefault("ai_models", [])
        model["id"] = str(int(datetime.now().timestamp() * 1000))
        models.append(model)
        self._write(cfg)

    def remove_ai_model(self, model_id: str):
        cfg = self._read()
        cfg["ai_models"] = [m for m in cfg.get("ai_models", []) if m.get("id") != model_id]
        self._write(cfg)

    def get_ai_models(self) -> list:
        cfg = self._read()
        return cfg.get("ai_models", [])


class ProjectStore:
    @staticmethod
    def _scan() -> list:
        if not GAMES_DIR.exists():
            return []
        projects = []
        for d in sorted(GAMES_DIR.iterdir()):
            if not d.is_dir():
                continue
            toml_path = d / "project.toml"
            info = {
                "id": d.name,
                "name": d.name,
                "path": str(d),
                "title": d.name,
                "author": "",
                "version": "",
                "has_script": False,
                "script_main": "",
            }
            if toml_path.exists():
                try:
                    cfg = toml.load(toml_path)
                    proj = cfg.get("project", {})
                    info["title"] = proj.get("title", d.name)
                    info["author"] = proj.get("author", "")
                    info["version"] = proj.get("version", "")
                except Exception:
                    pass

            script_dir = d / "script"
            if script_dir.exists():
                main_script = script_dir / "main.qf"
                if main_script.exists():
                    info["has_script"] = True
                    info["script_main"] = str(main_script)
                else:
                    qf_files = list(script_dir.glob("*.qf"))
                    if qf_files:
                        info["has_script"] = True
                        info["script_main"] = str(qf_files[0])

            projects.append(info)
        return projects

    def get_projects(self) -> list:
        return self._scan()

    def get_project(self, project_id: str) -> dict | None:
        proj_dir = GAMES_DIR / project_id
        if not proj_dir.exists():
            return None
        info = {"id": project_id, "name": project_id, "path": str(proj_dir)}
        toml_path = proj_dir / "project.toml"
        if toml_path.exists():
            try:
                cfg = toml.load(toml_path)
                proj = cfg.get("project", {})
                info["title"] = proj.get("title", project_id)
                info["author"] = proj.get("author", "")
                info["version"] = proj.get("version", "")
                info["display"] = cfg.get("display", {})
            except Exception:
                pass

        script_dir = proj_dir / "script"
        if script_dir.exists():
            main_script = script_dir / "main.qf"
            if main_script.exists():
                info["has_script"] = True
                info["script_main"] = str(main_script)
            else:
                qf_files = list(script_dir.glob("*.qf"))
                if qf_files:
                    info["has_script"] = True
                    info["script_main"] = str(qf_files[0])

        return info

    def import_project(self, zip_path: str) -> str:
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise ValueError("ZIP 文件不存在")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)

            toml_path = tmp / "project.toml"
            if not toml_path.exists():
                raise ValueError("ZIP 包中缺少 project.toml")

            cfg = toml.load(toml_path)
            proj_info = cfg.get("project", {})
            name = proj_info.get("name") or proj_info.get("title")

            if not name:
                raise ValueError("project.toml 中未找到 name 或 title 字段")

            name = "".join(c for c in name if c.isalnum() or c in '-_')
            name = name.strip().lower()

            if not name:
                raise ValueError("无法从 project.toml 生成有效的项目名称")

            dest = GAMES_DIR / name
            if dest.exists():
                suffix = 1
                while (GAMES_DIR / f"{name}_{suffix}").exists():
                    suffix += 1
                name = f"{name}_{suffix}"
                dest = GAMES_DIR / name

            shutil.move(str(tmp), str(dest))

        return name

    def delete_project(self, project_id: str):
        proj_dir = GAMES_DIR / project_id
        if proj_dir.exists():
            shutil.rmtree(proj_dir)


config_store = ConfigStore()
project_store = ProjectStore()
