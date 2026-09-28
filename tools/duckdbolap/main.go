package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "github.com/duckdb/duckdb-go/v2"
)

const (
	modulePath          = "github.com/duckdb/duckdb-go/v2"
	moduleVersionPinned = "v2.10504.0"
	moduleLicense       = "MIT"
)

type metrics struct {
	ModulePath              string         `json:"module_path"`
	ModuleVersionPinned     string         `json:"module_version_pinned"`
	ModuleLicense           string         `json:"module_license"`
	ParquetPath             string         `json:"parquet_path"`
	RowCount                int            `json:"row_count"`
	UniqueIntentCount       int            `json:"unique_intent_count"`
	PracticeAreaCount       int            `json:"practice_area_count"`
	PublicFlagOpenRows      int            `json:"public_flag_open_rows"`
	MaxVisibleTextBytes     int            `json:"max_visible_text_bytes"`
	AverageVisibleTextBytes float64        `json:"average_visible_text_bytes"`
	OfficialSourceURLTotal  int            `json:"official_source_url_total"`
	TopPracticeAreas        map[string]int `json:"top_practice_areas"`
	QueryDurationMillis     int64          `json:"query_duration_millis"`
}

func main() {
	root := flag.String("root", ".", "project root")
	parquetPath := flag.String("parquet", "", "content inventory parquet path")
	flag.Parse()

	if strings.TrimSpace(*parquetPath) == "" {
		*parquetPath = filepath.Join(*root, "data", "ops", "content_inventory.parquet")
	}
	record, err := run(context.Background(), *parquetPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "duckdb-content-inventory: "+err.Error())
		os.Exit(1)
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(record); err != nil {
		fmt.Fprintln(os.Stderr, "duckdb-content-inventory: "+err.Error())
		os.Exit(1)
	}
}

func run(ctx context.Context, parquetPath string) (metrics, error) {
	if _, err := os.Stat(parquetPath); err != nil {
		return metrics{}, err
	}
	db, err := sql.Open("duckdb", "")
	if err != nil {
		return metrics{}, err
	}
	defer db.Close()

	started := time.Now()
	from := "read_parquet(" + sqlStringLiteral(parquetPath) + ")"
	var record metrics
	record.ModulePath = modulePath
	record.ModuleVersionPinned = moduleVersionPinned
	record.ModuleLicense = moduleLicense
	record.ParquetPath = filepath.ToSlash(parquetPath)
	err = db.QueryRowContext(ctx, `
select
	count(*)::BIGINT as row_count,
	count(distinct unique_intent_id)::BIGINT as unique_intent_count,
	count(distinct practice_area)::BIGINT as practice_area_count,
	sum(case when public_flags_open then 1 else 0 end)::BIGINT as public_flag_open_rows,
	max(visible_text_bytes)::BIGINT as max_visible_text_bytes,
	avg(visible_text_bytes)::DOUBLE as average_visible_text_bytes,
	sum(official_source_url_count)::BIGINT as official_source_url_total
from `+from).Scan(
		&record.RowCount,
		&record.UniqueIntentCount,
		&record.PracticeAreaCount,
		&record.PublicFlagOpenRows,
		&record.MaxVisibleTextBytes,
		&record.AverageVisibleTextBytes,
		&record.OfficialSourceURLTotal,
	)
	if err != nil {
		return metrics{}, err
	}
	rows, err := db.QueryContext(ctx, `select practice_area, count(*)::BIGINT from `+from+` group by practice_area order by count(*) desc, practice_area asc limit 8`)
	if err != nil {
		return metrics{}, err
	}
	defer rows.Close()
	record.TopPracticeAreas = map[string]int{}
	for rows.Next() {
		var area string
		var count int
		if err := rows.Scan(&area, &count); err != nil {
			return metrics{}, err
		}
		record.TopPracticeAreas[area] = count
	}
	if err := rows.Err(); err != nil {
		return metrics{}, err
	}
	record.QueryDurationMillis = time.Since(started).Milliseconds()
	if record.QueryDurationMillis < 1 {
		record.QueryDurationMillis = 1
	}
	return record, nil
}

func sqlStringLiteral(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "''") + "'"
}
