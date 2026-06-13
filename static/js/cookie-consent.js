(function () {
  var storageKey = "micu_cookie_consent";
  var banner = document.getElementById("cookieConsent");
  var button = document.getElementById("cookieConsentAccept");

  if (!banner || !button) {
    return;
  }

  try {
    if (window.localStorage.getItem(storageKey) === "accepted") {
      return;
    }
  } catch (error) {
    return;
  }

  banner.hidden = false;

  button.addEventListener("click", function () {
    try {
      window.localStorage.setItem(storageKey, "accepted");
    } catch (error) {
      // Consent UI is best-effort when storage is unavailable.
    }
    banner.hidden = true;
  });
})();
