package db

import "database/sql"

const migration = `
CREATE TABLE IF NOT EXISTS user_info (
  agent_id TEXT PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  agency TEXT,
  area TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS property_listings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  address TEXT NOT NULL,
  suburb TEXT NOT NULL,
  postcode TEXT NOT NULL,
  status TEXT NOT NULL,
  update_date TEXT,
  FOREIGN KEY(agent_id) REFERENCES user_info(agent_id)
);

CREATE TABLE IF NOT EXISTS llm_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
`

func ApplyMigrations(db *sql.DB) error {
	_, err := db.Exec(migration)
	return err
}
