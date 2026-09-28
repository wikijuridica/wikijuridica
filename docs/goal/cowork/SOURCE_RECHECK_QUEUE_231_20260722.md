# Fila de recheck vivo — bloco sistemico official_source (run 20260722T1400Z)

Autoria: claude-cowork-fable (loop agendado 11:49). Origem: v2_ingest_report run v2-ingest-20260722T140000Z.

Paginas rejeitadas com par verified_at vazio + http_status=0: **225** (fora 8 casos special ja mapeados no funil).
URLs unicas a verificar: **120**. Padrao: shards INTEIROS caem juntos — lacuna de carimbo do pipeline, nao 231 fontes podres.

## Acao

1. Terminal: rodar o live audit sancionado (audit-v2-source-provenance) sobre os shards abaixo — a maioria deve carimbar em lote.
2. Cowork (proxima janela, orcamento web resetado): verificar ao vivo as que o live audit nao alcancar (client-rendered/WAF) e emitir cowork_source_recheck_*.jsonl no schema do verificador Go.

## URLs por contagem de paginas afetadas

```
 63  https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm
 31  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
 29  https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15040.htm
 22  https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm
 19  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm
 17  https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm
 12  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm
  8  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art206
  7  https://noticias.stf.jus.br/postsnoticias/plataformas-terao-60-dias-para-implementar-medidas-estruturais-decide-stf/
  7  https://www.in.gov.br/web/dou/-/enunciado-cd/anpd-n-1-de-22-de-maio-de-2023-485306934
  7  https://www.in.gov.br/web/dou/-/resolucao-normativa-aneel-n-1.000-de-7-de-dezembro-de-2021-368359651
  5  https://www.planalto.gov.br/ccivil_03/leis/l9394.htm#art48
  5  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art51
  5  https://www.planalto.gov.br/ccivil_03/leis/l7210compilado.htm
  4  https://noticias.stf.jus.br/postsnoticias/nota-a-imprensa-43/
  4  https://www.planalto.gov.br/ccivil_03/leis/l9870.htm#art1
  4  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art20
  4  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm
  4  https://www.planalto.gov.br/ccivil_03/leis/l9868.htm
  4  https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm
  4  https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm
  4  https://www.planalto.gov.br/ccivil_03/decreto-lei/1965-1988/del0261.htm
  3  https://www.planalto.gov.br/ccivil_03/leis/l9394.htm#art53
  3  https://www.planalto.gov.br/ccivil_03/leis/l9870.htm#art6
  3  https://www.gov.br/mec/pt-br/acesso-a-informacao/institucional/estrutura-organizacional/orgaos-especificos-singulares/secretaria-de-regulacao-e-supervisao-da-educacao-superior
  3  https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm#art5
  3  https://www.planalto.gov.br/ccivil_03/leis/l9784.htm
  3  https://noticias.stf.jus.br/postsnoticias/patentes-ja-concedidas-de-farmacos-e-equipamentos-de-saude-nao-terao-mais-prazo-estendido/
  3  https://noticias.stf.jus.br/postsnoticias/plenario-confirma-homologacao-de-acordo-sobre-prazos-para-analise-de-beneficios-do-inss/
  2  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art39
  2  https://www.gov.br/mec/pt-br/politica-regulacao-supervisao-educacao-superior/ead
  2  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art37
  2  https://noticias.stf.jus.br/postsnoticias/stf-afasta-exigencia-previa-de-autorizacao-para-biografias/
  2  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art62
  2  https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc41.htm
  2  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art62-a
  2  https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc19.htm
  2  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art41
  2  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art63
  1  https://noticias.stf.jus.br/postsnoticias/stf-conclui-que-direito-ao-esquecimento-e-incompativel-com-a-constituicao-federal/
  1  https://prouniportal.mec.gov.br/images/legislacao/2008/portaria_normativa_19_de_20112008_compilada.pdf
  1  https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/decreto/d5493.htm
  1  https://www.gov.br/mec/pt-br/assuntos/es/prouni
  1  https://www.gov.br/mec/pt-br/politica-regulacao-supervisao-educacao-superior
  1  https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.861.htm#art5
  1  https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11788.htm#art2
  1  https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11788.htm#art7
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art6
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art52
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art30
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art35
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art27
  1  https://www.planalto.gov.br/ccivil_03/leis/l9394.htm#art47
  1  https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art14
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art927
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art10
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art5
  1  https://www.planalto.gov.br/ccivil_03/leis/l9099.htm#art69
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art39
  1  https://www.planalto.gov.br/ccivil_03/leis/l9099.htm#art76
  1  https://www.planalto.gov.br/ccivil_03/leis/l9099.htm#art89
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art323
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art312
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art319
  1  https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art25
  1  https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l14843.htm
  1  https://portaldatransparencia.gov.br/entenda-a-gestao-publica/ceis
  1  https://licitacoesecontratos.tcu.gov.br/3-2-principios-das-licitacoes-e-dos-contratos-administrativos/
  1  https://www.planalto.gov.br/ccivil_03/leis/l9882.htm
  1  https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/lei/l13300.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l9507.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l4717.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l7347orig.htm
  1  https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11417.htm
  1  https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc45.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l9029.htm
  1  https://atos.cnj.jus.br/atos/detalhar/179
  1  https://www.planalto.gov.br/ccivil_03/leis/l8935.htm
  1  https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14382.htm
  1  https://conteudo.cvm.gov.br/legislacao/resolucoes/resol175.html
  1  https://www.planalto.gov.br/ccivil_03/leis/l6024.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l8036consol.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l6385compilada.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l9656.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l9099.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp101.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l9029.htm#art1
  1  https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm#art37
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art186
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art27
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art20
  1  https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc47.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art67
  1  https://www.planalto.gov.br/ccivil_03/leis/l9527.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art68
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art75
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art73
  1  https://www.planalto.gov.br/ccivil_03/leis/l8460compilada.htm
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art58
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art59
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art53
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art36
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art46
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art40
  1  https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm#art44
  1  https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=531
  1  https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=550
  1  https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=542
  1  https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp?classeProcesso=RE&incidente=4245763&numeroProcesso=688267&numeroTema=1022
  1  https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?dt=20200518&formato=PDF&nreg=201700107975&salvar=false&seq=106476234&tipo=91
  1  https://www.bcb.gov.br/meubc/faqs/p/consulta-a-valores-de-pessoas-falecidas
  1  https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/agua
  1  https://noticias.stf.jus.br/postsnoticias/stf-enquadra-homofobia-e-transfobia-como-crimes-de-racismo-ao-reconhecer-omissao-legislativa/
  1  https://noticias.stf.jus.br/postsnoticias/mes-da-mulher-trabalhadoras-gravidas-e-lactantes-nao-podem-atuar-em-atividades-insalubres/
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art189
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art943
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art186
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art932
  1  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art403
  1  https://noticias.stf.jus.br/postsnoticias/stf-afasta-incidencia-do-ir-sobre-pensoes-alimenticias-decorrentes-do-direito-de-familia/
```

