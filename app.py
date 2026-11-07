import json
import time

import pandas as pd
import streamlit as st

from bot import store
from bot.agent import CATALOG_FILE, generate_reply, load_catalog
from bot.config import load_config
from bot.worker import Worker

st.set_page_config(page_title="Instagram Sales Bot", page_icon="🛍️", layout="wide")
cfg = load_config()

# ---------- password gate ----------
if cfg.get("DASHBOARD_PASSWORD") and not st.session_state.get("authed"):
    st.title("🛍️ Instagram Sales Bot")
    pw = st.text_input("Password", type="password")
    if pw:
        if pw == cfg["DASHBOARD_PASSWORD"]:
            st.session_state.authed = True
            st.rerun()
        st.error("Wrong password")
    st.stop()


# ---------- one background bot per server process ----------
@st.cache_resource
def get_worker() -> Worker:
    w = Worker(cfg)
    ready = all(cfg.get(k) for k in ("ANTHROPIC_API_KEY", "FB_PAGE_ID", "IG_ACCOUNT_ID", "FB_PAGE_ACCESS_TOKEN"))
    if ready and cfg.get("AUTO_START", "true").lower() == "true":
        w.start()
    return w


worker = get_worker()

st.title("🛍️ Instagram Sales Bot")
if not cfg.get("ANTHROPIC_API_KEY"):
    st.error("Add ANTHROPIC_API_KEY to your secrets first (see README).")
    st.stop()

tab_bot, tab_test, tab_orders, tab_chats, tab_catalog = st.tabs(
    ["🤖 Bot", "💬 Test chat", "📦 Orders", "👥 Conversations", "🏷️ Catalog"]
)

