import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = [
    "Scanned At",
    "Store Name", "Store ID", "Store Address",
    "Manager", "Cashier", "Terminal ID", "Transaction ID",
    "Date", "Time",
    "Items Sold", "Items List",
    "Subtotal", "Tax Amount", "Tax Rate",
    "Total Amount", "Payment Method", "Amount Paid", "Change Due"
]


def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(creds)


def _get_sheet():
    gc = _get_client()
    sheet = gc.open_by_key(st.secrets["SHEET_ID"]).sheet1

    if sheet.row_count == 0 or sheet.row_values(1) != HEADERS:
        sheet.clear()
        sheet.append_row(HEADERS, value_input_option="RAW")

    return sheet


def append_receipt(fields: dict, scanned_at: str):
    sheet = _get_sheet()

    items = fields.get("items") or []
    items_list = " | ".join(
        f"{i.get('name', '?')} x{i.get('quantity', 1)} @ {i.get('unit_price', '?')} = {i.get('total', '?')}"
        for i in items
    )

    row = [
        scanned_at,
        fields.get("store_name") or "",
        fields.get("store_id") or "",
        fields.get("store_address") or "",
        fields.get("manager") or "",
        fields.get("cashier") or "",
        fields.get("terminal_id") or "",
        fields.get("transaction_id") or "",
        fields.get("date") or "",
        fields.get("time") or "",
        fields.get("items_sold") or str(len(items)),
        items_list,
        fields.get("subtotal") or "",
        fields.get("tax_amount") or "",
        fields.get("tax_rate") or "",
        fields.get("total_amount") or "",
        fields.get("payment_method") or "",
        fields.get("amount_paid") or "",
        fields.get("change_due") or "",
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")