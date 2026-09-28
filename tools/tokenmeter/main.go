// Command tokenmeter mede a razao BYTES POR TOKEN do corpus real deste portal.
//
// Por que existe. Dois lugares deste repositorio estimam contagem de token
// dividindo bytes por 4, e um deles alimenta um ledger de CUSTO:
// internal/openaireview.estimateInputTokens faz `len(json)/4` e o resultado vai
// para PrivacyCostLedgerRecord. O divisor 4 e a regra de bolso publicada para
// texto em INGLES. O corpus deste portal e portugues do Brasil, juridico,
// acentuado -- e acento custa mais de um byte em UTF-8 e frequentemente mais de
// um token. Estimar custo com o divisor de outro idioma e chute com aparencia
// de numero.
//
// Este programa mede a razao de verdade, com o tokenizador BPE oficial da
// familia GPT (github.com/tiktoken-go/tokenizer, MIT, v0.8.1), e grava
// evidencia reproduzivel.
//
// POR QUE VIVE NUM MODULO PROPRIO (tools/tokenmeter/go.mod) e nao no go.mod da
// raiz: a restricao e que o tokenizador NUNCA entre no caminho de resposta
// HTTP. Modulo isolado torna isso estrutural em vez de disciplinar -- o binario
// publico nao tem como importar o que nao esta no grafo dele. O consumidor da
// medicao e a CONSTANTE que ela produz, nao a biblioteca.
//
// `pkoukk/tiktoken-go` foi descartado: ele baixa o vocabulario em RUNTIME, o
// que significa chamada de rede dentro de uma ferramenta de medicao e
// resultado que muda conforme a rede. O tiktoken-go/tokenizer embute o
// vocabulario no binario.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/tiktoken-go/tokenizer"
)

type amostra struct {
	Rotulo                string  `json:"label"`
	Documentos            int     `json:"documents"`
	Bytes                 int     `json:"bytes"`
	Runas                 int     `json:"runes"`
	RunasNaoASCII         int     `json:"non_ascii_runes"`
	Tokens                int     `json:"tokens"`
	BytesPorToken         float64 `json:"bytes_per_token"`
	RunasPorToken         float64 `json:"runes_per_token"`
	ErroDaContagemPor4Pct float64 `json:"divisor_4_token_count_error_percent"`
}

type registro struct {
	EvidenceID           string    `json:"evidence_id"`
	RecordStatus         string    `json:"record_status"`
	Producer             string    `json:"producer"`
	ToolModulePath       string    `json:"tool_module_path"`
	ToolModuleVersion    string    `json:"tool_module_version"`
	ToolModuleLicense    string    `json:"tool_module_license"`
	ToolModFile          string    `json:"tool_mod_file"`
	Encoding             string    `json:"encoding"`
	EncodingRationale    string    `json:"encoding_rationale"`
	RuntimeNetworkUsed   bool      `json:"runtime_network_used"`
	InRequestPath        bool      `json:"in_http_request_path"`
	Samples              []amostra `json:"samples"`
	OverallBytesPerToken float64   `json:"overall_bytes_per_token"`
	RecommendedDivisor   float64   `json:"recommended_divisor"`
	LegacyDivisor        float64   `json:"legacy_divisor"`
	LegacyErrorPercent   float64   `json:"legacy_divisor_token_count_error_percent"`
	LegacyErrorMeaning   string    `json:"legacy_divisor_token_count_error_meaning"`
	ExecutedLive         bool      `json:"executed_live"`
	PublicationAllowed   bool      `json:"publication_allowed"`
	RenderAllowed        bool      `json:"render_allowed"`
	SitemapAllowed       bool      `json:"sitemap_allowed"`
	Approval             bool      `json:"approval"`
	PublicPath           string    `json:"public_path"`
	IndexPolicy          string    `json:"index_policy"`
	CheckedAt            string    `json:"checked_at"`
}

