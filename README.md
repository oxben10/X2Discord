# X2Discord

simple Python script that fetches new tweets matching your chosen keywords and posts them to a Discord channel using a webhook.

---

## How to Use

1. **Clone the repo**
2. **Install the requirements**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your `config.json`**
   - Add your Twitter Bearer Token and Discord webhook(s).
   - See the example config below for how to add or remove searches.
4. **Run the bot**
   ```bash
   python script.py
   ```

---

## Notes

- The bot keeps track of tweets it already sent in `sent_tweets.txt`.
- Only tweets with images will show images in Discord. If a tweet has no image, nothing will show.
- The tweet text is used as the description. If the tweet is empty or short, the description will be too.

---

## Example `config.json`

Here's an example of how your `config.json` might look. You can add, edit, or remove searches as you like. Each search can have its own Discord webhook and filters.

```jsonc
{
  "twitter_bearer_token": "YOUR_OPTIONAL_BEARER_TOKEN_HERE_FOR_EASY_SETUP",
  "notifications_webhook_url": "YOUR_OPTIONAL_ERROR_NOTIFICATION_WEBHOOK_URL_HERE",
  "search_limit_per_keyword": 50,
  "global_filters": {
    "min_followers": 0,
    "only_verified": false,
    "blacklist_usernames": [],
    "whitelist_usernames": []
  },
  "keyword_channels": {
    // Example 1: Exact phrase and specific language filter (English only)
    "Artificial Intelligence lang:en": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_AI_PHRASE",
      "user_filters": {
        "min_followers": 500,
        "only_verified": true
      }
    },
    // Example 2: Search for multiple hashtags using OR logic
    "#tips OR #AI OR #Hacking": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_MULTIPLE_HASHTAGS"
    },
    // Example 3: Simple hashtag search
    "#TechNews": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_TECHNEWS_HASHTAG"
    },
    // Example 4: Multiple keywords with AND (space)
    "Machine Learning": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_ML"
    },
    // Example 5: Multi-keyword search with OR logic, and excludes Spanish tweets
    "Python development OR Django OR Flask -lang:es": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_PYTHON_DEV",
      "user_filters": {
        "whitelist_usernames": ["ThePSF", "RealPython"]
      }
    },
    // Example 6: Keywords with negative filters and specific language (French only)
    "LLMs -is:retweet lang:fr": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_LLMS"
    },
    // Example 7: Complex query with specific tweet types, user filters, and excludes German
    "MyBrand -is:retweet is:quote -lang:de": {
      "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL_FOR_BRAND_QUOTES",
      "user_filters": {
        "min_followers": 100
      }
    }
  }
}
```

- To add a new search, copy one of the examples and change the query and webhook.
- To remove a search, just delete its block from `keyword_channels`.
- You can use any valid Twitter API v2 search query as a key.

---

## License

MIT
