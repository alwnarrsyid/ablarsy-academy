// Capture referral code from URL parameter and store in localStorage
// This runs on every page load to ensure referral code is captured
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const refFromUrl = urlParams.get("ref");
    if (refFromUrl) {
        localStorage.setItem("lms_referral_code", refFromUrl);
        console.log("Referral code captured:", refFromUrl);
    }
})();
