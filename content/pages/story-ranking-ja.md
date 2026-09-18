Title: 作品ランキング
Date: 2022-02-06 18:48 +0800
Modified: 2026-09-18 18:10 +0800
Slug: story-ranking
Summary: 好みの順に並べた、観た・読んだアニメ、映画、ドラマ、漫画、小説のランキングと感想の索引。
Lang: ja

[kazeの日本留学＆ACG](https://aurakaze.blog/list_anime/)と、Twitter で見かけた [TierMaker](https://tiermaker.com/create/anime-tier-list-300-anime-17194) に触発されて、自分用の作品ランキング／索引を作りました

どれくらい好きかで作品を Tier に分けています
同じ Tier のなかでの並び順に意味はありません
シーズンをまたいでも好みが大きく変わらなければ同じ Tier に置くので、各シーズンを必ず個別に並べているわけではありません

日本のアニメ以外は、まとめて実写映画・実写ドラマとして扱っています
スター・ウォーズは信仰込みで他と比べようがないので、独立させました

これはあくまで**私がどれくらい好きか**の記録で、作品そのものの品質や出来とは関係ありません
名作・良作とされている作品でも、私に合わなければ後ろのほうに置いてあります
私の神作があなたに刺さるとは限りませんし、私が退屈だと思った作品があなたの神作かもしれません（単に私が読み取れていないだけかも……）

このリストに入っていない良い作品を見つけたら、ぜひ布教してください 😆

ブログの更新が観る速度に追いつかないので、いくつかのサービスでも記録しています
よければこちらもどうぞ

* 日本のアニメ・漫画: [AniList](https://anilist.co/user/clleew/)
* そのほかの映画: [letterboxd](https://letterboxd.com/clleew/)
* そのほかのドラマ: [trakt](https://trakt.tv/users/clleew)

作品名は原題を優先していますが、原題が分からないものは台湾華語の表記のままです。
感想のリンク先は台湾華語の記事です。

**Tier 対応表**

| Tier | 私にとっての位置づけ | AniList | Letterboxd / Trakt |
|---|---|---|---|
| SSS | 揺るがない、これ以外にない | 10 | 5.0 |
| SS | 神作 | 9 | 4.5 |
| S | 良作以上、神作未満 | 8 | 4.0 |
| A | かなり好きな良作 | 7 | 3.5 |
| B | わりとおもしろかった | 6 | 3.0 |
| C | ふつう、または長所と短所が相殺 | 5 | 2.5 |
| D | 好きではない | 4 | 2.0 |
| E | 観ていて少しつらい | 3 | 1.5 |
| F | 観ていて本当につらい | 2 | 1.0 |
| G | 観なくてもいいけれど、友達には絶対すすめたい | 1 | 0.5 |

[TOC]

## アニメ
{% table data/story-ranking/anime.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## 実写映画（日本のアニメ以外を含む）
{% table data/story-ranking/live-action-movie.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## 実写ドラマ（日本のアニメ以外を含む）
{% table data/story-ranking/live-action-tv.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## ドキュメンタリー
{% table data/story-ranking/documentary.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## スター・ウォーズ
{% table data/story-ranking/star-wars.yaml fields="title,reviews" group_by="group" group_summary_at="group" field_labels="title:作品,reviews:感想" %}

## 完結した漫画
{% table data/story-ranking/manga-completed.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## 連載中の漫画
{% table data/story-ranking/manga-ongoing.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## 小説
{% table data/story-ranking/novel.yaml fields="title,reviews" group_by="tier" group_summary_at="tier" field_labels="title:作品,reviews:感想" %}

## 設定資料集
{% table data/story-ranking/artbook.yaml fields="title,reviews" field_labels="title:作品,reviews:感想" %}
