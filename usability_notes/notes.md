## Telex scraper
### Specs
Sitemap: 
- All articles: ✅
- Monthly: ❌
- Daily: ✅

URL:
- Main topic: ✅
- Day: ✅
- Month: ✅

Example: https://telex.hu/belfold/2026/05/20/gorog-zita-gyermekvedelem-krug-emilia

### Steps
1. Scrape all the relevant days for the URLs
2. Filter URLs to identify articles within the relevant main topic
3. Scrape the remaining URLs for the title, tags, text

## 444 scraper
### Specs
Sitemap: 
- All articles: ✅
- Monthly: ❌
- Daily: ❌

URL:
- Main topic: ❌
- Day: ✅
- Month: ✅

Example: https://444.hu/2026/05/22/negyedszer-is-kormanyt-alakithat-janez-jansa-szloveniaban

### Steps
1. Scrape the xml file for all the urls within the time frame (if it is possible to filter)
2. Scrape all the URLs in the relevant time frame: title, tags, text, topic
3. Filter the articles by topic

## HVG
### Specs
Sitemap: 
- All articles: ❌
- Monthly: ❌
- Daily: ❌
- Random devisions: ✅
    All the relevant URLs are in 2 files, each xml contains 10000 URLs so that is how they are divided
    The relevant sitemaps are:
    - https://24.hu/app/uploads/sitemap/24.hu_sitemap_1.xml (Feb + Beginning of March)
    - https://24.hu/app/uploads/sitemap/24.hu_sitemap_0.xml (March + April)

URL:
- Main topic: ✅
- Day: ✅
- Month: ✅

Example: https://444.hu/2026/05/22/negyedszer-is-kormanyt-alakithat-janez-jansa-szloveniaban

### Steps
1. Scrape the xml file for all the urls within the time frame (if it is possible to filter)
2. Scrape all the URLs in the relevant time frame: title, tags, text, topic
3. Filter the articles by topic


## Origo
### Specs
Sitemap: 
- All articles: ❌
- Monthly: ✅
- Daily: ❌

URL:
- Main topic: ✅
- Day: ❌
- Month: ✅

Example: https://www.origo.hu/kulpol/2026/03/szijjarto-peter-a-valasztas-tetje

### Steps
1. Scrape all the relevant months for the URLs
2. Filter URLs to identify articles within the relevant time frames
3. Filter the URLs to identify articles with relevant topics
3. Scrape the remaining URLs for the title, tags, text

## Magyar Nemzet
### Specs
Sitemap: 
- All articles: ❌
- Monthly: ✅
- Daily: ❌

URL:
- Main topic: ✅
- Day: ❌
- Month: ✅

Example: https://magyarnemzet.hu/gazdasag/2026/05/ukran-gabona-magyar-peter-hazugsaga-leplezodott-le

### Steps
1. Scrape all the relevant months for the URLs
2. Filter URLs to identify articles within the relevant time frames
3. Filter the URLs to identify articles with relevant topics
3. Scrape the remaining URLs for the title, tags, text

## Mandiner
### Specs
Sitemap: 
- All articles: ❌
- Monthly: ✅
- Daily: ❌

URL:
- Main topic: ✅
- Day: ❌
- Month: ✅

Example: https://mandiner.hu/sport/2026/03/gyokeres-lewandowski-torok-tuzijatek-olasz-vb-selejtezo

### Steps
1. Scrape all the relevant months for the URLs
2. Filter URLs to identify articles within the relevant time frames
3. Filter the URLs to identify articles with relevant topics
3. Scrape the remaining URLs for the title, tags, text

## General pipeline
1. Crawl possibly relevant URLs from all the outlets
2. Filter URLs to only include relevant topics (444.hu no effect)
3. Run scraper on all the remaining URLs to get title, tags, text body
