Title: 更新「電影院座位個人喜好」！
Date: 2026-05-01 22:15 +0800
Category: Review
Tags: Article
Slug: update-my-theatre-preference-page
Cover: /images/post-images/2026/update-my-theatre-preference-page/after.png
Authors: Wei Lee

當初只是想要把我在各電影院喜歡坐的位置公開在網路上
我自己買票的時候就可以輕鬆查到
沒想到[電影院座位個人喜好]變成我部落格中流量最高的頁面了
97% 的流量都在這（它甚至還不是文章）

<!--more-->

雖然之前改過一次編排方式，但 markdown 的列表在資料量開始大就會很難管理

最近乾脆訂了 Claude Code，讓它幫我把這件一直拖著的事做完
透過製作 [pelican-osm] 這個外掛，一次解決所有問題

## 🔧 改了些什麼？

* 更新前： 以「影廳種類」作為最上層分類，下面才是地區
* 更新後： 以「國家 → 城市 → 影城」的結構，[pelican-osm] 支援多層折疊就是為了所設計的

下面兩張圖片很長，點開不要嚇到 xD

<!-- rumdl-disable -->
??? 更新前
    ![before](/images/post-images/2026/update-my-theatre-preference-page/before.png)

??? 更新後
    ![after](/images/post-images/2026/update-my-theatre-preference-page/after.png)
<!-- rumdl-enable -->

[電影院座位個人喜好]: {filename}/pages/theaters-preference.md
[pelican-osm]: https://pypi.org/project/pelican-osm/
