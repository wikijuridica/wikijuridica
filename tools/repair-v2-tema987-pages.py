#!/usr/bin/env python3
"""Apply/check the paid-ad STF Tema 987 authorial corrections from 2026."""

import argparse
import json
import os
import stat
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools import audit_v2_pages as auditor
from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease


FINAL_SOURCE_URL = (
    'https://noticias.stf.jus.br/postsnoticias/'
    'plataformas-terao-60-dias-para-implementar-medidas-estruturais-decide-stf/')
FINAL_SOURCE = {
    'url': FINAL_SOURCE_URL,
    'name': 'STF — notícia oficial da conclusão dos embargos no Tema 987',
    'anchor_claim': (
        'registra a tese final e sua modulação: efeitos desde 5 de agosto de '
        '2025, tratamento dos atos continuados ou permanentes e preservação '
        'das decisões transitadas em julgado'),
    'verified_at': '2026-07-15',
    'http_status': 200,
}

FINAL_ANCHOR_CLAIMS = {
    'banc-golpe-telefone-falso-google-anuncio': (
        'item 4: anúncio pago gera presunção relativa de culpa '
        'independente de notificação, afastável por atuação diligente; inclui '
        'a modulação temporal final'),
    'banc-golpe-falso-leilao-veiculos': (
        'item 4: publicidade paga atrai presunção relativa de culpa, '
        'independente de notificação e afastável por prova de diligência; '
        'inclui a modulação final'),
    'banc-site-clonado-loja-falsa': (
        'item 4: impulsionamento pago sujeita a plataforma à presunção '
        'relativa de culpa, com defesa por diligência; inclui a modulação final'),
    'banc-golpe-aluguel-imovel-falso': (
        'item 4: anúncio patrocinado tem presunção relativa de culpa '
        'independente de notificação, afastável por diligência; inclui a '
        'modulação final'),
    'imob-golpe-anuncio-falso-aluguel': (
        'item 4: publicidade paga recebe presunção relativa de culpa, '
        'ressalvada prova diligente; inclui a modulação final'),
    'cons-site-falso-golpe-como-recuperar-dinheiro': (
        'item 4: anúncio pago recebe presunção relativa de culpa independente '
        'de notificação, afastável por diligência; distingue o regime orgânico '
        'e inclui a modulação final'),
    'banc-whatsapp-clonado-pedindo-dinheiro': (
        'distingue conta inautêntica denunciada, conta autêntica invadida e '
        'mensageria privada sujeita ao art. 19; inclui a modulação final'),
    'banc-instagram-invadido-venda-falsa': (
        'distingue cadastro inautêntico, suporte de conta e comunicação '
        'interpessoal privada sujeita ao art. 19; inclui a modulação final'),
    'banc-golpe-romance-relacionamento-virtual': (
        'fixa ciência e omissão para cadastro denunciado como inautêntico e '
        'registra a modulação temporal definida nos embargos'),
    'cons-golpe-em-compra-de-usado-entre-pessoas': (
        'item 7: marketplace submetido ao CDC é distinto do mero classificado '
        'sob o regime de conteúdo de terceiro; inclui a modulação final'),
}