## Shards afetados (paginas com par idx)

```
 22  educacao-04.jsonl
 22  glossario2-02.jsonl
 22  investimentos-06.jsonl
 20  seguros-05.jsonl
 19  servidor-05.jsonl
 17  glossario2-13.jsonl
 14  servidor-01.jsonl
 10  glossario-17.jsonl
 10  seguros-03.jsonl
  7  telecom_energia-05.jsonl
  5  investimentos-09.jsonl
  4  glossario2-19.jsonl
  4  servidor-03.jsonl
  4  transito-03.jsonl
  3  digital-05.jsonl
  3  educacao-03.jsonl
  3  glossario2-12.jsonl
  3  lgpd-05.jsonl
  3  previdenciario-20.jsonl
  3  servidor-02.jsonl
  3  servidor-10.jsonl
  2  digital-04.jsonl
  2  inpi-06.jsonl
  2  inpi-11.jsonl
  2  sucessoes2-02.jsonl
  1  imobiliario-04.jsonl
  1  inpi-12.jsonl
  1  investimentos-04.jsonl
  1  lgpd-02.jsonl
  1  lgpd-03.jsonl
  1  lgpd-08.jsonl
  1  lgpd-10.jsonl
  1  lgpd-11.jsonl
  1  procedimentos-13.jsonl
  1  servidor-09.jsonl
  1  servidor-11.jsonl
  1  sucessoes-14.jsonl
  1  telecom_energia-13.jsonl
  1  trabalhista-10.jsonl
  1  trabalhista-14.jsonl
  1  tributario-13.jsonl
```
