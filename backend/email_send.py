"""
Envio de e-mails transacionais (boas-vindas no cadastro).

Dois modos, escolhidos por variáveis de ambiente:
- RESEND_API_KEY  -> envia pela API do Resend (recomendado; https, funciona no Render)
- SMTP_HOST/USER/PASSWORD -> envia por SMTP (Brevo, Gmail, etc.)

Se nada estiver configurado, as funções apenas não enviam (sem erro).
"""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "Agenda Barber <onboarding@resend.dev>")
APP_BASE_URL = os.getenv(
    "APP_BASE_URL", "https://agenda-barber-o0to.onrender.com"
).rstrip("/")


def is_configured() -> bool:
    return bool(RESEND_API_KEY or (SMTP_HOST and SMTP_USER and SMTP_PASSWORD))


def _plain_from() -> str:
    # extrai só o endereço, se vier no formato "Nome <email>"
    if "<" in MAIL_FROM and ">" in MAIL_FROM:
        return MAIL_FROM.split("<", 1)[1].split(">", 1)[0].strip()
    return MAIL_FROM


def send_email(to: str, subject: str, html: str) -> bool:
    if RESEND_API_KEY:
        try:
            r = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={"from": MAIL_FROM, "to": [to], "subject": subject, "html": html},
                timeout=20,
            )
            if r.status_code >= 300:
                print(f"[email] Resend {r.status_code}: {r.text}")
            return r.status_code < 300
        except Exception as e:  # noqa: BLE001
            print(f"[email] Resend falhou: {e}")
            return False

    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = MAIL_FROM
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            ctx = ssl.create_default_context()
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                    s.sendmail(_plain_from(), [to], msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                    s.starttls(context=ctx)
                    s.login(SMTP_USER, SMTP_PASSWORD)
                    s.sendmail(_plain_from(), [to], msg.as_string())
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[email] SMTP falhou: {e}")
            return False

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
