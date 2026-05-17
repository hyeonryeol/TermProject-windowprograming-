function haversineDistance(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function distanceScore(distanceMeters, maxRadius = 3000) {
  return Math.max(0, 1 - distanceMeters / maxRadius);
}

function waitTimeScore(waitMinutes) {
  if (waitMinutes <= 5) return 1.0;
  if (waitMinutes <= 15) return 0.7;
  if (waitMinutes <= 30) return 0.4;
  return 0.1;
}

function calcRecommendScore(restaurant, userLat, userLng, sentimentAvg = 0.75) {
  const dist = haversineDistance(userLat, userLng, restaurant.location.lat, restaurant.location.lng);
  const rating = restaurant.rating / 5;
  const dScore = distanceScore(dist);
  const wScore = waitTimeScore(restaurant.waitTime);

  const score = rating * 0.4 + sentimentAvg * 0.3 + dScore * 0.2 + wScore * 0.1;

  const reasons = [];
  if (restaurant.openNow) reasons.push("현재 영업 중");
  if (restaurant.rating >= 4.3) reasons.push("리뷰 평점 높음");
  if (restaurant.waitTime <= 5) reasons.push("대기시간 짧음");
  if (restaurant.delivery) reasons.push("배달 가능");
  if (sentimentAvg >= 0.8) reasons.push("리뷰 감성 점수 우수");

  return { score: Math.round(score * 100 * 10) / 10, reasons, distance: Math.round(dist) };
}

module.exports = { haversineDistance, calcRecommendScore };
