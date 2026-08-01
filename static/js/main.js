document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss flash alert messages after 3 seconds
    const flashAlerts = document.querySelectorAll(".flash-alert");
    if (flashAlerts.length > 0) {
        setTimeout(function () {
            flashAlerts.forEach(function (alert) {
                alert.classList.add("fade-out");
                setTimeout(function () {
                    alert.remove();
                }, 500);
            });
        }, 3000);
    }
});
