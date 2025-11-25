package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	"chat-agent/backend/profile/internal/models"
)

type Repository struct {
	DB            *sql.DB
	ListingsLimit int
}

func NewRepository(db *sql.DB, listingsLimit int) *Repository {
	return &Repository{
		DB:            db,
		ListingsLimit: listingsLimit,
	}
}

func (r *Repository) GetAgentProfile(ctx context.Context, agentID string) (*models.AgentProfile, error) {
	var profile models.AgentProfile
	profile.AgentID = agentID

	var areaJSON string
	err := r.DB.QueryRowContext(ctx,
		`SELECT first_name, last_name, agency, area FROM user_info WHERE agent_id = ?`, agentID).
		Scan(&profile.FirstName, &profile.LastName, &profile.Agency, &areaJSON)
	if err != nil {
		return nil, err
	}

	if areaJSON != "" {
		if err := json.Unmarshal([]byte(areaJSON), &profile.Areas); err != nil {
			return nil, err
		}
	}

	rows, err := r.DB.QueryContext(ctx,
		`SELECT address, suburb, postcode, status, update_date FROM property_listings WHERE agent_id = ? LIMIT ?`,
		agentID, r.ListingsLimit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var (
			listing       models.Listing
			updateDateRaw sql.NullString
		)

		if err := rows.Scan(&listing.Address, &listing.Suburb, &listing.Postcode, &listing.Status, &updateDateRaw); err != nil {
			return nil, err
		}
		if updateDateRaw.Valid {
			if parsed, err := time.Parse(time.RFC3339, updateDateRaw.String); err == nil {
				listing.UpdateDate = &parsed
			}
		}

		profile.Listings = append(profile.Listings, listing)
	}

	return &profile, rows.Err()
}

func (r *Repository) GetAllAgents(ctx context.Context) ([]*models.AgentListItem, error) {
	rows, err := r.DB.QueryContext(ctx,
		`SELECT agent_id, first_name, last_name, agency, area FROM user_info`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var agents []*models.AgentListItem
	for rows.Next() {
		var agent models.AgentListItem
		var areaJSON string

		if err := rows.Scan(&agent.AgentID, &agent.FirstName, &agent.LastName, &agent.Agency, &areaJSON); err != nil {
			return nil, err
		}

		if areaJSON != "" {
			if err := json.Unmarshal([]byte(areaJSON), &agent.Areas); err != nil {
				return nil, err
			}
		}

		agents = append(agents, &agent)
	}

	return agents, rows.Err()
}

func (r *Repository) SaveConversation(ctx context.Context, conv *models.Conversation) error {
	_, err := r.DB.ExecContext(ctx,
		`INSERT INTO llm_conversations (agent_id, query, response) VALUES (?, ?, ?)`,
		conv.AgentID, conv.Query, conv.Response,
	)
	return err
}