UPDATES = {
    'banc-golpe-telefone-falso-google-anuncio': (
        'data/editorial/v2_pages/bancario-01.jsonl',
        'O anúncio fraudulento como prova e a responsabilidade da plataforma',
        'É preciso separar o resultado orgânico da publicidade remunerada. Conforme a tese final do Tema 987, formada depois dos embargos encerrados em 2026, a plataforma que colocou a fraude entre os resultados patrocinados fica sujeita a presunção relativa de culpa. A presunção incide mesmo sem notificação prévia. Para afastá-la, o serviço precisa apresentar prova de atuação diligente e tempestiva na prevenção ou retirada do anúncio enganoso.\n\nNos resultados orgânicos e em outros conteúdos de terceiro, a plataforma, depois de notificação extrajudicial que identifique suficientemente o conteúdo e a ilicitude apontada, pode responder quando a ciência e a omissão da plataforma se revelam na falta de remoção diligente em tempo razoável. Fica ressalvada a dúvida razoável sobre a ilicitude após análise qualificada. Essa notificação qualificada integra o regime orgânico. Já para o anúncio pago, denunciar continua sendo providência útil para interromper o golpe e produzir protocolo, mas a denúncia não é requisito para a presunção, que incide mesmo sem notificação prévia. Preserve a captura que identifique se o resultado era patrocinado, o endereço da página e o horário em que apareceu.'),
    'banc-whatsapp-clonado-pedindo-dinheiro': (
        'data/editorial/v2_pages/bancario-02.jsonl',
        'Fechando o caso: reparação possível e a lição de segurança',
        'Conta autêntica invadida não se confunde com conta inautêntica. A tese final do Tema 987, considerada a conclusão dos embargos em 2026, não transforma todo sequestro de conta em responsabilidade automática da plataforma. Para cadastro inautêntico denunciado, o provedor, ciente da falsidade, pode responder quando permanece omisso e não retira a conta. Já a falha de suporte para recuperar um acesso legítimo deve ser demonstrada pelo histórico de pedidos, protocolos e tempo de resposta.\n\nTambém é necessário separar o acesso à conta do conteúdo das conversas. Para comunicações interpessoais privadas e mensagens privadas, o art. 19 do Marco Civil continua a exigir ordem judicial específica; uma simples notificação extrajudicial não substitui esse requisito para responsabilização pelo conteúdo trocado entre pessoas. Identificado o invasor, permanece cabível cobrar dele os danos causados ao titular e aos contatos lesados.'),
    'banc-golpe-falso-leilao-veiculos': (
        'data/editorial/v2_pages/bancario-02.jsonl',
        'O leiloeiro imitado e a rede social do anúncio respondem?',
        'O leiloeiro cuja identidade foi clonada é, em regra, vítima como você: sem participação ou proveito, não responde pelo prejuízo. Para a plataforma que veiculou anúncio pago, porém, a questão deixou de estar em aberto. Depois que o STF encerrou os embargos do Tema 987 em 2026, a tese vinculante passou a estabelecer presunção relativa de culpa da plataforma por publicidade paga, independentemente de notificação. O serviço pode afastá-la se comprovar medidas diligentes e tempestivas que evitem a veiculação ou indisponibilizem o anúncio em tempo razoável.\n\nNo resultado orgânico, é preciso que a denúncia extrajudicial individualize o link ou a publicação e explique por que é ilícito. Nesse resultado orgânico, a ciência da plataforma pode levar à responsabilidade quando vem seguida de omissão, sem retirada cuidadosa e tempestiva. Dúvida razoável sobre a ilicitude no resultado orgânico exige avaliação qualificada e impede conclusão automática. O comprovante identifica o recebedor, mas eventual cobrança exige apurar participação, conduta e destino do valor. Uma avaliação jurídica pode organizar bloqueio, identificação e restituição a partir do dossiê digital, sem prometer recuperação automática.'),
    'banc-site-clonado-loja-falsa': (
        'data/editorial/v2_pages/bancario-02.jsonl',
        'Identificar quem operava o site: a trilha do Marco Civil',
        'Descobrir quem operava o domínio falso passa pelos registros guardados por provedores. O art. 22 do Marco Civil permite pedir ao juiz o fornecimento desses dados para processo cível ou penal; essa entrega mediante ordem judicial permanece distinta da responsabilidade pelo conteúdo.\n\nO desenho definitivo do Tema 987 resulta dos embargos concluídos pelo STF em 2026 e separa os papéis da plataforma. Se o provedor vendeu ou impulsionou publicidade paga para o site falso, há presunção relativa de culpa do provedor, independentemente de notificação. Para afastar essa presunção, a plataforma precisa demonstrar atuação diligente e tempestiva na prevenção ou na retirada do conteúdo fraudulento.\n\nNa exibição orgânica, é preciso que a notificação extrajudicial traga indicação específica do conteúdo e exponha a razão da ilicitude. Nessa exibição orgânica, a ciência da plataforma seguida de omissão e sem resposta diligente dentro de prazo razoável pode fundamentar responsabilidade. Na exibição orgânica, dúvida razoável sobre a ilicitude após exame qualificado impede responsabilização automática. Por isso, a prova deve indicar onde o link apareceu, se era patrocinado e qual empresa prestava cada serviço. Os registros podem levar ao operador; o recebedor bancário só deve ser cobrado quando houver participação, nexo, retenção sem causa ou outro fundamento demonstrado.'),
    'banc-golpe-romance-relacionamento-virtual': (
        'data/editorial/v2_pages/bancario-02.jsonl',
        'De quem cobrar: os titulares das contas e a trilha até o operador',
        'O “noivo” pode ser fictício, mas os comprovantes identificam contas e titulares. O nome é uma pista, não prova automática de dívida: o recebedor pode ter participado, cedido a conta sem compreender o esquema ou ser vítima de outra fraude. Cobrança ou restituição exigem demonstrar a conduta, o nexo ou a retenção sem causa, conforme o fundamento aplicável; dados completos podem ser requisitados aos bancos pelos meios próprios.\n\nQuando o esquema usa perfil falso, o art. 22 do Marco Civil permite obter judicialmente registros de acesso para chegar ao operador. A responsabilidade da rede social é questão diferente. Com os embargos do Tema 987 encerrados em 2026, o regime definitivo passou a alcançar o cadastro inautêntico denunciado: a plataforma pode responder quando, ciente da ilicitude, permanece omissa e não retira o perfil. Isso não dispensa a análise do tipo de conteúdo nem torna a indenização automática. Uma avaliação jurídica pode coordenar ofícios e medidas de recuperação com base nos documentos, sem antecipar resultado.'),
    'banc-instagram-invadido-venda-falsa': (
        'data/editorial/v2_pages/bancario-02.jsonl',
        'O dono do perfil responde? E a plataforma?',
        'O amigo que teve a conta tomada é vítima, não fornecedor: sem participação no golpe, não responde pelo prejuízo. Conta autêntica invadida não se confunde com conta inautêntica. Essa diferença importa porque a plataforma pode responder por cadastro falso denunciado quando, ciente da ilicitude, permanece omissa e não retira a conta. Para discutir a recuperação do acesso legítimo, documente os pedidos de suporte, os protocolos e o período em que o perfil continuou sob controle do invasor.\n\nOs embargos julgados em 2026 deram forma final ao Tema 987 e exigem distinguir superfícies. Quanto à publicação fraudulenta visível no perfil, a plataforma segue o regime de ciência e omissão, conforme a denúncia e a demora comprovadas. Quando o direct funciona como comunicação interpessoal privada, porém, o art. 19 continua a exigir ordem judicial específica para responsabilização pelo conteúdo da conversa. Essa separação impede tratar suporte da conta, post público e mensagem privada como se fossem o mesmo fato. O invasor permanece alvo direto; quanto ao recebedor bancário, é preciso provar participação, nexo ou outra base de restituição antes da cobrança.'),
    'banc-golpe-aluguel-imovel-falso': (
        'data/editorial/v2_pages/bancario-03.jsonl',
        'Quando o pedido de ressarcimento não avança',
        'Nem todo golpe de aluguel gera dever de indenizar por parte de terceiros. Se o anúncio era orgânico e não há falha identificável do banco ou da plataforma, a pretensão tende a mirar primeiro o autor da fraude; o recebedor aparente só deve ser cobrado após exame de participação, nexo ou fundamento restitutório. Para anúncio orgânico, é necessário que a notificação extrajudicial aponte com precisão o conteúdo e exponha a razão da ilicitude. Nesse anúncio orgânico, ciência e omissão da plataforma, sem providência efetiva em prazo razoável, podem sustentar a discussão. Uma avaliação fundamentada que revele dúvida razoável sobre a ilicitude afasta conclusão automática no anúncio orgânico.\n\nA publicidade paga recebe tratamento próprio. Na tese final definida depois dos embargos de 2026, há presunção relativa de culpa da plataforma quando ela veicula anúncio patrocinado, sem exigir notificação da vítima. O serviço pode afastar a presunção se provar atuação diligente e tempestiva para impedir a veiculação ou retirar o anúncio fraudulento. Ainda vale denunciar e guardar o protocolo, mas esse ato não condiciona a regra aplicável ao anúncio remunerado. A captura deve mostrar se havia selo de patrocínio ou impulsionamento.'),
    'cons-golpe-em-compra-de-usado-entre-pessoas': (
        'data/editorial/v2_pages/consumidor-02.jsonl',
        'E a plataforma de classificados, responde pelo golpe?',
        'A venda entre duas pessoas físicas pode ficar fora do CDC sem que isso resolva, por si só, a relação entre o usuário e a plataforma. A tese final do Tema 987, após os embargos encerrados em 2026, preserva uma fronteira importante: marketplace que intermedeia a venda ou processa o pagamento responde segundo o CDC. Já o mero classificado que apenas hospeda anúncio segue o regime geral aplicável a conteúdo de terceiro.\n\nPor isso, reúna os termos do serviço, a tela que mostra se houve pagamento ou garantia dentro da plataforma e o protocolo da denúncia. No mero classificado, ciência da ilicitude e omissão podem fundamentar a discussão; no marketplace, devem ser examinados os deveres próprios da relação de consumo. A responsabilidade não decorre apenas de o anúncio ter aparecido na internet, nem desaparece só porque comprador e vendedor eram particulares.'),
    'imob-golpe-anuncio-falso-aluguel': (
        'data/editorial/v2_pages/imobiliario-04.jsonl',
        'Regra geral exige nexo; anúncio pago admite presunção',
        'Identificado o autor, o art. 927 do Código Civil fundamenta a reparação do dano causado por ato ilícito. Banco, corretor ou titular de conta não responde automaticamente apenas por aparecer no caminho do pagamento; é preciso examinar conduta, dever de segurança, falha e nexo. Para conteúdo de terceiro em anúncio orgânico, é necessário que a notificação extrajudicial descreva precisamente o anúncio e indique a ilicitude. Nesse anúncio orgânico, a ciência da plataforma sobre a ilicitude pode fundamentar responsabilidade quando há omissão, e o parâmetro exigido é atuar diligentemente em tempo razoável. No anúncio orgânico, dúvida razoável sobre a ilicitude após análise qualificada impede conclusão automática.\n\nQuando vende espaço publicitário para a fraude, a plataforma fica sujeita a presunção relativa de culpa pelo anúncio pago, mesmo sem notificação da vítima. A tese final do Tema 987 consolidou essa regra nos embargos encerrados em 2026. O serviço pode afastar a presunção se demonstrar atuação diligente e tempestiva para prevenir a veiculação ou retirar o conteúdo. O protocolo da denúncia ainda é documento útil, mas sua ausência não elimina por si só a regra do material patrocinado. A captura deve registrar se havia patrocínio ou impulsionamento.'),
    'cons-site-falso-golpe-como-recuperar-dinheiro': (
        'data/editorial/v2_pages/consumidor-01.jsonl',
        'Anúncio pago, resultado orgânico e canais que realmente recebem o caso',
        'Procon e polícia recebem relatos mesmo quando o domínio já sumiu. O consumidor.gov.br só encaminha reclamação a fornecedor participante da plataforma; um site falso sem empresa cadastrada não terá destinatário ali. O protocolo do banco, o boletim, o anúncio e os comprovantes continuam úteis para identificar responsáveis e instruir eventual ação.\n\nDepois de o STF encerrar os embargos em 2026, a tese final do Tema 987 passou a distinguir publicidade remunerada de resultado orgânico. Quando a plataforma veicula anúncio pago fraudulento, há presunção relativa de culpa da plataforma, independentemente de notificação prévia. A plataforma pode afastar essa presunção se provar que atuou diligentemente e em tempo razoável para retirar o anúncio enganoso do ar.\n\nEm resultado orgânico, é necessário que a denúncia individualize a URL ou a publicação e indique a ilicitude. Para resultado orgânico, a plataforma que recebe ciência e permanece em omissão, sem remoção diligente em tempo razoável, pode responder. Se houver dúvida razoável sobre a ilicitude no resultado orgânico, a situação exige avaliação qualificada antes da medida.'),
}

