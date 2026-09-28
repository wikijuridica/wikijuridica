# ADR: lingua-go no gate PT-BR bloqueado

Data: 2026-06-22

## Decisão

Adotar `github.com/pemistahl/lingua-go v1.4.0` como dependência runtime Go direta, restrita a `internal/languagegate/`, para detectar prosa não PT-BR e reduzir falso verde em conteúdo jurídico bloqueado.

## Escopo Permitido

- uso interno em gate PT-BR e validação de amostras bloqueadas;
- evidência operacional no ledger de performance/checks;
- integração com heurística própria para termos jurídicos brasileiros;
- nenhum uso como aprovação pública autônoma;
- nenhuma escrita em `public/`, `content/pages.json`, `published_manifest`, sitemap real ou `.release-staging`.

## Justificativa

Conteúdo jurídico público precisa ter PT-BR correto, acentuação e naturalidade. O detector evita que texto em outro idioma ou amostra incompatível satisfaça gate editorial por acidente. A biblioteca fica atrás de adapter próprio para preservar testes, thresholds e possibilidade de troca.

## Riscos E Controles

Risco principal: falso positivo bloquear texto bom ou falso negativo deixar passar texto ruim. O controle é combinar lingua-go com heurística jurídica local, amostragem limitada, checks focados e bloqueio público permanente até revisão, fonte, OAB/CTA, anti-spam, HTML leve e release completo.

## Validação

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/languagegate ./internal/demandobservations ./internal/contract -run 'TestPortugueseBRGate|TestValidateRefinedPublicProse|TestCodex2PolicyEnforcement'`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern run ./cmd/check language-gate-ptbr --timings`
- `./tools/check-codex2-policy-enforcement`
