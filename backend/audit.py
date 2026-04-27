import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

results = []

# 1. Gemini / PersonaEngine
try:
    from core.persona import PersonaEngine
    pe = PersonaEngine()
    r = pe.client.models.generate_content(model='gemini-2.5-flash', contents='Say OK')
    results.append(('PersonaEngine (Gemini)', 'OK', r.text.strip()[:40]))
except Exception as e:
    results.append(('PersonaEngine (Gemini)', 'FAIL', str(e)[:80]))

# 2. BlackBook DB
try:
    from core.black_book import BlackBook
    bb = BlackBook()
    bb.execute_query('SELECT 1')
    results.append(('BlackBook (SQLite)', 'OK', 'DB accessible'))
except Exception as e:
    results.append(('BlackBook (SQLite)', 'FAIL', str(e)[:80]))

# 3. API Pool
try:
    from core.api_pool import api_pool
    status = api_pool.get_status()
    studio_keys = sum(1 for v in status.values() if v.get('studio_key'))
    results.append(('API Pool (9-account)', 'OK', str(studio_keys) + '/9 studio keys loaded'))
except Exception as e:
    results.append(('API Pool', 'FAIL', str(e)[:80]))

# 4. Google Custom Search
try:
    from core.google_search import google_search
    cse_id = os.getenv('GOOGLE_CSE_ID', '')
    label = 'OK' if cse_id else 'NO_KEY'
    results.append(('Google Custom Search', label, 'CSE_ID: ' + cse_id[:12] + '...'))
except Exception as e:
    results.append(('Google Custom Search', 'FAIL', str(e)[:80]))

# 5. Calendar OAuth token
try:
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
    label = 'OK' if creds.valid else 'EXPIRED'
    results.append(('Google Calendar OAuth', label, 'valid=' + str(creds.valid) + ' expiry=' + str(creds.expiry)))
except Exception as e:
    results.append(('Google Calendar OAuth', 'FAIL', str(e)[:80]))

# 6. CalendarSync live events
try:
    from integrations.calendar_sync import CalendarSync
    cal = CalendarSync()
    events = cal.fetch_todays_events()
    results.append(('CalendarSync (live)', 'OK', str(len(events)) + ' events today'))
except Exception as e:
    results.append(('CalendarSync (live)', 'FAIL', str(e)[:80]))

# 7. Playwright / Chromium
try:
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    b = p.chromium.launch(headless=True)
    b.close()
    p.stop()
    results.append(('Playwright/Chromium', 'OK', 'Browser launches OK'))
except Exception as e:
    results.append(('Playwright/Chromium', 'FAIL', str(e)[:80]))

# 8. Email Nexus
try:
    from core.email_nexus import email_nexus
    email_user = os.getenv('EMAIL_USER', '')
    label = 'OK' if email_user else 'NO_CREDS'
    results.append(('Email Nexus (Gmail)', label, 'EMAIL_USER=' + (email_user if email_user else 'not set')))
except Exception as e:
    results.append(('Email Nexus', 'FAIL', str(e)[:80]))

# 9. ElevenLabs Voice
try:
    key = os.getenv('ELEVEN_LABS_API_KEY', '')
    label = 'OK' if key else 'NO_KEY'
    results.append(('ElevenLabs Voice', label, 'Key present: ' + str(bool(key))))
except Exception as e:
    results.append(('ElevenLabs Voice', 'FAIL', str(e)[:80]))

# 10. Agent Runtime
try:
    from core.agent_runtime import agent_runtime
    results.append(('Agent Runtime', 'OK', 'cycles=' + str(agent_runtime.cycle_count) + ' running=' + str(agent_runtime.is_running)))
except Exception as e:
    results.append(('Agent Runtime', 'FAIL', str(e)[:80]))

# 11. Market Scanner
try:
    from core.market_scanner import market_scanner
    insights = market_scanner.get_recent_insights(days=7)
    results.append(('Market Scanner', 'OK', str(len(insights)) + ' recent insights in BlackBook'))
except Exception as e:
    results.append(('Market Scanner', 'FAIL', str(e)[:80]))

# 12. Wealth Manager
try:
    from core.wealth_manager import wealth_manager
    summary = wealth_manager.get_portfolio_summary()
    results.append(('Wealth Manager', 'OK', 'Wallets: ' + str(len(summary.get('wallets', {})))))
except Exception as e:
    results.append(('Wealth Manager', 'FAIL', str(e)[:80]))

# 13. GitHub PAT
try:
    import requests
    pat = os.getenv('GITHUB_PAT', '')
    if pat:
        r = requests.get('https://api.github.com/user', headers={'Authorization': 'token ' + pat}, timeout=8)
        login = r.json().get('login', 'unknown')
        results.append(('GitHub PAT', 'OK', 'Authenticated as: ' + login))
    else:
        results.append(('GitHub PAT', 'NO_KEY', 'Not configured'))
except Exception as e:
    results.append(('GitHub PAT', 'FAIL', str(e)[:80]))

# 14. Upwork session cookie
try:
    cookie = os.getenv('UPWORK_SESSION_COOKIE', '')
    label = 'OK' if cookie else 'NO_KEY'
    results.append(('Upwork Session Cookie', label, 'Set: ' + str(bool(cookie))))
except Exception as e:
    results.append(('Upwork Session Cookie', 'FAIL', str(e)[:80]))

# 15. LinkedIn cookie
try:
    cookie = os.getenv('LINKEDIN_LI_AT_COOKIE', '')
    label = 'OK' if cookie else 'NO_KEY'
    results.append(('LinkedIn Cookie', label, 'Set: ' + str(bool(cookie))))
except Exception as e:
    results.append(('LinkedIn Cookie', 'FAIL', str(e)[:80]))

# 16. Tool Registry
try:
    from core.tool_registry import tool_registry
    tools = list(tool_registry.tools.keys())
    results.append(('Tool Registry', 'OK', str(len(tools)) + ' tools: ' + ', '.join(tools)))
except Exception as e:
    results.append(('Tool Registry', 'FAIL', str(e)[:80]))

print()
print('=' * 80)
print('  ANDREW SYSTEM AUDIT')
print('=' * 80)
for name, status, detail in results:
    if status == 'OK':
        icon = '[OK  ]'
    elif status in ('NO_KEY', 'NO_CREDS', 'EXPIRED'):
        icon = '[WARN]'
    else:
        icon = '[FAIL]'
    print(icon + ' ' + name.ljust(28) + ' | ' + status.ljust(10) + ' | ' + detail)
print('=' * 80)

ok = sum(1 for _, s, _ in results if s == 'OK')
warn = sum(1 for _, s, _ in results if s in ('NO_KEY', 'NO_CREDS', 'EXPIRED'))
fail = sum(1 for _, s, _ in results if s == 'FAIL')
print('SUMMARY: ' + str(ok) + ' OK | ' + str(warn) + ' WARNINGS | ' + str(fail) + ' FAILURES')
print('=' * 80)
