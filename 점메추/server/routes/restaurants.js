const router = require("express").Router();
const https = require("https");
const { restaurants } = require("../data/mock");
const { haversineDistance, calcRecommendScore } = require("../services/scoring");

const KAKAO_KEY = process.env.KAKAO_REST_API_KEY;

// ── Kakao ────────────────────────────────────────────────
const KAKAO_CAT_MAP = [
  ["한식", "korean"], ["일식", "japanese"], ["중식", "chinese"],
  ["양식", "western"], ["패스트푸드", "western"], ["치킨", "korean"],
  ["분식", "korean"], ["카페", "korean"],
];

function mapKakaoCategory(name) {
  for (const [key, val] of KAKAO_CAT_MAP) {
    if (name.includes(key)) return val;
  }
  return "korean";
}

function httpsGet(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers }, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    });
    req.on("error", reject);
    req.setTimeout(8000, () => { req.destroy(); reject(new Error("timeout")); });
  });
}

async function fetchKakao(lat, lng, radius) {
  const url = `https://dapi.kakao.com/v2/local/search/category.json?category_group_code=FD6&x=${lng}&y=${lat}&radius=${radius}&sort=distance&size=15`;
  const data = await httpsGet(url, { Authorization: `KakaoAK ${KAKAO_KEY}` });
  return (data.documents || []).map((p) => {
    const dist = parseInt(p.distance) || 0;
    return {
      id: `kakao_${p.id}`,
      name: p.place_name,
      category: mapKakaoCategory(p.category_name || ""),
      priceRange: "medium",
      address: p.road_address_name || p.address_name,
      phone: p.phone || "-",
      location: { lat: parseFloat(p.y), lng: parseFloat(p.x) },
      distance: dist,
      rating: 4.0, reviewCount: 0, openNow: true, delivery: false,
      reservation: false, capacity: "medium", waitTime: 0,
      estimatedDeliveryTime: null, menus: [],
      sources: { kakao: 4.0 },
      reasons: ["카카오 검색 결과"],
      score: Math.round((4.0/5*0.4 + 0.75*0.3 + Math.max(0, 1-dist/5000)*0.2 + 1.0*0.1)*1000)/10,
      placeUrl: p.place_url,
    };
  });
}

// ── OpenStreetMap Overpass (키 불필요) ─────────────────────
const OSM_CUISINE_MAP = [
  [["korean", "korean_bbq", "bibimbap", "jjigae"], "korean"],
  [["japanese", "sushi", "ramen", "udon", "tempura", "izakaya"], "japanese"],
  [["chinese", "dim_sum", "noodle"], "chinese"],
  [["pizza", "burger", "italian", "american", "western", "sandwich", "steak", "pasta"], "western"],
  [["chicken", "fried_chicken"], "korean"],
];

function mapOSMCuisine(cuisine = "", amenity = "") {
  const c = cuisine.toLowerCase();
  for (const [keys, val] of OSM_CUISINE_MAP) {
    if (keys.some((k) => c.includes(k))) return val;
  }
  if (amenity === "fast_food") return "western";
  return "korean";
}

function httpsPost(hostname, path, body) {
  return new Promise((resolve, reject) => {
    const buf = Buffer.from(body);
    const req = https.request(
      { hostname, path, method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded", "Content-Length": buf.length } },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
      }
    );
    req.on("error", reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error("timeout")); });
    req.write(buf);
    req.end();
  });
}

async function fetchOSM(lat, lng, radius) {
  const query =
    `[out:json][timeout:15];` +
    `(node["amenity"~"restaurant|fast_food|food_court"](around:${radius},${lat},${lng});` +
    ` way["amenity"~"restaurant|fast_food|food_court"](around:${radius},${lat},${lng}););` +
    `out body center;`;

  const data = await httpsPost("overpass-api.de", "/api/interpreter", `data=${encodeURIComponent(query)}`);

  return (data.elements || [])
    .filter((e) => e.tags && e.tags.name)
    .map((e) => {
      const elat = e.lat ?? e.center?.lat ?? lat;
      const elng = e.lon ?? e.center?.lon ?? lng;
      const dist = Math.round(haversineDistance(lat, lng, elat, elng));
      const tags = e.tags;
      const category = mapOSMCuisine(tags.cuisine || "", tags.amenity || "");
      const score = Math.round((4.0/5*0.4 + 0.75*0.3 + Math.max(0, 1-dist/5000)*0.2 + 1.0*0.1)*1000)/10;
      return {
        id: `osm_${e.id}`,
        name: tags.name,
        category,
        priceRange: "medium",
        address: tags["addr:full"] || tags["addr:street"] || "-",
        phone: tags.phone || tags["contact:phone"] || "-",
        location: { lat: elat, lng: elng },
        distance: dist,
        rating: 4.0, reviewCount: 0, openNow: true, delivery: false,
        reservation: false, capacity: "medium", waitTime: 0,
        estimatedDeliveryTime: null, menus: [],
        sources: {},
        reasons: ["OpenStreetMap 검색 결과"],
        score,
        placeUrl: `https://www.openstreetmap.org/${e.type}/${e.id}`,
      };
    });
}

// ── Mock 폴백 ─────────────────────────────────────────────
function getMock(userLat, userLng, maxRadius) {
  return restaurants
    .map((r) => {
      const { score, reasons, distance } = calcRecommendScore(r, userLat, userLng);
      return { ...r, distance, score, reasons };
    })
    .filter((r) => r.distance <= maxRadius);
}

// ── 라우트 ────────────────────────────────────────────────
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
    try { result = await fetchKakao(userLat, userLng, maxRadius); }
    catch (e) { console.error("Kakao 오류:", e.message); result = null; }
  }
  if (!result) {
    try { result = await fetchOSM(userLat, userLng, maxRadius); }
    catch (e) { console.error("OSM 오류:", e.message); result = getMock(userLat, userLng, maxRadius); }
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
