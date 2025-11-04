package main

import (
	"chat-agent/backend/search/internal/search"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// InitElasticMockDB returns the mock elastic data as a slice of ElasticDataRecord
func InitElasticMockDB() []search.ElasticDataRecord {
	return []search.ElasticDataRecord{
		{
			ID: "person-001",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Michael",
					Last:  "Thompson",
				},
				Address: &search.PersonAddress{
					StreetNumber: "12",
					StreetName:   "Ocean Dr",
					Suburb:       "Bondi",
					State:        "NSW",
					PostCode:     "2026",
				},
				Mobile:       "+61 400 123 456",
				Email:        "michael.thompson@email.com",
				LastSeenDate: "2024-10-15T10:30:00Z",
			},
		},
		{
			ID: "person-002",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Lisa",
					Last:  "Chen",
				},
				Address: &search.PersonAddress{
					StreetNumber: "45",
					StreetName:   "Cliff St",
					Suburb:       "Coogee",
					State:        "NSW",
					PostCode:     "2034",
				},
				Mobile:       "+61 412 345 678",
				Email:        "lisa.chen@email.com",
				LastSeenDate: "2024-09-22T14:15:00Z",
			},
		},
		{
			ID: "person-003",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "David",
					Last:  "Brown",
				},
				Address: &search.PersonAddress{
					StreetNumber: "45",
					StreetName:   "King St",
					Suburb:       "Newtown",
					State:        "NSW",
					PostCode:     "2042",
				},
				Mobile:       "+61 423 456 789",
				LastSeenDate: "2024-11-01T09:00:00Z",
			},
		},
		{
			ID: "person-004",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Sarah",
					Last:  "Wilson",
				},
				Address: &search.PersonAddress{
					StreetNumber: "128",
					StreetName:   "Enmore Rd",
					Suburb:       "Marrickville",
					State:        "NSW",
					PostCode:     "2204",
				},
				Email:        "sarah.wilson@email.com",
				LastSeenDate: "2024-10-28T16:45:00Z",
			},
		},
		{
			ID: "person-005",
			Data: search.PersonData{
				Name: &search.PersonName{
					Last: "Martinez",
				},
				Address: &search.PersonAddress{
					StreetNumber: "67",
					StreetName:   "Wilson St",
					Suburb:       "Newtown",
					PostCode:     "2042",
				},
				Mobile:       "+61 434 567 890",
				LastSeenDate: "2024-09-10T11:20:00Z",
			},
		},
		{
			ID: "person-006",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "James",
					Last:  "Anderson",
				},
				Address: &search.PersonAddress{
					Suburb:   "Marrickville",
					State:    "NSW",
					PostCode: "2204",
				},
				Mobile:       "+61 445 678 901",
				Email:        "james.anderson@email.com",
				LastSeenDate: "2024-10-05T13:30:00Z",
			},
		},
		{
			ID: "person-007",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Emma",
					Last:  "Taylor",
				},
				Address: &search.PersonAddress{
					StreetNumber: "23",
					StreetName:   "The Spit Rd",
					Suburb:       "Mosman",
					State:        "NSW",
					PostCode:     "2088",
				},
				Mobile:       "+61 456 789 012",
				Email:        "emma.taylor@email.com",
				LastSeenDate: "2024-10-20T08:15:00Z",
			},
		},
		{
			ID: "person-008",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Robert",
				},
				Address: &search.PersonAddress{
					StreetNumber: "156",
					StreetName:   "Military Rd",
					Suburb:       "Neutral Bay",
					State:        "NSW",
					PostCode:     "2089",
				},
				LastSeenDate: "2024-09-30T15:00:00Z",
			},
		},
		{
			ID: "person-009",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Olivia",
					Last:  "White",
				},
				Address: &search.PersonAddress{
					StreetNumber: "34",
					StreetName:   "The Corso",
					Suburb:       "Manly",
					State:        "NSW",
					PostCode:     "2095",
				},
				Mobile:       "+61 467 890 123",
				Email:        "olivia.white@email.com",
				LastSeenDate: "2024-11-02T12:00:00Z",
			},
		},
		{
			ID: "person-010",
			Data: search.PersonData{
				Address: &search.PersonAddress{
					StreetNumber: "89",
					StreetName:   "Oliver St",
					Suburb:       "Freshwater",
					State:        "NSW",
					PostCode:     "2096",
				},
				Mobile: "+61 478 901 234",
			},
		},
		{
			ID: "person-011",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Daniel",
					Last:  "Harris",
				},
				Address: &search.PersonAddress{
					StreetNumber: "88",
					StreetName:   "Beach Rd",
					Suburb:       "Bondi",
					State:        "NSW",
					PostCode:     "2026",
				},
				Email:        "daniel.harris@email.com",
				LastSeenDate: "2024-10-12T10:00:00Z",
			},
		},
		{
			ID: "person-012",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Sophie",
					Last:  "Davis",
				},
				Address: &search.PersonAddress{
					StreetNumber: "234",
					StreetName:   "Illawarra Rd",
					Suburb:       "Marrickville",
					State:        "NSW",
					PostCode:     "2204",
				},
				Mobile:       "+61 489 012 345",
				Email:        "sophie.davis@email.com",
				LastSeenDate: "2024-10-25T14:30:00Z",
			},
		},
		{
			ID: "person-013",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Christopher",
				},
				Mobile:       "+61 490 123 456",
				LastSeenDate: "2024-09-15T09:45:00Z",
			},
		},
		{
			ID: "person-014",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Jessica",
					Last:  "Miller",
				},
				Address: &search.PersonAddress{
					StreetNumber: "67",
					StreetName:   "Manly Esplanade",
					Suburb:       "Manly",
					State:        "NSW",
					PostCode:     "2095",
				},
				Mobile:       "+61 401 234 567",
				Email:        "jessica.miller@email.com",
				LastSeenDate: "2024-10-30T11:20:00Z",
			},
		},
		{
			ID: "person-015",
			Data: search.PersonData{
				Address: &search.PersonAddress{
					StreetNumber: "123",
					StreetName:   "Queen St",
					Suburb:       "Freshwater",
					State:        "NSW",
					PostCode:     "2096",
				},
				Email: "contact@email.com",
			},
		},
		{
			ID: "person-016",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Andrew",
					Last:  "Garcia",
				},
				Address: &search.PersonAddress{
					StreetNumber: "45",
					StreetName:   "Bradleys Head Rd",
					Suburb:       "Mosman",
					State:        "NSW",
					PostCode:     "2088",
				},
				Mobile:       "+61 412 345 678",
				Email:        "andrew.garcia@email.com",
				LastSeenDate: "2024-10-18T16:00:00Z",
			},
		},
		{
			ID: "person-017",
			Data: search.PersonData{
				Name: &search.PersonName{
					Last: "Robinson",
				},
				Address: &search.PersonAddress{
					StreetNumber: "156",
					StreetName:   "Campbell Pde",
					Suburb:       "Bondi",
					PostCode:     "2026",
				},
				Mobile: "+61 423 456 789",
			},
		},
		{
			ID: "person-018",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Isabella",
					Last:  "Clark",
				},
				Address: &search.PersonAddress{
					StreetNumber: "12",
					StreetName:   "Addison Rd",
					Suburb:       "Marrickville",
					State:        "NSW",
					PostCode:     "2204",
				},
				Mobile:       "+61 434 567 890",
				Email:        "isabella.clark@email.com",
				LastSeenDate: "2024-10-08T13:15:00Z",
			},
		},
		{
			ID: "person-019",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Ryan",
				},
				Mobile: "+61 445 678 901",
				Email:  "ryan@email.com",
			},
		},
		{
			ID: "person-020",
			Data: search.PersonData{
				Name: &search.PersonName{
					First: "Mia",
					Last:  "Lewis",
				},
				Address: &search.PersonAddress{
					StreetNumber: "78",
					StreetName:   "Wycombe Rd",
					Suburb:       "Neutral Bay",
					State:        "NSW",
					PostCode:     "2089",
				},
				Mobile:       "+61 456 789 012",
				Email:        "mia.lewis@email.com",
				LastSeenDate: "2024-11-03T10:30:00Z",
			},
		},
	}
}

