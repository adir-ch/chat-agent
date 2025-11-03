INSERT INTO user_info (agent_id, first_name, last_name, agency, area_json)
VALUES 
  ('agent-123', 'Jordan', 'Lee', 'Harbor Realty', '[{"name":"Bondi","postcode":"2026"},{"name":"Coogee","postcode":"2034"}]'),
  ('agent-456', 'Sarah', 'Mitchell', 'Urban Properties', '[{"name":"Newtown","postcode":"2042"},{"name":"Marrickville","postcode":"2204"},{"name":"Enmore","postcode":"2042"}]'),
  ('agent-789', 'David', 'Chen', 'Premium Estates', '[{"name":"Mosman","postcode":"2088"},{"name":"Neutral Bay","postcode":"2089"}]'),
  ('agent-101', 'Emma', 'Williams', 'Coastal Living', '[{"name":"Manly","postcode":"2095"},{"name":"Freshwater","postcode":"2096"}]');

INSERT INTO property_listings (agent_id, address, suburb, postcode, status, sold_date)
VALUES
  -- Agent 123 listings
  ('agent-123', '12 Ocean Dr', 'Bondi', '2026', 'sold', '2024-05-14T00:00:00Z'),
  ('agent-123', '45 Cliff St', 'Coogee', '2034', 'active', NULL),
  ('agent-123', '88 Beach Rd', 'Bondi', '2026', 'sold', '2024-03-22T00:00:00Z'),
  ('agent-123', '23 Surf Ave', 'Coogee', '2034', 'withdrew', NULL),
  ('agent-123', '156 Campbell Pde', 'Bondi', '2026', 'active', NULL),
  
  -- Agent 456 listings (Inner West)
  ('agent-456', '45 King St', 'Newtown', '2042', 'sold', '2024-06-10T00:00:00Z'),
  ('agent-456', '128 Enmore Rd', 'Marrickville', '2204', 'active', NULL),
  ('agent-456', '67 Wilson St', 'Newtown', '2042', 'active', NULL),
  ('agent-456', '234 Illawarra Rd', 'Marrickville', '2204', 'sold', '2024-04-18T00:00:00Z'),
  ('agent-456', '89 Enmore St', 'Enmore', '2042', 'active', NULL),
  ('agent-456', '12 Addison Rd', 'Marrickville', '2204', 'withdrew', NULL),
  
  -- Agent 789 listings (North Shore)
  ('agent-789', '23 The Spit Rd', 'Mosman', '2088', 'active', NULL),
  ('agent-789', '156 Military Rd', 'Neutral Bay', '2089', 'sold', '2024-07-05T00:00:00Z'),
  ('agent-789', '45 Bradleys Head Rd', 'Mosman', '2088', 'active', NULL),
  ('agent-789', '78 Wycombe Rd', 'Neutral Bay', '2089', 'sold', '2024-05-30T00:00:00Z'),
  ('agent-789', '12 Raglan St', 'Mosman', '2088', 'active', NULL),
  
  -- Agent 101 listings (Northern Beaches)
  ('agent-101', '34 The Corso', 'Manly', '2095', 'active', NULL),
  ('agent-101', '67 Manly Esplanade', 'Manly', '2095', 'sold', '2024-08-12T00:00:00Z'),
  ('agent-101', '89 Oliver St', 'Freshwater', '2096', 'active', NULL),
  ('agent-101', '123 Queen St', 'Freshwater', '2096', 'sold', '2024-06-25T00:00:00Z'),
  ('agent-101', '45 Pittwater Rd', 'Manly', '2095', 'active', NULL),
  ('agent-101', '12 Lawrence St', 'Freshwater', '2096', 'withdrew', NULL);

