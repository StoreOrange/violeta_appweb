# config.py

import os
import pathlib

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


def _load_toml_config():
    data = {}
    paths = []
    env_path = os.environ.get('CONFIG_TOML_PATH')
    if env_path:
        paths.append(pathlib.Path(env_path))
    paths.append(pathlib.Path.cwd() / 'config.toml')
    paths.append(pathlib.Path.home() / '.codex' / 'config.toml')

    for path in paths:
        if path.is_file():
            try:
                content = path.read_text(encoding='utf-8')
                if not content.strip():
                    continue
                loaded = tomllib.loads(content)
            except Exception:
                continue
            if isinstance(loaded, dict):
                data.update(loaded)
    return data


_TOML = _load_toml_config()
_SMTP = _TOML.get('smtp', {}) if isinstance(_TOML.get('smtp'), dict) else {}


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-gestion-violeta')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://superuser:1234@localhost:5432/GESTIONDB'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_HOST = os.environ.get('SMTP_HOST', _SMTP.get('host', 'smtp.zoho.com'))
    SMTP_PORT = int(os.environ.get('SMTP_PORT', _SMTP.get('port', 587)))
    SMTP_USER = os.environ.get('SMTP_USER', _SMTP.get('user', ''))
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', _SMTP.get('password', ''))
    SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', _SMTP.get('sender_name', 'Violeta Workspace'))
    SMTP_USE_TLS = str(os.environ.get('SMTP_USE_TLS', _SMTP.get('use_tls', 'true'))).lower() in (
        '1', 'true', 'yes', 'on'
    )
