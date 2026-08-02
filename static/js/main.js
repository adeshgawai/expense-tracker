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

    // Date Range Presets logic for profile page
    const dateFilterForm = document.getElementById("dateFilterForm");
    if (dateFilterForm) {
        const startDateInput = document.getElementById("start_date");
        const endDateInput = document.getElementById("end_date");
        const presetChips = document.querySelectorAll(".preset-chip");

        if (!startDateInput || !endDateInput) return;

        function formatDate(d) {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }

        presetChips.forEach(function (chip) {
            chip.addEventListener("click", function () {
                const preset = chip.getAttribute("data-preset");
                const today = new Date();

                if (preset === "this_month") {
                    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                    startDateInput.value = formatDate(firstDay);
                    endDateInput.value = formatDate(today);
                } else if (preset === "last_30") {
                    const thirtyDaysAgo = new Date();
                    thirtyDaysAgo.setDate(today.getDate() - 30);
                    startDateInput.value = formatDate(thirtyDaysAgo);
                    endDateInput.value = formatDate(today);
                } else if (preset === "this_year") {
                    const janFirst = new Date(today.getFullYear(), 0, 1);
                    startDateInput.value = formatDate(janFirst);
                    endDateInput.value = formatDate(today);
                } else if (preset === "all_time") {
                    startDateInput.value = "";
                    endDateInput.value = "";
                }

                dateFilterForm.submit();
            });
        });
    }
});
