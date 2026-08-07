CREATE TABLE IF NOT EXISTS dim_country (

    country_id INTEGER PRIMARY KEY,

    country_name VARCHAR NOT NULL,

    iso3 VARCHAR,

    region VARCHAR,

    subregion VARCHAR

);

CREATE TABLE IF NOT EXISTS dim_council (

    council_id INTEGER PRIMARY KEY,

    council_name VARCHAR NOT NULL UNIQUE

);

CREATE TABLE IF NOT EXISTS dim_date (

    date_id INTEGER PRIMARY KEY,

    full_date DATE,

    year INTEGER,

    month INTEGER,

    quarter INTEGER

);

CREATE TABLE IF NOT EXISTS dim_resolution (

    resolution_id INTEGER PRIMARY KEY,

    resolution_number VARCHAR,

    title TEXT,

    resolution_link TEXT

);