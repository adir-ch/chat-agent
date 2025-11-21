package models

import "time"

type AgentProfile struct {
	AgentID  string   `json:"agent_id"`
	FirstName string  `json:"first_name"`
	LastName  string  `json:"last_name"`
	Agency    string  `json:"agency"`
	Areas     []Area  `json:"areas"`
	Listings  []Listing `json:"listings"`
}

type AgentListItem struct {
	AgentID   string `json:"agent_id"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Agency    string `json:"agency"`
	Areas     []Area `json:"areas"`
}

type Area struct {
	Name     string `json:"name"`
	Postcode string `json:"postcode"`
}

type Listing struct {
	Address   string     `json:"address"`
	Suburb    string     `json:"suburb"`
	Postcode  string     `json:"postcode"`
	Status    string     `json:"status"`
	UpdateDate *time.Time `json:"update_date,omitempty"`
}

type Conversation struct {
	ID        int64     `json:"id"`
	AgentID   string    `json:"agent_id"`
	Query     string    `json:"query"`
	Response  string    `json:"response"`
	CreatedAt time.Time `json:"created_at"`
}

