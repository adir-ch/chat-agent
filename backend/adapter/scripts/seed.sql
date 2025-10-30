INSERT INTO user_info (agent_id, first_name, last_name, agency, area_json)
VALUES (
  'agent-123',
  'Jordan',
  'Lee',
  'Harbor Realty',
  '[{"name":"Bondi","postcode":"2026"},{"name":"Coogee","postcode":"2034"}]'
);

INSERT INTO property_listings (agent_id, address, suburb, postcode, status, sold_date)
VALUES
  ('agent-123', '12 Ocean Dr', 'Bondi', '2026', 'sold', '2024-05-14T00:00:00Z'),
  ('agent-123', '45 Cliff St', 'Coogee', '2034', 'active', NULL);

