Title: 餐廳地圖
Date: 2026-04-18 00:00 +0800
Modified: 2026-08-04 00:00 +0800
Slug: restaurant-map
Summary: 記錄去過的餐廳

原本這些大概只會變成我寫在 Google Maps 裡的幾句短評
現在乾脆整理成一張自己的餐廳地圖

分數代表我有多喜歡、還想不想再去
口味本來就很主觀，所以這裡記錄的只是我個人的感受，不是什麼美食評鑑

旅途中一次性吃到的店沒有給分，只留紀錄

[TOC]

## 臺灣 / Taiwan

{% place_list restaurant/taiwan.yaml group_by="city,district" group_summary_at="city,district" %}
{% place restaurant/taiwan.yaml %}

## 日本 / Japan

{% place_list restaurant/japan.yaml group_by="city" group_summary_at="city" %}
{% place restaurant/japan.yaml %}
