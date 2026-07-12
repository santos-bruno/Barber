#!/usr/bin/env bash
#
# init_repo.sh
# Inicializa o repositório Git do projeto da Barbearia Sr. Perison.
#
# Uso:
#   chmod +x init_repo.sh
#   ./init_repo.sh
#
set -e

# 1. Inicializa o repositório (idempotente).
if [ ! -d ".git" ]; then
  git init
  git branch -M main
  echo "==> Repositório Git inicializado (branch main)."
else
  echo "==> Repositório Git já existe. Pulando 'git init'."
fi

# 2. Garante o .gitignore (só cria se ainda não existir).
if [ ! -f ".gitignore" ]; then
  cat > .gitignore <<'EOF'
# Node / Expo
node_modules/
.expo/
dist/
web-build/
frontend/android/
frontend/ios/

# Python
venv/
.venv/
__pycache__/
*.py[cod]
*.db

# Ambiente / segredos
.env
.env.*
!.env.example

# Sistema / IDE
.DS_Store
.idea/
.vscode/
EOF
  echo "==> .gitignore criado."
else
  echo "==> .gitignore já existe. Mantido."
fi

# 3. Primeiro commit.
git add .
git commit -m "feat: estrutura inicial e pipeline de auto-apk"
echo "==> Commit inicial criado com sucesso."

echo ""
echo "Próximos passos:"
echo "  git remote add origin <URL_DO_REPOSITORIO>"
echo "  git push -u origin main"
