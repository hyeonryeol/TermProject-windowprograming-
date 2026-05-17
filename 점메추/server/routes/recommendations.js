const router = require("express").Router();
const { restaurants, reviews } = require("../data/mock");
const { haversineDistance, calcRecommendScore } = require("../services/scoring");

router.get("/", (req, res) => {
  const { lat, lng, radius = 3000, delivery, time } = req.query;

  if (!lat || !lng) {
    return res.status(400).json({ success: false, data: null, error: "lat, lng는 필수 파라미터입니다." });
  }

  const userLat = parseFloat(lat);
  const userLng = parseFloat(lng);
  const maxRadius = parseInt(radius);

  let candidates = restaurants.filter((r) => {
    const dist = haversineDistance(userLat, userLng, r.location.lat, r.location.lng);
    return dist <= maxRadius && r.openNow;
  });

  if (delivery === "true") candidates = candidates.filter((r) => r.delivery);

  const results = candidates.map((r) => {
    const restaurantReviews = reviews[r.id] || [];
    const sentimentAvg = restaurantReviews.length
      ? restaurantReviews.reduce((sum, rv) => sum + (rv.sentimentScore || 0.75), 0) / restaurantReviews.length
      : 0.75;

    const { score, reasons } = calcRecommendScore(r, userLat, userLng, sentimentAvg);
    return { restaurantId: r.id, score, reason: reasons };
  });

  results.sort((a, b) => b.score - a.score);

  res.json({ success: true, data: results, error: null });
});

module.exports = router;
