CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    features TEXT NOT NULL,
    predicted INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL
);

