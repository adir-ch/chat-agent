package db

import (
	"database/sql"
	"log"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

func NewSQLite(path string) (*sql.DB, error) {
	// Ensure the directory exists
	dir := filepath.Dir(path)
	if dir != "." && dir != "" {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, err
		}
	}

	// Check if database file already exists
	_, err := os.Stat(path)
	dbExists := err == nil

	if dbExists {
		log.Printf("Opening existing database: %s", path)
	} else {
		log.Printf("Creating new database: %s", path)
	}

	// Open database (SQLite will create the file if it doesn't exist, but preserve existing data)
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	return db, nil
}
