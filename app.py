import streamlit as st
import pandas as pd
import json
from datetime import datetime
from extractor import process_invoice
from sheets import append_receipt

st.set_page_config(
    page_title="Walmart Receipt Parser",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Walmart Receipt Parser")
st.caption("Upload a receipt → GPT-4o Vision extracts and structures all fields")

with st.sidebar:
    st.header("About")
    st.info("Parses Walmart receipts into structured data using GPT-4o Vision.")
    st.markdown("**Supported formats:** JPG, PNG, PDF")
    st.markdown("**Built with:** OpenAI · Streamlit · Google Sheets")

uploaded_file = st.file_uploader(
    "Upload Walmart receipt",
    type=["pdf", "jpg", "jpeg", "png", "jfif"],
    help="Upload a clear photo or scan of your receipt"
)

if uploaded_file:
    col_img, col_results = st.columns([1, 2])

    with col_img:
        st.subheader("Receipt")
        if uploaded_file.type != "application/pdf":
            st.image(uploaded_file, use_container_width=True)
        else:
            st.info("PDF uploaded — processing first page")

    with col_results:
        file_bytes = uploaded_file.read()

        with st.spinner("Extracting receipt data..."):
            try:
                raw_text, fields = process_invoice(file_bytes, uploaded_file.name)
                st.success("Done!")
            except Exception as e:
                st.error(f"Extraction failed: {e}")
                st.stop()

        # --- Store Info ---
        st.subheader("🏪 Store Info")
        s1, s2, s3 = st.columns(3)
        s1.metric("Store", fields.get("store_name") or "—")
        s2.metric("Store ID", fields.get("store_id") or "—")
        s3.metric("Manager", fields.get("manager") or "—")

        s4, s5 = st.columns(2)
        s4.metric("Address", fields.get("store_address") or "—")
        s5.metric("Cashier", fields.get("cashier") or "—")

        # --- Transaction Info ---
        st.subheader("🧾 Transaction Info")
        t1, t2, t3 = st.columns(3)
        t1.metric("Date", fields.get("date") or "—")
        t2.metric("Time", fields.get("time") or "—")
        t3.metric("Terminal ID", fields.get("terminal_id") or "—")

        t4, t5 = st.columns(2)
        t4.metric("Transaction ID", fields.get("transaction_id") or "—")
        t5.metric("Items Sold", fields.get("items_sold") or "—")

        # --- Items Table ---
        st.subheader("🛒 Items Purchased")
        items = fields.get("items") or []

        if items:
            df = pd.DataFrame(items)
            for col in ["name", "quantity", "unit_price", "total", "taxable"]:
                if col not in df.columns:
                    df[col] = None
            df = df[["name", "quantity", "unit_price", "total", "taxable"]]
            df.columns = ["Item", "Qty", "Unit Price", "Total", "Taxable"]
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No items detected.")
            df = pd.DataFrame()

        # --- Payment Summary ---
        st.subheader("💳 Payment Summary")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Subtotal", fields.get("subtotal") or "—")
        p2.metric("Tax", fields.get("tax_amount") or "—")
        p3.metric("Total", fields.get("total_amount") or "—")
        p4.metric("Payment Method", fields.get("payment_method") or "—")

        p5, p6 = st.columns(2)
        p5.metric("Amount Paid", fields.get("amount_paid") or "—")
        p6.metric("Change Due", fields.get("change_due") or "—")

        # --- Save to Google Sheets ---
        st.subheader("📊 Google Sheets")
        if st.button("💾 Save to Google Sheets"):
            with st.spinner("Saving..."):
                try:
                    scanned_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    append_receipt(fields, scanned_at)
                    st.success("✅ Saved to Google Sheets!")
                except Exception as e:
                    import traceback
                    st.error(f"Failed to save: {e}")
                    st.code(traceback.format_exc())

        # --- Downloads ---
        st.subheader("⬇️ Export")
        dl1, dl2 = st.columns(2)
        with dl1:
            if not df.empty:
                st.download_button(
                    "Download Items CSV",
                    df.to_csv(index=False),
                    file_name="receipt_items.csv",
                    mime="text/csv"
                )
        with dl2:
            st.download_button(
                "Download Full JSON",
                json.dumps(fields, indent=2),
                file_name="receipt_data.json",
                mime="application/json"
            )

        with st.expander("Raw OCR text"):
            st.text(raw_text)

        with st.expander("Full extracted JSON"):
            st.json(fields)