func main() {
	raiz := flag.String("root", "", "raiz do repositorio (padrao: dois niveis acima do binario)")
	evidencia := flag.String("evidence", "data/ops/token_ratio_evidence.jsonl", "caminho da evidencia")
	maxDocs := flag.Int("max-docs", 4000, "teto de documentos por amostra")
	dryRun := flag.Bool("dry-run", false, "mede e imprime sem gravar")
	flag.Parse()

	root := *raiz
	if root == "" {
		wd, err := os.Getwd()
		if err != nil {
			falhar(err)
		}
		root = subirAteRepo(wd)
	}

	// o200k_base e a codificacao da familia GPT-4o/GPT-5, que e a usada por
	// internal/openaireview (ModelCandidate = "gpt-5.5").
	codec, err := tokenizer.Get(tokenizer.O200kBase)
	if err != nil {
		falhar(fmt.Errorf("tokenizer.Get(o200k_base): %w", err))
	}

	amostras := []amostra{}
	if a, err := medirCorpoV2(root, codec, *maxDocs); err == nil {
		amostras = append(amostras, a)
	} else {
		fmt.Fprintf(os.Stderr, "aviso: corpo v2 nao medido: %v\n", err)
	}
	if a, err := medirMarkdownPublico(root, codec, *maxDocs); err == nil {
		amostras = append(amostras, a)
	} else {
		fmt.Fprintf(os.Stderr, "aviso: markdown publico nao medido: %v\n", err)
	}
	if len(amostras) == 0 {
		falhar(fmt.Errorf("nenhuma amostra do corpus foi medida"))
	}

	totalBytes, totalTokens := 0, 0
	for _, a := range amostras {
		totalBytes += a.Bytes
		totalTokens += a.Tokens
	}
	geral := float64(totalBytes) / float64(totalTokens)

	reg := registro{
		EvidenceID:        "token-ratio-" + time.Now().UTC().Format(time.RFC3339),
		RecordStatus:      "token_ratio_evidence_blocked_no_publication",
		Producer:          "tools/tokenmeter",
		ToolModulePath:    "github.com/tiktoken-go/tokenizer",
		ToolModuleVersion: "v0.8.1",
		ToolModuleLicense: "MIT",
		ToolModFile:       "tools/tokenmeter/go.mod",
		Encoding:          "o200k_base",
		EncodingRationale: "familia GPT-4o/GPT-5; internal/openaireview.ModelCandidate = gpt-5.5",
		// O vocabulario vem embutido no binario: nenhuma chamada de rede, ao
		// contrario de pkoukk/tiktoken-go, que por isso foi descartado.
		RuntimeNetworkUsed:   false,
		InRequestPath:        false,
		Samples:              amostras,
		OverallBytesPerToken: arredonda(geral),
		RecommendedDivisor:   arredonda(geral),
		LegacyDivisor:        4,
		// ATENCAO AO SINAL, e o erro que eu mesmo cometi na primeira leitura:
		// a razao medida (bytes/token) ser MAIOR que 4 significa que dividir
		// por 4 produz tokens A MAIS, nao a menos. O erro da CONTAGEM e
		// geral/4 - 1, e nao (4-geral)/geral. Num ledger de custo, inverter
		// esse sinal e a diferenca entre superfaturar e subfaturar.
		LegacyErrorPercent: arredonda((geral/4 - 1) * 100),
		LegacyErrorMeaning: "positivo = `len(json)/4` SUPERESTIMA a contagem de tokens nesta proporcao",
		ExecutedLive:       true,
		PublicationAllowed: false,
		RenderAllowed:      false,
		SitemapAllowed:     false,
		Approval:           false,
		PublicPath:         "",
		IndexPolicy:        "noindex",
		CheckedAt:          time.Now().UTC().Format(time.RFC3339),
	}

	for _, a := range amostras {
		fmt.Printf("%-22s docs=%-6d bytes=%-10d tokens=%-9d bytes/token=%.3f  contagem por /4 erra %+.1f%%\n",
			a.Rotulo, a.Documentos, a.Bytes, a.Tokens, a.BytesPorToken, a.ErroDaContagemPor4Pct)
	}
	fmt.Printf("GERAL bytes/token=%.4f -- `len(json)/4` %s a contagem de tokens em %.1f%%\n",
		geral, direcao(reg.LegacyErrorPercent), abs(reg.LegacyErrorPercent))

	if *dryRun {
		return
	}
	caminho := filepath.Join(root, *evidencia)
	if err := os.MkdirAll(filepath.Dir(caminho), 0o755); err != nil {
		falhar(err)
	}
	corpo, err := json.Marshal(reg)
	if err != nil {
		falhar(err)
	}
	arquivo, err := os.OpenFile(caminho, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		falhar(err)
	}
	defer func() { _ = arquivo.Close() }()
	if _, err := arquivo.Write(append(corpo, '\n')); err != nil {
		falhar(err)
	}
	fmt.Printf("evidencia: %s\n", *evidencia)
}