# A operação ativa deste produtor é deliberadamente estreita: somente páginas
# que afirmam a regra de publicidade paga precisam migrar da antiga presunção
# de responsabilidade para a presunção relativa de culpa fixada nos embargos.
# Os demais ramos do Tema 987 continuam protegidos pelos gates semânticos, mas
# não podem ser reescritos por constantes históricas deste reparador.
ACTIVE_PAID_INTENTS = frozenset({
    'banc-golpe-telefone-falso-google-anuncio',
    'banc-golpe-falso-leilao-veiculos',
    'banc-site-clonado-loja-falsa',
    'banc-golpe-aluguel-imovel-falso',
    'imob-golpe-anuncio-falso-aluguel',
    'cons-site-falso-golpe-como-recuperar-dinheiro',
})


MODULATION_PARAGRAPHS = {
    'banc-golpe-telefone-falso-google-anuncio': (
        'Esse parâmetro temporal alcança fatos ocorridos desde 5 de agosto de '
        '2025. Condutas continuadas ou permanentes recebem a formulação final, '
        'enquanto decisões transitadas em julgado permanecem preservadas.'),
    'banc-whatsapp-clonado-pedindo-dinheiro': (
        'Em regra, a tese vale desde 5 de agosto de 2025. Para atos continuados '
        'ou permanentes, aplica-se o texto atual, sempre respeitadas as '
        'decisões transitadas em julgado.'),
    'banc-golpe-falso-leilao-veiculos': (
        'Os efeitos desse regime incidem desde 5 de agosto de 2025. Aos atos '
        'continuados ou permanentes aplica-se a formulação final, sem atingir '
        'decisões transitadas em julgado, que são preservadas.'),
    'banc-site-clonado-loja-falsa': (
        'A aplicação temporal começa em 5 de agosto de 2025. Condutas '
        'continuadas ou permanentes seguem a tese atual; o STF preservou '
        'decisões transitadas em julgado.'),
    'banc-golpe-romance-relacionamento-virtual': (
        'O regime passou a valer em 5 de agosto de 2025. Às condutas '
        'continuadas ou permanentes aplica-se a tese atual, com preservação '
        'das decisões transitadas em julgado.'),
    'banc-instagram-invadido-venda-falsa': (
        'A tese incide desde 5 de agosto de 2025. Nos atos continuados ou '
        'permanentes, aplica-se a formulação final, respeitadas as decisões '
        'transitadas em julgado.'),
    'banc-golpe-aluguel-imovel-falso': (
        'Esses efeitos alcançam fatos desde 5 de agosto de 2025. Atos '
        'continuados ou permanentes seguem a formulação final, preservadas as '
        'decisões transitadas em julgado.'),
    'cons-golpe-em-compra-de-usado-entre-pessoas': (
        'O recorte temporal vale desde 5 de agosto de 2025. Atos continuados '
        'ou permanentes recebem a tese atual, e as decisões transitadas em '
        'julgado ficam preservadas.'),
    'imob-golpe-anuncio-falso-aluguel': (
        'A regra incide sobre fatos desde 5 de agosto de 2025. Para condutas '
        'continuadas ou permanentes, aplica-se a tese atual, respeitadas as '
        'decisões transitadas em julgado.'),
    'cons-site-falso-golpe-como-recuperar-dinheiro': (
        'Os embargos foram encerrados em junho de 2026, com trânsito em '
        'julgado do caso. Os efeitos da tese final incidem desde 5 de agosto '
        'de 2025. A formulação final rege os atos continuados e as situações '
        'permanentes. A coisa julgada permanece resguardada.'),
}


