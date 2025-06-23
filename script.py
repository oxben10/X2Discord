import tweepy
import json
import os
import requests
import logging
from datetime import datetime, timezone


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = 'config.json'
SENT_TWEETS_FILE = 'sent_tweets.txt' 
BEARER_TOKEN_ENV_VAR = 'TWITTER_BEARER_TOKEN'

def load_config():
    """Loads configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"Configuration file '{CONFIG_FILE}' not found. Please create it.")
        exit(1)
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        return config
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from '{CONFIG_FILE}'. Please check its syntax.")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading config: {e}")
        exit(1)

def load_sent_tweet_ids():
    """Loads previously sent tweet IDs from a file."""
    if not os.path.exists(SENT_TWEETS_FILE):
        return set()
    try:
        with open(SENT_TWEETS_FILE, 'r') as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logging.error(f"Error loading sent tweet IDs: {e}")
        return set()

def save_sent_tweet_id(tweet_id):
    """Saves a new tweet ID to the file."""
    try:
        with open(SENT_TWEETS_FILE, 'a') as f:
            f.write(f"{tweet_id}\n")
    except Exception as e:
        logging.error(f"Error saving tweet ID {tweet_id}: {e}")

def build_twitter_query(keywords, logic):
    """Builds the Twitter API v2 query string based on keywords and logic."""
    if not keywords:
        return ""

    formatted_keywords = []
    for k in keywords:
        # Use quotes for multi-word phrases or special characters to search as exact phrase
        if ' ' in k or any(char in k for char in ['#', '@', '$', ':', '(', ')', '[', ']', '{', '}', '"', '\'']):
            formatted_keywords.append(f'"{k}"')
        else:
            formatted_keywords.append(k)

    if logic == "AND":
        return " ".join(formatted_keywords)
    elif logic == "OR":
        return " OR ".join(formatted_keywords)
    else:
        logging.warning(f"Unknown logic '{logic}'. Defaulting to 'OR'.")
        return " OR ".join(formatted_keywords)

def send_to_discord(webhook_url, tweet_author_name, tweet_author_username, tweet_text, tweet_url,
                    retweet_count=None, like_count=None, media_urls=None, is_error_notification=False):
    """Sends content to a Discord webhook."""
    
    if is_error_notification:
        color = 16711680 # Red 
        title = "❌ Bot Error Notification ❌"
        description = tweet_text # In this case, tweet_text is the error message
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "footer": {
                "text": "Twitter-Discord Bot Error"
            },
            "timestamp": datetime.now().isoformat()
        }
    else:
        color = 5814783 # A Discord-like blue color
        # Add a link after the tweet text
        tweet_text = f"{tweet_text}\n\n🔗 [View on Twitter]({tweet_url})"
        embed = {
            "title": f"New Tweet from @{tweet_author_username}",
            "description": tweet_text,
            "url": tweet_url,
            "color": color,
            "author": {
                "name": tweet_author_name,
                "url": f"https://twitter.com/{tweet_author_username}"
            },
            "footer": {
                "text": f"Likes: {like_count if like_count is not None else 'N/A'} | Retweets: {retweet_count if retweet_count is not None else 'N/A'} | Twitter Bot"
            },
            "timestamp": datetime.now().isoformat()
        }

        if media_urls:
            
            embed["image"] = {"url": media_urls[0]}
            if len(media_urls) > 1:
              
                additional_media_text = "\n\n**Additional Media:**\n" + "\n".join(media_urls[1:])
                embed["description"] += additional_media_text
        
    payload = {
        "embeds": [embed]
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        if not is_error_notification:
            logging.info(f"Successfully sent tweet to Discord.")
        else:
            logging.info(f"Successfully sent error notification to Discord.")
    except requests.exceptions.HTTPError as errh:
        logging.error(f"Discord Webhook HTTP Error: {errh} - Response: {response.text}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Discord Webhook Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Discord Webhook Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Discord Webhook Request Error: {err}")

def send_error_notification(error_message, notifications_webhook_url):
    """Sends a critical error notification to a dedicated Discord webhook."""
    if notifications_webhook_url:
        logging.error(f"Sending error notification: {error_message}")
        send_to_discord(
            webhook_url=notifications_webhook_url,
            tweet_author_name="Twitter Bot", # Placeholder
            tweet_author_username="bot_error", # Placeholder
            tweet_text=error_message,
            tweet_url="", # Not relevant for error
            is_error_notification=True
        )
    else:
        logging.error(f"Error notification webhook not configured. Error: {error_message}")

# logggggggic

def main():
    config = load_config()
    sent_tweet_ids = load_sent_tweet_ids()
    notifications_webhook_url = config.get("notifications_webhook_url")
    twitter_bearer_token = os.getenv(BEARER_TOKEN_ENV_VAR) or config.get("twitter_bearer_token")
    if not twitter_bearer_token:
        error_msg = f"Twitter Bearer Token not found. Please set the '{BEARER_TOKEN_ENV_VAR}' environment variable."
        logging.error(error_msg)
        send_error_notification(error_msg, notifications_webhook_url)
        exit(1)
    try:
        client = tweepy.Client(twitter_bearer_token)
    except Exception as e:
        error_msg = f"Error initializing Tweepy client: {e}"
        logging.error(error_msg)
        send_error_notification(error_msg, notifications_webhook_url)
        exit(1)
    global_filters = config.get("global_filters", {})
    search_limit = config.get("search_limit_per_keyword", 50)
    for query, channel in config.get("keyword_channels", {}).items():
        webhook_url = channel.get("discord_webhook_url")
        user_filters = global_filters.copy()
        user_filters.update(channel.get("user_filters", {}))
        min_followers = user_filters.get("min_followers", 0)
        only_verified = user_filters.get("only_verified", False)
        whitelist = [u.lower() for u in user_filters.get("whitelist_usernames", [])]
        blacklist = [u.lower() for u in user_filters.get("blacklist_usernames", [])]
        tweets = client.search_recent_tweets(
            query=query,
            expansions=['author_id', 'attachments.media_keys'],
            tweet_fields=['id', 'text', 'author_id', 'created_at', 'public_metrics', 'attachments'],
            user_fields=['name', 'username', 'public_metrics', 'verified'],
            media_fields=['url', 'preview_image_url', 'type'],
            max_results=search_limit
        )
        if not tweets.data:
            continue
        users = {u['id']: u for u in tweets.includes.get('users', [])} if tweets.includes else {}
        media_items = {m['media_key']: m for m in tweets.includes.get('media', [])} if tweets.includes else {}
        sent_count = 0
        today = datetime.now(timezone.utc).date()
        for tweet in tweets.data:
            if sent_count >= 5:
                break
            # Only send tweets created today
            tweet_created = tweet.created_at.date() if hasattr(tweet, 'created_at') and tweet.created_at else None
            if tweet_created != today:
                continue
            if str(tweet.id) in sent_tweet_ids:
                continue
            author = users.get(tweet.author_id)
            if not author:
                continue
            username = author.username.lower()
            if whitelist and username not in whitelist:
                continue
            if blacklist and username in blacklist:
                continue
            if min_followers and author.public_metrics.get('followers_count', 0) < min_followers:
                continue
            if only_verified and not author.verified:
                continue
            media_urls = []
            if tweet.attachments and tweet.attachments.get('media_keys'):
                for key in tweet.attachments['media_keys']:
                    m = media_items.get(key)
                    if m and m.type in ['photo', 'animated_gif'] and 'url' in m:
                        media_urls.append(m.url)
                    elif m and m.type == 'video' and 'preview_image_url' in m:
                        media_urls.append(m.preview_image_url)
            send_to_discord(webhook_url, author.name, author.username, tweet.text, f"https://twitter.com/{author.username}/status/{tweet.id}", tweet.public_metrics.get('retweet_count', 0), tweet.public_metrics.get('like_count', 0), media_urls)
            save_sent_tweet_id(tweet.id)
            sent_tweet_ids.add(str(tweet.id))
            sent_count += 1

if __name__ == "__main__":
    main()