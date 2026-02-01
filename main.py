import asyncio
from typing import Dict, Literal, Optional

from playwright.async_api import Page, expect

from camoufoxy import Camoufoxy
from data import generate_participants, get_fake_user_data
from fromtag import (
    click_proceed,
    click_ticket_by_title,
    select_both_tickets,
    select_time_slot,
)


class GotoOptions:
    def __init__(
        self,
        wait_until: Literal["load", "domcontentloaded", "networkidle"] = "load",
        load_timeout: int = 60000,
        selector: Optional[str] = None,
        selector_timeout: int = 60000,
    ):
        self.wait_until = wait_until
        self.load_timeout = load_timeout
        self.selector = selector
        self.selector_timeout = selector_timeout


async def goto(
    page: Page,
    url: str,
    options: Optional[GotoOptions] = None,
) -> None:
    if options is None:
        options = GotoOptions()

    await page.goto(
        url,
        wait_until=options.wait_until,  # type: ignore
        timeout=options.load_timeout,
    )

    if options.selector:
        await page.wait_for_selector(
            options.selector,
            timeout=options.selector_timeout,
        )


async def set_local_storage(page: Page, items: Dict[str, str]) -> None:
    await page.evaluate(
        """(items) => {
            for (const [key, value] of Object.entries(items)) {
                localStorage.setItem(key, value);
            }
        }""",
        items,
    )


async def fill_manager_form(page: Page):
    print("\n📝 Filling Manager Details...")
    user_data = get_fake_user_data()

    await page.locator('input[data-cy="managerSurname"]').fill(user_data["surname"])
    await page.locator('input[data-cy="managerName"]').fill(user_data["name"])

    print(f"  → Selecting Sex: {user_data['sex']}")
    await page.locator('input[data-cy="managerSex"]').click()

    await (
        page.locator(".select__list--item")
        .get_by_text(user_data["sex"], exact=True)
        .first.click()
    )

    print(f"  → Selecting Country: {user_data['country']}")
    await page.locator('input[data-cy="managerCountry"]').click()

    await (
        page.locator(".select__list--item")
        .get_by_text(user_data["country"], exact=True)
        .first.click()
    )

    await page.locator('input[data-cy="managerCity"]').fill(user_data["city"])

    print(f"  → Setting Birthdate: {user_data['birthDate']}")
    date_input = page.locator('input[data-cy="dateCalendar"]')

    await date_input.evaluate(
        """(el, date) => {
                el.removeAttribute('readonly');  // Unlock the field
                el.value = date;                 // Set value
                // Dispatch events so Angular detects the change
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
            }""",
        user_data["birthDate"],
    )

    await page.locator('input[data-cy="managerEmail"]').fill(user_data["email"])
    await page.locator('input[data-cy="managerConfirmEmail"]').fill(user_data["email"])
    await page.locator('input[data-cy="managerPhone"]').fill(user_data["phone"])

    print(f"  → Selecting Language: {user_data['language']}")
    await page.locator('input[data-cy="managerLanguage"]').click()

    await (
        page.locator(".select__list--item")
        .get_by_text(user_data["language"], exact=True)
        .click()
    )

    print("  ✓ Manager Form Filled Successfully!")


async def fill_participants_form(page: Page, participants_data: list[dict[str, str]]):
    print("\n👥 Filling Participant Details...")

    participant_blocks = page.locator(".participantElement")
    count = await participant_blocks.count()
    print(f"  → Page requires {count} participants.")

    for i in range(count):
        if i < len(participants_data):
            person = participants_data[i]
            p_name = person["name"]
            p_surname = person["surname"]
        else:
            p_name = f"Guest {i + 1}"
            p_surname = "Doe"

        surname_input = page.locator(f"#participantSurname_{i}")
        name_input = page.locator(f"#participantName_{i}")

        await surname_input.scroll_into_view_if_needed()
        await surname_input.fill(p_surname)
        await name_input.fill(p_name)

        print(f"    ✓ Filled Participant {i + 1}: {p_name} {p_surname}")

    print("  ✓ All participants filled!")


