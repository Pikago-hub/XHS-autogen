import os
import json
import asyncio
import time
from typing import Annotated
from playwright.async_api import async_playwright
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff

class RedNotePublisherAgent:
    def __init__(self, model_client):
        self.session_file = "rednote_session.json"
        self.playwright = None
        self.browser = None
        
        # Define the posting tool
        async def post_to_rednote(
            title: Annotated[str, "The post title in Chinese"],
            content: Annotated[str, "The main post content in Chinese"], 
            media_path: Annotated[str, "Path to the media file (image or video) to upload"]
        ) -> str:
            """Post content to RedNote with title, content and media (image or video)."""
            print(f"\nPOSTING TO REDNOTE...")
            print(f"   - Title: {title}")
            print(f"   - Content: {content[:100]}...")
            print(f"   - Media path: {media_path}")
            
            try:
                # Check if media file exists
                if not os.path.exists(media_path):
                    return f"Media file not found: {media_path} - WORKFLOW COMPLETE"
                
                print(f"\nStarting RedNote posting process...")
                
                # Check login status
                print(f"Checking login status...")
                if not self._is_logged_in():
                    print("No valid session found. Starting QR login...")
                    await self._qr_login_visible()
                    print("QR login completed")
                else:
                    print("Using existing session")
                
                # Post content using headless browser
                print(f"Starting headless posting...")
                result = await self._post_content_headless(title, content, media_path)
                print(f"Posting result: {result[:100]}...")
                
                # Always return a termination message to stop the workflow
                if "Success" in result:
                    return f"{result}\n\nContent posted to RedNote - WORKFLOW COMPLETE"
                else:
                    return f"{result}\n\nPosting failed - WORKFLOW COMPLETE"
                    
            except Exception as e:
                return f"Error in posting process: {str(e)} - WORKFLOW COMPLETE"
        
        # Create the agent with the tool
        self.agent = AssistantAgent(
            name="rednote_publisher",
            model_client=model_client,
            tools=[post_to_rednote],
            system_message="""You are the RedNote publisher agent. 

You ONLY post content to RedNote when you receive a message starting with "POST_APPROVED:".

When you receive "POST_APPROVED: [title]|[content]|[media_path]":
1. Parse the title, content, and media path from the message
2. Use the post_to_rednote tool to post the content
3. The tool handles login, uploading, and posting automatically

Special case - If you receive a message starting with "REGENERATE_IMAGE:" or "REGENERATE_VIDEO:", pass it along as-is to the next agent.

For any other messages, respond with "SKIP" and do nothing."""
            # No handoffs - this agent only posts when approved
        )
    
    def _is_logged_in(self) -> bool:
        """Check if we have a valid saved session"""
        if not os.path.exists(self.session_file):
            return False
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
                # Check if session has required fields
                return 'cookies' in session_data and len(session_data['cookies']) > 0
        except:
            return False
    
    async def _init_playwright(self):
        """Initialize playwright if not already done"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
    
    async def _close_playwright(self):
        """Clean up playwright"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _qr_login_visible(self):
        """Phase 1: Visible browser for QR code scanning"""
        await self._init_playwright()
        
        print("\nOpening RedNote login page...")
        
        # Launch visible browser for QR scanning
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                '--window-size=900,700',
                '--window-position=100,100'
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 900, 'height': 700},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to RedNote creator login
            print("Navigating to RedNote creator dashboard...")
            await page.goto('https://creator.xiaohongshu.com', wait_until='networkidle')
            
            # Wait a moment for page to load
            await asyncio.sleep(3)
            
            # Look for QR code or login elements
            print("Looking for QR code...")
            
            qr_selectors = [
                '.qr-code',
                '.qrcode', 
                '.login-qr',
                'canvas',
                '[class*="qr"]',
                '[class*="QR"]',
                'img[src*="qr"]'
            ]
            
            qr_found = False
            for selector in qr_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"Found QR code with selector: {selector}")
                    qr_found = True
                    break
                except:
                    continue
            
            if not qr_found:
                print("QR code not immediately visible, taking screenshot for manual inspection...")
                await page.screenshot(path='rednote_login_page.png')
                print("Screenshot saved as 'rednote_login_page.png'")
            
            print("\n" + "="*50)
            print("PLEASE SCAN THE QR CODE IN THE BROWSER WINDOW")
            print("Waiting for login (timeout: 3 minutes)...")
            print("="*50)
            
            # Wait for login success indicators
            login_selectors = [
                '.user-avatar',
                '.user-info', 
                '.profile',
                '[class*="user"]',
                '.header-user',
                '.login-success'
            ]
            
            # Wait for any login success indicator
            login_success = False
            start_time = asyncio.get_event_loop().time()
            timeout = 180  # 3 minutes
            
            while not login_success and (asyncio.get_event_loop().time() - start_time) < timeout:
                for selector in login_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        print(f"Login detected with selector: {selector}")
                        login_success = True
                        break
                    except:
                        continue
                
                if not login_success:
                    # Check if URL changed (indication of login)
                    current_url = page.url
                    if 'creator.xiaohongshu.com' in current_url and 'login' not in current_url.lower():
                        print("Login detected via URL change")
                        login_success = True
                    else:
                        await asyncio.sleep(2)
            
            if login_success:
                print("Login successful!")
                
                # Save session for future use
                print("Saving session...")
                await context.storage_state(path=self.session_file)
                print(f"Session saved to {self.session_file}")
                
            else:
                raise Exception("Login timeout - QR code not scanned within 3 minutes")
                
        except Exception as e:
            print(f"Login failed: {str(e)}")
            raise e
        finally:
            await self.browser.close()
            print("Login browser closed")
    
    async def _post_content_headless(self, title: str, content: str, media_path: str) -> str:
        """Phase 2: Headless browser for automated posting"""
        print(f"\n_post_content_headless called with:")
        print(f"   - Title: {title}")
        print(f"   - Content: {content[:50]}...")
        print(f"   - Media: {media_path}")
        
        # Determine media type
        file_ext = os.path.splitext(media_path)[1].lower()
        is_video = file_ext in ['.mp4', '.mov', '.avi', '.mkv']
        media_type = "video" if is_video else "image"
        print(f"   - Media type: {media_type}")
        
        # Make sure playwright is fresh
        if self.playwright:
            await self._close_playwright()
        
        await self._init_playwright()
        
        print("Launching fresh headless browser...")
        
        # Launch headless browser with saved session
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']  
        )
        
        context = await self.browser.new_context(
            storage_state=self.session_file,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Quick session validation test
            print("Validating session...")
            try:
                await page.goto('https://creator.xiaohongshu.com', wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(2)
                if 'login' in page.url.lower():
                    raise Exception("Session expired - need to re-login")
                print("Session is valid")
            except Exception as session_error:
                print(f"Session validation failed: {str(session_error)}")
                raise Exception("Invalid session - please run QR login again")
            # Navigate to publish page 
            publish_url = 'https://creator.xiaohongshu.com/publish/publish'
            
            print(f"Navigating to publish page (default: 上传视频)...")
            
            # Try navigation with different wait conditions if networkidle fails
            navigation_success = False
            for attempt in range(3):
                try:
                    if attempt == 0:
                        print(f"   Attempt {attempt + 1}: Using 'domcontentloaded' wait condition")
                        await page.goto(publish_url, wait_until='domcontentloaded', timeout=45000)
                    elif attempt == 1:
                        print(f"   Attempt {attempt + 1}: Using 'load' wait condition")
                        await page.goto(publish_url, wait_until='load', timeout=45000)
                    else:
                        print(f"   Attempt {attempt + 1}: Using 'commit' wait condition")
                        await page.goto(publish_url, wait_until='commit', timeout=45000)
                    
                    navigation_success = True
                    print("Page navigation successful")
                    break
                    
                except Exception as nav_error:
                    print(f"   Navigation attempt {attempt + 1} failed: {str(nav_error)[:100]}...")
                    if attempt < 2:
                        print("   Retrying with different wait condition...")
                        await asyncio.sleep(3)
                    continue
            
            if not navigation_success:
                raise Exception("Failed to navigate to publish page after 3 attempts")
            
            # Wait for page to stabilize
            await asyncio.sleep(5)
            
            current_url = page.url
            if 'login' in current_url.lower():
                raise Exception("Session expired - redirected to login page")
            
            if is_video:
                print("Using default video upload mode (上传视频) - no tab switching needed")
            else:
                print("Switching to image+text upload mode (上传图文)...")
                await asyncio.sleep(2)
                
                # Look for the 上传图文 tab in main content area
                image_tab_selectors = [
                    # Try exact text match
                    ':text("上传图文")',
                    # Try tab-like elements containing the text
                    'div:has-text("上传图文")',
                    'span:has-text("上传图文")',
                    'li:has-text("上传图文")',
                    # Try common tab CSS patterns
                    '[role="tab"]:has-text("上传图文")',
                    '[class*="tab"]:has-text("上传图文")',
                    '[class*="Tab"]:has-text("上传图文")',
                    # Try clickable elements
                    'button:has-text("上传图文")',
                    'a:has-text("上传图文")',
                    # Try partial text matches
                    ':text("图文")',
                    'div:has-text("图文")',
                    'span:has-text("图文")'
                ]
                

                await page.screenshot(path='rednote_publish_page_debug.png')
                print("Debug screenshot saved: rednote_publish_page_debug.png")
                
                try:
                    all_text_elements = await page.query_selector_all(':text("图文")')
                    print(f"Found {len(all_text_elements)} elements containing '图文'")
                    for i, element in enumerate(all_text_elements[:5]):  
                        tag_name = await element.evaluate('el => el.tagName')
                        text_content = await element.evaluate('el => el.textContent')
                        print(f"   {i+1}. <{tag_name.lower()}>{text_content}</{tag_name.lower()}>")
                except:
                    print("Could not query elements for debugging")
                
                tab_clicked = False
                for i, selector in enumerate(image_tab_selectors):
                    try:
                        print(f"Trying selector {i+1}/{len(image_tab_selectors)}: {selector}")
                        tab_element = await page.wait_for_selector(selector, timeout=3000)
                        

                        try:

                            await tab_element.click()
                            await asyncio.sleep(1)
                        except:
                            try:
                                await tab_element.evaluate('el => el.click()')
                                await asyncio.sleep(1)
                            except:
                                parent = await tab_element.evaluate('el => el.parentElement')
                                if parent:
                                    await page.evaluate('el => el.click()', parent)
                                    await asyncio.sleep(1)
                        

                        await asyncio.sleep(2)
                        

                        image_indicators = [
                            'text=选择图片',
                            'text=上传图片', 
                            '[accept*="image"]',
                            'text=添加图片'
                        ]
                        
                        tab_switched = False
                        for indicator in image_indicators:
                            try:
                                await page.wait_for_selector(indicator, timeout=2000)
                                tab_switched = True
                                break
                            except:
                                continue
                        
                        if tab_switched:
                            print("Successfully switched to 上传图文 tab (verified)")
                            tab_clicked = True
                            break
                        else:
                            print(f"   Tab element clicked but didn't switch - trying next selector")
                            continue
                            
                    except Exception as e:
                        print(f"   Selector failed: {str(e)[:50]}...")
                        continue
                
                if not tab_clicked:
                    print("Could not find 上传图文 tab, using default upload")
                    print("   Check rednote_publish_page_debug.png to see the page layout")
                    print("   Will attempt to upload image using video upload interface")
            
            # Wait for page to load after any tab switching
            print("Waiting for page to stabilize...")
            await asyncio.sleep(3)
            
            if 'login' in page.url.lower():
                raise Exception("Session expired - need to login again")
            
            if is_video:
                print(f"Uploading {media_type} via 上传视频 tab...")
            else:
                print(f"Uploading {media_type} via 上传图文 tab...")
            
            # Look for media upload input
            media_input_selectors = [
                'input[type="file"]',
                'input[accept*="video"]' if is_video else 'input[accept*="image"]',
                '[class*="upload"] input',
                '.upload-input'
            ]
            
            media_uploaded = False
            for selector in media_input_selectors:
                try:
                    upload_input = await page.wait_for_selector(selector, timeout=5000)
                    await upload_input.set_input_files(media_path)
                    print(f"{media_type.title()} upload initiated")
                    media_uploaded = True
                    break
                except:
                    continue
            
            if not media_uploaded:
                await page.screenshot(path='rednote_upload_page.png')
                raise Exception(f"Could not find {media_type} upload input")
            
            # Wait for media to process (videos take longer)
            processing_time = 10 if is_video else 5
            print(f"Waiting for {media_type} processing...")
            await asyncio.sleep(processing_time)
            
            # Fill in title
            print("Filling in title...")
            title_selectors = [
                'input[placeholder*="标题"]',
                'input[placeholder*="title"]', 
                '.title-input',
                '[class*="title"] input'
            ]
            
            title_filled = False
            for selector in title_selectors:
                try:
                    title_input = await page.wait_for_selector(selector, timeout=5000)
                    await title_input.fill(title)
                    print("Title filled")
                    title_filled = True
                    break
                except:
                    continue
            
            # Fill in content
            print("Filling in content...")
            content_selectors = [
                'textarea[placeholder*="内容"]',
                'textarea[placeholder*="content"]',
                '.content-textarea',
                '[class*="content"] textarea',
                'div[contenteditable="true"]'
            ]
            
            content_filled = False
            for selector in content_selectors:
                try:
                    content_input = await page.wait_for_selector(selector, timeout=5000)
                    await content_input.fill(content)
                    print("Content filled")
                    content_filled = True
                    break
                except:
                    continue
            
            # Look for publish button
            print("Looking for publish button...")
            publish_selectors = [
                'button[class*="publish"]',
                'button:has-text("发布")',
                'button:has-text("发表")',
                'button:has-text("提交")',
                '.publish-btn',
                '.submit-btn'
            ]
            
            # Take screenshot before publishing for debugging
            await page.screenshot(path='rednote_before_publish.png')
            
            published = False
            for selector in publish_selectors:
                try:
                    publish_btn = await page.wait_for_selector(selector, timeout=5000)
                    await publish_btn.click()
                    print("Publish button clicked")
                    published = True
                    break
                except:
                    continue
            
            if published:
                await asyncio.sleep(5)
                await page.screenshot(path='rednote_after_publish.png')
                
                return f"""Successfully posted to RedNote!

Title: {title}
Content: {content[:100]}{'...' if len(content) > 100 else ''}
{media_type.title()}: {media_path}

Screenshots saved for verification:
- rednote_before_publish.png
- rednote_after_publish.png"""
            
            else:
                await page.screenshot(path='rednote_publish_failed.png')
                return "Could not find publish button - check rednote_publish_failed.png"
                
        except Exception as e:
            await page.screenshot(path='rednote_error.png')
            return f"Posting failed: {str(e)} - check rednote_error.png"
            
        finally:
            # Small delay to ensure all operations complete
            await asyncio.sleep(2)
            if self.browser:
                await self.browser.close()
                self.browser = None
            await self._close_playwright()
            print("Headless browser closed")