# 地點資料回填 — 待補清單

> 產生於 2026-08-04，對應分支 `place-data-backfill`。
> 這份清單列的是**機器補不了、需要你決定或提供資訊**的部分。
> 已經查證完成並寫進 YAML 的不在這裡。
>
> 原則：座標與地址一律查證取得，查不到就留白。**這份清單上的項目寧可空著，也不要憑印象填**——
> 錯誤的座標日後不會有人再去驗證它。

## 目前完成度

| 資料集 | 已建檔 | 待補 |
|---|---|---|
| 演唱會／舞台場館 `content/places/venues.yaml` | 19 | 3 個場館 ＋ **39 筆紀錄根本沒留場館資訊** |
| 旅遊地點 `content/places/travel/*.yaml` | 38（日本 20／美國 15／臺灣 3） | 20 |
| 餐廳 `content/places/restaurant.yaml` | 17（既有 13 ＋ 新增 4） | 11 |
| 其他地點 `content/places/other.yaml` | 1（未變動） | 1 |
| 聖地巡禮 `content/places/pilgrimage/` | 56 個作品（未變動） | 見下方「順手發現」 |

---

## 一、最大的缺口：39 筆演出紀錄沒有場館資訊

`content/data/concerts.yaml` 與 `stage-performances.yaml` 裡有 39 筆紀錄**連 `venue` 欄位都沒有**，
也沒有可推斷的 href。這批只能靠你回想或翻票根，機器沒有任何線索可用。

其中兩個是系統性缺漏，補起來一次解決多筆：

- **大港開唱**（2023、2026 兩筆）
- **STAR WARS 電影交響音樂會**（2019-01-19 / 09-07 / 09-08 三筆，理論上同場館）

以下是逐筆清單，每筆都附「已經查過什麼」，你只需要補場館名：

### concerts.yaml（26 筆）

1. 2026-03-21 — 大港開唱 2026 — concerts.yaml:45 — 查過：無 venue 欄位、無 title href。年度音樂節但標題未寫場地名稱；與下方 #9（大港開唱 2023）同名系列，推斷方式相同，皆未查。
2. 2025-03-12 — 姜根新番組！GINGER ROOT LIVE IN TAIPEI 2025 — concerts.yaml:108-111 — 查過：title href `https://offtimemusic.kktix.cc/events/gingerroot2025`，僅為 kktix 售票頁 slug，不含場地文字。
3. 2024-10-25 — 2024藥師寺寬邦亞洲巡迴演唱會「悟」-Satori — concerts.yaml:163-165 — 查過：無 href、無其他線索。
4. 2023-12-23 — BANG!ACG 音樂祭 — concerts.yaml:300 — 查過：無 href、無其他線索。
5. 2023-11-18 — HIROMI ～SOLO～ — concerts.yaml:313 — 查過：無 href、無其他線索。
6. 2023-07-14 — Distant Worlds: music from FINAL FANTASY — concerts.yaml:345 — 查過：無 href、無其他線索。
7. 2023-06-21 — Real Collective Jazz Quartet 爵士精選四重奏 — concerts.yaml:350 — 查過：無 href、無其他線索。
8. 2023-04-01 — 大港開唱 2023 — concerts.yaml:361 — 同 #1，未查得場地。
9. 2023-03-18 — Aimer Arena Tour 2023 -nuit immersive- — concerts.yaml:366 — 查過：無 href；同系列 2024-2025 場次（福岡太陽宮／橫濱國際平和會議場）皆有 href，此筆缺漏、無法比對推斷。
10. 2022-10-10 — 天外奇蹟 | 電影交響音樂會 — concerts.yaml:387 — 查過：無 href、無其他線索。
11. 2020-09-27 — 2020森林市集 - 江松霖 — concerts.yaml:451 — 查過：無 href；「森林市集」疑為活動名而非場館名。
12. 2020-06-25 — WAU！Vol. 1 - 防疫新生活（廖文強 / 江松霖）— concerts.yaml:456 — 查過：無 href、無其他線索。
13. 2019-10-19 — LisAni！LIVE TAIWAN 2019 — concerts.yaml:466 — 查過：無 href、無其他線索。
14. 2019-09-08 — STAR WARS：The Force Awakens in Concert — concerts.yaml:471 — 查過：無 href、無其他線索；與下一筆（Return of the Jedi，9/7）日期相鄰，疑似同一活動系列連續兩場，但無直接文字證據可推斷場館，未臆測。
15. 2019-09-07 — STAR WARS：Return of the Jedi in Concert — concerts.yaml:476 — 同上。
16. 2019-04-13 — 江松霖【 時光曬衣場 】 春季小巡迴 — concerts.yaml:481 — 查過：無 href、無其他線索。
17. 2019-01-19 — Star Wars A New Hope - In Concert — concerts.yaml:486 — 查過：無 href、無其他線索。
18. 2018-04-29 — 江松霖「佳日提案＿晚春巡迴」— concerts.yaml:491 — 查過：無 href、無其他線索。
19. 2017-12-23 — 耶誕金曲音樂派對 — concerts.yaml:496 — 查過：無 href、無其他線索。
20. 2017-11-04 — 江松霖【 日 日 好 光 景 】 高雄場 — concerts.yaml:501 — 查過：title 含「高雄場」，僅能推斷城市為高雄，無法推斷具體場館名稱，未硬填。
21. 2017-10-06 — 「轉動高雄青春夢」— concerts.yaml:506 — 查過：title 含「高雄」，同上，僅有城市線索。
22. 2017-09-09 — 內地小搖滾（江松霖）— concerts.yaml:511 — 查過：無 href、無其他線索。
23. 2017-05-19 — 江松霖『 1 7 : 4 2 』 春季巡迴 — concerts.yaml:516 — 查過：無 href、無其他線索。
24. 2017-03-04 — 午後時光音樂會 — concerts.yaml:521 — 查過：無 href、無其他線索。
25. 2016-10-08 — 草悟野餐音樂節 — concerts.yaml:526 — 查過：title 含「草悟」（可能對應台中「草悟道」一帶地名），但無法確認具體場館正式名稱與座標，未使用訓練記憶臆測，故未列入候選清單。
26. 2016-08-27 — 南國音樂節 — concerts.yaml:531 — 查過：無 href、無其他線索，「南國」為泛稱非地名。

