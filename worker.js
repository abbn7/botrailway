export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    const url = new URL(request.url);
    const targetURL = "https://agentrouter.org" + url.pathname + url.search;

    const newRequest = new Request(targetURL, {
      method: request.method,
      headers: {
        "Content-Type": "application/json",
        "Authorization": request.headers.get("Authorization") || "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://agentrouter.org",
        "Referer": "https://agentrouter.org/",
        "Accept": "application/json",
      },
      body: request.method !== "GET" ? request.body : undefined,
    });

    const response = await fetch(newRequest);
    const newResponse = new Response(response.body, response);
    newResponse.headers.set("Access-Control-Allow-Origin", "*");
    return newResponse;
  },
};
