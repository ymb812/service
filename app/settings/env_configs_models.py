from pydantic import BaseModel, Field, SecretStr, field_validator


class APPSettings(BaseModel):
    prod_mode: bool = Field(alias='PROD_MODE', default=False)
    x_auth_token: SecretStr = Field(alias='X_AUTH_TOKEN')
    runware_api_key: SecretStr = Field(alias='RUNWARE_API_KEY')


class DataBaseConfigsModel(BaseModel):
    db_user: str = Field(alias='POSTGRES_USER')
    db_host: str = Field(alias='POSTGRES_HOST')
    db_port: int = Field(alias='POSTGRES_PORT')
    db_pass: SecretStr = Field(alias='POSTGRES_PASSWORD')
    db_name: SecretStr = Field(alias='POSTGRES_DATABASE')


class RestAPISettings(BaseModel):
    rest_host: str = Field(alias='REST_HOST')
    rest_port: int = Field(alias='REST_PORT')


class OllamaSettings(BaseModel):
    ollama_url: str = Field(alias='OLLAMA_URL')
    ollama_model: str = Field(alias='OLLAMA_MODEL')
    ollama_temperature: float = Field(alias='OLLAMA_TEMPERATURE')
    ollama_num_predict: int = Field(alias='OLLAMA_NUM_PREDICT')


class Settings(
    APPSettings,
    DataBaseConfigsModel,
    RestAPISettings,
    OllamaSettings,
):
    pass
