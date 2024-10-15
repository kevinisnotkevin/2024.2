CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '1';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE phones(
	id SERIAL PRIMARY KEY,
	phone VARCHAR(100) NOT NULL
);

CREATE TABLE emails(
	id SERIAL PRIMARY KEY,
	email VARCHAR(100) NOT NULL
);

INSERT INTO phones(phone)
VALUES ('89999999999'), ('87777777777');

INSERT INTO emails(email)
VALUES ('user1@test.com'), ('user2@test.com');
