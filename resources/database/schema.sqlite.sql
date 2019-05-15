CREATE TABLE IF NOT EXISTS "version" (
	"db_version" INTEGER DEFAULT 1 UNIQUE,
	PRIMARY KEY(db_version)
);

CREATE TABLE IF NOT EXISTS "request_cache" (
	"request_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"url" TEXT UNIQUE,
	"results" TEXT,
	"current_page" INTEGER DEFAULT 1,
	"total_pages" INTEGER DEFAULT 1,
	"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE IF NOT EXISTS "search_history" (
	"search_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"search_type" TEXT DEFAULT "username",
	"query" TEXT,
	"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (search_type, query)
);

CREATE TABLE IF NOT EXISTS "install_history" (
	"install_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"addon_id" TEXT,
	"source" TEXT,
	"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (addon_id)
);

CREATE VIEW IF NOT EXISTS "cached_requests" AS 
	SELECT request_cache.*, (strftime('%s','now') -  strftime('%s',ts))  AS age 
	FROM request_cache
;

/* Begin Version 2 */;

CREATE TABLE IF NOT EXISTS "feed_subscriptions" (
	"feed_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"name",
	"url" TEXT,
	"enabled" INTEGER DEFAULT 1,
	"last_update" TIMESTAMP,
	UNIQUE (url)
);

INSERT INTO feed_subscriptions ("name", "url", "enabled") VALUES ('TV ADDONS Library', 'http://indigo.tvaddons.co/installer/tva_english.xml', '1');

/* Begin Version 3 */;

CREATE TABLE IF NOT EXISTS "failed_depends" ( 
	"fail_id" INTEGER PRIMARY KEY AUTOINCREMENT, 
	"addon_id" TEXT, "source" TEXT,
	"resolved" INTEGER DEFAULT 0,
	"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
	UNIQUE (addon_id)
);