TOP_LEVEL_UPDATES = {
    'banc-whatsapp-clonado-pedindo-dinheiro': {
        'h1': 'Invadiram meu WhatsApp e estão pedindo dinheiro aos meus contatos',
    },
    'banc-instagram-invadido-venda-falsa': {
        'opening': (
            'O anúncio veio do perfil real de um amigo, colega ou pequena loja '
            'que você acompanha há anos. Fotos plausíveis, preço atraente e '
            'conversa pelo direct exploram a confiança já construída. Só '
            'depois do pagamento surge a descoberta de que a conta estava sob '
            'controle de terceiro.\n\nHá duas vítimas possíveis: quem pagou e '
            'quem perdeu o acesso ao perfil. A reação deve investigar o '
            'operador, verificar a participação ou a base restitutória do '
            'recebedor bancário e, quando houver falha própria, examinar a '
            'plataforma. O nome no comprovante é pista, não responsabilidade '
            'automática.'),
    },
}


SECTION_HEADING_UPDATES = {
    'imob-golpe-anuncio-falso-aluguel': (
        'Regra geral exige nexo; anúncio pago admite presunção',
        'Anúncio pago: presunção relativa de culpa da plataforma'),
}


FAQ_UPDATES = {
    'banc-golpe-falso-leilao-veiculos': {
        'Arrematei em leilão verdadeiro e o carro veio com problemas: é o mesmo caso?': (
            'Não. Em leilão verdadeiro, a solução depende do edital, da '
            'modalidade da alienação, de quem vendeu e da relação jurídica '
            'subjacente. O CDC pode incidir em situações próprias, mas não se '
            'aplica automaticamente, sobretudo em alienação judicial. Não se '
            'presume estelionato apenas pelo vício do bem.'),
    },
    'banc-instagram-invadido-venda-falsa': {
        'O produto era de uma lojinha com CNPJ que foi invadida. Muda algo?': (
            'Muda a análise. A invasão pode tornar a empresa também vítima, '
            'mas isso não exclui automaticamente eventual falha própria de '
            'segurança, aparência ou resposta. Preserve a prova, avise-a e '
            'examine participação, dever de cuidado e nexo antes de atribuir '
            'responsabilidade.'),
    },
    'cons-site-falso-golpe-como-recuperar-dinheiro': {
        'O banco é obrigado a devolver o dinheiro de um golpe via Pix?': (
            'Não. O MED submete a denúncia à análise das instituições e só '
            'devolve recursos que forem localizados e bloqueados nas contas '
            'envolvidas no fluxo da fraude, de forma integral ou parcial. '
            'Acione o banco rapidamente pelos canais oficiais e preserve o '
            'protocolo.'),
        'Denunciar no Procon adianta se o site já saiu do ar?': (
            'O Procon pode registrar e encaminhar a questão. Já o '
            'consumidor.gov.br depende de o fornecedor verdadeiro participar '
            'da plataforma; um domínio falso sem empresa cadastrada não '
            'recebe reclamação por esse canal.'),
    },
}


