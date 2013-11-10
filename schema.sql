drop table if exists books;
create table books (
	id integer primary key autoincrement,
	title text not null,
	image text not null,
	content text not null
);

drop table if exists users;
create table users (
	id integer primary key autoincrement,
	name text not null,
	password text not null
);

drop table if exists comments;
create table comments (
	id integer primary key autoincrement,
	section integer not null,
	book integer not null,
	username integer not null,
	comment text not null
);

drop table if exists finished;
create table finished (
	id integer primary key autoincrement,
	userid integer not null,
	bookid integer not null
);

insert into users (name, password) VALUES ("cam", "test");
insert into users (name, password) VALUES ("arpit", "monkey");
insert into users (name, password) VALUES ("srikar", "tree");
