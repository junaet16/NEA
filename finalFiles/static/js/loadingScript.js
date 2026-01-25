// Continuously checks the status of the database creation process
function checkFlag() {

    // Send a request to the backend to check the current database status
    fetch('/check_flag')
        .then(r => r.json())
        .then(data => {

            // If database creation was successful
            if (data.status === "success") {
                // Redirect the user back to the page they were on before loading
                window.location.href = data.previousPage;
            }

            // If database creation failed
            else if (data.status === "failed") {
                // Store the error message in sessionStorage so it can be accessed on the error page
                sessionStorage.setItem("db_error", data.error);

                // Redirect the user to the database error page
                window.location.href = "/db_error";
            }

            // If database creation is still in progress
            else {
                // Wait 2 seconds before checking again
                setTimeout(checkFlag, 2000);
            }
        });
}

// Start checking the database status once the page has fully loaded
window.onload = checkFlag;
