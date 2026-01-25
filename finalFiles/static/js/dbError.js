// Add an event listener to the "Retry" form on the database error page
document.getElementById("retryForm").addEventListener("submit", async function (event) {
    // Prevent the default form submission behavior (page reload)
    event.preventDefault();

    // Send a POST request to the server to reset or update the flags for database setup
    await fetch("/updateFlags", {
        method: "POST"
    });

    // After updating the flags, redirect the user back to the main page or login
    window.location.href = "/";
});