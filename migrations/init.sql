-- Create emails table
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    category VARCHAR(50),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    message_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id);