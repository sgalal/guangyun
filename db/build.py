#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import repeat
import os
import pandas
import sqlite3
import sys
import urllib

# Prepare files

def download_file_if_not_exist(name):
	url = 'https://raw.githubusercontent.com/sgalal/ytenx/kyonh/ytenx/sync/kyonh/' + name
	local_name = 'db/' + name
	try:
		if not os.path.exists(local_name):
			urllib.request.urlretrieve(url, local_name)
	except urllib.error.HTTPError as e:
		print(name, e)
		sys.exit(0)

download_file_if_not_exist('YonhMiuk.txt')
download_file_if_not_exist('SieuxYonh.txt')
download_file_if_not_exist('YonhMux.txt')
download_file_if_not_exist('Dzih.txt')
download_file_if_not_exist('YonhGheh.txt')
download_file_if_not_exist('PrengQim.txt')
download_file_if_not_exist('Dauh.txt')

if os.path.exists('docs/data.sqlite3'):
	os.remove('docs/data.sqlite3')

conn = sqlite3.connect('docs/data.sqlite3')
cur = conn.cursor()

## Emplace TEMP 廣韻小韻1

cur.execute('''
CREATE TEMP TABLE 廣韻小韻1
( '小韻號' INTEGER PRIMARY KEY
, '小韻' TEXT
, '母' TEXT NOT NULL
, '韻1' TEXT NOT NULL
, '韻' TEXT NOT NULL
, '反切' TEXT
);''')

data_small_rhyme_1 = pandas.read_csv('db/SieuxYonh.txt', sep=' ', header=None, usecols=[0, 1, 2, 3, 4, 5], names=['SmallRhymeId', 'SmallRhyme', 'Initial', 'Rhyme1', 'Rhyme', 'Fanqie'])
cur.executemany('INSERT INTO 廣韻小韻1 VALUES (?, ?, ?, ?, ?, ?)', zip(data_small_rhyme_1['SmallRhymeId'], data_small_rhyme_1['SmallRhyme'], data_small_rhyme_1['Initial'], data_small_rhyme_1['Rhyme1'], data_small_rhyme_1['Rhyme'], data_small_rhyme_1['Fanqie']))

## Emplace TEMP 廣韻小韻2

cur.execute('''
CREATE TEMP TABLE 廣韻小韻2
( 'id' INTEGER PRIMARY KEY
, '韻1' TEXT NOT NULL
, '等' INTEGER NOT NULL
, '開合' TEXT NOT NULL
);''')

data_small_rhyme_2 = pandas.read_csv('db/YonhMux.txt', sep=' ', na_filter=False, usecols=['#韻母', '等', '呼'])
cur.executemany('INSERT INTO 廣韻小韻2 VALUES (?, ?, ?, ?)', zip(repeat(None), data_small_rhyme_2['#韻母'], data_small_rhyme_2['等'], data_small_rhyme_2['呼']))

## Emplace 廣韻小韻3

cur.execute('''
CREATE TEMP TABLE 廣韻小韻3
( '小韻號' INTEGER PRIMARY KEY
, '古韻羅馬字' TEXT NOT NULL
, '有女羅馬字' TEXT
, '白一平轉寫' TEXT NOT NULL
, '推導中州音' TEXT NOT NULL
, '推導普通話' TEXT
);''')

data_extd_small_rhyme = pandas.read_csv('db/PrengQim.txt', sep=' ', keep_default_na=False, na_values=[''])  # https://stackoverflow.com/a/27173640
data_extd_small_rhyme2 = pandas.read_csv('db/Dauh.txt', sep=' ', na_filter=False, usecols=['推導中州音', '推導普通話'])
cur.executemany('INSERT INTO 廣韻小韻3 VALUES (?, ?, ?, ?, ?, ?)', zip(data_extd_small_rhyme['#序號'], data_extd_small_rhyme['古韻'], data_extd_small_rhyme['有女'], data_extd_small_rhyme['Baxter'], data_extd_small_rhyme2['推導中州音'], data_extd_small_rhyme2['推導普通話']))

## Emplace 廣韻小韻

cur.execute('''
CREATE TABLE 廣韻小韻
( '小韻號' INTEGER PRIMARY KEY
, '小韻' TEXT NOT NULL
, '韻' TEXT NOT NULL
, '母' TEXT NOT NULL
, '開合' TEXT NOT NULL
, '等' INTEGER NOT NULL
, '上字' TEXT
, '下字' TEXT
, '古韻羅馬字' TEXT NOT NULL
, '有女羅馬字' TEXT
, '白一平轉寫' TEXT NOT NULL
, '推導中州音' TEXT NOT NULL
, '推導普通話' TEXT
CHECK
(   LENGTH(小韻) = 1
AND LENGTH(母) = 1
AND 開合 IN ('開', '合')
AND 等 >= 1
AND 等 <= 4
AND LENGTH(上字) = 1
AND LENGTH(下字) = 1
)
);''')