### stage-performances.yaml（13 筆）

1. 2025-09-14 — ミュージカル「Fate/Zero ~A Hero of Justice~」— stage-performances.yaml:14-17 — 查過：href `https://stage-fatezero.com/` 為官網首頁，不含場地文字線索。
2. 2025-08-16 — 我在詐騙公司上班 — stage-performances.yaml:21-24 — 查過：href `https://godot.org.tw/site/article/627`，網域本身可能與特定劇團站台相關，但未憑網域臆測劇場名稱；與下方 #11（2022-11-13 同名演出，無 href）疑似同齣戲重演，但無法確認是否為同一場館。
3. 2024-12-18 — 「進撃の巨人」-The Musical- — stage-performances.yaml:37-39 — 查過：href `https://www.shingeki-musical.com/` 為官網首頁，不含場地文字線索。
4. 2024-12-17 — 演劇【推しの子】2.5次元舞台編 — stage-performances.yaml:43-46 — 查過：href `https://www.marv.jp/special/theater_lalalai/blade/`，URL 路徑含 "theater_lalalai" 字樣可能與劇場名稱有關，但僅為 URL slug、無法確認正式場館名稱，未臆測。
5. 2024-12-08 — 《神明便利商店》音樂劇 — stage-performances.yaml:50-52 — 查過：href 為 opentix 售票頁（純數字活動 ID），不含場地文字線索。
6. 2024-08-07 — 2024百老匯經典音樂劇《芝加哥》— stage-performances.yaml:56 — 查過：無 href、無其他線索。
7. 2024-03-11 — KÀ by CIRQUE DU SOLEIL — stage-performances.yaml:90 — 查過：無 href、無其他線索。
8. 2024-02-28 — ジョジョの奇妙な冒険 — stage-performances.yaml:95 — 查過：無 href、無其他線索。
9. 2023-12-02 — 《吼呦～杰哥不要啦！！》— stage-performances.yaml:100 — 查過：無 href、無其他線索。
10. 2023-08-09 — 全本音樂劇《貓》CATS — stage-performances.yaml:111 — 查過：無 href、無其他線索。
11. 2022-11-13 — 我在詐騙公司上班 — stage-performances.yaml:116 — 查過：無 href；見上方 #2 同名演出。
12. 2021-04-23 — 2021TIFA 黃翊工作室 +《小螞蟻與機器人：遊牧咖啡館》— stage-performances.yaml:121 — 查過：title 含「TIFA」（台灣國際藝術節縮寫）。2024-04-12 那筆同為 TIFA 節目且明確寫出「國家兩廳院」，但此筆標題未寫，若比照推斷需要「TIFA＝兩廳院」這個訓練記憶前提，未使用，僅列為觀察供使用者參考。
13. 2019-05-25 — 悲慘世界 — stage-performances.yaml:133 — 查過：無 href、無其他線索。

---

## 二、查到候選但不敢採信／查無的地點

## 旅遊地點

