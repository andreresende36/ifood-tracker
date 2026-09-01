#!/usr/bin/env bash
#
# Sobe o dashboard do iFood tracker.
# Pergunta o perfil (André, Carolina ou Casal) e se deve coletar antes de
# abrir, e ao fechar o dashboard chama publish.sh sozinho.
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

# Sempre ${VAR} nas mensagens: em locale UTF-8 o bash 3.2 (o do macOS) engole o
# primeiro byte de um caractere acentuado colado no $VAR para dentro do nome da
# variável — "$PERFIL_NOME…" virava a variável 'PERFIL_NOME\xe2', que com
# `set -u` mata o script.

# ── venv ──────────────────────────────────────────────────────────────────────
if [[ ! -x .venv/bin/python ]]; then
    echo "▶ Criando .venv…"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    # requirements.txt é o mesmo que a réplica hospedada instala (enxuto, sem
    # playwright); requirements-scraper.txt é só desta máquina, para coletar.
    pip install --quiet -r requirements.txt -r requirements-scraper.txt
    playwright install chromium
else
    source .venv/bin/activate
fi

CASAL="$(python -c 'import database; print(database.CASAL)')"

# ── pergunta 1: perfil ────────────────────────────────────────────────────────
# Chaves e nomes vêm do próprio projeto (data/*.db + data/profiles.json),
# então um perfil novo aparece aqui sozinho. Casal só aparece quando há mais
# de uma pessoa — não existe "conjunto" de uma pessoa só — igual ao dashboard.
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
if len(ps) > 1:
    print(database.CASAL, 'Casal', sep='\t')
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

# Quem coletar: o próprio perfil, ou os dois reais quando é o Casal —
# coletar é sempre por pessoa, o conjunto é só leitura combinada no dashboard.
if [[ "${PERFIL}" == "${CASAL}" ]]; then
    COLETA_KEYS=()
    COLETA_NOMES=()
    for i in "${!KEYS[@]}"; do
        [[ "${KEYS[$i]}" == "${CASAL}" ]] && continue
        COLETA_KEYS+=("${KEYS[$i]}")
        COLETA_NOMES+=("${NOMES[$i]}")
    done
else
    COLETA_KEYS=("${PERFIL}")
    COLETA_NOMES=("${PERFIL_NOME}")
fi

# ── pergunta 2: coletar? ──────────────────────────────────────────────────────
echo
echo "⬇️  Atualizar pedidos na abertura?"
echo "   1) Sim — abre o Chrome e atualiza antes do dashboard"
echo "   2) Não — abre direto com os dados que já existem"
read -r -p "   Escolha [1]: " esc
COLETAR=1
[[ "${esc:-1}" == "2" ]] && COLETAR=0

# ── coleta ────────────────────────────────────────────────────────────────────
if (( COLETAR )); then
    for i in "${!COLETA_KEYS[@]}"; do
        chave="${COLETA_KEYS[$i]}"
        nome="${COLETA_NOMES[$i]}"
        echo
        echo "▶ Coletando pedidos de ${nome}…"
        echo "  (Chrome vai abrir. Se aparecer captcha, resolva na janela.)"
        if python scraper.py --profile-name "${chave}" --auto 2>&1 | tee "data/scrape_${chave}.log"; then
            echo "✅ Coleta de ${nome} concluída."
        else
            echo "⚠️  Coleta de ${nome} falhou — seguindo com os dados que já existem."
        fi
    done
fi

# ── dashboard ─────────────────────────────────────────────────────────────────
echo
echo "▶ Abrindo o dashboard (${PERFIL_NOME})…"
export IFOOD_PROFILE="${PERFIL}"
# Sem `exec` e com `|| true`: Ctrl+C sai do streamlit com código != 0, e com
# `set -e` isso pularia o publish.sh abaixo — fechar o dashboard não é erro.
streamlit run dashboard.py || true

# ── publica ───────────────────────────────────────────────────────────────────
# Roda ao fechar o dashboard (Ctrl+C ou fechando a aba), não antes: só faz
# sentido publicar depois que a sessão de uso/coleta terminou.
echo
./publish.sh