SOURCE_ANCHOR_UPDATES = {
    'banc-golpe-telefone-falso-google-anuncio': {
        'l10406compilada.htm': (
            'contém a disciplina civil de reparação e prescrição aplicável '
            'conforme a causa de pedir, sem prazo universal para todos os réus'),
    },
    'banc-golpe-romance-relacionamento-virtual': {
        'l10406compilada.htm': (
            'fundamenta restituição ou reparação conforme retenção, conduta e '
            'nexo, sem transformar titularidade da conta em dívida automática'),
    },
    'banc-instagram-invadido-venda-falsa': {
        'del2848compilado.htm': (
            'contém os tipos de estelionato eletrônico e invasão de '
            'dispositivo, cujo enquadramento depende do modo de acesso e da prova'),
    },
    'cons-golpe-em-compra-de-usado-entre-pessoas': {
        'l10406compilada.htm#art445': (
            'art. 445 e § 1º: prazo para bem móvel e regra do vício oculto '
            'conhecido depois, contado da ciência e limitado a 180 dias'),
        'l12965.htm#art19': (
            'registra o texto do art. 19, cotejado com os parâmetros finais '
            'do Tema 987 para conteúdo de terceiro'),
    },
    'cons-site-falso-golpe-como-recuperar-dinheiro': {
        'o-que-e-e-como-funciona-o-mecanismo-especial-de-devolucao-med': (
            'explica o prazo de solicitação, a análise da fraude e que a '
            'recuperação integral ou parcial depende dos recursos encontrados'),
    },
}


