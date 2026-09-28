package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"portaljuridico/internal/content"
	"portaljuridico/internal/ondemand"
	"portaljuridico/internal/render"
)

var slugRe = regexp.MustCompile(`[^a-z0-9-]+`)

func slugify(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	s = slugRe.ReplaceAllString(s, "-")
	s = strings.Trim(strings.ReplaceAll(s, "--", "-"), "-")
	return s
}

func main() {
	repo, err := content.LoadRepository("/opt/wiki")
	if err != nil {
		fmt.Println("load:", err)
		os.Exit(1)
	}
	raw, err := os.ReadFile("/opt/wiki/tools/_tmp_hubread/members.json")
	if err != nil {
		fmt.Println("members:", err)
		os.Exit(1)
	}
	var members map[string][][]string
	if err := json.Unmarshal(raw, &members); err != nil {
		fmt.Println("unmarshal:", err)
		os.Exit(1)
	}
	seen := map[string]bool{}
	for area, list := range members {
		for _, m := range list {
			slug := slugify(m[0])
			if slug == "" {
				continue
			}
			path := "/" + area + "/" + slug + "/"
			if seen[path] {
				continue
			}
			seen[path] = true
			repo.Pages = append(repo.Pages, content.Page{
				Path:         path,
				PageType:     "wiki",
				Status:       "published",
				IndexPolicy:  "index",
				Title:        m[1],
				Heading:      m[1],
				CanonicalURL: repo.BaseURL + path,
				ReviewedAt:   "2026-07-30",
			})
		}
	}
	set, err := ondemand.BuildAreaHubSet(repo)
	if err != nil {
		fmt.Println("hubset:", err)
		os.Exit(1)
	}
	out := "/opt/wiki/tools/_tmp_hubread/out"
	os.MkdirAll(out, 0o755)
	type row struct{ area, title, meta, heading, summary string; items, pages, bytes int }
	var rows []row
	titles, metas := map[string][]string{}, map[string][]string{}
	worstTitle, worstMeta := 0, 0
	for _, v := range set.Views {
		htmlStr, err := render.AreaHubPage(v)
		if err != nil {
			fmt.Println("render", v.Area, v.PageNumber, err)
			continue
		}
		key := fmt.Sprintf("%s-p%d", v.Area, v.PageNumber)
		titles[v.Title] = append(titles[v.Title], key)
		metas[v.MetaDescription] = append(metas[v.MetaDescription], key)
		if n := len([]rune(v.Title)); n > worstTitle {
			worstTitle = n
		}
		if n := len([]rune(v.MetaDescription)); n > worstMeta {
			worstMeta = n
		}
		if v.PageNumber != 1 {
			continue
		}
		os.WriteFile(filepath.Join(out, v.Area+".html"), []byte(htmlStr), 0o644)
		rows = append(rows, row{v.Area, v.Title, v.MetaDescription, v.Heading, v.Summary, v.TotalItems, v.TotalPages, len(htmlStr)})
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].items > rows[j].items })
	fmt.Printf("%-17s %5s %4s %7s %4s %4s  %s\n", "AREA", "ITENS", "PGS", "BYTES", "TIT", "MET", "TITLE")
	for _, r := range rows {
		fmt.Printf("%-17s %5d %4d %7d %4d %4d  %s\n", r.area, r.items, r.pages, r.bytes,
			len([]rune(r.title)), len([]rune(r.meta)), r.title)
	}
	dupT, dupM := 0, 0
	for _, k := range titles {
		if len(k) > 1 {
			dupT++
		}
	}
	for _, k := range metas {
		if len(k) > 1 {
			dupM++
		}
	}
	fmt.Printf("\nviews totais=%d | titles distintos=%d (colisoes=%d) | metas distintas=%d (colisoes=%d)\n",
		len(set.Views), len(titles), dupT, len(metas), dupM)
	fmt.Printf("maior title=%d runas | maior meta=%d runas\n", worstTitle, worstMeta)
}
