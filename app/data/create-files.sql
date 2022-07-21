CREATE TABLE files (
    fileId INT NOT NULL PRIMARY KEY,
    userId INT,
    fileName VARCHAR,
    fileBytes INT,
    fileType VARCHAR,
    fileWidth INT,
    fileHeight INT,
    dateCreated datetime,
    dateUpdated datetime,
	tag VARCHAR
);