### 查到候選但不敢採信（6 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| 京都塔 | 日本 | `05:149` | 名稱無實質重疊：name='京都塔' vs display_name='東京都市大学, 1, 玉堤一丁目, 玉堤, 世田谷區, 东京都/東京都, 158-8557, 日本' |
| 大須商店街 | 日本 | `05:211` | 名稱無實質重疊：name='大須商店街' vs display_name='キャニオンプラザ大須賀, 純情商店街, 高円寺北二丁目, 高円寺北, 高円寺, 杉並區, 东京都/東京都, 166 |
| 東京一番街 | 日本 | `06:71,91-93` | 名稱無實質重疊：name='東京一番街' vs display_name='千葉ニュータウンプラザプラザ西白井1番街 3号棟, 北千葉道路, けやき台一丁目, 白井市, 千葉縣, 270-1 |
| 東武百貨店池袋店 | 日本 | `06:28,53` | 名稱無實質重疊：name='東武百貨店池袋店' vs display_name='スターバックス, 25, 西池袋一丁目, 西池袋, 丰岛区 / 豐島區, 东京都/東京都, 171-8512 |
| 花間小路 | 日本 | `05:100,112` | 名稱無實質重疊：name='花間小路' vs display_name='花見小路, 祇園町南側, 辰巳町, 東山区, 京都市, 京都府, 605-0074, 日本' |
| 萌黃之館 | 日本 | `05:75` | country 不符：expected='日本' vs got='中国'；名稱無實質重疊：name='萌黃之館' vs display_name='长寿山地质地貌景观区, 石河镇, 山海关区 |

### Nominatim 查無（14 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| .andwork | 日本 | `06:73,98-102,111` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| Animate 池袋本店 | 日本 | `06:70,86-88` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| Bina's Creature Stall | 美國 | `01:354-357` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| Jewels of Bith | 美國 | `01:353` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| Mubo's Droid Depot | 美國 | `01:421-430` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| PARKサイクルライフ | 日本 | `08:73-90` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| animate 池袋總店 | 日本 | `07:111,124-139` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 下北澤一帶 | 日本 | `06:126,131-134` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 京王廣場飯店 八王子 | 日本 | `07:112,141-147` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 京阪電車宇治站 | 日本 | `05:147` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 山中湖 PICA山中湖 | 日本 | `10:37-40` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 池袋旅客案内所 | 日本 | `06:27` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 涉谷任天堂商店 | 日本 | `06:129` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 舊豐田佐助宅 | 日本 | `05:192,196-198` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |

### 不是地點（13 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| AnimeJapan 2023 | 日本 | `06:149,159-165,173-187` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| NO LIMIT! 遊行 | 日本 | `05:123` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| SING on Tour | 日本 | `05:122` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| SPY x FAMILY 機密任務 | 日本 | `05:119` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| ゆるキャン△BASE POP UP SHOP | 日本 | `06:127-128` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 咒術迴戰THE REAL 4D | 日本 | `05:118` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 哆啦A夢 XR乘車遊 | 日本 | `05:120` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 小小兵瘋狂乘車遊 | 日本 | `05:129` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 機動戦士ガンダム水星の魔女周遊活動 | 日本 | `06:72` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 水世界 | 日本 | `05:121` | 名稱無實質重疊：name='水世界' vs display_name='世界平和統一家庭連合 水都家庭教会, 8, 東中島歩道橋, 東中島一丁目, 東淀川區, 大阪市, 大阪府, 533-8 |
| 瑪利歐賽車～庫巴的挑戰書～ | 日本 | `05:127` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 耀西冒險 | 日本 | `05:128` | 名稱無實質重疊：name='耀西冒險' vs display_name='竹内薬店, 岩崎西目屋弘前線, 大字常盤坂二丁目, 常盤坂1, 常盤坂, 弘前市, 青森县, 036-8273, 日 |
| 飛天翼龍 | 日本 | `05:126` | country 不符：expected='日本' vs got='中国'；名稱無實質重疊：name='飛天翼龍' vs display_name='合肥市第五十中学天鹅湖校区, 仙龙湖路,  |

## 餐廳

