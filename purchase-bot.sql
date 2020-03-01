-- DROP TABLE purchase;
-- DROP TABLE types;

create table types (
	id BIGSERIAL NOT NULL PRIMARY KEY,
	type_of_spending VARCHAR(100) NOT NULL
);

create table purchase (
    id BIGSERIAL NOT NULL PRIMARY KEY,
	purchase_amount NUMERIC(19, 2) NOT NULL,
	date_of_purchase DATE NOT NULL,
    purchase_description VARCHAR(100),
	purchase_id BIGINT REFERENCES types (id)
);

insert into types (type_of_spending) values ('grocery');
insert into types (type_of_spending) values ('entertainment');
insert into types (type_of_spending) values ('clothes');
insert into types (type_of_spending) values ('home');
insert into types (type_of_spending) values ('lunch');
insert into types (type_of_spending) values ('others');



-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('20.50', '2020-02-12',  'description check', 1);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('17.00', '2020-02-15', null, 2);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('30.80', '2020-02-17', null, 3);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('50.00', '2020-02-20',  'description check', 4);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('20.50', '2020-02-21',  'description check', 5);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('20.50', '2020-02-22',  'description check', 6);
-- insert into purchase (purchase_amount, date_of_purchase, purchase_description, purchase_id) values ('15.50', '2020-02-23',  'description check', 1);