// LoadMockDB loads elastic-data.json into MockDB
func LoadMockDB() ([]search.ElasticDataRecord, error) {
	// Get the directory where the executable is located
	execPath, err := os.Executable()
	if err != nil {
		// Fallback to current working directory if we can't get executable path
		cwd, _ := os.Getwd()
		execPath = cwd
	}
	execDir := filepath.Dir(execPath)

	// Try multiple possible paths
	paths := []string{
		// Same directory as executable (for compiled binary)
		filepath.Join(execDir, "elastic-data.json"),
		// Relative to executable directory (cmd/search/)
		filepath.Join(execDir, "cmd", "search", "elastic-data.json"),
		// Current working directory
		"elastic-data.json",
		filepath.Join(".", "elastic-data.json"),
		// Relative to working directory
		filepath.Join("cmd", "search", "elastic-data.json"),
		filepath.Join("backend", "search", "cmd", "search", "elastic-data.json"),
	}

	// Add paths relative to current working directory
	if cwd, err := os.Getwd(); err == nil {
		paths = append(paths,
			filepath.Join(cwd, "elastic-data.json"),
			filepath.Join(cwd, "cmd", "search", "elastic-data.json"),
			filepath.Join(cwd, "backend", "search", "cmd", "search", "elastic-data.json"),
		)
	}

	var data []search.ElasticDataRecord
	var lastErr error

	for _, path := range paths {
		file, err := os.Open(path)
		if err != nil {
			lastErr = err
			continue
		}

		decoder := json.NewDecoder(file)
		if err := decoder.Decode(&data); err == nil {
			file.Close()
			return data, nil
		}
		file.Close()
		lastErr = err
	}

	return data, fmt.Errorf("failed to load elastic-data.json from any of the attempted paths: %w", lastErr)
}
