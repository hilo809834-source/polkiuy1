"""Capture screenshots of all screens using Playwright."""
import asyncio
from playwright.async_api import async_playwright

async def capture_screens():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Desktop screenshots
        print("Capturing desktop screens...")
        desktop = await browser.new_context(viewport={'width': 1280, 'height': 800})
        desktop_page = await desktop.new_page()
        
        await desktop_page.goto('http://localhost:5000/')
        await desktop_page.screenshot(path='screenshots/01_desktop_home.png')
        
        await desktop_page.goto('http://localhost:5000/new-project')
        await desktop_page.screenshot(path='screenshots/02_desktop_new_project.png')
        
        await desktop_page.goto('http://localhost:5000/project/proj_1/questions')
        await desktop_page.screenshot(path='screenshots/03_desktop_questions.png')
        
        await desktop_page.goto('http://localhost:5000/project/proj_1')
        await desktop_page.screenshot(path='screenshots/04_desktop_workspace.png')
        
        await desktop_page.goto('http://localhost:5000/settings')
        await desktop_page.screenshot(path='screenshots/05_desktop_settings.png')
        
        await desktop_page.goto('http://localhost:5000/import/github')
        await desktop_page.screenshot(path='screenshots/06_desktop_github_import.png')
        
        await desktop.close()
        
        # Mobile screenshots
        print("Capturing mobile screens...")
        mobile = await browser.new_context(viewport={'width': 375, 'height': 812})
        mobile_page = await mobile.new_page()
        
        await mobile_page.goto('http://localhost:5001/')
        await mobile_page.screenshot(path='screenshots/07_mobile_home.png')
        
        await mobile_page.goto('http://localhost:5001/new')
        await mobile_page.screenshot(path='screenshots/08_mobile_new_idea.png')
        
        await mobile_page.goto('http://localhost:5001/project/proj_1/questions')
        await mobile_page.screenshot(path='screenshots/09_mobile_questions.png')
        
        await mobile_page.goto('http://localhost:5001/project/proj_1')
        await mobile_page.screenshot(path='screenshots/10_mobile_project.png')
        
        await mobile_page.goto('http://localhost:5001/settings')
        await mobile_page.screenshot(path='screenshots/11_mobile_settings.png')
        
        await mobile.close()
        await browser.close()
        
        print("All screenshots captured!")

if __name__ == '__main__':
    asyncio.run(capture_screens())
