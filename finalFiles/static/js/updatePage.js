document.addEventListener("DOMContentLoaded", () => {

    /* Load Default Values*/
    const loadDefaultBtn = document.querySelector('button[name="loadDefault"]');
    if (loadDefaultBtn) {
        loadDefaultBtn.addEventListener("click", async () => {
            const response = await fetch("/load_default_parameters");
            const data = await response.json();

            document.getElementById("param1").value = data.CHANGING_TIME;
            document.getElementById("param2").value = data.MAX_TIME_WINDOW;
            document.getElementById("param3").value = data.rawArrivalPeakOffset;
            document.getElementById("param4").value = data.rawDeparturePeakOffset;
            document.getElementById("param5").value = data.ATTENDANCE;
            document.getElementById("param6").value = data.TRAIN_PROPORTION;
            document.getElementById("param7").value = data.SIGMA_FACTOR;
            document.getElementById("param8").value = data.MINIMUM_PEOPLE;
            document.getElementById("param9").value = data.PERSON_DELAY;
            document.getElementById("param10").value = data.PROPAGATION_FACTOR;
            document.getElementById("param11").value = data.WALKING_TIME;
            document.getElementById("param12").value = data.WALKING_SPEED;
            document.getElementById("param13").value = data.NORMAL;
            document.getElementById("param14").value = data.SLIGHTLY;
            document.getElementById("param15").value = data.BUSY;
        });
    }


    /* Save Parameters */
    const saveBtn = document.querySelector('button[name="save"]');
    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {

            const payload = {
                CHANGING_TIME: document.getElementById("param1").value,
                MAX_TIME_WINDOW: document.getElementById("param2").value,
                rawArrivalPeakOffset: document.getElementById("param3").value,
                rawDeparturePeakOffset: document.getElementById("param4").value,
                ATTENDANCE: document.getElementById("param5").value,
                TRAIN_PROPORTION: document.getElementById("param6").value,
                SIGMA_FACTOR: document.getElementById("param7").value,
                MINIMUM_PEOPLE: document.getElementById("param8").value,
                PERSON_DELAY: document.getElementById("param9").value,
                PROPAGATION_FACTOR: document.getElementById("param10").value,
                WALKING_TIME: document.getElementById("param11").value,
                WALKING_SPEED: document.getElementById("param12").value,
                NORMAL: document.getElementById("param13").value,
                SLIGHTLY: document.getElementById("param14").value,
                BUSY: document.getElementById("param15").value
            };

            fetch("/save_parameters", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            window.location.href = "/main"
        });
    }


    const logoutBtn = document.querySelector('button[name="logOut"]');
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            await fetch("/logout", {
                method: "POST"
            });
            window.location.href = "/";  // Redirect to login page
        });
    }


    const fetchNewDataBtn = document.querySelector('button[name="new"]');
    if (fetchNewDataBtn) {
        fetchNewDataBtn.addEventListener("click", async () => {
            const response = await fetch("/fetch_new_data", {
                method: "POST"
            });
            if (response.redirected) {
                window.location.href = response.url;
            }
        });
    }



    /* Numeric only enforcement */
    document.querySelectorAll('input[type="number"]').forEach(input => {
        // Block e, E, +, -
        input.addEventListener("keydown", e => {
            if (["e", "E", "+", "-"].includes(e.key)) {
                e.preventDefault();
            }
        });

        // Clean pasted input
        input.addEventListener("input", () => {
            input.value = input.value.replace(/[^0-9.]/g, "");
        });
    });
});
