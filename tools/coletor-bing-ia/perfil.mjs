/**
 * perfil.mjs — onde mora o perfil de navegador do coletor de citação por IA, e
 * por que ele NÃO é o perfil do publicador social.
 *
 * PERFIL SEPARADO, E ISSO É DECISÃO, NÃO ARRUMAÇÃO. O publicador social guarda
 * as sessões de Facebook e LinkedIn do titular e é frente que FUNCIONA hoje
 * (5/5 em Facebook e LinkedIn, medido). Pôr a conta Microsoft dentro do mesmo
 * diretório significaria que qualquer defeito desta frente — um perfil
 * corrompido por encerramento abrupto, uma limpeza de cookies para destravar um
 * login, um `--login` que sobrescreve o estado — cairia sobre aquela. São duas
 * contas de serviços distintos, com ciclos de expiração distintos, e não há
 * ganho nenhum em compartilhá-las.
 *
 * FORA DA ÁRVORE DO REPOSITÓRIO, pelo mesmo motivo medido em 2026-09-05 no
 * publicador: um perfil Chromium carrega `Default/Cookies` e
 * `Default/Login Data` — credencial viva. `.gitignore` impede o commit; não
 * impede que o diretório viaje em cópia, backup, worktree, tarball ou varredura
 * de scanner de segredos. E `gitleaks dir` varre o DISCO, não o índice: o alvo
 * `tools` levava 405 s por passada, ~85% disso varrendo perfil de navegador.
 *
 * O endereço é `XDG_STATE_HOME/wikijuridica/perfil-bing-ia`, que é exatamente a
 * categoria que a especificação define: estado que persiste entre execuções, é
 * específico da máquina e não deve ser versionado nem sincronizado.
 *
 * NÃO HÁ MIGRAÇÃO DE LEGADO AQUI, ao contrário de `publicador-social/perfil.mjs`:
 * este perfil nasce neste endereço. Um `renameSync` de um diretório que nunca
 * existiu seria código morto se passando por cuidado.
 */

import { existsSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import process from 'node:process';

/** Onde o perfil deve morar. Fonte única — o coletor deriva daqui. */
export function caminhoDoPerfil() {
  const forcado = process.env.WIKI_PERFIL_BING_IA;
  if (forcado && forcado.trim() !== '') {
    return forcado;
  }
  const estado =
    process.env.XDG_STATE_HOME && process.env.XDG_STATE_HOME.trim() !== ''
      ? process.env.XDG_STATE_HOME
      : join(homedir(), '.local', 'state');
  return join(estado, 'wikijuridica', 'perfil-bing-ia');
}

/**
 * Devolve o caminho do perfil e diz se ele JÁ EXISTIA antes desta chamada.
 *
 * O booleano importa: perfil recém-criado nunca está autenticado, e essa é a
 * diferença entre "a sessão da conta Microsoft expirou" e "esta máquina nunca
 * viu um login". As duas pedem o mesmo comando ao titular, mas a segunda não é
 * defeito nenhum — é a primeira execução — e o relatório precisa saber separar
 * as duas para não gritar defeito onde só falta a estreia.
 */
export function perfilPronto() {
  const destino = caminhoDoPerfil();
  const jaExistia = existsSync(destino);
  mkdirSync(destino, { recursive: true });
  return { caminho: destino, jaExistia };
}
