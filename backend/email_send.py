"""
Envio de e-mails transacionais (boas-vindas no cadastro).

Dois modos, escolhidos por variáveis de ambiente:
- RESEND_API_KEY  -> envia pela API do Resend (recomendado; https, funciona no Render)
- SMTP_HOST/USER/PASSWORD -> envia por SMTP (Brevo, Gmail, etc.)

Se nada estiver configurado, as funções apenas não enviam (sem erro).
"""
import html as html_lib
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "Agenda Barber <onboarding@resend.dev>")
APP_BASE_URL = os.getenv(
    "APP_BASE_URL", "https://agenda-barber-o0to.onrender.com"
).rstrip("/")
# Para onde vão os avisos internos (novo cadastro, nova assinatura).
# Se não definido, usa o próprio remetente verificado.
OWNER_NOTIFY_EMAIL = os.getenv("OWNER_NOTIFY_EMAIL", "")


def is_configured() -> bool:
    return bool(
        BREVO_API_KEY
        or RESEND_API_KEY
        or (SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    )


def _from_parts() -> tuple:
    """Devolve (nome, email) a partir de MAIL_FROM ('Nome <email>' ou 'email')."""
    if "<" in MAIL_FROM and ">" in MAIL_FROM:
        name = MAIL_FROM.split("<", 1)[0].strip().strip('"')
        email = MAIL_FROM.split("<", 1)[1].split(">", 1)[0].strip()
        return (name or "Agenda Barber", email)
    return ("Agenda Barber", MAIL_FROM.strip())


def diagnose() -> dict:
    """Estado da configuração de e-mail (sem expor segredos)."""
    if BREVO_API_KEY:
        mode = "brevo-api"
    elif RESEND_API_KEY:
        mode = "resend"
    elif SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        mode = "smtp"
    else:
        mode = "nenhum"
    sender_name, sender_email = _from_parts()
    return {
        "configured": is_configured(),
        "mode": mode,
        "from": MAIL_FROM,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "smtp_host": SMTP_HOST or None,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER or None,
        "smtp_password_set": bool(SMTP_PASSWORD),
        "resend_key_set": bool(RESEND_API_KEY),
        "brevo_key_set": bool(BREVO_API_KEY),
    }


def send_test(to: str) -> dict:
    """Envia um e-mail de teste e devolve o resultado real (com o erro, se houver)."""
    if not is_configured():
        return {"ok": False, "error": "E-mail não configurado. Defina BREVO_API_KEY (ou RESEND_API_KEY / SMTP_*) no Render."}
    html = (
        "<div style='font-family:Arial,sans-serif;padding:16px'>"
        "<h2 style='color:#F0C24B'>✅ Teste do Agenda Barber</h2>"
        "<p>Se você recebeu este e-mail, o envio está funcionando.</p></div>"
    )
    try:
        detail = _send_raw(to, "Teste de e-mail — Agenda Barber 💈", html)
        return {"ok": True, "detail": detail}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _plain_from() -> str:
    # extrai só o endereço, se vier no formato "Nome <email>"
    if "<" in MAIL_FROM and ">" in MAIL_FROM:
        return MAIL_FROM.split("<", 1)[1].split(">", 1)[0].strip()
    return MAIL_FROM


def _html_to_text(html: str) -> str:
    """Versão em texto puro do e-mail (melhora a entrega; evita filtro de spam)."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr)>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def _send_raw(to: str, subject: str, html: str) -> str:
    """Envia de fato. Levanta exceção em caso de falha (não engole o erro).

    Devolve um detalhe do provedor (ex.: messageId do Brevo) para diagnóstico.
    """
    if BREVO_API_KEY:
        # API HTTP do Brevo (porta 443) — funciona no Render, que bloqueia SMTP.
        name, email = _from_parts()
        r = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": BREVO_API_KEY, "accept": "application/json"},
            json={
                "sender": {"name": name, "email": email},
                "to": [{"email": to}],
                "replyTo": {"email": email, "name": name},
                "subject": subject,
                "htmlContent": html,
                "textContent": _html_to_text(html),
            },
            timeout=20,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Brevo {r.status_code}: {r.text}")
        try:
            mid = r.json().get("messageId", "")
        except Exception:  # noqa: BLE001
            mid = ""
        return f"Brevo {r.status_code} · messageId={mid}"

    if RESEND_API_KEY:
        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": MAIL_FROM, "to": [to], "subject": subject, "html": html},
            timeout=20,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Resend {r.status_code}: {r.text}")
        return f"Resend {r.status_code}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))
    ctx = ssl.create_default_context()
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=20) as s:
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(_plain_from(), [to], msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(_plain_from(), [to], msg.as_string())
    return f"SMTP {SMTP_HOST}:{SMTP_PORT} ok"


def send_email(to: str, subject: str, html: str) -> bool:
    if not is_configured():
        return False
    try:
        _send_raw(to, subject, html)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[email] falhou: {e}")
        return False


def _welcome_html(owner_name: str, shop_name: str, slug: str, trial_days: int) -> str:
    link = f"{APP_BASE_URL}/agendar/{slug}"
    gerente = f"{APP_BASE_URL}/gerente"
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0F1115;color:#F4F6FB;padding:24px;border-radius:16px;max-width:560px;margin:0 auto">
      <div style="text-align:center">
        <div style="font-size:44px">💈</div>
        <h1 style="color:#F0C24B;margin:6px 0">Agenda Barber</h1>
      </div>
      <p>Olá, <strong>{owner_name}</strong>! 👋</p>
      <p>A conta da <strong>{shop_name}</strong> foi criada com sucesso. Você tem
      <strong>{trial_days} dias grátis</strong> para testar tudo.</p>

      <h3 style="color:#F0C24B">Seu link de agendamento</h3>
      <p>Divulgue no Instagram, WhatsApp e anúncios — os clientes agendam sozinhos:</p>
      <p><a href="{link}" style="color:#F0C24B">{link}</a></p>

      <h3 style="color:#F0C24B">Como gerenciar</h3>
      <ul style="line-height:1.7">
        <li><strong>No computador:</strong> <a href="{gerente}" style="color:#F0C24B">{gerente}</a> (entre com seu e-mail e senha)</li>
        <li><strong>No celular:</strong> baixe o app Android e entre com o mesmo login</li>
        <li><strong>Guia de primeiros passos (PDF):</strong> <a href="{APP_BASE_URL}/guia.pdf" style="color:#F0C24B">baixar aqui</a></li>
      </ul>

      <h3 style="color:#F0C24B">Primeiros passos</h3>
      <ol style="line-height:1.7">
        <li>Confira seus <strong>serviços</strong> e <strong>horários</strong> de funcionamento</li>
        <li>Cadastre seus <strong>barbeiros</strong> (cada um com login próprio)</li>
        <li>Compartilhe o <strong>link de agendamento</strong> com seus clientes</li>
        <li>Acompanhe a <strong>agenda</strong> e o <strong>fluxo de caixa</strong></li>
      </ol>

      <p style="color:#9AA3B2;font-size:13px;margin-top:24px">Precisa de ajuda? É só responder este e-mail.</p>
      <p style="color:#9AA3B2;font-size:12px">Agenda Barber — sistema de agendamento para barbearias</p>
    </div>
    """


def send_welcome(owner_name: str, shop_name: str, email: str, slug: str, trial_days: int) -> None:
    if not is_configured():
        return
    send_email(
        email,
        f"Bem-vindo ao Agenda Barber, {shop_name}! 💈",
        _welcome_html(owner_name, shop_name, slug, trial_days),
    )


def _invite_html(barber_name: str, shop_name: str, email: str, password: str) -> str:
    gerente = f"{APP_BASE_URL}/gerente"
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0F1115;color:#F4F6FB;padding:24px;border-radius:16px;max-width:560px;margin:0 auto">
      <div style="text-align:center"><div style="font-size:40px">✂️</div>
      <h1 style="color:#F0C24B;margin:6px 0">Agenda Barber</h1></div>
      <p>Olá, <strong>{barber_name}</strong>!</p>
      <p>A <strong>{shop_name}</strong> criou um acesso para você no Agenda Barber.
      Com ele, você vê <strong>a sua agenda</strong> e os seus atendimentos.</p>
      <div style="background:#171A21;border:1px solid #262B36;border-radius:12px;padding:14px;margin:14px 0">
        <p style="margin:4px 0"><strong>Login:</strong> {email}</p>
        <p style="margin:4px 0"><strong>Senha:</strong> {password}</p>
      </div>
      <p><strong>Como entrar:</strong></p>
      <ul style="line-height:1.7">
        <li>No computador: <a href="{gerente}" style="color:#F0C24B">{gerente}</a></li>
        <li>No celular: baixe o app Android e entre com esse login</li>
      </ul>
      <p style="color:#9AA3B2;font-size:13px">Recomendamos trocar a senha no primeiro acesso.</p>
    </div>
    """


def send_barber_invite(barber_name: str, shop_name: str, email: str, password: str) -> None:
    if not is_configured():
        return
    send_email(
        email,
        f"Seu acesso na {shop_name} — Agenda Barber ✂️",
        _invite_html(barber_name, shop_name, email, password),
    )


def _owner_notify_to() -> str:
    """Para quem enviar os avisos internos (dono do SaaS)."""
    return OWNER_NOTIFY_EMAIL or _plain_from()


def _owner_html(title: str, rows: list) -> str:
    items = "".join(
        f'<p style="margin:6px 0"><strong style="color:#F0C24B">{k}:</strong> {v}</p>'
        for k, v in rows
    )
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0F1115;color:#F4F6FB;padding:24px;border-radius:16px;max-width:560px;margin:0 auto">
      <div style="text-align:center"><div style="font-size:38px">💈</div>
      <h1 style="color:#F0C24B;margin:6px 0;font-size:20px">{title}</h1></div>
      <div style="background:#171A21;border:1px solid #262B36;border-radius:12px;padding:16px;margin:14px 0">{items}</div>
      <p style="text-align:center"><a href="{APP_BASE_URL}/painel" style="color:#F0C24B">Abrir o painel do dono</a></p>
    </div>
    """


def send_owner_new_signup(shop_name: str, owner_name: str, owner_email: str, whatsapp: str) -> None:
    """Avisa o dono do SaaS quando uma nova barbearia se cadastra (trial)."""
    if not is_configured():
        return
    send_email(
        _owner_notify_to(),
        f"🎉 Nova barbearia cadastrada: {shop_name}",
        _owner_html("Nova barbearia no Agenda Barber", [
            ("Barbearia", shop_name),
            ("Responsável", owner_name),
            ("E-mail", owner_email),
            ("WhatsApp", whatsapp or "—"),
            ("Status", "Período de teste (trial)"),
        ]),
    )


def send_owner_new_subscription(shop_name: str, plan: str, owner_email: str = "") -> None:
    """Avisa o dono do SaaS quando uma assinatura é paga/ativada."""
    if not is_configured():
        return
    send_email(
        _owner_notify_to(),
        f"💳 Nova assinatura ativa: {shop_name}",
        _owner_html("Nova assinatura paga! 🚀", [
            ("Barbearia", shop_name),
            ("Plano", (plan or "—").capitalize()),
            ("E-mail", owner_email or "—"),
            ("Status", "Assinatura ATIVA"),
        ]),
    )
