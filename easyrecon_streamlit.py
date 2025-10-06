import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="EasyRecon – GST Reconciliation", layout="wide")

st.title("🧾 EasyRecon – GST Reconciliation Made Effortless")
st.markdown("""
Built by a CA, for CAs – **CA Ashwini Hegde**  
✅ Clean GSTR-2A / 2B | ✅ Reconcile Effortlessly | ✅ Spot Mismatches Instantly
""")

# ---------------- Upload files ----------------
books_file = st.file_uploader("Upload Purchase Register (Books)", type=["xls", "xlsx"])
gstr_file = st.file_uploader("Upload GSTR-2A / 2B", type=["xls", "xlsx"])
tolerance = st.number_input("Tolerance (₹)", min_value=0.0, value=0.5, step=0.5)

# ---------------- Reconciliation ----------------
def reconcile(books_df, gstr_df, tol):
    # Normalize column names
    books_df.columns = [c.strip().lower() for c in books_df.columns]
    gstr_df.columns = [c.strip().lower() for c in gstr_df.columns]

    # Create a reconciliation key: GSTIN + Invoice No
    books_df["key"] = books_df["gstin"].astype(str).str.upper().str.strip() + "|" + books_df["invoice no"].astype(str).str.upper().str.strip()
    gstr_df["key"] = gstr_df["gstin"].astype(str).str.upper().str.strip() + "|" + gstr_df["invoice no"].astype(str).str.upper().str.strip()

    merged = pd.merge(
        books_df, gstr_df, on="key", how="outer", suffixes=("_books", "_gstr"), indicator=True
    )

    # Status calculation
    def status(row):
        if row["_merge"] == "both":
            diff = abs(row.get("invoice value_books", 0) - row.get("invoice value_gstr", 0))
            return "Matched" if diff <= tol else "Mismatch (Value)"
        elif row["_merge"] == "left_only":
            return "Missing in GSTR"
        else:
            return "Missing in Books"

    merged["Status"] = merged.apply(status, axis=1)
    return merged

# ---------------- Run Reconciliation ----------------
if st.button("🚀 Reconcile Now"):
    if not books_file or not gstr_file:
        st.warning("⚠️ Please upload both files!")
    else:
        books_df = pd.read_excel(books_file)
        gstr_df = pd.read_excel(gstr_file)

        result_df = reconcile(books_df, gstr_df, tolerance)

        # Display top 20 rows
        st.subheader("📄 Sample Reconciliation Results")
        st.dataframe(result_df.head(20))

        # Display summary
        st.subheader("📊 Summary")
        summary = result_df["Status"].value_counts().to_dict()
        st.json(summary)

        # Download option
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Reconciliation")
        st.download_button(
            label="⬇️ Download Result Excel",
            data=output.getvalue(),
            file_name="EasyRecon_Result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