// medirCorpoV2 le o corpo autoral das paginas v2. O corpo NAO tem chave `text`:
// ele e a soma de opening + sections + faq (armadilha catalogada em
// docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md).
func medirCorpoV2(root string, codec tokenizer.Codec, maxDocs int) (amostra, error) {
	padrao := filepath.Join(root, "data", "editorial", "v2_pages", "*.jsonl")
	arquivos, err := filepath.Glob(padrao)
	if err != nil {
		return amostra{}, err
	}
	if len(arquivos) == 0 {
		return amostra{}, fmt.Errorf("nenhum shard em %s", padrao)
	}
	sort.Strings(arquivos)
	a := amostra{Rotulo: "corpo_autoral_v2"}
	for _, arquivo := range arquivos {
		if a.Documentos >= maxDocs {
			break
		}
		corpo, err := os.ReadFile(arquivo) // #nosec G304 -- caminho derivado da raiz do repo.
		if err != nil {
			continue
		}
		for _, linha := range strings.Split(string(corpo), "\n") {
			if a.Documentos >= maxDocs {
				break
			}
			linha = strings.TrimSpace(linha)
			if linha == "" {
				continue
			}
			var pagina map[string]any
			if err := json.Unmarshal([]byte(linha), &pagina); err != nil {
				continue
			}
			if pulado, _ := pagina["skipped"].(bool); pulado {
				continue
			}
			texto := textoDoCorpoV2(pagina)
			if strings.TrimSpace(texto) == "" {
				continue
			}
			acumular(&a, codec, texto)
		}
	}
	if a.Tokens == 0 {
		return amostra{}, fmt.Errorf("corpo v2 sem token medido")
	}
	finalizar(&a)
	return a, nil
}

func textoDoCorpoV2(pagina map[string]any) string {
	var b strings.Builder
	coletar(pagina["opening"], &b)
	coletar(pagina["sections"], &b)
	coletar(pagina["faq"], &b)
	return b.String()
}

func coletar(no any, b *strings.Builder) {
	switch valor := no.(type) {
	case string:
		b.WriteString(valor)
		b.WriteByte('\n')
	case []any:
		for _, item := range valor {
			coletar(item, b)
		}
	case map[string]any:
		chaves := make([]string, 0, len(valor))
		for chave := range valor {
			chaves = append(chaves, chave)
		}
		sort.Strings(chaves)
		for _, chave := range chaves {
			coletar(valor[chave], b)
		}
	}
}

// medirMarkdownPublico le a superficie de leitura barata que os agentes de IA
// consomem -- e o texto que efetivamente viaja para um modelo.
func medirMarkdownPublico(root string, codec tokenizer.Codec, maxDocs int) (amostra, error) {
	base := filepath.Join(root, "public")
	a := amostra{Rotulo: "markdown_publico"}
	err := filepath.WalkDir(base, func(caminho string, entrada os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return nil
		}
		if a.Documentos >= maxDocs {
			return filepath.SkipAll
		}
		if entrada.IsDir() || !strings.HasSuffix(entrada.Name(), ".md") {
			return nil
		}
		corpo, err := os.ReadFile(caminho) // #nosec G304 -- caminho derivado da raiz do repo.
		if err != nil {
			return nil
		}
		acumular(&a, codec, string(corpo))
		return nil
	})
	if err != nil {
		return amostra{}, err
	}
	if a.Tokens == 0 {
		return amostra{}, fmt.Errorf("nenhum markdown publico medido")
	}
	finalizar(&a)
	return a, nil
}

func acumular(a *amostra, codec tokenizer.Codec, texto string) {
	ids, _, err := codec.Encode(texto)
	if err != nil {
		return
	}
	a.Documentos++
	a.Bytes += len(texto)
	a.Tokens += len(ids)
	a.Runas += utf8.RuneCountInString(texto)
	for _, r := range texto {
		if r > unicode.MaxASCII {
			a.RunasNaoASCII++
		}
	}
}

func finalizar(a *amostra) {
	a.BytesPorToken = arredonda(float64(a.Bytes) / float64(a.Tokens))
	a.RunasPorToken = arredonda(float64(a.Runas) / float64(a.Tokens))
	a.ErroDaContagemPor4Pct = arredonda((a.BytesPorToken/4 - 1) * 100)
}

func subirAteRepo(dir string) string {
	atual := dir
	for i := 0; i < 8; i++ {
		if _, err := os.Stat(filepath.Join(atual, "go.mod")); err == nil {
			if corpo, err := os.ReadFile(filepath.Join(atual, "go.mod")); err == nil &&
				strings.HasPrefix(string(corpo), "module portaljuridico\n") {
				return atual
			}
		}
		pai := filepath.Dir(atual)
		if pai == atual {
			break
		}
		atual = pai
	}
	return dir
}

func arredonda(v float64) float64 {
	return float64(int64(v*10000+0.5)) / 10000
}

func abs(v float64) float64 {
	if v < 0 {
		return -v
	}
	return v
}

func direcao(erroPct float64) string {
	if erroPct > 0 {
		return "SUPERESTIMA"
	}
	return "SUBESTIMA"
}

func falhar(err error) {
	fmt.Fprintf(os.Stderr, "tokenmeter: %v\n", err)
	os.Exit(1)
}
