CREATE TABLE users (
    userId INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(320),
    passwordHash VARCHAR,
    firstName VARCHAR,
    lastName VARCHAR,
    subdomain VARCHAR,
    dateCreated datetime,
    dateUpdated datetime,
    totalSize INT,
    moneySpent FLOAT,
);
