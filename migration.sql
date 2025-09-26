ALTER TABLE Client RENAME TO client;
ALTER TABLE Person RENAME TO person;
ALTER TABLE Client_Organization RENAME TO organization;
ALTER TABLE Client_State RENAME TO state;
ALTER TABLE Lga RENAME TO lga;
ALTER TABLE Client_Occupation RENAME TO occupation;

ALTER TABLE state RENAME COLUMN state TO name;
ALTER TABLE lga RENAME COLUMN lga TO name;
ALTER TABLE occupation RENAME COLUMN occupation TO name;
