const router = require("express").Router();
const https = require("https");

const NAVER_ID = process.env.NAVER_CLIENT_ID;
const NAVER_SECRET = process.env.NAVER_CLIENT_SECRET;

function httpsGet(url, headers) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.setTimeout(5000, () => { req.destroy(); reject(new Error("timeout")); });
  });
}

// GET /v1/naver/search?query=김치찌개&display=5
router.get("/search", async (req, res) => {
  if (!NAVER_ID || !NAVER_SECRET) {
    return res.status(503).json({ success: false, data: null, error: "Naver API 키가 설정되지 않았습니다." });
  }

  const query = encodeURIComponent(req.query.query || "음식점");
  const display = parseInt(req.query.display) || 5;
  const url = `https://openapi.naver.com/v1/search/local.json?query=${query}&display=${display}&sort=random`;

  try {
    const data = await httpsGet(url, {
      "X-Naver-Client-Id": NAVER_ID,
      "X-Naver-Client-Secret": NAVER_SECRET,
    });
    res.json({ success: true, data: data.items || [], error: null });
  } catch (e) {
    res.status(500).json({ success: false, data: null, error: e.message });
  }
});

module.exports = router;
