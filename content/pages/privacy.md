Title: 隱私權說明
Date: 2026-08-16 15:01 +0800
Modified: 2026-08-16 15:01 +0800
Slug: privacy
Summary: 本站會讓哪些第三方服務接觸到你的瀏覽資訊，以及聯絡方式。
Lang: zh-tw

本頁另有 [English](/pages/privacy-en.html) 與 [日本語](/ja/pages/privacy.html) 版本。三份內容相同；若有出入，以臺灣華語版為準。

### 我不做的事

本站沒有註冊、沒有電子報、沒有廣告，也沒有廣告追蹤。我不會主動蒐集、保存或販售你的個人資料，也沒有任何後台能讓我知道「某一位讀者是誰」。

不過，你造訪這個站的時候，仍然會有幾項第三方服務接觸到一些技術資訊。下面逐項說明。

### 流量統計

本站使用 [Umami Cloud](https://umami.is/) 統計瀏覽數。依 Umami 官方說明，其追蹤程式碼不使用 cookie，也不蒐集可識別個人身分的資訊，蒐集到的資料都會匿名化；詳情請見 [Umami 的隱私權政策](https://umami.is/privacy)。

我在後台看到的是彙總數字：哪幾篇文章被看了幾次、從哪個網站連過來、大略的國家與裝置類型。我看不到個別讀者，也無法把兩次瀏覽對應到同一個人。

需要說明的是，瀏覽器向 `cloud.umami.is` 發出請求這件事本身，技術上就會讓對方的伺服器看到你的 IP 位址與瀏覽器資訊。

### 留言

留言功能使用 [utterances](https://github.com/utterance/utterances)，它把留言存成本站 GitHub repository（`Lee-W/travlog`）的 issue 留言。因此：

* 留言需要 GitHub 帳號，並授權 utterances 代你發表
* 留言內容與你的 GitHub 帳號名稱是**公開的**，任何人都看得到，也會被搜尋引擎與各種爬蟲收錄
* 這些資料實際存放在 GitHub，適用 [GitHub 的隱私權聲明](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)
* 想刪除留言，你可以自己在 GitHub 上刪除，或寄信給我代為處理

### 會連到站外的內容

本站部分頁面會載入其他網站的資源：

* 地圖頁面（聖地巡禮、餐廳、影廳、旅遊地圖等）的圖磚來自 [OpenStreetMap](https://osmfoundation.org/wiki/Privacy_Policy)，地圖程式庫由 unpkg 提供
* 不少文章嵌入 Spotify 的樂曲播放器，少數文章嵌入 YouTube 影片
* 部落卷頁面的友站徽章，直接連到對方網站上的圖檔

這類請求都會讓對方的伺服器看到你的 IP 位址與瀏覽器資訊；影音平台的嵌入內容通常還會依其自身政策放置 cookie。若不希望如此，可以使用會阻擋外部連線的瀏覽器擴充套件——本站的文字內容在沒有這些資源的情況下仍然可讀。

### 主機與連線紀錄

本站託管於 Cloudflare Workers 的靜態資源服務，網頁由 Cloudflare 的節點傳送給你。Cloudflare 會在其服務運作所需的範圍內處理連線紀錄，適用 [Cloudflare 的隱私權政策](https://www.cloudflare.com/privacypolicy/)。這部分的紀錄我沒有存取權，也不會去調閱。

### Cookie 與瀏覽器儲存

本站不會放置自己的 cookie。唯一存在你瀏覽器裡的東西是深色／淺色模式的偏好設定（`localStorage` 中的 `attila_theme`），它只留在你的裝置上，不會傳送給我或任何第三方。

上述第三方服務可能會放置它們自己的 cookie，例如你在 GitHub 上登入以留言、或播放嵌入的影音內容的時候。

### 聯絡方式

對本頁內容、或對與你有關的資料有任何疑問與要求，請寄信至 [hello+travlog@wei-lee.me](mailto:hello+travlog@wei-lee.me?subject=%E9%9A%B1%E7%A7%81%E6%AC%8A%E8%AA%AA%E6%98%8E)。

本頁描述的是本站目前實際的做法；站上使用的服務有變動時，我會更新這一頁。本頁不是法律意見。
