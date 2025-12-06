# expense_tracker_final_edit_delete.py
# Author: Jenifer Molnár
#
# Daily Expense Tracker with:
# - Add / Edit / Delete rows
# - Currency conversion (HUF, EUR, USD, GBP)
# - Modern, colorful UI with cards
# - Scrollable layout
# - Pie chart showing category distribution

import flet as ft

# --------------------------- CURRENCY HELPERS ---------------------------- #

CURRENCY_RATES = {
    "HUF": 1.0,        # base currency
    "EUR": 0.0026,     # approx
    "USD": 0.0028,
    "GBP": 0.0022,
}


def huf_to_currency(amount_huf: float, currency: str) -> float:
    """Convert HUF → selected currency."""
    return amount_huf * CURRENCY_RATES.get(currency, 1.0)


def currency_to_huf(amount: float, currency: str) -> float:
    """Convert selected currency → HUF."""
    rate = CURRENCY_RATES.get(currency, 1.0)
    if rate == 0:
        return amount
    return amount / rate


# ------------------------------ MAIN APP --------------------------------- #

def main(page: ft.Page):
    page.title = "Daily Expense Tracker"
    page.theme_mode = "light"
    page.bgcolor = ft.Colors.GREY_50
    page.padding = 20
    page.scroll = True
    page.horizontal_alignment = "stretch"

    # Category colors (soft pastel)
    categories = {
        "Food": ft.Colors.RED_200,
        "Transport": ft.Colors.BLUE_200,
        "Shopping": ft.Colors.GREEN_200,
        "Bills": ft.Colors.PURPLE_200,
    }

    # List of all entries, each entry is a dict:
    # {"id": int, "category": str, "description": str, "amount_huf": float}
    entries: list[dict] = []
    next_entry_id = 1

    # Current totals (in HUF) – recomputed from entries when needed
    totals_huf = {cat: 0.0 for cat in categories}

    # Track which entry is currently being edited (None = add mode)
    editing_entry_id: int | None = None

    # ------------------------- SMALL HELPERS ------------------------- #

    def recalculate_totals():
        """Recalculate category totals from all entries (always in HUF)."""
        for cat in totals_huf:
            totals_huf[cat] = 0.0
        for entry in entries:
            totals_huf[entry["category"]] += entry["amount_huf"]

    def modern_textfield(label: str, icon=None, width: int = 200) -> ft.TextField:
        """Common style for all text fields."""
        return ft.TextField(
            label=label,
            width=width,
            border_radius=12,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.BLUE_400,
            prefix_icon=icon,
            bgcolor=ft.Colors.WHITE,
            cursor_color=ft.Colors.BLUE_400,
        )

    def card(content: ft.Control) -> ft.Container:
        """Reusable card style."""
        return ft.Container(
            content=content,
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=1,
                color=ft.Colors.GREY_300,
                offset=ft.Offset(0, 3),
            ),
        )

    # --------------------------- INPUT CONTROLS --------------------------- #

    category_field = ft.Dropdown(
        label="Category",
        width=200,
        border_radius=12,
        options=[ft.dropdown.Option(cat) for cat in categories.keys()],
    )

    description_field = modern_textfield("Description", ft.Icons.NOTE_ALT, 260)

    currency_selector = ft.Dropdown(
        label="Currency",
        width=130,
        border_radius=12,
        options=[
            ft.dropdown.Option("HUF"),
            ft.dropdown.Option("EUR"),
            ft.dropdown.Option("USD"),
            ft.dropdown.Option("GBP"),
        ],
        value="HUF",
    )

    amount_field = modern_textfield(
        f"Amount ({currency_selector.value})", ft.Icons.PAID, 160
    )
    amount_field.keyboard_type = ft.KeyboardType.NUMBER

    # --------------------------- TABLE + PIE CHART --------------------------- #

    amount_column_title = ft.Text(f"Amount ({currency_selector.value})")

    expense_table = ft.DataTable(
        column_spacing=15,
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_300),
        columns=[
            ft.DataColumn(ft.Text("Category")),
            ft.DataColumn(ft.Text("Description")),
            ft.DataColumn(amount_column_title),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=[],
    )

    pie_chart = ft.PieChart(expand=True, height=300, sections=[])

    # ------------------------- UPDATE UI SECTIONS ------------------------- #

    def update_pie():
        """Refresh pie chart based on current totals and selected currency."""
        cur = currency_selector.value
        pie_chart.sections = [
            ft.PieChartSection(
                value=huf_to_currency(totals_huf[cat], cur),
                title=f"{cat} ({huf_to_currency(totals_huf[cat], cur):.1f} {cur})",
                color=color,
                radius=60,
                title_style=ft.TextStyle(size=12, weight="bold"),
            )
            for cat, color in categories.items()
        ]
        page.update()

    def rebuild_table():
        """Rebuild the entire DataTable from the entries list."""
        expense_table.rows.clear()
        cur = currency_selector.value

        for entry in entries:
            display_amount = huf_to_currency(entry["amount_huf"], cur)

            def make_edit_handler(entry_id: int):
                def handler(e):
                    nonlocal editing_entry_id
                    # Load the entry into the form
                    for en in entries:
                        if en["id"] == entry_id:
                            editing_entry_id = entry_id
                            category_field.value = en["category"]
                            description_field.value = en["description"]
                            amount_field.value = f"{huf_to_currency(en['amount_huf'], currency_selector.value):.1f}"
                            # Switch button appearance to "update" mode
                            add_btn.text = "Update Expense"
                            add_btn.icon = ft.Icons.SAVE
                            add_btn.bgcolor = ft.Colors.BLUE_400
                            page.update()
                            break
                return handler

            def make_delete_handler(entry_id: int):
                def handler(e):
                    nonlocal editing_entry_id
                    # Remove the entry from list
                    index = next(
                        (i for i, en in enumerate(entries) if en["id"] == entry_id),
                        None,
                    )
                    if index is not None:
                        entries.pop(index)
                        # If we were editing this entry, cancel edit mode
                        if editing_entry_id == entry_id:
                            editing_entry_id = None
                            reset_form_button()
                    # Recalculate totals and refresh UI
                    recalculate_totals()
                    rebuild_table()
                    update_pie()
                return handler

            actions = ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.EDIT,
                        icon_color=ft.Colors.BLUE_400,
                        tooltip="Edit",
                        on_click=make_edit_handler(entry["id"]),
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Delete",
                        on_click=make_delete_handler(entry["id"]),
                    ),
                ],
                spacing=0,
            )

            expense_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(entry["category"], weight="bold"),
                                bgcolor=categories[entry["category"]],
                                padding=6,
                                border_radius=8,
                            )
                        ),
                        ft.DataCell(ft.Text(entry["description"])),
                        ft.DataCell(ft.Text(f"{display_amount:.1f}")),
                        ft.DataCell(actions),
                    ]
                )
            )

        expense_table.update()

    # ------------------------------ BUTTON BEHAVIOR ------------------------------ #

    def reset_form_button():
        """Return the main button to 'Add' state."""
        add_btn.text = "Add Expense"
        add_btn.icon = ft.Icons.ADD_CIRCLE
        add_btn.bgcolor = ft.Colors.ORANGE_400

    def clear_inputs():
        description_field.value = ""
        amount_field.value = ""
        category_field.value = None
        page.update()

    def save_expense(e):
        nonlocal next_entry_id, editing_entry_id

        cat = category_field.value
        desc = description_field.value
        amt_text = amount_field.value
        cur = currency_selector.value

        if not (cat and desc and amt_text):
            page.snack_bar = ft.SnackBar(ft.Text("Please fill all fields!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            amount_in_current = float(amt_text)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Amount must be numeric"))
            page.snack_bar.open = True
            page.update()
            return

        # Always store internal values in HUF
        amount_huf = currency_to_huf(amount_in_current, cur)

        if editing_entry_id is None:
            # ADD MODE
            entries.append(
                {
                    "id": next_entry_id,
                    "category": cat,
                    "description": desc,
                    "amount_huf": amount_huf,
                }
            )
            next_entry_id += 1
        else:
            # EDIT MODE
            for en in entries:
                if en["id"] == editing_entry_id:
                    en["category"] = cat
                    en["description"] = desc
                    en["amount_huf"] = amount_huf
                    break
            editing_entry_id = None
            reset_form_button()

        # Recalculate totals and refresh UI
        recalculate_totals()
        rebuild_table()
        update_pie()
        clear_inputs()

    add_btn = ft.ElevatedButton(
        "Add Expense",
        icon=ft.Icons.ADD_CIRCLE,
        bgcolor=ft.Colors.ORANGE_400,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=save_expense,
    )

    # ------------------------- CURRENCY CHANGE HANDLER ------------------------- #

    def on_currency_change(e):
        # Update amount field label
        amount_field.label = f"Amount ({currency_selector.value})"
        amount_field.update()

        # Update column header
        amount_column_title.value = f"Amount ({currency_selector.value})"
        amount_column_title.update()

        # Rebuild table to show converted values
        rebuild_table()
        # Update pie chart
        update_pie()

    currency_selector.on_change = on_currency_change

    # ------------------------------ UI LAYOUT ------------------------------ #

    form_card = card(
        ft.Column(
            [
                ft.Text("Add / Edit Expense", size=22, weight="bold"),
                category_field,
                description_field,
                amount_field,
                currency_selector,
                add_btn,
            ],
            spacing=15,
        )
    )

    table_card = card(
        ft.Column(
            [
                ft.Text("Expenses", size=22, weight="bold"),
                expense_table,
            ]
        )
    )

    pie_card = card(
        ft.Column(
            [
                ft.Text("Category Distribution", size=22, weight="bold"),
                pie_chart,
            ]
        )
    )

    page.add(
        ft.Column(
            [
                ft.Text("Daily Expense Tracker", size=30, weight="bold"),
                ft.Divider(),
                form_card,
                ft.Container(height=20),
                table_card,
                ft.Container(height=20),
                pie_card,
            ],
            spacing=20,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
