Title: Day 1 前往山中湖
Subtitle: 聽說是這趟最辛苦的一天...
Date: 2025-01-26 18:23 +0800
Category: Travel
Tags: Japan, Biking, 富士山
Slug: 2024-mt-fugi-biking-day-1
Series: 富士山輕鬆（？）騎 - 0.27 袋米扛 58,647 樓
Cover: /images/post-images/2024-mt-fugi-biking/d1-before-room.jpg
Authors: Wei Lee

第一天只有 20 km 應該是還好吧
恩，這是確實 🤔
不還好的是上升 800 m 😱

<!--more-->

![d1-wanderer](/images/post-images/2024-mt-fugi-biking/d1-wanderer.jpg)

第一天從御殿場出發，前往山中湖
雖然距離不算太遠，但爬升對菜鳥來說是真的有點挑戰
大概騎半個小時到一個小時就會開始餓
難怪出發前需要備那麼多的糧食
真的是會用到...

中間在這個點停了一下
聽說是 2020 東京奧運自行車會經過的路徑

![d1-Olympic](/images/post-images/2024-mt-fugi-biking/d1-Olympic.jpg)

剩下停得比較久的點就只剩 [東口本宮 冨士浅間神社](https://maps.app.goo.gl/C7QAnsNbACuAcbKU9)
繞著富士山的路上會遇到很多神社，正好是收集朱印的好機會
印象中剛好下起了小雨，稍微躲了一下

![d1-stop](/images/post-images/2024-mt-fugi-biking/d1-stop.jpg)

再來就是撐完最後一段直到 check-in
我們住在 [山中湖 PICA山中湖](https://www.pica-resort.jp/en/yamanakako/index.html)，住起來蠻舒服的小木屋
空間很適合 team building ，推薦給大家

![d1-room](/images/post-images/2024-mt-fugi-biking/d1-room.jpg)

抵達的時候差不多是中午
稍作休息就騎車到附近找午餐吃
都來到山梨了，不吃ほうとう是不能被接受的吧 🙅‍♂️
最後吃了[小作 山中湖店](https://maps.app.goo.gl/YrrdZLzYDkKNGMF4A)
印象中味道不錯，也還蠻平價的

![d1-lunch](/images/post-images/2024-mt-fugi-biking/d1-lunch.jpg)

回程的路上，拍了一張山中湖畔

![d1-before-room](/images/post-images/2024-mt-fugi-biking/d1-before-room.jpg)

畢竟這趟騎行，還是需要工作的
就直接把小木屋當成我的 Day 1 辦公室
桌子有點低，還好有帶筆電支架

![d1-work](/images/post-images/2024-mt-fugi-biking/d1-work.jpg)

晚餐去吃了 [食事処 味里](https://maps.app.goo.gl/DrMaGk1UJyptVTjH7)
味道就已經沒什麼印象了

![d1-dinner](/images/post-images/2024-mt-fugi-biking/d1-dinner.jpg)

### GPX 紀錄

為了寫這篇文，找了如何把 GPX 連起來的工具
最後的選擇是 [wanderer](https://github.com/Flomp/wanderer)
原因是它足夠好，而且不用額外去處理 API token
雖然它有說在 production 環境要把把 `MEILI_MASTER_KEY` 換掉
但我只是本地端用的應該還好吧 🤔
之所以說「足夠好」，而不是很好
是因為它有個奇怪的 bug
它創建 list 後，把 trail 加進去會失敗
但要把 trail 關聯到一個 list 是沒問題的
姑且還算能用，我就繼續用下去了

另外，很棒的工具是 [gpx.studio](https://gpx.studio/)
透過它的官網可以產出像這樣的圖

![d1-gpx-studio](/images/post-images/2024-mt-fugi-biking/d1-gpx-studio.jpg)

但如果想自架的話，就需要去弄 [mapbox](https://www.mapbox.com/) 的 API token
覺得有點麻煩，後來就沒用了
也許之後有空再研究一下
