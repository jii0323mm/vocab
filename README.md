# 單字本

記下不會的英文單字，自動補上音標、詞性、中文意思和例句，再照間隔複習。
純靜態網頁，可以裝到手機桌面，離線也能打開。

## 網址

https://jii0323mm.github.io/vocab/

## 加到手機桌面

- **iPhone**：一定要用 **Safari** 打開上面的網址（Chrome 不行），
  點下方分享鍵 → 往下滑選「加入主畫面」。
- **Android**：用 Chrome 打開，右上角選單 → 「安裝應用程式」。

裝好之後圖示長得跟一般 App 一樣，打開沒有網址列。

## 之後要改東西

在 GitHub 上直接編輯 `index.html`，commit 完一兩分鐘就更新了。
改完如果手機還是舊的，把 `sw.js` 裡的 `VERSION` 改成 `vocab-v2`，
舊快取就會被清掉。

## 資料存在哪

存在瀏覽器的 localStorage，**只在這支裝置上**，沒有雲端、沒有帳號。

- 換手機、清除瀏覽器資料 → 單字會不見
- 所以「更多」頁有匯出備份，記得偶爾按一下，存到 iCloud 雲碟或 Google Drive

## 資料來源

- 音標、詞性、英文釋義、例句：[Free Dictionary API](https://dictionaryapi.dev)
- 中文翻譯：[MyMemory](https://mymemory.translated.net)

兩個都免費、不用申請金鑰。翻得怪的時候點單字卡上的「編輯」自己改。
