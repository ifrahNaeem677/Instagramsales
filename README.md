# Instagram Sales Bot

An AI assistant that answers your Instagram DMs, helps customers choose products, takes orders, and sends each order to your WhatsApp.

**What it does**
- Replies to every DM sent to your Instagram Business account, in English.
- Comment-to-DM: when someone comments "price", "info" and similar words on a post, it sends them a private DM.
- Walks the customer through product, colour, size, name, phone, address and payment, then confirms the total.
- Sends confirmed orders to your WhatsApp and saves them in `data/orders.jsonl`.
- Hands the chat to you, and alerts you on WhatsApp, for complaints, refunds, discounts or anything it doesn't know.
- Pauses automatically when you reply yourself in the Instagram app. Send `#bot` in that chat to turn the AI back on.

**What it does not do:** it never messages people who haven't contacted you first, because Meta doesn't allow that and bans accounts that try. Get new customers through posts, reels, ads and comment-to-DM.

---

## 1. Edit your catalog
Open `catalog.json` and replace the sample products, prices, currency, delivery, payment and return policies with your own. The bot only sells what's listed there.

## 2. Install and test locally
You need Node.js 20 or newer and an Anthropic API key from console.anthropic.com.

```bash
npm install
```

```bash
cp .env.example .env
```

Put your `ANTHROPIC_API_KEY` in `.env`, then chat with the bot in your terminal:

```bash
npm run chat
```

## 3. Host it
Meta needs a public HTTPS URL. Any Node host works: Render, Railway, Fly.io or a VPS. Set the variables from `.env` in the host's dashboard. Your webhook URL will be `https://YOUR-APP-DOMAIN/webhook`.

For quick testing from your own computer, use `ngrok http 3000`.

## 4. Meta app setup (Instagram)
1. Go to developers.facebook.com, choose **Create App**, then **Business**.
2. Add the **Instagram** product, using the "API setup with Facebook login" option, and the **Messenger** product.
3. In Instagram app settings, under **Connected tools**, turn on **Allow access to messages**.
4. Generate a **Page access token** for your Facebook Page with these permissions: `instagram_basic`, `instagram_manage_messages`, `instagram_manage_comments`, `pages_manage_metadata`, `pages_show_list`. Exchange it for a long-lived token and put it in `FB_PAGE_ACCESS_TOKEN`.
5. Fill in `FB_PAGE_ID`, `IG_ACCOUNT_ID` and `META_APP_SECRET` (found under App settings, then Basic).
6. Under **Webhooks**, set the object to **Instagram**, the callback URL to `https://YOUR-APP-DOMAIN/webhook`, and the verify token to the same value as `META_VERIFY_TOKEN`. Subscribe to `messages`, `messaging_postbacks` and `comments`.
7. While the app is in **Development mode**, only people with a role on the app (admins and testers) can trigger the bot. To serve real customers, submit for **App Review** with Advanced Access to `instagram_manage_messages` and `instagram_manage_comments`, then switch the app to **Live**.

## 5. WhatsApp order alerts
1. In the same Meta app, add the **WhatsApp** product. You get a test business number and can add a real one later.
2. Put the **Phone number ID** and a **permanent access token** (from a System User in Business Settings) into `.env`. Set `OWNER_WHATSAPP_NUMBER` to your personal number, digits only, with the country code.
3. WhatsApp only lets a business send free-form messages within 24 hours after you last messaged it. To get alerts any time, create a message template in WhatsApp Manager:
   - Name: `new_order_alert`
   - Category: **Utility**
   - Language: English
   - Body: `New alert from your Instagram shop: {{1}}`

   Once it's approved, set `WHATSAPP_TEMPLATE_NAME=new_order_alert`.

Orders are always saved to `data/orders.jsonl`, even if a WhatsApp message fails.

## 6. Start
```bash
npm start
```

## Files
| File | Purpose |
|---|---|
| `catalog.json` | Your products and policies |
| `src/agent.js` | AI salesperson: prompt, order and hand-off tools |
| `src/server.js` | Instagram webhook, comment-to-DM, pause/resume |
| `src/instagram.js` | Sends DMs |
| `src/whatsapp.js` | Sends alerts to you |
| `src/store.js` | Saves conversations and orders under `data/` |

## Cost
Each customer message costs a fraction of a cent to a few cents, depending on conversation length. Set `CLAUDE_EFFORT` to `low` (the default) for fast, cheap chat replies. For cheaper still, set `CLAUDE_MODEL=claude-haiku-5-5`.