EXTRA_SECTION_UPDATES = {
    'banc-golpe-telefone-falso-google-anuncio': {
        'Um exemplo do roteiro e os limites da tese contra o banco': (
            'Pense num motorista de aplicativo que pesquisou o telefone do '
            'banco para renegociar uma dívida, ligou para o primeiro resultado '
            'patrocinado e, em vinte minutos, foi convencido a fazer um '
            '“pagamento de caução” de R$ 3.600. A conta dele nunca havia feito '
            'transferência parecida, e nenhuma confirmação extra foi exigida. '
            'É esse contraste que mantém a discussão viva contra a instituição.'
            '\n\nSe, porém, a operação era única e compatível com o histórico, '
            'a tese contra o banco enfraquece, sem eliminar a investigação do '
            'golpista e da plataforma que lucrou com o anúncio. O prazo para '
            'cobrar não se resume universalmente a três anos: depende do réu, '
            'da relação jurídica e da causa de pedir, inclusive das normas '
            'consumeristas eventualmente aplicáveis.'),
    },
    'banc-whatsapp-clonado-pedindo-dinheiro': {
        'Avisar os contatos não é só gentileza: é dever de mitigar': (
            'Enquanto a conta não volta, use outros canais — ligação, redes '
            'sociais ou contatos em comum — para avisar que o número está nas '
            'mãos de golpistas. Cada alerta pode interromper negociações em '
            'andamento e reduzir o número de vítimas.\n\nEsse cuidado também '
            'documenta a reação do titular. Na regra geral do art. 186 do '
            'Código Civil, a responsabilidade por ato próprio exige conduta ou '
            'omissão, dano, nexo e o elemento subjetivo cabível; regimes '
            'objetivos previstos em outras normas não são afastados por essa '
            'frase. A mera titularidade da conta invadida não transfere o '
            'prejuízo dos contatos, mas uma inércia comprovada depois da '
            'ciência pode integrar a análise concreta de culpa e causalidade.'),
        'Identificar o invasor: registros de acesso e a ordem judicial do Marco Civil': (
            'A plataforma de mensagens guarda registros de acesso à aplicação, '
            'como endereço IP, data e hora, e o Marco Civil prevê seu '
            'fornecimento por ordem judicial nos arts. 15 e 22. Esses dados '
            'podem indicar uma conexão ou assinante, mas não provam sozinhos '
            'autoria nem endereço físico do agente: CGNAT, VPN, rede '
            'compartilhada e credenciais usadas por terceiro exigem correlação '
            'com outros elementos.\n\nA investigação pode combinar registros de '
            'aplicação, dados do provedor de conexão, aparelhos e informações '
            'bancárias. A vítima também pode pedir preservação e exibição em '
            'medida própria. A providência deve ser rápida porque a lei prevê '
            'períodos limitados de guarda obrigatória.'),
    },
    'banc-golpe-falso-leilao-veiculos': {
        'A cópia que se trai: domínio recém-criado e Pix para conta estranha': (
            'Sites fraudulentos costumam clonar a identidade de leiloeiros '
            'reais, mudando uma letra do endereço ou a terminação do domínio. '
            'Sinais relevantes são o registro recente do endereço, a pressão '
            'para usar somente Pix sem conferir o edital e as instruções '
            'oficiais de pagamento, e um beneficiário sem relação demonstrada '
            'com o leiloeiro. O Pix, isoladamente, não prova a fraude; é o '
            'conjunto das inconsistências que exige interromper a operação.'
            '\n\nGuarde tudo antes que a página suma: endereço completo do '
            'site, capturas do catálogo e do “arremate”, conversas e '
            'comprovante. Esses registros documentam o ardil e permitem '
            'investigar o vínculo da conta recebedora com o esquema.'),
        'Pagou o lance: bloqueio do saldo e a devolução dentro do Pix': (
            'Acione o seu banco no mesmo dia para registrar a fraude e abrir o '
            'fluxo de devolução do arranjo do Pix contra a conta que recebeu o '
            'lance. O alcance é limitado ao saldo ainda existente, e quadrilhas '
            'de falso leilão esvaziam contas em horas — a rapidez define o '
            'resultado.\n\nPara valores maiores, também é possível pedir ao juiz '
            'a indisponibilidade cautelar do dinheiro. O requerimento se apoia '
            'nos requisitos do art. 300 do Código de Processo Civil: '
            'probabilidade do direito e perigo de dano. O comprovante, as '
            'capturas do site e a ocorrência ajudam a demonstrar esses dois '
            'pontos, sem assegurar que ainda haverá saldo a bloquear.'),
    },
    'banc-golpe-romance-relacionamento-virtual': {
        'Muitas transferências, muitos relógios: o alcance real da devolução no Pix': (
            'O pedido de devolução por fraude do Pix é analisado por transação: '
            'cada envio tem data, registro e saldo próprios. A contestação pode '
            'ser aberta em até oitenta dias, mas agir cedo aumenta a chance de '
            'encontrar recursos; por isso, uma transferência feita há semanas '
            'ou poucos meses não deve ser descartada sem conferir a data '
            'exata.\n\nLeve ao banco a lista completa. Operações fora da janela '
            'ou sem saldo podem exigir outras medidas, inclusive investigação '
            'e via judicial, enquanto os registros antigos ajudam a demonstrar '
            'o padrão da fraude e a identificar contas recebedoras.'),
        'Expectativa sincera: dano moral existe, dinheiro de volta nem sempre': (
            'A reparação moral pode ser discutida quando a manipulação afetiva '
            'e suas consequências são demonstradas, mas não nasce '
            'automaticamente de toda fraude. A recuperação patrimonial também '
            'depende de localizar responsáveis e bens; uma sentença sem '
            'patrimônio executável pode não produzir pagamento.\n\nA estratégia '
            'prudente prioriza bloqueio do saldo recente, identificação do '
            'operador e eventual responsabilização de participantes ou '
            'recebedores cuja conduta e base jurídica sejam provadas. O '
            'resultado pode ser parcial ou inexistente. Desconfie de '
            '“recuperadores de dinheiro” que cobram antecipado e prometem '
            'resgate certo das perdas.'),
    },
    'banc-instagram-invadido-venda-falsa': {
        'Estelionato e invasão de dispositivo: duas possíveis figuras penais': (
            'Vender produto inexistente mediante ardil pode configurar '
            'estelionato qualificado por fraude eletrônica, nos termos do art. '
            '171, § 2º-A, do Código Penal. A tomada do perfil pode também se '
            'enquadrar no art. 154-A, mas isso depende do modo de obtenção do '
            'acesso. Engenharia social, uso de credencial entregue ou sessão '
            'já autenticada exigem apuração e não autorizam afirmar invasão de '
            'dispositivo automaticamente.\n\nNa ocorrência, descreva os fatos '
            'sem escolher o tipo penal: como o dono perdeu acesso, quais '
            'alertas recebeu e quem negociou. A autoridade cruza registros da '
            'plataforma e dados bancários para definir autoria e enquadramento.'),
        'Registros de acesso podem ajudar a identificar o operador': (
            'A identificação de quem operava o perfil no momento da venda '
            'passa pelos registros de acesso guardados pela plataforma. O art. '
            '22 do Marco Civil autoriza requerer ao juiz o fornecimento desses '
            'registros para instruir processo cível ou penal, inclusive em '
            'medida anterior à ação principal.\n\nO cruzamento desses dados '
            'com a conta bancária cria linhas de investigação, não dois réus '
            'automáticos. Antes de cobrar o titular aparente, é preciso apurar '
            'participação, conduta, nexo e destino do valor, pois a conta pode '
            'pertencer a interposta pessoa sem ciência ou a outra vítima. O '
            'prazo aplicável também depende da causa de pedir e de quem será '
            'demandado.'),
    },
    'banc-golpe-aluguel-imovel-falso': {
        'O papel do banco que abriu a conta usada no golpe': (
            'Quando a conta recebedora foi aberta com documentos falsos ou '
            'fraude de identidade, a instituição pode responder por falha de '
            'verificação, à luz do art. 14 do Código de Defesa do Consumidor. '
            'Se a conta pertence a pessoa real, a discussão muda, mas o banco '
            'não fica automaticamente excluído: ainda é necessário examinar '
            'cadastro, autenticação, monitoramento e outras falhas próprias, '
            'além da conduta do titular.'),
        'Prazo para cobrar o reembolso e reunir provas': (
            'O prazo para buscar reparação não deve ser tratado como um número '
            'único para todos os envolvidos. Ele varia conforme o réu, a '
            'relação jurídica e a causa de pedir; a regra civil do art. 206, '
            '§ 3º, V, pode incidir em certas pretensões, enquanto relações de '
            'consumo e pedidos de outra natureza exigem enquadramento próprio.'
            '\n\nIsso não recomenda espera. Quanto antes a vítima comunicar o '
            'banco recebedor e registrar a ocorrência, maior a possibilidade '
            'de localizar saldo e preservar dados antes que desapareçam.'),
    },
    'cons-golpe-em-compra-de-usado-entre-pessoas': {
        'O vício oculto do item entregue: art. 441 do Código Civil': (
            'Se o item recebido tinha defeito oculto que o tornava impróprio '
            'para o uso ao qual se destina, ou que diminuía seu valor — por '
            'exemplo, um celular anunciado como funcional que já chegou com a '
            'bateria inutilizável e o vendedor sabia disso —, o art. 441 do '
            'Código Civil permite ao comprador enjeitar a coisa por vício '
            'redibitório, pedindo a rescisão do contrato ou, alternativamente, '
            'o abatimento no preço, conforme o art. 442.\n\nPara bens móveis, '
            'o art. 445 estabelece trinta dias a partir da entrega efetiva. Se '
            'o adquirente já mantinha o bem em sua posse quando ocorreu a '
            'alienação, o prazo é contado desse negócio e cai pela metade. '
            'Quando, pela natureza do vício, ele só puder ser conhecido mais '
            'tarde, o § 1º conta o prazo da ciência, observado o limite máximo '
            'de 180 dias para bem móvel. A data da descoberta precisa ser '
            'documentada.'),
        'Quando não é vício oculto, mas fraude deliberada': (
            'Saber do defeito e omiti-lo pode produzir consequências civis, '
            'mas não transforma automaticamente o vendedor em autor de '
            'estelionato. O crime do art. 171 do Código Penal exige intenção '
            'fraudulenta preexistente de obter vantagem ilícita mediante erro '
            'da vítima. Receber o preço já decidido a não entregar o produto, '
            'usar identidade falsa ou construir ardil para esconder o bem '
            'podem fornecer essa prova. O mero inadimplemento ou a controvérsia '
            'sobre defeito continuam sujeitos à apuração civil quando falta '
            'esse propósito inicial.'),
        'Caminho prático': (
            'Se o problema é vício oculto, notifique o vendedor por escrito '
            'dentro do prazo aplicável do art. 445, registrando também quando '
            'o defeito foi descoberto, e peça a resolução ou o abatimento. Se '
            'há indícios de fraude preexistente, o boletim de ocorrência e a '
            'pretensão civil podem seguir em paralelo.\n\nQuando o vendedor '
            'desaparece e o prazo decadencial corre, uma avaliação jurídica '
            'individual pode ajudar a escolher o pedido, identificar o réu e '
            'organizar os documentos, sem promessa de resultado.'),
    },
    'cons-site-falso-golpe-como-recuperar-dinheiro': {
        'Primeiro contato: o banco ou a operadora do cartão': (
            'Avise imediatamente a instituição usada no pagamento. No cartão, '
            'registre contestação e entregue anúncio, comprovante e prova de '
            'que o vendedor desapareceu; a análise da operadora pode resultar '
            'em estorno, mas o resultado não é automático. Se o pagamento foi '
            'Pix, peça ao banco a abertura do Mecanismo Especial de Devolução, '
            'o MED. O pedido pode ser apresentado em até oitenta dias da '
            'transação, mas agir sem demora aumenta a possibilidade de '
            'encontrar recursos.\n\nO Banco Central explica que as instituições '
            'analisam a fraude e podem bloquear valores localizados nas contas '
            'envolvidas no fluxo do dinheiro. O MED não garante restituição '
            'integral: o resultado depende da conclusão da análise e dos '
            'recursos encontrados, podendo haver devolução parcial. Use apenas '
            'o aplicativo ou o contato oficial do banco.'),
        'Quando a recuperação do valor é mais difícil': (
            'No Pix, a falta de recursos nas contas alcançadas pelo rastreamento '
            'pode impedir restituição total mesmo após o MED reconhecer a '
            'fraude. No cartão, a contestação segue análise própria e também '
            'não equivale a promessa de crédito. Se o autor não for identificado '
            'e nenhum terceiro tiver falhado em dever juridicamente demonstrável, '
            'a recuperação pode continuar inviável.\n\nA ação judicial precisa '
            'indicar conduta e nexo de cada réu. O banco não responde '
            'automaticamente por toda transferência autorizada, assim como a '
            'plataforma não responde apenas porque um link orgânico apareceu '
            'na busca. Na publicidade paga, o Tema 987 estabelece presunção '
            'relativa de culpa, ressalvada a prova de diligência da plataforma.'),
    },
}


