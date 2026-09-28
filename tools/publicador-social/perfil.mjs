/**
 * perfil.mjs — onde mora o perfil de navegador do publicador social, e por que
 * ele NÃO mora dentro da árvore do repositório.
 *
 * O PROBLEMA, MEDIDO EM 2026-09-05
 * Até aqui o perfil vivia em `tools/publicador-social/.perfil-navegador`, com
 * `.gitignore` próprio. São 275 MB de perfil Chromium, e dentro deles estão
 * `Default/Cookies` e `Default/Login Data` — ou seja, as SESSÕES AUTENTICADAS
 * de Facebook e LinkedIn do titular, em claro, dentro da árvore do projeto.
 *
 * Duas consequências, e nenhuma delas é hipotética:
 *
 * 1. SEGURANÇA. Credencial viva dentro da árvore é credencial que viaja em
 *    qualquer cópia, backup, worktree, tarball ou varredura que alcance o
 *    diretório. `.gitignore` impede o commit; não impede nada disso. O scanner
 *    de segredos deste repositório achou uma `gcp-api-key` embutida nos
 *    resources do Chromium ali dentro — prova de que a árvore de fato carrega
 *    material sensível que ninguém pôs lá de propósito.
 *
 * 2. CUSTO. `gitleaks dir` varre o DISCO, não o índice do git: o `.gitignore`
 *    não o detém. O alvo `tools` levava 405 s por passada, e ~85% disso era
 *    varrer este perfil. Pior, ele muda a cada publicação social, então `tools`
 *    nunca estabilizava em cache nenhum.
 *
 * A CORREÇÃO É ONDE ELE MORA, e não uma allowlist. Silenciar o scanner sobre um
 * diretório que guarda cookie de sessão seria calar o alarme e deixar o cofre
 * aberto — resolve o vermelho e piora o risco.
 *
 * O perfil passa a viver sob XDG_STATE_HOME (por padrão
 * `~/.local/state/wikijuridica/perfil-navegador`), que é exatamente a categoria
 * definida pela especificação: estado que persiste entre execuções, é
 * específico da máquina e não deve ser versionado nem sincronizado.
 *
 * MIGRAÇÃO SEM RELOGIN: se o perfil antigo existir e o novo não, ele é MOVIDO
 * na primeira execução. Mover preserva os cookies, então o titular não precisa
 * autenticar de novo — o que importa, porque reautenticar exige a GUI do dono,
 * que tem a VM com PJe/e-SAJ e o certificado.
 */

import { existsSync, mkdirSync, renameSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

/** Caminho legado, dentro da árvore. Só existe para a migração. */
export function perfilLegado(diretorioDoPublicador) {
  return join(diretorioDoPublicador, '.perfil-navegador');
}

/** Onde o perfil deve morar. Fonte única — os quatro scripts derivam daqui. */
export function caminhoDoPerfil() {
  const forcado = process.env.WIKI_PERFIL_NAVEGADOR;
  if (forcado && forcado.trim() !== '') {
    return forcado;
  }
  const estado =
    process.env.XDG_STATE_HOME && process.env.XDG_STATE_HOME.trim() !== ''
      ? process.env.XDG_STATE_HOME
      : join(homedir(), '.local', 'state');
  return join(estado, 'wikijuridica', 'perfil-navegador');
}

/**
 * Devolve o caminho do perfil, migrando o legado uma única vez.
 *
 * Falha RUIDOSAMENTE se a migração não completar. O modo de falha silencioso
 * seria pior: criar um perfil vazio no destino novo faria o publicador abrir um
 * navegador não autenticado e o operador levaria a sessão inteira para
 * descobrir que estava deslogado — com o perfil autenticado intacto no lugar
 * antigo, ainda dentro da árvore.
 */
export function perfilPronto(diretorioDoPublicador) {
  const destino = caminhoDoPerfil();
  const legado = perfilLegado(diretorioDoPublicador);

  if (!existsSync(destino) && existsSync(legado)) {
    mkdirSync(dirname(destino), { recursive: true });
    try {
      renameSync(legado, destino);
      console.error(
        `publicador-social: perfil migrado para fora da arvore do repositorio\n` +
          `  de:    ${legado}\n` +
          `  para:  ${destino}\n` +
          `  motivo: Cookies e Login Data nao devem viver dentro da arvore do projeto,\n` +
          `          e o scanner de segredos gastava ~85%% do tempo do alvo "tools" ali.\n` +
          `  as sessoes autenticadas foram preservadas: nao e preciso repetir --login.`,
      );
    } catch (erro) {
      throw new Error(
        `publicador-social: nao consegui migrar o perfil de ${legado} para ${destino}: ${erro.message}\n` +
          `Nao vou seguir com um perfil vazio: o navegador abriria deslogado e a publicacao\n` +
          `falharia no fim, depois de montar tudo. Mova o diretorio a mao e rode de novo.`,
      );
    }
  }

  mkdirSync(destino, { recursive: true });
  return destino;
}
