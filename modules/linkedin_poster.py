import os

from playwright.sync_api import sync_playwright
from modules.paths import COOKIES_FILE


def _click_with_fallback(page, selectors, timeout=15000):
	"""Try selectors in order and click the first one that appears."""
	last_error = None
	for selector in selectors:
		try:
			page.wait_for_selector(selector, timeout=timeout)
			page.click(selector)
			return
		except Exception as err:
			last_error = err
	raise RuntimeError(f"Unable to find/click any selector: {selectors}") from last_error


def post_to_linkedin(post_text):
	"""
	Publish a LinkedIn post using Playwright.
	"""
	try:
		is_ci = os.getenv("GITHUB_ACTIONS", "").lower() == "true" or os.getenv("LINKEDIN_AUTONOMOUS", "").lower() == "true"
		use_saved_session = os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0

		with sync_playwright() as p:
			browser = p.chromium.launch(headless=is_ci)
			context_kwargs = {"storage_state": COOKIES_FILE} if use_saved_session else {}
			context = browser.new_context(**context_kwargs)
			page = context.new_page()
			page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")

			if not is_ci:
				input("Login to LinkedIn and press ENTER...")
				# Save local authenticated session for future automated runs.
				try:
					os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
					context.storage_state(path=COOKIES_FILE)
				except Exception:
					pass

			# Start post button with fallback selectors.
			_click_with_fallback(
				page,
				[
					'button:has-text("Start a post")',
					'span:has-text("Start a post")',
					'[aria-label*="Start a post"]',
				],
			)

			page.wait_for_selector('div[role="textbox"]', timeout=15000)
			page.click("[contenteditable='true']")
			page.keyboard.type(post_text, delay=5)

			post_button = page.locator(
				"div[role='dialog'] button.artdeco-button--primary:has-text('Post')"
			)
			post_button.wait_for(state="visible", timeout=10000)
			post_button.wait_for(state="attached")
			post_button.click()
			print("Clicked correct Post button inside modal")
			page.wait_for_timeout(5000)

			print("Post successfully published")
			context.close()
			browser.close()
			return True

	except Exception as err:
		print(f"Failed to publish LinkedIn post: {err}")
		return False
