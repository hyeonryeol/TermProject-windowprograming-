const router = require("express").Router();
const https = require("https");
const { restaurants } = require("../data/mock");
const { haversineDistance, calcRecommendScore } = require("../services/scoring");

const KAKAO_KEY = process.env.KAKAO_REST_API_KEY;

const KAKAO_CAT_MAP = [
  ["한식", "korean"], ["일식", "japanese"], ["중식", "chinese"],
  ["양식", "western"], ["패스트푸드", "western"], ["치킨", "korean"],
  ["분식", "korean"], ["카페", "korean"],
];

function mapKakaoCategory(categoryName) {
  for (const [key, val] of KAKAO_CAT_MAP) {
    if (categoryName.includes(key)) return val;
  }
  return "korean";
}

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

async function fetchKakaoRestaurants(lat, lng, radius) {
  const url = `https://dapi.kakao.com/v2/local/search/category.json?category_group_code=FD6&x=${lng}&y=${lat}&radius=${radius}&sort=distance&size=15`;
  const data = await httpsGet(url, { Authorization: `KakaoAK ${KAKAO_KEY}` });
  return (data.documents || []).map((p) => {
    const dist = parseInt(p.distance) || 0;
    const category = mapKakaoCategory(p.category_name || "");
    return {
      id: `kakao_${p.id}`,
      name: p.place_name,
      category,
      priceRange: "medium",
      address: p.road_address_name || p.address_name,
      phone: p.phone || "-",
      location: { lat: parseFloat(p.y), lng: parseFloat(p.x) },
      distance: dist,
      rating: 4.0,
      reviewCount: 0,
      openNow: true,
      delivery: false,
      reservation: false,
      capacity: "medium",
      waitTime: 0,
      estimatedDeliveryTime: null,
      menus: [],
      sources: { kakao: 4.0 },
      reasons: ["카카오 검색 결과"],
      score: Math.round((4.0 / 5 * 0.4 + 0.75 * 0.3 + Math.max(0, 1 - dist / 5000) * 0.2 + 1.0 * 0.1) * 1000) / 10,
      placeUrl: p.place_url,
    };
  });
}

function getMockResult(userLat, userLng, maxRadius) {
  return restaurants
    .map((r) => {
      const { score, reasons, distance } = calcRecommendScore(r, userLat, userLng);
      return { ...r, distance, score, reasons };
    })
    .filter((r) => r.distance <= maxRadius);
}

router.get("/", async (req, res) => {
  const { lat, lng, radius = 3000, openNow, delivery, category, sort = "score", priceRange } = req.query;

  if (!lat || !lng) {
    return res.status(400).json({ success: false, data: null, error: "lat, lng는 필수 파라미터입니다." });
  }

  const userLat = parseFloat(lat);
  const userLng = parseFloat(lng);
  const maxRadius = parseInt(radius);

  let result;
  if (KAKAO_KEY) {
    try {
      result = await fetchKakaoRestaurants(userLat, userLng, maxRadius);
    } catch (e) {
      console.error("Kakao API 오류:", e.message, "→ 샘플 데이터 사용");
      result = getMockResult(userLat, userLng, maxRadius);
    }
  } else {
    result = getMockResult(userLat, userLng, maxRadius);
  }

  if (openNow === "true") result = result.filter((r) => r.openNow);
  if (delivery === "true") result = result.filter((r) => r.delivery);
  if (category) result = result.filter((r) => r.category === category);
  if (priceRange) result = result.filter((r) => r.priceRange === priceRange);

  const sortFn = {
    score: (a, b) => b.score - a.score,
    rating: (a, b) => b.rating - a.rating,
    distance: (a, b) => a.distance - b.distance,
    waitTime: (a, b) => a.waitTime - b.waitTime,
  };
  result.sort(sortFn[sort] || sortFn.score);

  res.json({ success: true, data: result, error: null });
});

router.get("/:id", (req, res) => {
  const restaurant = restaurants.find((r) => r.id === req.params.id);
  if (!restaurant) {
    return res.status(404).json({ success: false, data: null, error: "음식점을 찾을 수 없습니다." });
  }
  const { password, ...data } = restaurant;
  res.json({ success: true, data, error: null });
});

module.exports = router;