EXTRA_OFFICIAL_SOURCES = {
    'cons-site-falso-golpe-como-recuperar-dinheiro': [{
        'url': 'https://www.bcb.gov.br/detalhenoticia/20817/nota',
        'name': 'Banco Central — aprimoramento do MED com rastreamento do Pix',
        'anchor_claim': (
            'registra o rastreamento de recursos para outras contas e sua '
            'adoção obrigatória no arranjo Pix em 2026'),
        'verified_at': '2026-07-11',
        'http_status': 200,
    }],
}


def _replace_final_source(page):
    replacement = dict(FINAL_SOURCE)
    replacement['anchor_claim'] = FINAL_ANCHOR_CLAIMS[page.get('intent_id')]
    sources = page.setdefault('official_sources', [])
    current_indexes = []
    legacy_indexes = []
    for index, source in enumerate(sources):
        url = (source.get('url') or '').strip().lower()
        if url == FINAL_SOURCE_URL.lower():
            current_indexes.append(index)
        elif 'tema=987' in url or 'numerotema=987' in url or (
                'noticias.stf.jus.br' in url and
                'responsabilizacao-de-plataformas' in url):
            legacy_indexes.append(index)
    if len(current_indexes) > 1 or len(legacy_indexes) > 1:
        raise ValueError(
            f"{page.get('intent_id')}: duplicate final STF source identity")
    if current_indexes and legacy_indexes:
        raise ValueError(
            f"{page.get('intent_id')}: current and legacy final STF sources coexist")
    if current_indexes:
        source = sources[current_indexes[0]]
        if not (source.get('name') or '').strip():
            raise ValueError(
                f"{page.get('intent_id')}: current final STF source name missing")
        if not (source.get('anchor_claim') or '').strip():
            raise ValueError(
                f"{page.get('intent_id')}: current final STF source anchor missing")
        # Preservar nome/âncora editorial mais específicos, mas nunca tratar a
        # URL sozinha como evidência live. A mesma URL foi verificada em
        # 2026-07-15 para o lote; campos ausentes recebem esse recibo comum e
        # campos presentes inválidos reprovam em vez de serem mascarados.
        verified_at = source.get('verified_at')
        if verified_at in (None, ''):
            source['verified_at'] = FINAL_SOURCE['verified_at']
        elif auditor.parse_source_verified_at(verified_at) is None:
            raise ValueError(
                f"{page.get('intent_id')}: current final STF source verified_at invalid")
        status = source.get('http_status')
        if status is None:
            source['http_status'] = FINAL_SOURCE['http_status']
        elif (not isinstance(status, int) or isinstance(status, bool) or
              status not in {200, 203, 206}):
            raise ValueError(
                f"{page.get('intent_id')}: current final STF source http_status invalid")
        return
    if legacy_indexes:
        sources[legacy_indexes[0]] = replacement
        return
    if len(sources) >= 5:
        raise ValueError(f"{page.get('intent_id')}: no slot for final STF source")
    sources.append(replacement)


