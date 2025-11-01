from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    db_host: str = "db"
    db_port: int = 3306
    db_user: str = "appuser"
    db_pass: str = "devpass"
    db_name: str = "appdb"
    jwt_secret: str = "change_this_now"
    jwt_expire_minutes: int = 60
    password_scheme: str = "bcrypt"
    parameter_spec_path: str = "参数输入规范.md"
    parameter_validation_enabled: bool = True
    parameter_validation_require_optional: bool = True
    parameter_validation_optional_min_count: int = 1

    @property
    def sql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