# ---------- Bot status ----------
with tab_bot:
    ig_ready = all(cfg.get(k) for k in ("FB_PAGE_ID", "IG_ACCOUNT_ID", "FB_PAGE_ACCESS_TOKEN"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Running ✅" if worker.running else "Stopped ⏸️")
    c2.metric("Last check", time.strftime("%H:%M:%S", time.localtime(worker.last_poll)) if worker.last_poll else "-")
    c3.metric("WhatsApp alerts", "On" if cfg.get("WHATSAPP_ACCESS_TOKEN") else "Not set up")

    if not ig_ready:
        st.warning("Instagram isn't connected yet. Add FB_PAGE_ID, IG_ACCOUNT_ID and FB_PAGE_ACCESS_TOKEN to your secrets. You can still use the Test chat tab.")
    else:
        b1, b2, b3 = st.columns([1, 1, 4])
        if b1.button("▶️ Start", disabled=worker.running):
            worker.start()
            st.rerun()
        if b2.button("⏹️ Stop", disabled=not worker.running):
            worker.stop()
            time.sleep(1)
            st.rerun()
        if b3.button("🔄 Refresh"):
            st.rerun()

    if worker.last_error:
        st.error(f"Last error: {worker.last_error}")
    st.caption("The bot keeps running while this app's server is up, even if you close this page.")
    st.subheader("Activity")
    st.code("\n".join(worker.log) or "No activity yet.", language=None)

# ---------- Test chat ----------
with tab_test:
    st.caption("Chat as a customer to test replies. Orders placed here are real test orders (they go to WhatsApp and the Orders tab).")
    if "test_conv" not in st.session_state or st.button("Start new test chat"):
        st.session_state.test_conv = store.new_conversation("dashboard-test", "test-customer")
        st.session_state.test_view = []
    conv = st.session_state.test_conv
    for role, text in st.session_state.test_view:
        st.chat_message(role).write(text)
    if conv["human_takeover"]:
        st.info("The bot handed this chat to a human. Start a new test chat to continue testing.")
    elif prompt := st.chat_input("Type a message as the customer..."):
        st.chat_message("user").write(prompt)
        with st.spinner("Typing..."):
            try:
                reply = generate_reply(cfg, conv, prompt)
            except Exception as e:
                reply = f"[Error: {e}]"
        st.session_state.test_view += [("user", prompt), ("assistant", reply)]
        st.chat_message("assistant").write(reply)

# ---------- Orders ----------
with tab_orders:
    orders = store.load_orders()
    if not orders:
        st.info("No orders yet.")
    else:
        rows = [
            {
                "Order": o["order_id"],
                "Time (UTC)": o["created_at"],
                "Customer": o["customer_name"],
                "Phone": o["phone"],
                "City": o["city"],
                "Items": "; ".join(f"{i['quantity']}x {i['name']} ({i['color']}, {i['size']})" for i in o["items"]),
                "Total": o["total"],
                "Payment": o["payment_method"],
                "Address": o["address"],
                "Instagram": o.get("instagram_user", ""),
                "Notes": o.get("notes", ""),
            }
            for o in reversed(orders)
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button("Download orders (CSV)", df.to_csv(index=False), "orders.csv", "text/csv")

# ---------- Conversations ----------
with tab_chats:
    convs = [c for c in store.list_conversations() if c["user_id"] != "dashboard-test"]
    if not convs:
        st.info("No Instagram conversations yet.")
    for c in convs:
        label = f"@{c.get('username') or c['user_id']}  ·  {'🙋 with you' if c['human_takeover'] else '🤖 AI'}  ·  {time.strftime('%d %b %H:%M', time.localtime(c['updated_at']))}"
        with st.expander(label):
            for m in c["messages"]:
                if isinstance(m["content"], str):
                    st.chat_message(m["role"]).write(m["content"])
                else:
                    for b in m["content"]:
                        if b.get("type") == "text" and b.get("text"):
                            st.chat_message("assistant").write(b["text"])
                        elif b.get("type") == "tool_use":
                            st.caption(f"⚙️ {b['name']}")
            if c["human_takeover"] and st.button("Switch AI back on", key="resume-" + c["user_id"]):
                with store.lock:
                    fresh = store.load_conversation(c["user_id"])
                    fresh["human_takeover"] = False
                    store.save_conversation(fresh)
                st.rerun()

# ---------- Catalog ----------
with tab_catalog:
    catalog = load_catalog()
    st.caption("Your products and policies. The bot only sells what is listed here. Changes apply to the next message.")
    with st.form("policies"):
        catalog["store_name"] = st.text_input("Store name", catalog["store_name"])
        catalog["currency"] = st.text_input("Currency", catalog["currency"])
        catalog["delivery"] = st.text_area("Delivery", catalog["delivery"])
        catalog["payment"] = st.text_area("Payment", catalog["payment"])
        catalog["returns"] = st.text_area("Returns", catalog["returns"])
        catalog["contact_hours"] = st.text_input("Team hours", catalog["contact_hours"])
        st.markdown("**Products** (colours and sizes: separate with commas)")
        prod_df = pd.DataFrame(
            [{**p, "colors": ", ".join(p["colors"]), "sizes": ", ".join(p["sizes"])} for p in catalog["products"]]
        )
        edited = st.data_editor(
            prod_df,
            num_rows="dynamic",
            width="stretch",
            column_order=["sku", "name", "category", "price", "colors", "sizes", "in_stock", "description"],
        )
        if st.form_submit_button("💾 Save catalog"):
            products = []
            for p in edited.to_dict("records"):
                if not p.get("sku") or not p.get("name"):
                    continue
                products.append(
                    {
                        "sku": str(p["sku"]).strip(),
                        "name": str(p["name"]).strip(),
                        "category": str(p.get("category") or "").strip(),
                        "price": float(p.get("price") or 0),
                        "colors": [x.strip() for x in str(p.get("colors") or "").split(",") if x.strip()],
                        "sizes": [x.strip() for x in str(p.get("sizes") or "").split(",") if x.strip()],
                        "in_stock": bool(p.get("in_stock")),
                        "description": str(p.get("description") or "").strip(),
                    }
                )
            catalog["products"] = products
            CATALOG_FILE.write_text(json.dumps(catalog, indent=2))
            st.success(f"Saved {len(products)} products.")
    st.warning("On Streamlit Community Cloud, edits made here are lost when the app restarts. To keep them, also update catalog.json in your GitHub repo.")
