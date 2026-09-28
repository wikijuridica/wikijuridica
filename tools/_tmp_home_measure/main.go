// Comando de MEDIÇÃO da home (efêmero, fora do git por tools/_tmp_*).
// Renderiza a home pelo caminho de produção em três estados — cópia antiga (do
// HEAD), cópia nova sem hub viva e cópia nova com o catálogo inteiro — e
// imprime bytes, contagem de links e recortes do HTML.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"strings"

	"portaljuridico/internal/content"
	"portaljuridico/internal/render"
)

func homeFrom(path string) content.Page {
	raw, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}
	var pages []content.Page
	if err := json.Unmarshal(raw, &pages); err != nil {
		panic(err)
	}
	for _, page := range pages {
		if page.Path == "/" {
			return page
		}
	}
	panic("home ausente em " + path)
}

var hrefPattern = regexp.MustCompile(`href="(/[^"]*)"`)

func internalLinks(htmlText string) []string {
	found := []string{}
	for _, match := range hrefPattern.FindAllStringSubmatch(htmlText, -1) {
		found = append(found, match[1])
	}
	return found
}

func report(label string, htmlText string) {
	links := internalLinks(htmlText)
	css := ""
	if start := strings.Index(htmlText, "<style>"); start >= 0 {
		if end := strings.Index(htmlText, "</style>"); end > start {
			css = htmlText[start+7 : end]
		}
	}
	fmt.Printf("%-46s html=%6d bytes  css_inline=%5d bytes  links_internos=%3d\n", label, len(htmlText), len(css), len(links))
}

func main() {
	repo, err := content.LoadRepository(".")
	if err != nil {
		panic(err)
	}
	identity := repo.EditorialIdentity
	baseURL := repo.BaseURL

	novo := homeFrom("content/pages.json")
	antigo := homeFrom(os.Args[1])

	antigoHTML := render.HomePage(antigo, identity, baseURL, nil)
	novoVazio := render.HomePage(novo, identity, baseURL, nil)
	novoCheio := render.HomePage(novo, identity, baseURL, render.HomeAreaCatalogNav(0))

	// Estado de lançamento com contagem real: usa os volumes medidos no
	// portfolio só para dimensionar bytes — nenhum número entra em produção sem
	// vir do índice vivo.
	comContagem := render.HomePage(novo, identity, baseURL, render.HomeAreaCatalogNav(650))

	report("ANTES  (cópia do HEAD, sem hub viva)", antigoHTML)
	report("DEPOIS (cópia nova, sem hub viva=hoje)", novoVazio)
	report("DEPOIS (cópia nova + catálogo, sem contagem)", novoCheio)
	report("DEPOIS (cópia nova + catálogo + contagem)", comContagem)

	if len(os.Args) > 2 && os.Args[2] == "-dump" {
		os.Stdout.WriteString(comContagem)
	}
	if len(os.Args) > 2 && os.Args[2] == "-dumpold" {
		os.Stdout.WriteString(antigoHTML)
	}
	if len(os.Args) > 2 && os.Args[2] == "-dumplive" {
		os.Stdout.WriteString(novoVazio)
	}
}
