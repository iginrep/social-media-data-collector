db = db.getSiblingDB('bni_bions_sentiment');

// collections
[
  'collector_providers',
  'keywords',
  'schedules',
  'collection_runs',
  'collection_checkpoints',
  'social_items',
  'sentiment_jobs',
  'sentiment_results',
  'exports',
  'dashboard_views',
  'dashboard_actions',
  'system_events',
  'labeled_examples',
  'model_versions'
].forEach(function (name) {
  if (!db.getCollectionNames().includes(name)) db.createCollection(name);
});

// collector_providers
db.collector_providers.createIndex({ platform: 1, providerName: 1 }, { unique: true });
db.collector_providers.createIndex({ isEnabled: 1, riskLevel: 1 });
db.collector_providers.createIndex({ 'health.status': 1, 'health.lastCheckedAt': -1 });

// keywords
db.keywords.createIndex({ platform: 1, targetEntity: 1, isActive: 1 });
db.keywords.createIndex({ providerId: 1, isActive: 1, priority: -1 });
db.keywords.createIndex({ keyword: 1, platform: 1, sourceType: 1 }, { unique: true });
db.keywords.createIndex({ normalizedKeyword: 'text', targetEntity: 'text' });

// schedules
db.schedules.createIndex({ isActive: 1, timezone: 1 });
db.schedules.createIndex({ keywordIds: 1 });
db.schedules.createIndex({ providerIds: 1 });

// collection_runs
db.collection_runs.createIndex({ platform: 1, startedAt: -1 });
db.collection_runs.createIndex({ providerId: 1, startedAt: -1 });
db.collection_runs.createIndex({ keywordId: 1, startedAt: -1 });
db.collection_runs.createIndex({ status: 1, startedAt: -1 });
db.collection_runs.createIndex({ scheduleId: 1, startedAt: -1 });

// collection_checkpoints
db.collection_checkpoints.createIndex({ platform: 1, windowStart: 1, windowEnd: 1 }, { unique: true });
db.collection_checkpoints.createIndex({ platform: 1, status: 1, windowEnd: -1 });

// social_items
db.social_items.createIndex(
  { platform: 1, sourceType: 1, sourceId: 1 },
  { unique: true, partialFilterExpression: { sourceId: { $type: 'string' } } }
);
db.social_items.createIndex(
  { platform: 1, sourceType: 1, 'content.contentHash': 1, parentSourceId: 1 },
  { unique: true, partialFilterExpression: { 'content.contentHash': { $exists: true } } }
);
db.social_items.createIndex({ targetEntity: 1, postedAt: -1 });
db.social_items.createIndex({ platform: 1, postedAt: -1 });
db.social_items.createIndex({ sourceType: 1, postedAt: -1 });
db.social_items.createIndex({ keywordId: 1, collectedAt: -1 });
db.social_items.createIndex({ 'sentiment.label': 1, postedAt: -1 });
db.social_items.createIndex({ 'sentiment.topics': 1, postedAt: -1 });
db.social_items.createIndex({ 'processing.analysisStatus': 1, collectedAt: 1 });
db.social_items.createIndex({ 'metrics.rating': 1, postedAt: -1 });
db.social_items.createIndex({ conversationId: 1, postedAt: 1 });
db.social_items.createIndex(
  { 'content.text': 'text', 'content.cleanedText': 'text' },
  { default_language: 'none', language_override: 'none' }
);

// sentiment_jobs / results
db.sentiment_jobs.createIndex({ status: 1, startedAt: -1 });
db.sentiment_jobs.createIndex({ method: 1, modelVersion: 1, startedAt: -1 });
db.sentiment_results.createIndex({ socialItemId: 1, createdAt: -1 });
db.sentiment_results.createIndex({ label: 1, createdAt: -1 });
db.sentiment_results.createIndex({ method: 1, modelVersion: 1, createdAt: -1 });
db.sentiment_results.createIndex({ topics: 1, createdAt: -1 });

// exports
db.exports.createIndex({ createdAt: -1 });
db.exports.createIndex({ status: 1, createdAt: -1 });
db.exports.createIndex({ requestedBy: 1, createdAt: -1 });

// dashboard
db.dashboard_views.createIndex({ createdBy: 1, isDefault: -1 });
db.dashboard_views.createIndex({ name: 1 }, { unique: true });
db.dashboard_actions.createIndex({ socialItemId: 1, createdAt: -1 });
db.dashboard_actions.createIndex({ actionType: 1, createdAt: -1 });
db.dashboard_actions.createIndex({ userId: 1, createdAt: -1 });

// system events
db.system_events.createIndex({ level: 1, createdAt: -1 });
db.system_events.createIndex({ component: 1, createdAt: -1 });
db.system_events.createIndex({ providerId: 1, createdAt: -1 });

// optional labels/models
db.labeled_examples.createIndex({ socialItemId: 1, createdAt: -1 });
db.labeled_examples.createIndex({ label: 1, createdAt: -1 });
db.model_versions.createIndex({ method: 1, version: 1 }, { unique: true });
db.model_versions.createIndex({ isActive: 1, method: 1 });

