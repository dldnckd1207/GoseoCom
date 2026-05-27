const http = require('http');
const fs = require('fs');
const path = require('path');

const HOST = '127.0.0.1';
const PORT = 8787;
const MODEL = 'gemini-2.0-flash';
const ROOT = __dirname;

function loadEnv() {
  const envPath = path.join(ROOT, '.env');
  if (!fs.existsSync(envPath)) return;

  const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const index = trimmed.indexOf('=');
    if (index === -1) continue;
    const key = trimmed.slice(0, index).trim();
    const value = trimmed.slice(index + 1).trim().replace(/^["']|["']$/g, '');
    if (key && !process.env[key]) process.env[key] = value;
  }
}

function sendJson(res, status, data) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
  });
  res.end(JSON.stringify(data));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 1024 * 1024) {
        req.destroy();
        reject(new Error('요청이 너무 큽니다.'));
      }
    });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

async function handleGemini(req, res) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    sendJson(res, 500, { error: '.env 파일에 GEMINI_API_KEY를 설정해 주세요.' });
    return;
  }

  let payload;
  try {
    payload = JSON.parse(await readBody(req));
  } catch {
    sendJson(res, 400, { error: '요청 JSON을 읽을 수 없습니다.' });
    return;
  }

  const prompt = String(payload.prompt || '').trim();
  if (!prompt) {
    sendJson(res, 400, { error: 'prompt가 비어 있습니다.' });
    return;
  }

  try {
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{
          role: 'user',
          parts: [{ text: prompt }]
        }]
      })
    });

    const data = await response.json();
    if (!response.ok) {
      sendJson(res, response.status, { error: data?.error?.message || 'Gemini API 요청에 실패했습니다.' });
      return;
    }

    const text = data?.candidates?.[0]?.content?.parts?.map((part) => part.text || '').join('').trim();
    sendJson(res, 200, { text: text || '응답을 생성하지 못했습니다.' });
  } catch (error) {
    sendJson(res, 500, { error: error.message || 'Gemini 서버 연결에 실패했습니다.' });
  }
}

function serveHtml(res) {
  const filePath = path.join(ROOT, '개발중.html');
  fs.readFile(filePath, (error, html) => {
    if (error) {
      sendJson(res, 404, { error: '개발중.html을 찾을 수 없습니다.' });
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
  });
}

loadEnv();

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    sendJson(res, 204, {});
    return;
  }

  if (req.url === '/' && req.method === 'GET') {
    serveHtml(res);
    return;
  }

  if (req.url === '/api/gemini' && req.method === 'POST') {
    await handleGemini(req, res);
    return;
  }

  sendJson(res, 404, { error: '찾을 수 없는 경로입니다.' });
});

server.listen(PORT, HOST, () => {
  console.log(`AI backend running at http://${HOST}:${PORT}`);
  console.log('Open http://127.0.0.1:8787 in your browser.');
});
