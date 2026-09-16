CREATE TABLE IF NOT EXISTS quote_requests (
  id VARCHAR(32) PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status VARCHAR(20) NOT NULL DEFAULT 'new'
    CHECK (status IN ('new', 'contacted', 'confirmed', 'completed', 'cancelled')),
  items JSONB NOT NULL,
  total INTEGER NOT NULL CHECK (total >= 0),
  customer_name VARCHAR(50) NOT NULL,
  phone VARCHAR(30) NOT NULL,
  email VARCHAR(254) NOT NULL,
  address VARCHAR(120) NOT NULL,
  preferred_date DATE NOT NULL,
  notes VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS quote_requests_created_at_idx
  ON quote_requests (created_at DESC);

CREATE INDEX IF NOT EXISTS quote_requests_status_idx
  ON quote_requests (status);