// seed providers
const now = new Date();
[
  ['provider_google_play_reviews', 'google_play', 'google-play-scraper', 'GooglePlayAdapter', 'unofficial_api', 'free', 'medium', true, false, false, false],
  ['provider_app_store_reviews', 'app_store', 'itunes-rss-json', 'AppStoreAdapter', 'rss', 'free', 'low', true, false, false, false],
  ['provider_youtube_comments', 'youtube', 'youtube-data-api-v3', 'YouTubeAdapter', 'official_api', 'free', 'low', true, false, false, true],
  ['provider_google_news_rss', 'news', 'google-news-rss', 'GoogleNewsRssAdapter', 'rss', 'free', 'low', true, false, false, false],
  ['provider_bing_news_rss', 'news', 'bing-news-rss', 'BingNewsRssAdapter', 'rss', 'free', 'low', true, false, false, false],
  ['provider_stockbit_playwright', 'stockbit', 'playwright', 'StockbitPlaywrightAdapter', 'automation', 'free', 'high', false, true, true, false],
  ['provider_x_twscrape', 'x', 'twscrape', 'XTwScrapeAdapter', 'unofficial_api', 'free', 'high', false, true, false, false],
  ['provider_instagram_instaloader', 'instagram', 'instaloader', 'InstagramInstaloaderAdapter', 'unofficial_api', 'free', 'high', false, true, false, false],
  ['provider_threads_api', 'threads', 'threads-api-official', 'ThreadsApiAdapter', 'official_api', 'free', 'medium', false, true, false, true],
  ['provider_tiktok_api', 'tiktok', 'TikTokApi', 'TikTokApiAdapter', 'unofficial_api', 'free', 'high', false, false, true, false]
].forEach(function (p) {
  db.collector_providers.updateOne(
    { _id: p[0] },
    { $setOnInsert: {
      _id: p[0], platform: p[1], providerName: p[2], adapterClass: p[3], sourceTypes: [],
      accessMode: p[4], costLevel: p[5], riskLevel: p[6], enabledByDefault: p[7], isEnabled: p[7],
      requiresAuth: p[8], requiresBrowser: p[9], requiresApiKey: p[10],
      rateLimit: { requestsPerMinute: 10, burst: 2, backoffSeconds: 60 },
      health: { status: 'unknown', lastCheckedAt: null, lastSuccessAt: null, lastError: null },
      createdAt: now, updatedAt: now
    } },
    { upsert: true }
  );
});

// seed keywords
[
  ['kw_bions_google_play', 'BIONS', 'bions', 'product', 'google_play', 'app_review', 'provider_google_play_reviews', {
    appId: 'id.bions.bnis.android',
    url: 'https://play.google.com/store/apps/details?id=id.bions.bnis.android&hl=id',
    country: 'id', language: 'id', sort: 'newest', saveUsername: true
  }],
  ['kw_bions_app_store', 'BIONS', 'bions', 'product', 'app_store', 'app_review', 'provider_app_store_reviews', {
    appId: '6736508566',
    url: 'https://apps.apple.com/id/app/bions/id6736508566',
    country: 'id', saveUsername: true
  }],
  ['kw_bni_youtube_channel', 'BNI', 'bni', 'brand', 'youtube', 'comment', 'provider_youtube_comments', {
    channelHandle: 'BNI1946', channelUrl: 'https://www.youtube.com/@BNI1946', saveUsername: true
  }],
  ['kw_bni_sekuritas_youtube_channel', 'BNI Sekuritas', 'bni_sekuritas', 'brand', 'youtube', 'comment', 'provider_youtube_comments', {
    channelHandle: 'bnisekuritas46', channelUrl: 'https://www.youtube.com/@bnisekuritas46', saveUsername: true
  }],
  ['kw_bni_news', 'BNI', 'bni', 'brand', 'news', 'news_article', 'provider_google_news_rss', { query: 'BNI OR "BNI Sekuritas" OR BIONS', country: 'id' }],
  ['kw_bions_youtube', 'BIONS', 'bions', 'product', 'youtube', 'comment', 'provider_youtube_comments', { query: 'BIONS BNI Sekuritas', saveUsername: true }],
  ['kw_bbni_stockbit', 'BBNI', 'bbni', 'ticker', 'stockbit', 'finance_forum', 'provider_stockbit_playwright', { symbol: 'BBNI' }]
].forEach(function (k) {
  db.keywords.updateOne(
    { _id: k[0] },
    { $setOnInsert: {
      _id: k[0], keyword: k[1], normalizedKeyword: k[2], targetEntity: k[2], entityType: k[3],
      platform: k[4], sourceType: k[5], providerId: k[6], queryConfig: k[7],
      isActive: true, priority: 100, createdAt: now, updatedAt: now
    } },
    { upsert: true }
  );
});
