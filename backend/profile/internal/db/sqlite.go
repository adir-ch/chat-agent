package db

import (
	"database/sql"

	_ "github.com/mattn/go-sqlite3"
)

func NewSQLite(path string) (*sql.DB, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	return db, nil
}

