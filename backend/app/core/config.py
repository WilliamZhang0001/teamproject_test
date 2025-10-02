from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    db_host: str
    db_port: int
    db_user: str
    db_pass: str
    db_name: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    password_scheme: str = "bcrypt"

    @property
    def sql_url(self):
        return f"mysql+mysqlconnector://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