async def accept_terms_and_conditions(page: Page):
    print("\n⚖️ Accepting Terms & Conditions...")

    rules_checkbox = page.locator('mat-checkbox[data-cy="acceptChk-1"] input')
    await rules_checkbox.scroll_into_view_if_needed()
    await rules_checkbox.click()
    await asyncio.sleep(1)
    print("  → Clicked General Rules checkbox")

    close_btn = page.locator('button[data-cy="purchase-rules-close-btn"]')

    try:
        await close_btn.wait_for(state="visible", timeout=10 * 1000)
        print("  → Modal opened. Closing it...")
        await close_btn.click()
        await asyncio.sleep(1)

        await page.locator("app-purchase-rules").wait_for(state="hidden")
        print("  → Modal closed.")

    except Exception as e:
        print("  (Modal did not appear or was already closed, continuing...)", e)

    other_checkboxes = page.locator('mat-checkbox[data-cy="acceptChk-2"] input')
    count = await other_checkboxes.count()
    print(f"  → Found {count} additional terms.")

    for i in range(count):
        checkbox = other_checkboxes.nth(i)
        if not await checkbox.is_checked():
            await checkbox.click()
            await asyncio.sleep(1)
            print(f"  ✓ Checked additional term #{i + 1}")

    print("  ✓ All terms accepted.")


async def handle_turnstile(page: Page):
    print("\n🛡️ Handling Cloudflare Turnstile...")
    widget_wrapper = page.locator("ngx-turnstile")
    hidden_input = page.locator('input[name="cf-turnstile-response"]')
    try:
        await widget_wrapper.wait_for(state="visible", timeout=10000)
        await widget_wrapper.scroll_into_view_if_needed()
        print("  → Widget found.")
    except Exception as e:
        print("  ⚠️ Widget not found (might not be required).", e)
        return
    initial_val = await hidden_input.get_attribute("value")
    if initial_val:
        print("  ✅ Turnstile Auto-Solved! (Success)")
        return

    print("  → Clicking Turnstile box...")
    await asyncio.sleep(1)
    await widget_wrapper.click(force=True)
    print("  → Waiting for challenge to resolve...")
    try:
        await expect(hidden_input).not_to_have_value("", timeout=20 * 1000)
        token = await hidden_input.get_attribute("value")
        if token:
            print("  ✅ SUCCESS: Turnstile Solved!")
        else:
            print("  ❌ Failed to retrieve token.")
    except Exception as e:
        print("  ❌ Timeout: Turnstile was not solved in time.", e)


async def click_on_buy(page: Page):
    await page.click('[data-cy="buyButton"]')
    await page.wait_for_timeout(3 * 1000)


async def main() -> None:
    time_slot = "16:30"
    async with Camoufoxy() as browser:
        page = await browser.new_page()

        # async def route_handler(route):
        #     blocked_resources = ["image"]  # for now this
        #     # blocked_resources = ["image", "stylesheet", "font", "media"]
        #     if route.request.resource_type in blocked_resources:
        #         await route.abort()
        #     else:
        #         await route.continue_(
        #             headers={
        #                 **route.request.headers,
        #                 "Cache-Control": "max-age=3600",
        #             }
        #         )

        # await page.route("**/*", route_handler)
        print("Opening...")
        await page.goto("https://tickets.museivaticani.va")
        print("opened")
        await set_local_storage(page, {"lang": "en"})

        await goto(
            page,
            "https://tickets.museivaticani.va/home/fromtag/2/1772130600000/MV-Biglietti/1",
            GotoOptions(selector=".muvaTicketsContainer"),
        )

        await click_ticket_by_title(page, "Vatican Museums - Admission Ticket")
        await page.wait_for_timeout(5000)
        await select_both_tickets(page)
        print("sselect")
        await select_time_slot(page, time_slot)
        print("click_proceed")
        await click_proceed(page)
        print("fill_manager_form")
        await fill_manager_form(page)
        print("fill_participants_form")
        await fill_participants_form(page, generate_participants(2))
        print("accept_terms_and_conditions")
        await accept_terms_and_conditions(page)
        print("handle_turnstile")
        await handle_turnstile(page)
        print("click_on_buy")
        await click_on_buy(page)
        print(",,,")
        await page.wait_for_timeout(30 * 1000)
        print(page.url)


if __name__ == "__main__":
    asyncio.run(main())
