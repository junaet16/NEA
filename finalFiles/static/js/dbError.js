document.getElementById("retryForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    await fetch("/updateFlags", {
        method: "POST"
    });

    window.location.href = "/";
});