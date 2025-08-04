# Cloud Selenium browser exposed through Python + FastAPI

Supporting:
1. Get URL HTML after page finished loading everything + JS
2. Passing headers and cookies through JSON payload
3. Stealth browser
4. Proxy (for headers and cookies) + HTTPS support

Docker image: https://hub.docker.com/r/pedroegg/cloud-selenium

## Usage

1. Run `make run-docker` to run with docker (no other actions needed).
2. Do POST requests to `http://127.0.0.1:8000/browser/html` passing the `url` (required), `timeout` (optional), `stealth` (optional), `headers` (optional) and `cookies` (optional) data through JSON body.

Example of JSON body:
```json
{
	"url": "https://www.tiktok.com",
	"timeout": 15,
	"stealth": true,
	"headers": {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
		"Accept-Language": "en-US,en;q=0.9"
	},
	"cookies": {
		"xf_csrf": "1jzOZZ7YpMu46XNP"
	}
}
```

- `url`: The website you want to access.
- `timeout`: Max timeout in seconds for the request to answer (stopping the page loading wait if needed).
- `stealth`: Use `true` for enabling the stealth mode browser, and `false` (or not passing this field) to disable it.
- `headers`: The HTTP headers you want to send for the request. Use it for `Authorization`, `User-Agent` and this kind of stuff.
- `cookies`: The HTTP cookies you want to send.

## Running locally:

1. Run `make install` to install poetry and all the dependecies needed. Ensure you already have the correct python version needed (currently >= 3.11).
2. Then, run `make run-dev` to run it locally.
