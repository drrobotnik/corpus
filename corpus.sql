#
# Created: June 12, 2017 at 3:05:58 PM PDT
# Encoding: Unicode (UTF-8)
#


CREATE TABLE `dictionary` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `body` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  FULLTEXT KEY `body` (`body`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `dictionary_meta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dict_id` int(11) DEFAULT '0',
  `sound_file` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=utf8;

