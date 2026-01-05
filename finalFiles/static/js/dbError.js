document.getElementById("retryForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent immediate form submission

    const messageEl = document.getElementById("message");
    messageEl.innerText = "Redirecting to login page in 3 seconds";

    setTimeout(() => {
        // Navigate to the login page
        window.location.href = "/";
    }, 3000); // 3 seconds
});