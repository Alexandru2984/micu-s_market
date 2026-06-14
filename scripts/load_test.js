import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = (__ENV.BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const searchTerm = __ENV.SEARCH_TERM || "telefon";
const listingSlug = __ENV.LISTING_SLUG || "";

export const options = {
  scenarios: {
    browse: {
      executor: "ramping-vus",
      stages: [
        { duration: "30s", target: Number(__ENV.BROWSE_VUS || 10) },
        { duration: "1m", target: Number(__ENV.BROWSE_VUS || 10) },
        { duration: "30s", target: 0 },
      ],
      exec: "browse",
    },
    api: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.API_RATE || 20),
      timeUnit: "1s",
      duration: __ENV.API_DURATION || "2m",
      preAllocatedVUs: Number(__ENV.API_PREALLOCATED_VUS || 20),
      maxVUs: Number(__ENV.API_MAX_VUS || 80),
      exec: "api",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{surface:page}": ["p(95)<800", "p(99)<1500"],
    "http_req_duration{surface:api}": ["p(95)<500", "p(99)<1000"],
  },
};

export function browse() {
  const responses = http.batch([
    ["GET", `${baseUrl}/`, null, { tags: { surface: "page", route: "home" } }],
    ["GET", `${baseUrl}/anunturi/`, null, { tags: { surface: "page", route: "listings" } }],
    ["GET", `${baseUrl}/anunturi/?search=${encodeURIComponent(searchTerm)}`, null, { tags: { surface: "page", route: "search" } }],
  ]);

  for (const response of responses) {
    check(response, {
      "page status is 200": (r) => r.status === 200,
      "page has body": (r) => r.body && r.body.length > 200,
    });
  }

  if (listingSlug) {
    const detail = http.get(`${baseUrl}/anunt/${listingSlug}/`, {
      tags: { surface: "page", route: "listing-detail" },
    });
    check(detail, {
      "detail status is 200": (r) => r.status === 200,
    });
  }

  sleep(1);
}

export function api() {
  const response = http.get(`${baseUrl}/api/listings/?q=${encodeURIComponent(searchTerm)}&per_page=20`, {
    tags: { surface: "api", route: "api-listings" },
  });

  check(response, {
    "api status is 200": (r) => r.status === 200,
    "api returns results array": (r) => {
      try {
        return Array.isArray(r.json("results"));
      } catch (error) {
        return false;
      }
    },
  });
}
