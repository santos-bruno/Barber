# Front-end — Barbearia e Belezaria Sr. Perison

App mobile em **React Native + Expo**.

## Telas
- **Home** — dados da barbearia (endereço, WhatsApp, mapa).
- **Serviços** — lista de serviços (consumida da API, com fallback offline).
- **Agendamento** — seleção de serviço, nome, data e hora; envia o resumo
  direto para o WhatsApp do estabelecimento.

## Rodando localmente

```bash
cd frontend
npm install
npx expo start
```

Leia o QR Code com o app **Expo Go** ou rode em emulador Android/iOS.

### Apontando para o back-end
Defina a URL da API (o app usa `http://localhost:8000` por padrão):

```bash
EXPO_PUBLIC_API_URL=http://SEU_IP:8000 npx expo start
```

## Build do APK
O APK é gerado automaticamente pela pipeline em
`.github/workflows/android-apk.yml` a cada `push` na branch `main`, e fica
disponível como *Artifact* do GitHub Actions.

Para gerar localmente:

```bash
cd frontend
npx expo prebuild --platform android
cd android
./gradlew assembleRelease
# APK em: android/app/build/outputs/apk/release/
```
