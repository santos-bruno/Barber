"""Envio de notificações push via Firebase Cloud Messaging (FCM HTTP v1).

Configuração (no Render):
  FCM_SERVICE_ACCOUNT_JSON  -> conteúdo do JSON da conta de serviço do Firebase
                               (Configurações do projeto > Contas de serviço >
                                Gerar nova chave privada). É SECRETO.
  FCM_PROJECT_ID            -> opcional; se vazio, usa o project_id do JSON.

Tudo é best-effort: se não estiver configurado ou falhar, não quebra o fluxo.
"""
import json
import os

import httpx

FCM_SERVICE_ACCOUNT_JSON = os.getenv("FCM_SERVICE_ACCOUNT_JSON", "")
FCM_PROJECT_ID = os.getenv("FCM_PROJECT_ID", "")
_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"

_creds = None
_project = ""


def is_configured() -> bool:
    return bool(FCM_SERVICE_ACCOUNT_JSON.strip())


def _load():
    """Carrega (uma vez) as credenciais da conta de serviço."""
    global _creds, _project
    if _creds is not None:
        return _creds, _project
    from google.oauth2 import service_account

    info = json.loads(FCM_SERVICE_ACCOUNT_JSON)
    _creds = service_account.Credentials.from_service_account_info(info, scopes=[_SCOPE])
    _project = FCM_PROJECT_ID or info.get("project_id", "")
    return _creds, _project


def _access_token(creds) -> str:
    import google.auth.transport.requests

    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def send_push(tokens, title: str, body: str, data: dict | None = None) -> int:
    """Envia a notificação para uma lista de tokens de dispositivo (FCM).
    Devolve quantos foram aceitos. Nunca levanta exceção."""
    tokens = [t for t in (tokens or []) if t]
    if not tokens or not is_configured():
        return 0
    try:
        creds, project = _load()
        if not project:
            return 0
        token = _access_token(creds)
        url = f"https://fcm.googleapis.com/v1/projects/{project}/messages:send"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload_data = {str(k): str(v) for k, v in (data or {}).items()}
        ok = 0
        for tk in tokens:
            msg = {
                "message": {
                    "token": tk,
                    "notification": {"title": title, "body": body},
                    "data": payload_data,
                    "android": {"priority": "high"},
                }
            }
            try:
                r = httpx.post(url, headers=headers, json=msg, timeout=15)
                if r.status_code < 300:
                    ok += 1
                else:
                    print(f"[push] FCM {r.status_code}: {r.text[:180]}")
            except Exception as e:  # noqa: BLE001
                print(f"[push] envio falhou: {e}")
        return ok
    except Exception as e:  # noqa: BLE001
        print(f"[push] erro: {e}")
        return 0
