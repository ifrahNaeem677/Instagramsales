# Instagram Sales Bot (Streamlit)

An AI assistant that answers your Instagram DMs, takes orders, and sends them to your WhatsApp. It comes with a Streamlit dashboard where you can:

- **Bot:** start and stop the bot and watch live activity
- **Test chat:** chat with the AI as if you were a customer
- **Orders:** see every order and download them as CSV
- **Conversations:** read customer chats and switch the AI back on after a hand-off
- **Catalog:** edit products, prices and policies

**How it works:** Streamlit can't receive Instagram webhooks, so the bot checks your Instagram inbox every 20 seconds and answers new messages. It only replies to people who message you first.

---

## Step 1: Run it on your computer

1. Install Python 3.10 or newer from python.org. On Windows, tick **Add Python to PATH** during setup.
2. Open a terminal in this folder and install the packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`. Fill in `ANTHROPIC_API_KEY` (from console.anthropic.com) and `DASHBOARD_PASSWORD`.
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Your browser opens. Go to the **Catalog** tab to enter your products, then the **Test chat** tab to try conversations.

## Step 2: Put it online (Streamlit Community Cloud, free)

1. Upload this folder to a **private** GitHub repository. `secrets.toml` is excluded automatically, so your keys aren't uploaded.
2. Go to share.streamlit.io, choose **Create app**, and pick your repository with `app.py` as the main file.
3. Open **Advanced settings**, then **Secrets**, and paste the contents of your `secrets.toml`.
4. Deploy. You'll get a link like `https://your-shop.streamlit.app`.

**Important limits of the free Streamlit Cloud plan:**
- **The app sleeps.** If nobody opens it for a while, it shuts down and the bot stops answering until someone visits the link and wakes it up. For a bot that runs 24/7, host the same app on a small paid server instead, such as Render, Railway or a VPS, using `streamlit run app.py --server.port $PORT`.
- **Saved data is wiped on restart.** Orders and catalog edits stored on the server are lost. Every order still reaches your WhatsApp. Keep your real catalog in `catalog.json` on GitHub.

## Step 3: Connect Instagram

1. Go to developers.facebook.com, choose **Create App**, then **Business**, and add the **Instagram** product using the "API setup with Facebook login" option.
2. In the Instagram app on your phone, go to Settings, then **Messages and story replies**, then **Connected tools**, and turn on **Allow access to messages**.
3. Generate a long-lived **Page access token** with these permissions: `instagram_basic`, `instagram_manage_messages`, `pages_manage_metadata`, `pages_show_list`, `pages_read_engagement`.
4. Add `FB_PAGE_ID`, `IG_ACCOUNT_ID` and `FB_PAGE_ACCESS_TOKEN` to your secrets, then reboot the app. You don't need a webhook.
5. On the **Bot** tab the status should show **Running**. DM your shop from a tester account to check it replies.
6. To serve real customers, submit the Meta app for **App Review** to get Advanced Access to `instagram_manage_messages`, then switch the app to **Live**.

## Step 4: WhatsApp order alerts

1. Add the **WhatsApp** product to the same Meta app.
2. Put the Phone number ID, a permanent access token and your own number (digits only, with the country code) into the secrets.
3. In WhatsApp Manager, create a **Utility** template named `new_order_alert` with the body `New alert from your Instagram shop: {{1}}`. Once it's approved, set `WHATSAPP_TEMPLATE_NAME = "new_order_alert"`.

## Daily use
- **New orders** arrive on WhatsApp and appear in the **Orders** tab.
- **If you reply to a customer yourself** in Instagram, the AI stops replying in that chat. To turn it back on, send `#bot` in the chat or click **Switch AI back on** in the Conversations tab.
- **The bot hands chats to you** and alerts you on WhatsApp for complaints, refunds, discount requests and questions it can't answer.
- **The bot only replies to messages sent after it was first started**, so old chats are left alone.
