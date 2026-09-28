# PROJECT_VISION.md

O projeto e um portal juridico brasileiro de alta escala, com codigo proprio, prioridade humana e controle editorial antes de crescimento de URLs.

Objetivos iniciais:
- criar uma plataforma propria para wiki juridica, legislacao, jurisprudencia, noticias, artigos, glossario, perguntas e hubs tematicos;
- publicar apenas conteudo com intencao unica, fonte, autoria, revisao e aviso informativo quando juridico;
- manter busca interna, filtros, parametros e paginas operacionais fora do indice;
- operar sem Next.js, sem framework frontend pesado, sem CMS pronto e sem dependencia externa por conveniencia.

P0 materializa contrato tecnico e acervo juridico bloqueado em crescimento real. Conteudo juridico substantivo continua bloqueado ate fonte, proveniencia e revisao passarem pelos gates, mas isso nao autoriza tratar P0 como arquitetura sem conteudo, nem adiar a meta publica minima para outro objetivo quando houver camada executavel no repo.

Meta de crescimento: o produto deve chegar neste `/goal` a no minimo 10 mil paginas juridicas informativas aprovadas e preparar arquitetura para centenas de milhares ou milhoes de paginas possiveis, com alta intencao de contratar advogado e CTA proprio de WhatsApp para contratacao quando os gates de intenção, ética, fonte e revisão classificarem a página para CTA. A meta só é comprovada pelo contador vivo reconciliado entre `published_manifest`, `content/pages.json`, `public/`, sitemap, release transacional e checks como `p0-cycle-close-indexable-10k`; artefato parcial ou contador histórico não basta. Ela exige fabrica massiva por lotes, conteudo unico, fonte oficial atual, score humano/natural, validacao em massa, revisao juridico-editorial, HTML leve no primeiro response e CTA contextual calibrado por familia; ela nao autoriza spam, template, conteudo IA-like, thin content, pagina sem valor ou pagina pesada que desperdice crawl/render.

A plataforma tambem deve ser desenhada como canal de contratacao juridica remota quando a intencao permitir. Pesquisa de palavras-chave, servicos juridicos e paid-intent devem considerar demanda real de busca na internet e viabilidade de jornada 100% digital: leitura, triagem contextual, envio remoto de documentos, WhatsApp e atendimento online, inclusive para usuario fora da localidade do advogado. O produto nao deve orientar a jornada padrao para atendimento presencial; necessidade de ato presencial ou diligencia local deve ser tratada como limite juridico informado, nao como oferta principal.

O projeto nao deve crescer por spam, permutacao de palavras-chave ou texto mecanico. A escala precisa vir de pesquisa de fonte correta, escrita natural, utilidade humana, revisao algoritmica, validacao massiva e refinamento repetido em laboratorio.

O agente Codex neste repositorio opera com autonomia de engenheiro senior, arquiteto e criador de conteudo juridico. Ele deve usar engenharia agressiva inteligente, continuar o trabalho dentro do escopo, pesquisar fontes oficiais quando criar ou corrigir conteudo substantivo, construir coletores/checks quando faltar ferramenta para demanda externa, corrigir bugs e lacunas sem aguardar aprovacao normal e persistir cada ciclo em checkpoint e commit.

Commit nao e conclusao do `/goal`. Antes de commitar, o agente deve fazer autocrítica, registrar o que foi resolvido, o que ainda pode melhorar e o proximo ciclo executavel. O trabalho continua enquanto a meta massiva, a arquitetura, a qualidade e a indexacao nao estiverem comprovadas.

Perguntas de engenharia registradas em checkpoint ou documentacao nao sao pausa nem formulario. Elas devem orientar decisao tecnica precisa: qual vertical P0 aumenta paginas unicas com qualidade, qual fonte oficial e sinal externo sustentam a proxima familia, qual algoritmo/teste reduz falso positivo ou falso negativo, qual dado permanente precisa nascer no repo e qual prova de HTML leve/Googlebot/release ainda falta. Quando a pergunta aponta requisito ja contratado, a resposta correta e implementar, validar e registrar evidencia no mesmo `/goal`.

Nenhum requisito contratado neste projeto é recomendação passiva. Arquitetura, conteúdo jurídico, demanda de alta intenção, atendimento digital, dados versionados, pesquisa oficial, SEO/crawl, HTML leve, testes robustos e publicação segura compõem a mesma entrega. Quando o repositório ainda não tiver coletor, API, scraper metadata-only permitido, check, schema ou gerador necessário, a decisão de engenharia é construir a peça faltante e operar com bloqueio público, mantendo qualidade e continuidade.

Pedido explícito, contrato vivo, checkpoint, roadmap, pergunta de engenharia e achado integrado de agente exigem execução verificável do `/goal` ativo, não comentário, recomendação ou fase posterior. Todo requisito executável pertence a este `/goal`. A visão do produto só é respeitada quando o próximo ciclo materializa camada técnica ou editorial com prova: pesquisa externa, fonte oficial, rascunho autoral, revisão, HTML leve, Googlebot, sitemap/canonical/robots, CTA classificado, teste robusto, manifesto/transação preparada, publicação aprovada com gate completo e correção executável das páginas reprovadas.
