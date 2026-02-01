from playwright.async_api import Page


async def click_ticket_by_title(page: Page, ticket_title: str) -> None:
    tickets = await page.query_selector_all('[id^="ticket_"]')

    for ticket in tickets:
        title_element = await ticket.query_selector(
            ".muvaTicketTitle, .muvaTicketTitleLong"
        )

        if title_element:
            title = await title_element.text_content()
            if title and title.strip() == ticket_title:
                book_button = await ticket.query_selector("button:not([disabled])")
                if book_button:
                    button_text = await book_button.text_content()

                    if button_text and button_text.strip() == "BOOK":
                        await book_button.click()
                        print(f"Clicked BOOK for: {ticket_title}")
                        return

    raise Exception(f"Could not find bookable ticket: {ticket_title}")


async def set_ticket_quantity_internal(
    page: Page,
    ticket_name: str,
    quantity: int,
) -> None:
    print(
        f'\n⚡ Setting quantity for "{ticket_name}" to {quantity} (via Internal JS)...'
    )
    container = page.locator(".priceContainer").filter(has_text=ticket_name).first

    if await container.count() == 0:
        print(f'❌ Row "{ticket_name}" not found.')
        return

    await container.evaluate(
        """(row, qty) => {
            const visibleInput = row.querySelector('input[data-cy="ticketQuantity"]');
            const hiddenInput = row.querySelector('input[type="hidden"]');

            if (visibleInput) {
                visibleInput.removeAttribute('readonly');
                visibleInput.value = qty.toString();
                visibleInput.dispatchEvent(new Event('input', { bubbles: true }));
                visibleInput.dispatchEvent(new Event('change', { bubbles: true }));
                visibleInput.dispatchEvent(new Event('blur', { bubbles: true }));
            }

            if (hiddenInput) {
                hiddenInput.value = qty.toString();
                hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""",
        quantity,
    )

    print(f"  ✓ Value forced to {quantity}")


async def select_both_tickets(page: Page) -> None:
    print("=== Starting Automation (Internal Mode) ===")
    await page.wait_for_selector(".priceContainer", timeout=30000)
    await set_ticket_quantity_internal(page, "Full Price Ticket", 1)
    await set_ticket_quantity_internal(page, "Reduced Ticket", 1)
    print("✓ All done!")


async def select_time_slot(page: Page, time: str) -> None:
    print(f'\n⚡ Selecting time "{time}"...')
    slot_card = (
        page.locator(".muvaCalendarDayBorder:visible").filter(has_text=time).first
    )

    if await slot_card.count() == 0:
        print(f'  Slot "{time}" not seen immediately. Checking tabs...')
        afternoon_tab = (
            page.locator(".tab:not(.selected)").filter(has_text="AFTERNOON").first
        )

        if await afternoon_tab.is_visible():
            print("  → Switching to 'AFTERNOON' tab...")
            await afternoon_tab.click()
            await page.wait_for_timeout(800)
            slot_card = (
                page.locator(".muvaCalendarDayBorder:visible")
                .filter(has_text=time)
                .first
            )

    if await slot_card.count() == 0:
        print(f'❌ Time slot "{time}" is fully sold out or not found.')
        return

    is_sold_out = await slot_card.locator(
        ".muvaCalendarDaySoldOut"
    ).count() > 0 or "disabled" in (await slot_card.get_attribute("class") or "")

    if is_sold_out:
        print(f'❌ Time slot "{time}" is SOLD OUT.')
        return

    text_number = slot_card.locator(".muvaCalendarNumber")
    print(f'  ✓ Found "{time}". Clicking...')

    await text_number.click(force=True)

    try:
        element_handle = await slot_card.element_handle()
        await page.wait_for_function(
            "(el) => el.classList.contains('selected')",
            arg=element_handle,
            timeout=3000,
        )
        print("  ✅ SUCCESS: Time slot selected.")
    except Exception:
        print(
            "  ⚠️ WARNING: Clicked, but visually 'selected' class didn't appear. (Might still work)"
        )


async def click_proceed(page: Page) -> None:
    print("\n🚀 Clicking PROCEED...")

    proceed_btn = page.locator('button[data-cy="bookVisit"]')

    if await proceed_btn.is_visible() and await proceed_btn.is_enabled():
        await proceed_btn.click()
        print("  ✓ Clicked PROCEED")

        try:
            await page.wait_for_url("**/checkout**", timeout=30000)
            print("  ✓ Navigation to Checkout successful.")
        except Exception:
            print("  ⚠️ Warning: URL did not change to '/checkout' within 30s.")
    else:
        print("❌ PROCEED button found but is disabled or hidden.")
