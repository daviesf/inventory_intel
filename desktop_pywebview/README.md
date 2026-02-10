# IntelliStock Desktop App (PyWebView)

Aplicativo desktop leve usando **PyWebView** - uma alternativa simples e estável ao Neutralino.

## Requisitos

- Python 3.8+ (já instalado no projeto)
- PyWebView (já instalado via pip)

## Como Rodar

Na pasta do projeto, execute:

```powershell
.\desktop_pywebview\run.bat
```

Ou diretamente:

```powershell
.venv\Scripts\python.exe desktop_pywebview\app.py
```

## O Que Faz

1. Verifica se a engine (API) está rodando
2. Se não estiver, inicia automaticamente via uvicorn
3. Abre uma janela desktop com o Dashboard
4. Ao fechar, encerra a engine (se iniciada pelo app)

## Configuração

Edite as variáveis `CONFIG` em `app.py`:

```python
CONFIG = {
    "engine_port": 8000,
    "dashboard_url": "http://127.0.0.1:8000/dashboard",
    "auto_start_engine": True,
}
```