cur.execute('''
INSERT INTO 廣韻小韻
SELECT 小韻號, 小韻, 韻, 母, 開合, 等,
substr(反切, 1, 1) AS 上字, substr(反切, 2) AS 下字,
古韻羅馬字, 有女羅馬字, 白一平轉寫, 推導中州音, 推導普通話
FROM 廣韻小韻1 INNER JOIN 廣韻小韻2
USING (韻1)
INNER JOIN 廣韻小韻3
USING (小韻號);''')

## Emplace 廣韻字頭

cur.execute('''
CREATE TABLE 廣韻字頭
( '小韻號' INTEGER NOT NULL REFERENCES '廣韻小韻'
, '小韻內字序' INTEGER NOT NULL
, '字頭' TEXT NOT NULL
, '解釋' TEXT NOT NULL
, PRIMARY KEY (小韻號, 小韻內字序)
);''')

data_char_entity = pandas.read_csv('db/Dzih.txt', sep=' ', na_filter=False, header=None, names=['Name', 'SmallRhymeId', 'NumInSmallRhyme', 'Explanation'])
cur.executemany('INSERT INTO 廣韻字頭 VALUES (?, ?, ?, ?)', zip(data_char_entity['SmallRhymeId'], data_char_entity['NumInSmallRhyme'], data_char_entity['Name'], data_char_entity['Explanation']))

# Extra

韻到韻賅上去 = pandas.read_csv('db/subgroup.csv', na_filter=False)
韻到韻賅上去SQL = '\n'.join("WHEN '" + x + "' THEN '" + y + "'" for x, y in zip(韻到韻賅上去['Rhyme'], 韻到韻賅上去['Subgroup']))

韻到韻賅上去入 = pandas.read_csv('db/YonhMiuk.txt', sep=' ', na_filter=False, usecols=['#韻目', '韻系'])
韻到韻賅上去入SQL = '\n'.join("WHEN '" + x + "' THEN '" + y + "'" for x, y in zip(韻到韻賅上去入['#韻目'], 韻到韻賅上去入['韻系']))

韻賅上去入到攝 = pandas.read_csv('db/YonhGheh.txt', sep=' ', na_filter=False)
韻賅上去入到攝SQL = '\n'.join("WHEN '" + x + "' THEN '" + y + "'" for x, y in zip(韻賅上去入到攝['#韻系'], 韻賅上去入到攝['攝']))

母到母號 = pandas.read_csv('db/initial.csv', dtype=str, na_filter=False)
母到母號SQL = '\n'.join("WHEN '" + x + "' THEN " + y for x, y in zip(母到母號['Initial'], 母到母號['InitialID']))

cur.execute(f'''
CREATE VIEW 廣韻小韻全 AS
SELECT 小韻號, 小韻,
小韻號 || 小韻 || '小韻' AS 小韻全名,
母 || 開合 || 等漢字 || 韻賅上去入 || 聲 AS 音韻地位,
韻,
CASE 韻 {韻到韻賅上去SQL} END AS 韻賅上去,
韻賅上去入,
CASE 韻賅上去入 {韻賅上去入到攝SQL} END AS 攝,
CASE 母 {母到母號SQL} END AS 母號,
母, 開合, 等, 等漢字, 聲, 上字, 下字,
古韻羅馬字, 有女羅馬字, 白一平轉寫, 推導中州音, 推導普通話
FROM (SELECT 小韻號, 小韻, 韻,
CASE 韻 {韻到韻賅上去入SQL} END AS 韻賅上去入,
母, 開合, 等,
CASE 等
WHEN 1 THEN '一'
WHEN 2 THEN '二'
WHEN 3 THEN '三'
ELSE '四'
END AS 等漢字,
CASE
WHEN 小韻號 <= 1156 THEN '平'
WHEN 小韻號 <= 2091 THEN '上'
WHEN 小韻號 <= 3182 THEN '去'
WHEN 小韻號 <= 3874 THEN '入'
END AS 聲,
上字, 下字,
古韻羅馬字, 有女羅馬字, 白一平轉寫, 推導中州音, 推導普通話
FROM 廣韻小韻);''')

cur.execute('''
CREATE VIEW 廣韻字頭全 AS
SELECT 字頭號, 字頭, 解釋, 小韻號, 小韻, 小韻全名, 音韻地位, 小韻內字序, 韻, 韻賅上去,
韻賅上去入, 攝, 母號, 母, 開合, 等, 等漢字, 聲, 上字, 下字,
古韻羅馬字, 有女羅馬字, 白一平轉寫, 推導中州音, 推導普通話
FROM (SELECT row_number() OVER (ORDER BY 小韻號, 小韻內字序) AS 字頭號,
小韻號, 小韻內字序, 字頭, 解釋
FROM 廣韻字頭)
INNER JOIN 廣韻小韻全
USING (小韻號);''')

cur.close()
conn.commit()
conn.execute('VACUUM')
conn.close()
