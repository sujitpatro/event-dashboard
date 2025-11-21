# app.py
import streamlit as st
import pandas as pd
from sqlalchemy import text, inspect
from database import engine
import plotly.express as px

st.set_page_config(page_title="Events Dashboard", layout="wide")

# ------------------------------
# Utility Functions
# ------------------------------
@st.cache_data(ttl=60)
def list_tables():
    insp = inspect(engine)
    return insp.get_table_names(schema="public")


@st.cache_data(ttl=60)
def get_columns(table):
    insp = inspect(engine)
    cols = insp.get_columns(table, schema="public")
    return [(c["name"], str(c["type"])) for c in cols]


@st.cache_data(ttl=30)
def read_table_sample(table, limit=20000):
    sql = text(f"SELECT * FROM public.{table} LIMIT :limit")
    df = pd.read_sql(sql, engine.connect(), params={"limit": limit})
    return df


# ------------------------------
# MAIN APP
# ------------------------------
def main():

    st.title("🎉 Events / Registrations Dashboard")

    st.sidebar.header("📌 Navigation")
    selection = st.sidebar.radio(
        "Choose View",
        [
            "Overview",
            "Table Browser",
            "Event-wise Student List",
            "Payments Dashboard",
        ]
    )

    table_names = list_tables()

    # =====================================================
    # 1️⃣ OVERVIEW
    # =====================================================
    if selection == "Overview":

        st.subheader("📊 Event Registrations Summary")

        if "events" in table_names and "registrations" in table_names:

            regs = read_table_sample("registrations", limit=20000)
            events = read_table_sample("events", limit=20000)

            if not regs.empty and not events.empty:

                # Merge registrations + events to get names + categories
                merged = regs.merge(
                    events,
                    left_on="event_id",
                    right_on="id",
                    how="left"
                )

                # Build summary table
                summary = merged.groupby(["name", "category"]).agg(
                    Total_Registrations=("no", "count"),
                    Total_Paid=("is_paid", "sum"),
                ).reset_index()

                # Calculate unpaid
                summary["Total_Unpaid"] = summary["Total_Registrations"] - summary["Total_Paid"]

                # Sort
                summary = summary.sort_values("Total_Registrations", ascending=False)

                # Show table
                st.dataframe(summary)

                # Chart 1
                fig1 = px.bar(
                    summary,
                    x="name",
                    y="Total_Registrations",
                    color="category",
                    title="Event-wise Total Registrations",
                )
                st.plotly_chart(fig1, use_container_width=True)

                # Chart 2
                fig2 = px.bar(
                    summary,
                    x="name",
                    y=["Total_Paid", "Total_Unpaid"],
                    title="Paid vs Unpaid Per Event",
                    barmode="group",
                )
                st.plotly_chart(fig2, use_container_width=True)

            else:
                st.info("Need data in both events and registrations tables.")

    # =====================================================
    # 2️⃣ TABLE BROWSER
    # =====================================================
    elif selection == "Table Browser":

        st.subheader("🔎 Table Browser")

        selected_table = st.selectbox("Choose a table", table_names)
        cols = get_columns(selected_table)

        st.write("### Columns:")
        for c in cols:
            st.write(f"- `{c[0]}` — {c[1]}")

        st.markdown("---")
        st.write("### Sample Rows")

        df = read_table_sample(selected_table, limit=5000)
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            file_name=f"{selected_table}.csv",
            mime="text/csv"
        )

    # =====================================================
    # 3️⃣ EVENT-WISE STUDENT LIST
    # =====================================================
    elif selection == "Event-wise Student List":

        st.header("📋 Event-wise Student List")

        events = read_table_sample("events", limit=20000)
        regs = read_table_sample("registrations", limit=20000)
        members = read_table_sample("members", limit=20000)

        if events.empty or regs.empty or members.empty:
            st.error("Missing required data (events, registrations, members)")
            return

        st.subheader("Filter")

        # Category filter
        categories = events["category"].dropna().unique()
        selected_category = st.selectbox("Select Category", ["All"] + sorted(categories))

        if selected_category != "All":
            filtered_events = events[events["category"] == selected_category]
        else:
            filtered_events = events

        event_name = st.selectbox(
            "Select Event",
            filtered_events["name"].sort_values().unique()
        )
        event_id = filtered_events.loc[filtered_events["name"] == event_name, "id"].values[0]

        event_regs = regs[regs["event_id"] == event_id]

        merged = members.merge(event_regs, left_on="reg_no", right_on="no", how="inner")

        event_category = filtered_events.loc[
            filtered_events["id"] == event_id, "category"
        ].values[0]

        final_df = pd.DataFrame({
            "Roll No": merged["rollno"],
            "Name": merged["name"],
            "Email": merged["email"],
            "Phone": merged["phone"],
            "Paid": merged["is_paid"],
            "Payment Status": merged["payment_status"],
            "Team Name": merged["team_name"],
            "Solo Event?": merged["is_solo"],
            "Event Category": event_category,
        })

        st.subheader(f"Participants for: **{event_name}** ({event_category})")
        st.dataframe(final_df)

        st.download_button(
            "Download Participant List (CSV)",
            final_df.to_csv(index=False),
            file_name=f"{event_name}_participants.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.subheader("Summary")

        total = len(final_df)
        paid = final_df["Paid"].sum()
        unpaid = total - paid

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Participants", total)
        c2.metric("Paid", paid)
        c3.metric("Unpaid", unpaid)

        fig = px.pie(final_df, names="Paid", title=f"Paid vs Unpaid — {event_name}")
        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # 4️⃣ PAYMENTS DASHBOARD
    # =====================================================
    elif selection == "Payments Dashboard":

        st.header("💰 Payments Dashboard")

        regs = read_table_sample("registrations", limit=20000)
        events = read_table_sample("events", limit=20000)

        if regs.empty:
            st.error("No registration data available.")
            return

        # Paid vs Unpaid
        st.subheader("Paid vs Unpaid")
        paid_counts = regs["is_paid"].value_counts().reset_index()
        paid_counts.columns = ["Paid?", "Count"]
        st.dataframe(paid_counts)
        st.plotly_chart(px.pie(paid_counts, names="Paid?", values="Count"), use_container_width=True)

        # Payment Status
        st.subheader("Payment Status Breakdown")
        status_counts = regs["payment_status"].value.value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        st.dataframe(status_counts)
        st.plotly_chart(px.bar(status_counts, x="Status", y="Count"), use_container_width=True)

        # Event-wise Paid Registrations + Revenue
        st.subheader("Event-wise Paid Registrations & Revenue")

        merged = regs.merge(events, left_on="event_id", right_on="id", how="left")
        paid_only = merged[merged["is_paid"] == True]

        event_paid = paid_only.groupby(["name", "registration_fee"])["no"].count().reset_index()
        event_paid.columns = ["Event Name", "Registration Fee", "Paid Registrations"]

        # Calculate revenue
        event_paid["Total Revenue"] = event_paid["Registration Fee"] * event_paid["Paid Registrations"]

        event_paid = event_paid.sort_values("Total Revenue", ascending=False)

        st.dataframe(event_paid)

        fig_rev = px.bar(
            event_paid,
            x="Event Name",
            y="Total Revenue",
            title="Event-wise Revenue",
            text="Total Revenue",
        )
        st.plotly_chart(fig_rev, use_container_width=True)

        grand_total = event_paid["Total Revenue"].sum()
        st.metric("💰 Grand Total Revenue", f"₹ {grand_total}")

# ------------------------------
# Run App
# ------------------------------
if __name__ == "__main__":
    main()