def _ensure_extra_official_sources(page):
    sources = page.setdefault('official_sources', [])
    for desired in EXTRA_OFFICIAL_SOURCES.get(page.get('intent_id'), []):
        matching = [index for index, source in enumerate(sources)
                    if source.get('url') == desired['url']]
        if len(matching) > 1:
            raise ValueError(
                f"{page.get('intent_id')}: duplicate extra source {desired['url']}")
        if matching:
            sources[matching[0]] = dict(desired)
            continue
        if len(sources) >= 5:
            raise ValueError(
                f"{page.get('intent_id')}: no slot for {desired['url']}")
        sources.append(dict(desired))


def _updated_page(page):
    intent = page.get('intent_id')
    _, heading, text = UPDATES[intent]
    desired_heading = heading
    if intent in SECTION_HEADING_UPDATES:
        original_heading, desired_heading = SECTION_HEADING_UPDATES[intent]
        if heading != original_heading:
            raise ValueError(f'{intent}: heading mapping drift')
    matching = [section for section in page.get('sections', [])
                if section.get('heading') in (heading, desired_heading)]
    if len(matching) != 1:
        raise ValueError(f'{intent}: expected one section {heading!r}, got {len(matching)}')
    matching[0]['heading'] = desired_heading
    matching[0]['text'] = text + '\n\n' + MODULATION_PARAGRAPHS[intent]
    for field, value in TOP_LEVEL_UPDATES.get(intent, {}).items():
        page[field] = value
    for extra_heading, extra_text in EXTRA_SECTION_UPDATES.get(intent, {}).items():
        extra_matching = [section for section in page.get('sections', [])
                          if section.get('heading') == extra_heading]
        if len(extra_matching) != 1:
            raise ValueError(
                f'{intent}: expected one section {extra_heading!r}, '
                f'got {len(extra_matching)}')
        extra_matching[0]['text'] = extra_text
    for question, answer in FAQ_UPDATES.get(intent, {}).items():
        faq_matching = [item for item in page.get('faq', [])
                        if item.get('q') == question]
        if len(faq_matching) != 1:
            raise ValueError(
                f'{intent}: expected one FAQ {question!r}, got '
                f'{len(faq_matching)}')
        faq_matching[0]['a'] = answer
    _replace_final_source(page)
    _ensure_extra_official_sources(page)
    for url_part, anchor in SOURCE_ANCHOR_UPDATES.get(intent, {}).items():
        source_matching = [source for source in page.get('official_sources', [])
                           if url_part in (source.get('url') or '')]
        if len(source_matching) != 1:
            raise ValueError(
                f'{intent}: expected one source containing {url_part!r}, got '
                f'{len(source_matching)}')
        source_matching[0]['anchor_claim'] = anchor
    page['word_count'] = auditor.body_word_count(page)
    return page


def _render_file(path, expected_intents):
    with open(path, 'rb') as source:
        before = source.read()
    out = []
    seen = set()
    for line_number, raw in enumerate(before.decode('utf-8').splitlines(), 1):
        if not raw.strip():
            raise ValueError(f'{path}:{line_number}: blank JSONL line')
        page = json.loads(raw)
        intent = page.get('intent_id')
        if intent in expected_intents:
            original_page = page
            page = json.loads(raw)
            page = _updated_page(page)
            # Idempotência é semântica: não normalize espaços nem a ordem de
            # serialização de um registro que já contém o estado desejado.
            if page != original_page:
                compact = raw.startswith('{"') and '": ' not in raw[:128]
                separators = (',', ':') if compact else None
                raw = json.dumps(
                    page, ensure_ascii=False, separators=separators)
            seen.add(intent)
        out.append(raw)
    missing = expected_intents - seen
    if missing:
        raise ValueError(f'{path}: missing intents {sorted(missing)}')
    return before, ('\n'.join(out) + '\n').encode('utf-8')


def _atomic_replace_if_unchanged(path, before, after):
    if before == after:
        return False
    if open(path, 'rb').read() != before:
        raise RuntimeError(f'{path}: concurrent writer changed file; refusing replace')
    mode = stat.S_IMODE(os.stat(path, follow_symlinks=False).st_mode)
    directory = os.path.dirname(path)
    fd, temporary = tempfile.mkstemp(prefix='.tema987-repair-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as target:
            target.write(after)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(temporary, mode)
        if open(path, 'rb').read() != before:
            raise RuntimeError(f'{path}: concurrent writer changed file before commit')
        os.replace(temporary, path)
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write corrections; default is check-only')
    args = parser.parse_args(argv)
    by_file = {}
    missing_updates = ACTIVE_PAID_INTENTS - UPDATES.keys()
    if missing_updates:
        raise SystemExit(
            f'repair-v2-tema987-pages: missing active intents '
            f'{sorted(missing_updates)}')
    for intent in sorted(ACTIVE_PAID_INTENTS):
        relative, _, _ = UPDATES[intent]
        by_file.setdefault(relative, set()).add(intent)
    changed = 0
    canonical_root = ROOT
    try:
        # A mesma época EX cobre a primeira leitura usada pelo CAS, a segunda
        # leitura de confirmação e todo write/fsync/rename do lote.
        with canonical_stock_write_lease(canonical_root):
            for relative, intents in sorted(by_file.items()):
                path = os.path.join(ROOT, relative)
                before, after = _render_file(path, intents)
                if args.apply:
                    changed += int(_atomic_replace_if_unchanged(path, before, after))
                elif before != after:
                    raise SystemExit(
                        f'repair-v2-tema987-pages: stale {relative}; run --apply')
    except StockEpochBusy as error:
        print(
            f'repair-v2-tema987-pages: canonical stock busy: {error}',
            file=sys.stderr,
        )
        return 75
    print(f'repair-v2-tema987-pages: mode={"apply" if args.apply else "check"} scope=paid intents={len(ACTIVE_PAID_INTENTS)} files={len(by_file)} changed_files={changed} publication=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
