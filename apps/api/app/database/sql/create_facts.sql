CREATE TABLE IF NOT EXISTS fact_votes (

    vote_id BIGINT PRIMARY KEY,

    country_id INTEGER,

    resolution_id INTEGER,

    date_id INTEGER,

    council_id INTEGER,

    vote_code VARCHAR,

    vote_label VARCHAR,

    vote_score INTEGER,

    token BIGINT

);