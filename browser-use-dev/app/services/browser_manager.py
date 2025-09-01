import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import asyncio
import aiohttp
 
from browser_use.agent.service import Agent, Controller 
from browser_use.browser.types import async_playwright
from browser_use.agent.views import ActionResult
from browser_use.browser import BrowserSession
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.google.chat import ChatGoogle
from app.utility.local_storage import save_agent_history_to_local
from browser_use.llm.deepseek.chat import ChatDeepSeek

# Set up logging
logger = logging.getLogger(__name__)

 
BROWSERS = {}
CONTEXTS = {}
SESSION_PAGES={}
AGENTS ={}
USER_DATA_DIR_BASE = "/app/tmp/browser_profiles"
playwright = None
extension_path = "/app/extensions/capsolver"
controller= Controller()

# HIL_WEBHOOK_URL = "http://host.docker.internal:5678/webhook-test/65853ebc-c934-43a7-9297-f16ea7e7c285"
# HIL_WAIT_SECONDS = 180  # 3 minutes



# @controller.action("Trigger human review: notify webhook and wait")
# async def trigger_human_review(
#     question_text: str,
#     session_id: str,
#     browser_session: BrowserSession,
#     vnc_url: str | None = None,
# ):
#     """
#     Notify the HIL webhook via GET (no payload) and then wait before resuming.
#     """
#     warn = None

#     # 1) Fire webhook (GET, no payload)
#     try:
#         logger.info(f"[HIL] Notifying webhook via GET: {HIL_WEBHOOK_URL}")
#         timeout = aiohttp.ClientTimeout(total=15)
#         async with aiohttp.ClientSession(timeout=timeout) as client:
#             # No payload, no params — per requirement
#             resp = await client.get(HIL_WEBHOOK_URL)
#             text = await resp.text()
#             logger.info(
#                 f"[HIL] Webhook GET -> {HIL_WEBHOOK_URL} "
#                 f"status={resp.status} body={text[:500]}"
#             )
#             if resp.status // 100 != 2:
#                 warn = f"Webhook returned HTTP {resp.status}. Proceeding to wait anyway."
#     except Exception as e:
#         logger.exception(f"[HIL] Webhook GET failed: {e}")
#         warn = f"Webhook call failed: {e}. Proceeding to wait anyway."

#     # 2) Wait
#     try:
#         await asyncio.sleep(HIL_WAIT_SECONDS)
#     except asyncio.CancelledError:
#         msg = "Human-in-the-loop wait was cancelled."
#         logger.info(f"[HIL] {msg}")

#         return ActionResult(error=msg)

#     # 3) Resume
#     msg = (
#         f"Human-in-the-loop notified via GET; waited {HIL_WAIT_SECONDS} seconds and resuming."
#         + (f" Note: {warn}" if warn else "")
#     )
#     logger.info(f"[HIL] {msg}")
#     return ActionResult(extracted_content=msg, include_in_memory=True)

@controller.action('Upload file to interactive element with file path')
async def upload_file(index: int, path: str, browser_session: BrowserSession, available_file_paths: list[str]):
    # Allow files in the available_file_paths list OR files created by the agent in its temp directory
    is_allowed_file = (
        path in available_file_paths or
        'browser_use_agent_' in path or
        'browseruse_agent_data' in path or
        path.endswith('.txt') or
        path.endswith('.pdf')
    )

    # Resolve absolute path
    absolute_path = path
    if not os.path.isabs(path):
        possible_paths = [
            f'/app/{path}',
            f'/app/tmp/{path}',
            f'/tmp/{path}',
            os.path.join('/app', path)
        ]
        for possible_path in possible_paths:
            if os.path.exists(possible_path):
                absolute_path = possible_path
                break
        else:
            absolute_path = f'/app/tmp/{path}'
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, 'w') as f:
                if path.endswith('.pdf'):
                    f.write('%PDF-1.4 dummy pdf\n%%EOF')
                else:
                    f.write(f'Test file content for {path}')

    logger.info(f"Upload attempt - Path: {path}, Absolute path: {absolute_path}, Is allowed: {is_allowed_file}, Exists: {os.path.exists(absolute_path)}")

    if not is_allowed_file:
        return ActionResult(error=f'File path {path} is not available. Available paths: {available_file_paths}')
    if not os.path.exists(absolute_path):
        return ActionResult(error=f'File {absolute_path} does not exist')

    try:
        dom_element = await browser_session.get_dom_element_by_index(index)
        if dom_element is None:
            return ActionResult(error=f'No element found at index {index}')

        page = await browser_session.get_current_page()

        # ✅ If it's not a file input, try to find one inside or next to it
        if dom_element.tag_name.lower() != 'input' or dom_element.attributes.get('type') != 'file':
            logger.info(f'Index {index} is {dom_element.tag_name}, not <input type=file>. Searching for nested/sibling file input...')
            try:
                # Try: input inside the same label/div
                locator = page.locator(f'xpath=(.//input[@type="file"])[1]').locator(f'xpath=ancestor::*[{index}]')
            except Exception:
                # Fallback: just grab the first file input on the page
                locator = page.locator('input[type="file"]').first
        else:
            # It is a file input, build locator directly
            if dom_element.attributes.get('id'):
                locator = page.locator(f'#{dom_element.attributes["id"]}')
            elif dom_element.attributes.get('name'):
                locator = page.locator(f'input[name="{dom_element.attributes["name"]}"]')
            else:
                locator = page.locator('input[type="file"]').first

        await locator.set_input_files(absolute_path, timeout=60000)

        msg = f'Successfully uploaded file {absolute_path} (resolved index {index})'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        msg = f'Failed to upload file to index {index}: {str(e)}'
        logger.exception(msg)
        return ActionResult(error=msg)


