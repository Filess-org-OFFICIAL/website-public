CREATE TABLE plan (
    ID INT NOT NULL PRIMARY KEY,
    planId INT NOT NULL,
    userId INT,
    storageSize BIGINT,
    tags INT,
    subdomains INT,
    dateCreated datetime,
    dateExpired datetime,
    spent VARCHAR,
);
