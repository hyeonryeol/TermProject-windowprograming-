const router = require("express").Router();
const { restaurants } = require("../data/mock");
const { haversineDistance } = require("../services/scoring");

router.get("/", (req, res) => {
  const { lat, lng, radius = 3000, openNow, delivery, category, sort = "rating", priceRange } = req.query;

  if (!lat || !lng) {
    return res.status(400).json({ success: false, data: null, error: "lat, lng는 필수 파라미터입니다." });
  }

  const userLat = parseFloat(lat);
  const userLng = parseFloat(lng);
  const maxRadius = parseInt(radius);

  let result = restaurants
    .map((r) => ({
      ...r,
      distance: Math.round(haversineDistance(userLat, userLng, r.location.lat, r.location.lng)),
    }))
    .filter((r) => r.distance <= maxRadius);

  if (openNow === "true") result = result.filter((r) => r.openNow);
  if (delivery === "true") result = result.filter((r) => r.delivery);
  if (category) result = result.filter((r) => r.category === category);
  if (priceRange) result = result.filter((r) => r.priceRange === priceRange);

  const sortMap = {
    rating: (a, b) => b.rating - a.rating,
    distance: (a, b) => a.distance - b.distance,
    popularity: (a, b) => b.reviewCount - a.reviewCount,
    waitTime: (a, b) => a.waitTime - b.waitTime,
  };
  result.sort(sortMap[sort] || sortMap.rating);

  res.json({
    success: true,
    data: result.map(({ id, name, location, distance, rating, reviewCount, openNow, delivery, estimatedDeliveryTime, waitTime, category }) => ({
      id, name, location, distance, rating, reviewCount, openNow, delivery, estimatedTime: estimatedDeliveryTime, waitTime, category,
    })),
    error: null,
  });
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