async def setup_browser_for_session(session_id:str,display:str):
    global playwright
    if playwright is None:
        playwright = await  async_playwright().start()
    if session_id not in BROWSERS:
        profile_dir = os.path.join(USER_DATA_DIR_BASE, session_id)
        Path(profile_dir).mkdir(parents=True, exist_ok=True)
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=[
                "--no-sandbox",
                f"--display={display}",
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}"
            ]
        )
 
        BROWSERS[session_id] = context.browser  # context.browser is the actual browser instance
        CONTEXTS[session_id] = context
    return CONTEXTS[session_id]
 
 
async def run_task(task: str, session_id: str, display: str):
    """
    Run the task in the browser for the given session and store screenshots to MongoDB.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY environment variable not set.")

        # Launch browser and page
        context = await setup_browser_for_session(session_id, display)
        page = await context.new_page()
        await page.bring_to_front()
        SESSION_PAGES[session_id] = page
        available_file_paths = ['/app/tmp/dummy_upload_file.pdf']
        extended_prompt ="""
        You are a browser automation agent that interacts with websites like a human.
        ...
        IMPORTANT: If a CAPTCHA is detected (e.g., reCAPTCHA, hCaptcha), do not interact with it manually.
        Instead, wait for 5–10 seconds. A browser extension will solve it automatically in the background.
        Once it's solved, continue as normal.

		if a file upload is required or "Add Attachments", "Add files" is detected, use the `Upload file to interactive element with file path` action with the file path.
		if a file path is available in prompt  then use that as available_file_paths otherwise the default given in available_file_paths

         
        """
        # Use container-appropriate paths, not Windows paths
       
        for file_path in available_file_paths:
              if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    # Create a simple PDF file (the agent will treat it as a test file)
                    with open(file_path, 'w') as f:
                        f.write('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n301\n%%EOF')



        # Run agent
        agent = Agent(
            task=task,
            
             llm=ChatGoogle(api_key=api_key,model="gemini-2.5-pro",temperature=0.5),
         
            page=page,
            extend_system_message=extended_prompt,
            controller=controller,
            custom_context={'available_file_paths': available_file_paths,'request_description': 'example_request_id' + str(os.getpid())},
 

 
        )
        AGENTS[session_id] = agent
        result_agent = await agent.run()
        save_agent_history_to_local(agent, session_id)
        return {"result":result_agent}
 
    except Exception as e:
        logging.error(f"❌ run_task() failed for session {session_id}: {str(e)}")
        raise
def get_page(session_id: str):
    """
    Get the page object for the given session ID.
    """
    if session_id in SESSION_PAGES:
        return SESSION_PAGES[session_id]
    else:
        raise ValueError(f"No page found for session ID: {session_id}")
 
 
def get_status(session_id: str):
    """
    Get the status of the session.
    """
 
    if session_id in AGENTS:
        agent = AGENTS[session_id]
        if agent.state.stopped :
            return "stopped"
        elif agent.state.paused:
            return "paused"
        elif hasattr(agent,"_task") and agent._task and agent._task.done():
            return "completed"
        return "running"
    else:
        raise ValueError(f"No agent found for session ID: {session_id}")