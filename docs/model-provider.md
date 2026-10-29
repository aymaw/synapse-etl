# Model transport contract

Set MODEL_BASE_URL and MODEL_NAME explicitly; MODEL_API_KEY is optional. The
transport appends `/chat/completions` to the base URL and sends JSON containing
model, temperature 0, max_tokens 2048, and system/user messages. The server must
return `choices[0].message.content` as a string containing one JSON object.
Markdown fences, arrays, missing fields, and malformed JSON are rejected.

No SDK or ambient service credentials are used. `.env.example` is a template,
not an automatically loaded file. HTTP is allowed only for literal loopback
hosts or localhost; remote endpoints require HTTPS. URL credentials, queries,
and fragments are rejected. Redirects and ambient HTTP proxies are disabled.

Requests are bounded to 64 KB, response reads to 1 MB, and timeouts to 30 seconds
by default. Transport errors omit headers, response bodies, and credentials.
There are no automatic retries. Model output remains untrusted. Only synthetic
or explicitly permitted data should be sent. No external model was used to
produce the default demonstration.
