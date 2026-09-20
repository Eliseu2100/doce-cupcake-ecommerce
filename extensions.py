"""
Extensões compartilhadas da aplicação.

Fica num módulo separado (em vez de dentro de app.py) para não criar
importação circular: os Controllers precisam do `limiter` para decorar
suas rotas, e app.py precisa dos Controllers — se o limiter estivesse
dentro de app.py, um importaria o outro em círculo.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Limite por endereço IP. Guarda o contador em memória (suficiente para
# um serviço com uma instância só, como este projeto no Render/PythonAnywhere;
# em um ambiente com várias instâncias, o storage_uri apontaria para Redis).
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