### 查到候選但不敢採信（5 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| cafe&bar menu | 日本 | `06:29-32,49` | country 不符：expected='日本' vs got='德国;德國'；名稱無實質重疊：name='cafe&bar menu' vs display_name="Elo's Caf |
| やきとん大地 | 日本 | `06:74` | 名稱無實質重疊：name='やきとん大地' vs display_name='やきとん, 白山通り, 神田神保町一丁目, 神田神保町, 千代田區, 东京都/東京都, 101-0051, 日本 |
| 藤義 | 日本 | `07:72,98-104` | 第一輪已標可疑：文章脈絡在身延／鰍沢一帶，命中點在甲斐市，相距約 40 公里；第二輪 city 比對只到山梨縣層級才誤放行 |
| 靜岡炭烤漢堡排 さわやか | 日本 | `08:105-109` | 連鎖餐廳，比對地址發現非預期分店：候選為靜岡市葵區/駿河區/三島市分店，非文章脈絡的御殿場市分店；OSM 名稱查詢僅回傳 4 個分店且無御殿場，需人工確認正確分店或改查地址 |
| 食事処 味里 | 日本 | `10:60-63` | 名稱無實質重疊：name='食事処 味里' vs display_name='お食事処 松屋, 明石高砂線, 別府町本町二丁目, 別府町西町, 加古川市, 兵库县/兵庫縣, 675-0022 |

### Nominatim 查無（6 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| SMILE BASE CAFE 池袋店 | 日本 | `06:177-197` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 日南市じとっこ組合 御殿場駅前店 | 日本 | `08:101-103` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 晴天の月 大井町店 | 日本 | `06:157` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 炸牛排 あおな御徒町本店 | 日本 | `06:112,117-121` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 肉×日本酒 Fukuyaバル | 日本 | `07:33,39-42` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |
| 芬尼根酒吧&燒烤 | 日本 | `05:124` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |

## 場館

### 查到候選但不敢採信（2 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| 國家兩廳院 | 臺灣 | `venues-extract.md:53` | 名稱無實質重疊：name='國家兩廳院' vs display_name='自由廣場, 東門里, 中正區, 龍匣口, 臺北市, 10001, 臺灣' |
| 小地方 | 臺灣 | `venues-extract.md:52` | 命中 type=restaurant 的同名店家，無法確認即為江松霖演出的展演空間 |

### Nominatim 查無（1 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| Legacy mini @ amba | 臺灣 | `venues-extract.md:50` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |

## 其他地點

### Nominatim 查無（1 筆）

| 地點 | 國家 | 出處 | 卡在哪 |
|---|---|---|---|
| 冒險者公會 The A.G's Bar | 臺灣 | `other-extract.md:29-37` | 四種查詢字串（name+city+country / name+country / name_alt+country / name）皆無結果 |

---

## 三、順手發現，需要你確認

1. **`Nippongaishi Hall`（日本特殊陶業市民會館）可能是上面某筆缺 venue 的答案。**
   它是從 2023 Aimer Tour 的遊記抽出來的演出場館，座標已查得
   （`愛知県名古屋市南区豊田町堤町五丁目`），但我沒有自動接上 concerts.yaml 的任何一筆——
   要對上哪一場，得你確認。

2. **`花間小路` 可能是文章寫錯字。** Nominatim 回的是祇園的 **`花見小路`**（京都市東山区），
   位置與文章脈絡完全吻合。若確認是錯字，`2023/02-2023-aimer-tour-kansai-nagoya-itinerary.md`
   的內文也要一併修。

3. **`2023/02-2023-aimer-tour-kansai-nagoya-itinerary.md` Day 3 前後矛盾**：
   標題寫「→ 大阪」，內文寫「移動到京都後」，但北堀江（Live House 所在）在大阪。
   看起來是內文筆誤，我沒有擅自改。

4. **pilgrimage 疑似漏收**（在 2023 遊記出現，但不在對應的作品 YAML 裡）：
   - `三重縣廳舍`（明治村內，Fate/Zero）→ 不在 `pilgrimage/12-fate-series.yaml`
   - `身延山久遠寺`、`本栖高校`（搖曳露營）→ 不在 `pilgrimage/19-yuru-camp.yaml`
   前兩者的座標本次已查得，寫在 `travel/japan.yaml`；若要移進 pilgrimage 可直接搬。

5. **`content/places/theaters/taiwan.yaml` 第 592、609 行是 `city: 台南`**，
   全檔其餘用 `臺北`。想收斂成 `臺南` 的話這兩行要改。
   本次沒動，因為該檔當時有你未 commit 的修改。

---

## 四、被判定「不是地點」而不建檔的項目

USJ 的限定活動與遊行、快閃店、期間限定聯名——這些不是能導航過去、明年還在原地的實體場所，
OSM 也不會收錄。母場館（環球影城、東京國際展示場、マルイファミリー溝口）本身已查得座標。

若你認為這些仍該留下紀錄，比較合適的作法是寫進母場館那筆的 `notes`，而不是各自建成地點。

---

## 五、這份清單怎麼用

補完任一項後：

1. 把資料填進對應的 `content/places/*.yaml`
2. 跑 `uv run inv build`，確認 exit 0
3. 確認 `output/static/places/<檔名>.geojson` 的 feature 數有增加
4. 把該項從這份清單移除
