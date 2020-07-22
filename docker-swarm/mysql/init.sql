--
-- Create the database and the user.
--
SET GLOBAL time_zone = 'Europe/Bucharest';

CREATE DATABASE IF NOT EXISTS mysql_database;

USE mysql_database;

CREATE USER 'mysql_user'@'%' IDENTIFIED BY 'mysql_resu_password';

GRANT ALL ON mysql_database.* TO 'mysql_user'@'%';

CREATE TABLE IF NOT EXISTS symbols (
  symbol varchar(15) NOT NULL UNIQUE,
  weight float(5, 2) NOT NULL,
  open_price float(10, 4) NOT NULL,
  buy_price float(10, 4) NOT NULL,
  variation varchar(15) NOT NULL,
  medium_price float(10, 4) NOT NULL,
  min_price float(10, 4) NOT NULL,
  max_price float(10, 4) NOT NULL,
  dividend_yield varchar(15) NOT NULL,
  volume bigint(15) NOT NULL,
  shares bigint(15) NOT NULL,
  company varchar(255) NOT NULL UNIQUE,
  free_float_factor float(10, 6) NOT NULL,
  representation_factor float(10, 6) NOT NULL,
  price_correction_factor float(10, 6) NOT NULL,
  PRIMARY KEY (symbol)
);
