-- create database payments
-- 	with owner postgres;

create table users
(
	id bigserial not null
		constraint users_pk
			primary key,
	name varchar not null,
	country varchar,
	city varchar,
	date timestamp default now() not null
);

alter table users owner to postgres;

create unique index users_user_id_uindex
	on users (id);

create unique index users_user_name_uindex
	on users (name);

create table transactions
(
	id bigserial not null
		constraint transactions_pk
			primary key,
	amount double precision not null,
	currency varchar(6) not null,
	operation varchar not null,
	status varchar not null,
	user_id integer,
	date timestamp default now() not null
);

alter table transactions owner to postgres;

create unique index transactions_tx_id_uindex
	on transactions (id);

create table balance
(
	id bigserial not null
		constraint balance_pk
			primary key,
	date timestamp default now() not null,
	tx_id integer not null,
	balance real not null,
	reserved real not null,
	user_id integer not null,
	currency varchar(6),
	operation varchar not null
);

alter table balance owner to postgres;

create unique index balance_id_uindex
	on balance (id);
