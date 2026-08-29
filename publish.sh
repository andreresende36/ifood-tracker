#!/usr/bin/env bash
#
# Publica o banco local na nuvem: comita e empurra SÓ data/*.db e
# data/profiles.json. A réplica hospedada não escreve nada — ela só existe
# porque este script mandou dado novo para o repo, e o Streamlit Community
# Cloud reinicia o app sozinho a cada push em main.
#
# Roda depois de uma coleta (./run.sh), quando você quiser que a versão da
# nuvem passe a mostrar o dado novo. Nunca roda sozinho.
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

ALVOS=(data/orders.db data/carol.db data/profiles.json)
EXISTENTES=()
for f in "${ALVOS[@]}"; do
    [[ -f "$f" ]] && EXISTENTES+=("$f")
done

if [[ ${#EXISTENTES[@]} -eq 0 ]]; then
    echo "Nenhum dos arquivos de dado existe ainda (${ALVOS[*]}). Nada a publicar." >&2
    exit 1
fi

if git diff --quiet -- "${EXISTENTES[@]}" && git diff --cached --quiet -- "${EXISTENTES[@]}"; then
    echo "Sem mudança em ${EXISTENTES[*]} — a nuvem já está com o dado mais recente."
    exit 0
fi

echo "▶ Mudanças a publicar:"
git diff --stat -- "${EXISTENTES[@]}"
echo

read -r -p "Publicar para a nuvem agora? [s/N] " resp
if [[ "${resp:-}" != "s" && "${resp:-}" != "S" ]]; then
    echo "Cancelado — nada foi publicado."
    exit 0
fi

git add -- "${EXISTENTES[@]}"
git commit -q -m "dados: coleta de $(date +%d/%m/%Y)"
git push
echo "✅ Publicado. O Streamlit Community Cloud reinicia o app sozinho em alguns minutos."
