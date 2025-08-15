import os
import warnings

from dotenv import load_dotenv
load_dotenv()

class Config:
    """Base configuration class."""
    def _get_env_var(var_name, default):
        value = os.getenv(var_name, default)
        if value == default and os.environ.get(var_name) is None:
            warnings.warn(f"Environment variable '{var_name}' not found. Using default: {default}")
        return value

    MYSQL_HOST = _get_env_var('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(_get_env_var('MYSQL_PORT', 3306))
    MYSQL_USER = _get_env_var('MYSQL_USER', 'root')
    MYSQL_PASSWORD = _get_env_var('MYSQL_PASSWORD', '111234')
    DATABASE_NAME = _get_env_var('DATABASE_NAME', 'app_db')
    SECRET_KEY = _get_env_var('SECRET_KEY', 'secret-key-for-user-hash-generation')