#!/usr/bin/env bash
#
# Sobe o dashboard do iFood tracker.
# Pergunta o perfil e se deve coletar antes de abrir.
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

# ── venv ──────────────────────────────────────────────────────────────────────
if [[ ! -x .venv/bin/python ]]; then
    echo "▶ Criando .venv…"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    playwright install chromium
else
    source .venv/bin/activate
fi

# ── pergunta 1: perfil ────────────────────────────────────────────────────────
# Chaves e nomes vêm do próprio projeto (data/*.db + data/profiles.json),
# então um perfil novo aparece aqui sozinho.
KEYS=()
NOMES=()
while IFS=$'\t' read -r chave nome; do
    KEYS+=("$chave")
    NOMES+=("$nome")
done < <(python -c "
import database
ps = database.list_profiles() or ['default']
# 'default' primeiro, igual ao seletor do dashboard
ps = ['default'] * ('default' in ps) + [p for p in ps if p != 'default']
for k in ps:
    print(k, database.profile_display_name(k), sep='\t')
")

echo
echo "👤 Qual perfil?"
for i in "${!NOMES[@]}"; do
    printf "   %d) %s\n" "$((i + 1))" "${NOMES[$i]}"
done
read -r -p "   Escolha [1]: " esc
esc="${esc:-1}"
if ! [[ "$esc" =~ ^[0-9]+$ ]] || (( esc < 1 || esc > ${#KEYS[@]} )); then
    echo "   Opção inválida — usando ${NOMES[0]}." >&2
    esc=1
fi
PERFIL="${KEYS[$((esc - 1))]}"
PERFIL_NOME="${NOMES[$((esc - 1))]}"

# ── pergunta 2: coletar? ──────────────────────────────────────────────────────
echo
echo "⬇️  Coletar pedidos na abertura?"
echo "   1) Sim — abre o Chrome e atualiza antes do dashboard"
echo "   2) Não — abre direto com os dados que já existem"
read -r -p "   Escolha [1]: " esc
COLETAR=1
[[ "${esc:-1}" == "2" ]] && COLETAR=0

# ── coleta ────────────────────────────────────────────────────────────────────
if (( COLETAR )); then
    echo
    echo "▶ Coletando pedidos de $PERFIL_NOME…"
    echo "  (Chrome vai abrir. Se aparecer captcha, resolva na janela.)"
    if python scraper.py --profile-name "$PERFIL" --auto 2>&1 | tee "data/scrape_${PERFIL}.log"; then
        echo "✅ Coleta concluída."
    else
        echo "⚠️  Coleta falhou — abrindo o dashboard com os dados que já existem."
    fi
fi

# ── dashboard ─────────────────────────────────────────────────────────────────
echo
echo "▶ Abrindo o dashboard ($PERFIL_NOME)…"
export IFOOD_PROFILE="$PERFIL"
exec streamlit run dashboard.py
